"""loglens count コマンドの現在の動作を固定するテスト。"""

import pytest

from loglens import main

SAMPLE_LINES = [
    "2026-07-18 09:12:03 INFO Server started on port 8080",
    "2026-07-18 09:12:05 WARN Disk usage at 85%",
    "2026-07-18 09:12:07 ERROR Connection refused",
    "",
    "Traceback (most recent call last):",
    '  File "app.py", line 10, in <module>',
    "2026-07-18 09:12:09 ERROR Timeout waiting for response",
    "   ",
    "2026-07-18 09:12:11 INFO Retry succeeded",
]


@pytest.fixture
def logfile(tmp_path):
    path = tmp_path / "app.log"
    path.write_text("\n".join(SAMPLE_LINES) + "\n", encoding="utf-8")
    return path


def run_count(path, capsys):
    rc = main(["count", str(path)])
    captured = capsys.readouterr()
    return rc, captured


def parse_output(stdout):
    """出力の各行を {ラベル: 件数} の辞書にする。"""
    result = {}
    for line in stdout.splitlines():
        label, value = line.split()
        result[label] = int(value)
    return result


def test_count_levels(logfile, capsys):
    rc, captured = run_count(logfile, capsys)
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 2
    assert counts["WARN"] == 1
    assert counts["INFO"] == 2
    assert counts["OTHER"] == 2


def test_total_matches_non_blank_lines(logfile, capsys):
    rc, captured = run_count(logfile, capsys)
    assert rc == 0
    counts = parse_output(captured.out)
    non_blank = sum(1 for line in SAMPLE_LINES if line.strip())
    assert counts["TOTAL"] == non_blank
    assert counts["TOTAL"] == (
        counts["ERROR"] + counts["WARN"] + counts["INFO"] + counts["OTHER"]
    )


def test_output_format(logfile, capsys):
    rc, captured = run_count(logfile, capsys)
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 2",
        "WARN  1",
        "INFO  2",
        "OTHER 2",
        "TOTAL 7",
    ]


def test_missing_file_returns_1(tmp_path, capsys):
    missing = tmp_path / "no_such.log"
    rc = main(["count", str(missing)])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err.startswith("error:")
    assert captured.out == ""


@pytest.mark.parametrize(
    "level,expected",
    [("ERROR", 2), ("WARN", 1), ("INFO", 2), ("OTHER", 2)],
)
def test_level_option_shows_single_line(logfile, capsys, level, expected):
    rc = main(["count", str(logfile), "--level", level])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == f"{level} {expected}\n"


def test_level_option_zero_count(tmp_path, capsys):
    path = tmp_path / "info_only.log"
    path.write_text(
        "2026-07-18 09:12:03 INFO Server started on port 8080\n",
        encoding="utf-8",
    )
    rc = main(["count", str(path), "--level", "ERROR"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "ERROR 0\n"


def test_level_option_rejects_unknown_level(logfile, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["count", str(logfile), "--level", "DEBUG"])
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert captured.out == ""


def test_since_until_range_inclusive(logfile, capsys):
    rc = main(["count", str(logfile), "--since", "09:12:05", "--until", "09:12:09"])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 2  # 09:12:07 と 09:12:09（両端を含む）
    assert counts["WARN"] == 1   # 09:12:05
    assert counts["INFO"] == 0
    assert counts["OTHER"] == 0  # 時刻を持たない行は除外
    assert counts["TOTAL"] == 3


def test_since_only(logfile, capsys):
    rc = main(["count", str(logfile), "--since", "09:12:09"])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 1  # 09:12:09
    assert counts["WARN"] == 0
    assert counts["INFO"] == 1   # 09:12:11
    assert counts["OTHER"] == 0
    assert counts["TOTAL"] == 2


def test_until_only(logfile, capsys):
    rc = main(["count", str(logfile), "--until", "09:12:05"])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 0
    assert counts["WARN"] == 1   # 09:12:05
    assert counts["INFO"] == 1   # 09:12:03
    assert counts["OTHER"] == 0
    assert counts["TOTAL"] == 2


def test_time_range_with_level(logfile, capsys):
    rc = main(
        [
            "count",
            str(logfile),
            "--since",
            "09:12:05",
            "--until",
            "09:12:09",
            "--level",
            "ERROR",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "ERROR 2\n"


def test_time_range_excludes_other_even_with_level(logfile, capsys):
    rc = main(["count", str(logfile), "--since", "09:12:00", "--level", "OTHER"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "OTHER 0\n"


def test_no_time_options_keeps_other(logfile, capsys):
    rc, captured = run_count(logfile, capsys)
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["OTHER"] == 2

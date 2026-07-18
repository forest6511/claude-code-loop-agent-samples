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

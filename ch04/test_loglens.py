"""loglens count コマンドの現在の動作を固定するテスト。"""

from pathlib import Path

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


# --- JSON Lines 入力（sample.jsonl で挙動を固定する） ---

JSONL_SAMPLE = Path(__file__).parent / "sample.jsonl"


def test_jsonl_count_levels(capsys):
    rc, captured = run_count(JSONL_SAMPLE, capsys)
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 3
    assert counts["WARN"] == 2
    assert counts["INFO"] == 3
    # 不正なレベル・キー欠落・JSON でない行の3行が OTHER
    assert counts["OTHER"] == 3


def test_jsonl_total_matches_non_blank_lines(capsys):
    rc, captured = run_count(JSONL_SAMPLE, capsys)
    assert rc == 0
    counts = parse_output(captured.out)
    non_blank = sum(
        1
        for line in JSONL_SAMPLE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    assert counts["TOTAL"] == non_blank
    assert counts["TOTAL"] == (
        counts["ERROR"] + counts["WARN"] + counts["INFO"] + counts["OTHER"]
    )


@pytest.mark.parametrize(
    "level,expected",
    [("ERROR", 3), ("WARN", 2), ("INFO", 3), ("OTHER", 3)],
)
def test_jsonl_level_option(capsys, level, expected):
    rc = main(["count", str(JSONL_SAMPLE), "--level", level])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == f"{level} {expected}\n"


def test_jsonl_since_until_range_inclusive(capsys):
    rc = main(
        ["count", str(JSONL_SAMPLE), "--since", "09:12:05", "--until", "09:12:13"]
    )
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 2  # 09:12:05 と 09:12:11（両端を含む）
    assert counts["WARN"] == 0
    assert counts["INFO"] == 1   # 09:12:13
    assert counts["OTHER"] == 0  # 範囲指定時は OTHER を除外
    assert counts["TOTAL"] == 3


def test_jsonl_time_range_excludes_other(capsys):
    rc = main(["count", str(JSONL_SAMPLE), "--since", "09:00:00", "--level", "OTHER"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "OTHER 0\n"


# --- 複数ファイル入力（合算して1つの集計として表示する） ---


def test_multi_file_sums_counts(logfile, capsys):
    rc = main(["count", str(logfile), str(JSONL_SAMPLE)])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    # app.log: ERROR 2 / WARN 1 / INFO 2 / OTHER 2
    # sample.jsonl: ERROR 3 / WARN 2 / INFO 3 / OTHER 3
    assert counts["ERROR"] == 5
    assert counts["WARN"] == 3
    assert counts["INFO"] == 5
    assert counts["OTHER"] == 5
    assert counts["TOTAL"] == 18


def test_multi_file_output_format(logfile, capsys):
    rc = main(["count", str(logfile), str(JSONL_SAMPLE)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 5",
        "WARN  3",
        "INFO  5",
        "OTHER 5",
        "TOTAL 18",
    ]


def test_multi_file_same_file_twice(logfile, capsys):
    rc = main(["count", str(logfile), str(logfile)])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 4
    assert counts["WARN"] == 2
    assert counts["INFO"] == 4
    assert counts["OTHER"] == 4
    assert counts["TOTAL"] == 14


def test_multi_file_with_level(logfile, capsys):
    rc = main(["count", str(logfile), str(JSONL_SAMPLE), "--level", "ERROR"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "ERROR 5\n"


def test_multi_file_with_time_range(logfile, capsys):
    rc = main(
        [
            "count",
            str(logfile),
            str(JSONL_SAMPLE),
            "--since",
            "09:12:05",
            "--until",
            "09:12:09",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    # app.log: ERROR 2 (09:12:07, 09:12:09) / WARN 1 (09:12:05)
    # sample.jsonl: ERROR 1 (09:12:05)。09:12:07/09:12:09 は OTHER 行のため除外
    assert counts["ERROR"] == 3
    assert counts["WARN"] == 1
    assert counts["INFO"] == 0
    assert counts["OTHER"] == 0
    assert counts["TOTAL"] == 4


def test_multi_file_missing_one_returns_1(logfile, tmp_path, capsys):
    missing = tmp_path / "no_such.log"
    rc = main(["count", str(logfile), str(missing)])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err.startswith("error:")
    assert captured.out == ""


def test_count_requires_at_least_one_file(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["count"])
    assert excinfo.value.code == 2

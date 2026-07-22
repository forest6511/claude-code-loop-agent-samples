"""loglens count コマンドの現在の動作を固定するテスト。"""

import json
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


# --- --top N（頻出メッセージ上位表示） ---

TOP_LINES = [
    "2026-07-18 09:00:01 INFO Server started",
    "2026-07-18 09:00:02 ERROR Connection refused",
    "2026-07-18 09:00:03 ERROR Connection refused",
    "2026-07-18 09:00:04 WARN Disk usage at 85%",
    "2026-07-18 09:00:05 ERROR Connection refused",
    "2026-07-18 09:00:06 INFO Server started",
    "Traceback (most recent call last):",
    "2026-07-18 09:00:07 WARN Disk usage at 85%",
]


@pytest.fixture
def top_logfile(tmp_path):
    path = tmp_path / "top.log"
    path.write_text("\n".join(TOP_LINES) + "\n", encoding="utf-8")
    return path


def test_top_appends_most_common_after_summary(top_logfile, capsys):
    rc = main(["count", str(top_logfile), "--top", "2"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 3",
        "WARN  2",
        "INFO  2",
        "OTHER 1",
        "TOTAL 8",
        "3 Connection refused",
        "2 Server started",
    ]


def test_top_tie_broken_by_first_appearance(top_logfile, capsys):
    rc = main(["count", str(top_logfile), "--top", "3"])
    captured = capsys.readouterr()
    assert rc == 0
    # Server started(09:00:01) が Disk usage(09:00:04) より先に出現
    assert captured.out.splitlines()[-3:] == [
        "3 Connection refused",
        "2 Server started",
        "2 Disk usage at 85%",
    ]


def test_top_larger_than_message_variety(top_logfile, capsys):
    rc = main(["count", str(top_logfile), "--top", "10"])
    captured = capsys.readouterr()
    assert rc == 0
    # メッセージは3種類しかないので、ある分（3件）だけ表示する
    # OTHER 行（Traceback）は集計対象に含めない
    assert captured.out.splitlines()[5:] == [
        "3 Connection refused",
        "2 Server started",
        "2 Disk usage at 85%",
    ]


def test_top_with_level(top_logfile, capsys):
    rc = main(["count", str(top_logfile), "--level", "INFO", "--top", "5"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "INFO 2\n2 Server started\n"


def test_top_with_time_range(top_logfile, capsys):
    rc = main(
        [
            "count",
            str(top_logfile),
            "--since",
            "09:00:03",
            "--until",
            "09:00:06",
            "--top",
            "2",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    # 範囲内: ERROR(03), WARN(04), ERROR(05), INFO(06)
    assert captured.out.splitlines()[5:] == [
        "2 Connection refused",
        "1 Disk usage at 85%",
    ]


def test_top_with_jsonl(capsys):
    rc = main(["count", str(JSONL_SAMPLE), "--top", "2"])
    captured = capsys.readouterr()
    assert rc == 0
    # 全メッセージ1件ずつなので先に出現した順・OTHER 行の内容は含めない
    assert captured.out.splitlines()[5:] == [
        "1 Server started on port 8080",
        "1 Disk usage at 85%",
    ]


def test_top_multi_file_merges_messages(top_logfile, logfile, capsys):
    rc = main(["count", str(top_logfile), str(logfile), "--top", "1"])
    captured = capsys.readouterr()
    assert rc == 0
    # top.log の 3件 + app.log の 1件 = 4件
    assert captured.out.splitlines()[5:] == ["4 Connection refused"]


def test_without_top_output_unchanged(top_logfile, capsys):
    rc = main(["count", str(top_logfile)])
    captured = capsys.readouterr()
    assert rc == 0
    assert len(captured.out.splitlines()) == 5


# --- --format json（集計結果の JSON 出力） ---


def test_format_json_exact_output(logfile, capsys):
    rc = main(["count", str(logfile), "--format", "json"])
    captured = capsys.readouterr()
    assert rc == 0
    # インデント2・キーは counts(ERROR/WARN/INFO/OTHER) → total の順
    assert captured.out == (
        "{\n"
        '  "counts": {\n'
        '    "ERROR": 2,\n'
        '    "WARN": 1,\n'
        '    "INFO": 2,\n'
        '    "OTHER": 2\n'
        "  },\n"
        '  "total": 7\n'
        "}\n"
    )


def test_format_json_is_single_valid_object(logfile, capsys):
    rc = main(["count", str(logfile), "--format", "json"])
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert list(data.keys()) == ["counts", "total"]
    assert list(data["counts"].keys()) == ["ERROR", "WARN", "INFO", "OTHER"]
    assert data["total"] == sum(data["counts"].values())


def test_format_json_with_top(top_logfile, capsys):
    rc = main(["count", str(top_logfile), "--format", "json", "--top", "2"])
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert list(data.keys()) == ["counts", "total", "top"]
    assert data["top"] == [
        {"count": 3, "message": "Connection refused"},
        {"count": 2, "message": "Server started"},
    ]
    # 各要素内のキーも count → message の順
    assert [list(item.keys()) for item in data["top"]] == [
        ["count", "message"],
        ["count", "message"],
    ]


def test_format_json_with_level(logfile, capsys):
    rc = main(["count", str(logfile), "--format", "json", "--level", "ERROR"])
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert data == {"counts": {"ERROR": 2}, "total": 2}


def test_format_json_with_time_range(logfile, capsys):
    rc = main(
        [
            "count",
            str(logfile),
            "--format",
            "json",
            "--since",
            "09:12:05",
            "--until",
            "09:12:09",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert data == {
        "counts": {"ERROR": 2, "WARN": 1, "INFO": 0, "OTHER": 0},
        "total": 3,
    }


def test_format_json_multi_file_with_jsonl(logfile, capsys):
    rc = main(["count", str(logfile), str(JSONL_SAMPLE), "--format", "json"])
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert data == {
        "counts": {"ERROR": 5, "WARN": 3, "INFO": 5, "OTHER": 5},
        "total": 18,
    }


def test_format_text_explicit_matches_default(logfile, capsys):
    rc = main(["count", str(logfile)])
    default_out = capsys.readouterr().out
    rc2 = main(["count", str(logfile), "--format", "text"])
    text_out = capsys.readouterr().out
    assert rc == 0 and rc2 == 0
    assert text_out == default_out


def test_format_rejects_unknown_value(logfile, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["count", str(logfile), "--format", "xml"])
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert captured.out == ""


# --- --format csv（集計結果の CSV 出力） ---


def test_format_csv_exact_output(logfile, capsys):
    rc = main(["count", str(logfile), "--format", "csv"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "level,count",
        "ERROR,2",
        "WARN,1",
        "INFO,2",
        "OTHER,2",
        "TOTAL,7",
    ]


def test_format_csv_with_top(top_logfile, capsys):
    rc = main(["count", str(top_logfile), "--format", "csv", "--top", "2"])
    captured = capsys.readouterr()
    assert rc == 0
    # 集計の後に空行を1行おき、ヘッダ count,message に続けて上位順
    assert captured.out.splitlines() == [
        "level,count",
        "ERROR,3",
        "WARN,2",
        "INFO,2",
        "OTHER,1",
        "TOTAL,8",
        "",
        "count,message",
        "3,Connection refused",
        "2,Server started",
    ]


def test_format_csv_quotes_special_messages(tmp_path, capsys):
    path = tmp_path / "special.log"
    path.write_text(
        "\n".join(
            [
                '2026-07-18 09:00:01 ERROR Failed to connect, retrying',
                '2026-07-18 09:00:02 WARN Disk "almost" full',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rc = main(["count", str(path), "--format", "csv", "--top", "2"])
    captured = capsys.readouterr()
    assert rc == 0
    # カンマ入りはダブルクォート囲み、引用符は "" に二重化する
    assert captured.out.splitlines()[7:] == [
        "count,message",
        '1,"Failed to connect, retrying"',
        '1,"Disk ""almost"" full"',
    ]


def test_format_csv_with_level(logfile, capsys):
    rc = main(["count", str(logfile), "--format", "csv", "--level", "ERROR"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "level,count",
        "ERROR,2",
    ]


def test_format_csv_with_time_range(logfile, capsys):
    rc = main(
        [
            "count",
            str(logfile),
            "--format",
            "csv",
            "--since",
            "09:12:05",
            "--until",
            "09:12:09",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "level,count",
        "ERROR,2",
        "WARN,1",
        "INFO,0",
        "OTHER,0",
        "TOTAL,3",
    ]


def test_format_csv_multi_file_with_jsonl(logfile, capsys):
    rc = main(["count", str(logfile), str(JSONL_SAMPLE), "--format", "csv"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "level,count",
        "ERROR,5",
        "WARN,3",
        "INFO,5",
        "OTHER,5",
        "TOTAL,18",
    ]


# --- --regex（メッセージの正規表現フィルタ） ---


def test_regex_filters_by_message(logfile, capsys):
    rc = main(["count", str(logfile), "--regex", "refused|Timeout"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 2",
        "WARN  0",
        "INFO  0",
        "OTHER 0",
        "TOTAL 2",
    ]


def test_regex_is_case_sensitive(logfile, capsys):
    # "Timeout" はあるが小文字の "timeout" には一致しない
    rc = main(["count", str(logfile), "--regex", "timeout"])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["TOTAL"] == 0


def test_regex_uses_search_not_fullmatch(logfile, capsys):
    # "port" はメッセージ中間の部分一致(re.search)で拾う
    rc = main(["count", str(logfile), "--regex", "port"])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["INFO"] == 1  # Server started on port 8080
    assert counts["TOTAL"] == 1


def test_regex_excludes_lines_without_message(logfile, capsys):
    # OTHER 行(Traceback 等)はメッセージを持たないため、どのパターンでも除外
    rc = main(["count", str(logfile), "--regex", "."])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    assert counts["ERROR"] == 2
    assert counts["WARN"] == 1
    assert counts["INFO"] == 2
    assert counts["OTHER"] == 0
    assert counts["TOTAL"] == 5


def test_regex_invalid_pattern_exits_2(logfile, capsys):
    import re as re_module

    try:
        re_module.compile("[invalid")
    except re_module.error as e:
        reason = str(e)
    rc = main(["count", str(logfile), "--regex", "[invalid"])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "[invalid" in captured.err  # パターン
    assert reason in captured.err      # re.error の理由


def test_regex_with_level(logfile, capsys):
    rc = main(
        ["count", str(logfile), "--regex", "refused|Timeout", "--level", "ERROR"]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "ERROR 2\n"


def test_regex_with_time_range(top_logfile, capsys):
    rc = main(
        [
            "count",
            str(top_logfile),
            "--since",
            "09:00:03",
            "--until",
            "09:00:06",
            "--regex",
            "refused",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    # 範囲内は ERROR(03), WARN(04), ERROR(05), INFO(06)。うち refused は ERROR 2件
    assert counts["ERROR"] == 2
    assert counts["WARN"] == 0
    assert counts["INFO"] == 0
    assert counts["TOTAL"] == 2


def test_regex_with_top(top_logfile, capsys):
    rc = main(["count", str(top_logfile), "--regex", "Connection", "--top", "5"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 3",
        "WARN  0",
        "INFO  0",
        "OTHER 0",
        "TOTAL 3",
        "3 Connection refused",
    ]


def test_regex_with_jsonl(capsys):
    rc = main(["count", str(JSONL_SAMPLE), "--regex", "Disk"])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    # Disk usage at 85% (WARN) と Disk full (ERROR)
    assert counts["ERROR"] == 1
    assert counts["WARN"] == 1
    assert counts["INFO"] == 0
    assert counts["OTHER"] == 0
    assert counts["TOTAL"] == 2


def test_regex_multi_file(logfile, capsys):
    rc = main(["count", str(logfile), str(JSONL_SAMPLE), "--regex", "refused"])
    captured = capsys.readouterr()
    assert rc == 0
    counts = parse_output(captured.out)
    # app.log と sample.jsonl に Connection refused が1件ずつ
    assert counts["ERROR"] == 2
    assert counts["TOTAL"] == 2


def test_regex_with_format_json(logfile, capsys):
    rc = main(
        ["count", str(logfile), "--format", "json", "--regex", "refused|Timeout"]
    )
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert data == {
        "counts": {"ERROR": 2, "WARN": 0, "INFO": 0, "OTHER": 0},
        "total": 2,
    }


def test_regex_with_format_csv(logfile, capsys):
    rc = main(
        ["count", str(logfile), "--format", "csv", "--regex", "refused|Timeout"]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "level,count",
        "ERROR,2",
        "WARN,0",
        "INFO,0",
        "OTHER,0",
        "TOTAL,2",
    ]


# --- --stats（時間帯別集計） ---

STATS_LINES = [
    "2026-07-18 23:10:00 WARN Cache miss",
    "2026-07-18 09:00:01 INFO Server started",
    "2026-07-18 09:30:02 ERROR Connection refused",
    "Traceback (most recent call last):",
    "2026-07-19 00:05:00 INFO Nightly job done",
]


@pytest.fixture
def stats_logfile(tmp_path):
    path = tmp_path / "stats.log"
    path.write_text("\n".join(STATS_LINES) + "\n", encoding="utf-8")
    return path


def test_stats_appends_hourly_counts_after_summary(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    # ファイル中の出現順(23時が先頭)ではなく時刻順。OTHER 行は含めない
    assert captured.out.splitlines() == [
        "ERROR 1",
        "WARN  1",
        "INFO  2",
        "OTHER 1",
        "TOTAL 5",
        "",
        "00時 1件",
        "09時 2件",
        "23時 1件",
    ]


def test_stats_without_flag_output_unchanged(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 1",
        "WARN  1",
        "INFO  2",
        "OTHER 1",
        "TOTAL 5",
    ]


def test_stats_only_timestampless_lines_yields_empty_block(tmp_path, capsys):
    path = tmp_path / "other_only.log"
    path.write_text("Traceback (most recent call last):\n", encoding="utf-8")
    rc = main(["count", str(path), "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    # 空行はおくが、1件以上ある時間帯がないので時間帯の行は出さない
    assert captured.out.splitlines() == [
        "ERROR 0",
        "WARN  0",
        "INFO  0",
        "OTHER 1",
        "TOTAL 1",
        "",
    ]


def test_stats_with_level_counts_only_that_level(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), "--level", "INFO", "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "INFO 2",
        "",
        "00時 1件",
        "09時 1件",
    ]


def test_stats_with_time_range(stats_logfile, capsys):
    rc = main(
        [
            "count",
            str(stats_logfile),
            "--since",
            "09:00:00",
            "--until",
            "12:00:00",
            "--stats",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 1",
        "WARN  0",
        "INFO  1",
        "OTHER 0",
        "TOTAL 2",
        "",
        "09時 2件",
    ]


def test_stats_with_regex(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), "--regex", "refused", "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 1",
        "WARN  0",
        "INFO  0",
        "OTHER 0",
        "TOTAL 1",
        "",
        "09時 1件",
    ]


def test_stats_after_top_block(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), "--top", "1", "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    # --top の出力の後に空行をおいて時間帯集計を出す
    assert captured.out.splitlines() == [
        "ERROR 1",
        "WARN  1",
        "INFO  2",
        "OTHER 1",
        "TOTAL 5",
        "1 Cache miss",
        "",
        "00時 1件",
        "09時 2件",
        "23時 1件",
    ]


def test_stats_with_jsonl(capsys):
    rc = main(["count", str(JSONL_SAMPLE), "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    # 有効8行はすべて09時台。OTHER の3行は含めない
    assert captured.out.splitlines()[5:] == [
        "",
        "09時 8件",
    ]


def test_stats_jsonl_timestamp_without_time_excluded(tmp_path, capsys):
    path = tmp_path / "no_time.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"timestamp": "2026-07-18 09:12:03", "level": "INFO", "message": "a"}',
                '{"timestamp": "2026-07-18", "level": "INFO", "message": "b"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rc = main(["count", str(path), "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    # INFO は2件だが、時刻を持たない行は時間帯集計に含めない
    assert captured.out.splitlines() == [
        "ERROR 0",
        "WARN  0",
        "INFO  2",
        "OTHER 0",
        "TOTAL 2",
        "",
        "09時 1件",
    ]


def test_stats_multi_file_sums_hours(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), str(stats_logfile), "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines()[5:] == [
        "",
        "00時 2件",
        "09時 4件",
        "23時 2件",
    ]


def test_stats_format_json_adds_stats_key_last(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), "--format", "json", "--stats"])
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert list(data.keys()) == ["counts", "total", "stats"]
    assert data["stats"] == {"00": 1, "09": 2, "23": 1}
    # 出現した時間帯のみ・時刻順
    assert list(data["stats"].keys()) == ["00", "09", "23"]


def test_stats_format_json_without_flag_has_no_stats_key(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), "--format", "json"])
    captured = capsys.readouterr()
    assert rc == 0
    data = json.loads(captured.out)
    assert "stats" not in data


def test_stats_format_csv_rejected_exit_2(stats_logfile, capsys):
    rc = main(["count", str(stats_logfile), "--format", "csv", "--stats"])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.err.startswith("error:")
    assert captured.out == ""


# --- --output PATH（結果のファイル書き出し） ---


def test_output_writes_text_and_prints_wrote(logfile, tmp_path, capsys):
    rc = main(["count", str(logfile)])
    expected = capsys.readouterr().out
    out_path = tmp_path / "result.txt"
    rc2 = main(["count", str(logfile), "--output", str(out_path)])
    captured = capsys.readouterr()
    assert rc == 0 and rc2 == 0
    # 標準出力は wrote: PATH の1行だけ
    assert captured.out == f"wrote: {out_path}\n"
    # ファイル内容は --output なしの標準出力と一致(UTF-8・末尾改行あり)
    content = out_path.read_text(encoding="utf-8")
    assert content == expected
    assert content.endswith("\n")


def test_output_with_format_json(logfile, tmp_path, capsys):
    rc = main(["count", str(logfile), "--format", "json"])
    expected = capsys.readouterr().out
    out_path = tmp_path / "result.json"
    rc2 = main(
        ["count", str(logfile), "--format", "json", "--output", str(out_path)]
    )
    captured = capsys.readouterr()
    assert rc == 0 and rc2 == 0
    assert captured.out == f"wrote: {out_path}\n"
    assert out_path.read_text(encoding="utf-8") == expected


def test_output_with_format_csv(logfile, tmp_path, capsys):
    rc = main(["count", str(logfile), "--format", "csv"])
    expected = capsys.readouterr().out
    out_path = tmp_path / "result.csv"
    rc2 = main(
        ["count", str(logfile), "--format", "csv", "--output", str(out_path)]
    )
    captured = capsys.readouterr()
    assert rc == 0 and rc2 == 0
    assert captured.out == f"wrote: {out_path}\n"
    assert out_path.read_text(encoding="utf-8") == expected


def test_output_with_top(top_logfile, tmp_path, capsys):
    rc = main(["count", str(top_logfile), "--top", "2"])
    expected = capsys.readouterr().out
    out_path = tmp_path / "result.txt"
    rc2 = main(
        ["count", str(top_logfile), "--top", "2", "--output", str(out_path)]
    )
    captured = capsys.readouterr()
    assert rc == 0 and rc2 == 0
    assert captured.out == f"wrote: {out_path}\n"
    assert out_path.read_text(encoding="utf-8") == expected


def test_output_overwrites_existing_file(logfile, tmp_path, capsys):
    out_path = tmp_path / "result.txt"
    out_path.write_text("古い内容\n", encoding="utf-8")
    rc = main(["count", str(logfile), "--output", str(out_path)])
    capsys.readouterr()
    assert rc == 0
    content = out_path.read_text(encoding="utf-8")
    assert "古い内容" not in content
    assert content.splitlines()[0] == "ERROR 2"


def test_output_missing_parent_dir_exits_2(logfile, tmp_path, capsys):
    out_path = tmp_path / "no_such_dir" / "result.txt"
    rc = main(["count", str(logfile), "--output", str(out_path)])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.err.startswith("error:")
    assert captured.out == ""
    assert not out_path.exists()


def test_without_output_unchanged(logfile, capsys):
    rc = main(["count", str(logfile)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.splitlines() == [
        "ERROR 2",
        "WARN  1",
        "INFO  2",
        "OTHER 2",
        "TOTAL 7",
    ]


# --- alert サブコマンド（しきい値アラート） ---
# fixture logfile: ERROR 2 / WARN 1 / INFO 2 / OTHER 2
# sample.jsonl:    ERROR 3 / WARN 2 / INFO 3 / OTHER 3


def test_alert_not_fired_exit_0(logfile, capsys):
    rc = main(["alert", str(logfile), "--threshold", "3"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "OK: ERROR 2 < 3\n"
    assert captured.err == ""


def test_alert_fired_exit_3_stdout_and_stderr(logfile, capsys):
    rc = main(["alert", str(logfile), "--threshold", "1"])
    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out == "ALERT: ERROR 2 >= 1\n"
    assert captured.err == "ALERT: ERROR 2 >= 1\n"


def test_alert_boundary_exactly_threshold_fires(logfile, capsys):
    rc = main(["alert", str(logfile), "--threshold", "2"])
    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out == "ALERT: ERROR 2 >= 2\n"
    assert captured.err == "ALERT: ERROR 2 >= 2\n"


def test_alert_level_warn(logfile, capsys):
    rc = main(["alert", str(logfile), "--threshold", "2", "--level", "WARN"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "OK: WARN 1 < 2\n"
    assert captured.err == ""


def test_alert_level_other_alone(logfile, capsys):
    rc = main(["alert", str(logfile), "--threshold", "2", "--level", "OTHER"])
    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out == "ALERT: OTHER 2 >= 2\n"
    assert captured.err == "ALERT: OTHER 2 >= 2\n"


def test_alert_since_until_filters_before_judge(logfile, capsys):
    # 09:12:05〜09:12:09 の ERROR は 2 件 (09:12:07 / 09:12:09) < 3
    rc = main(
        [
            "alert",
            str(logfile),
            "--threshold",
            "3",
            "--since",
            "09:12:05",
            "--until",
            "09:12:09",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "OK: ERROR 2 < 3\n"
    assert captured.err == ""


def test_alert_regex_filters_before_judge(logfile, capsys):
    # fixture の ERROR で "Timeout" を含むのは 1 件のみ
    rc = main(["alert", str(logfile), "--threshold", "1", "--regex", "Timeout"])
    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out == "ALERT: ERROR 1 >= 1\n"
    assert captured.err == "ALERT: ERROR 1 >= 1\n"


def test_alert_jsonl_input(capsys):
    rc = main(["alert", str(JSONL_SAMPLE), "--threshold", "4"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "OK: ERROR 3 < 4\n"
    assert captured.err == ""


def test_alert_multi_file_sum_fires(logfile, capsys):
    # 単体では logfile(2) も sample.jsonl(3) も 4 未満だが、合算 5 で発火
    rc = main(["alert", str(logfile), str(JSONL_SAMPLE), "--threshold", "4"])
    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out == "ALERT: ERROR 5 >= 4\n"
    assert captured.err == "ALERT: ERROR 5 >= 4\n"


def test_alert_threshold_missing_exits_2(logfile, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["alert", str(logfile)])
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert captured.out == ""


def test_alert_threshold_not_integer_exits_2(logfile, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["alert", str(logfile), "--threshold", "abc"])
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert captured.out == ""


@pytest.mark.parametrize("threshold", ["0", "-1"])
def test_alert_threshold_zero_or_negative_exits_2(logfile, capsys, threshold):
    rc = main(["alert", str(logfile), "--threshold", threshold])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.err.startswith("error:")
    assert captured.out == ""


def test_alert_other_with_regex_exits_2(logfile, capsys):
    rc = main(
        ["alert", str(logfile), "--threshold", "1", "--level", "OTHER", "--regex", "x"]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.err.startswith("error:")
    assert captured.out == ""


@pytest.mark.parametrize("option", ["--since", "--until"])
def test_alert_other_with_time_range_exits_2(logfile, capsys, option):
    rc = main(
        [
            "alert",
            str(logfile),
            "--threshold",
            "1",
            "--level",
            "OTHER",
            option,
            "09:00:00",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.err.startswith("error:")
    assert captured.out == ""


def test_alert_invalid_regex_exits_2(logfile, capsys):
    rc = main(["alert", str(logfile), "--threshold", "1", "--regex", "["])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.err.startswith("error:")
    assert captured.out == ""


def test_alert_missing_file_exits_1(tmp_path, capsys):
    missing = tmp_path / "no_such.log"
    rc = main(["alert", str(missing), "--threshold", "1"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err.startswith("error:")
    assert captured.out == ""


def test_alert_one_of_multiple_files_missing_exits_1(logfile, tmp_path, capsys):
    # 1つでも読めなければ部分合算で判定せず exit 1
    missing = tmp_path / "no_such.log"
    rc = main(["alert", str(logfile), str(missing), "--threshold", "1"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.err.startswith("error:")
    assert captured.out == ""

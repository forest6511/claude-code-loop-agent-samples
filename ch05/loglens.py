#!/usr/bin/env python3
"""loglens: ログファイルのレベル別件数を集計する CLI。

使い方:
    python3 loglens.py count <ログファイル>
    python3 loglens.py count <ログファイル> --since 09:00:00 --until 12:00:00
    python3 loglens.py count a.log b.jsonl  (複数ファイルは合算して集計)
    python3 loglens.py count sample.log --top 3  (頻出メッセージ上位3件も表示)

複数ファイルを指定した場合は全ファイルの件数を合算して1つの集計として
表示する。.log と .jsonl の混在も可能で、形式はファイルごとに判定する。
--level / --since / --until はすべてのファイルに適用される。

ログ行の形式（テキスト形式）:
    2026-07-18 09:12:03 INFO Server started on port 8080
    (日付 時刻 レベル メッセージ)

拡張子が .jsonl のファイルは JSON Lines として解釈する（1行 = 1 JSON オブジェクト）:
    {"timestamp": "2026-07-18 09:12:03", "level": "INFO", "message": "..."}
    レベルが ERROR/WARN/INFO 以外・キー欠落・JSON として不正な行は OTHER に数える。
"""

import argparse
import json
import sys
from collections import Counter

LEVELS = ["ERROR", "WARN", "INFO"]
OTHER = "OTHER"


def parse_level(line):
    """ログ1行からレベルを取り出す。形式外の行(Traceback 等)は OTHER を返す。"""
    parts = line.split(maxsplit=3)
    if len(parts) >= 3 and parts[2] in LEVELS:
        return parts[2]
    return OTHER


def parse_time(line):
    """ログ1行から時刻部分(HH:MM:SS)を取り出す。形式外の行は None を返す。"""
    parts = line.split(maxsplit=3)
    if len(parts) >= 3 and parts[2] in LEVELS:
        return parts[1]
    return None


def parse_message(line):
    """ログ1行からメッセージ部分を取り出す。形式外の行は None を返す。"""
    parts = line.split(maxsplit=3)
    if len(parts) >= 4 and parts[2] in LEVELS:
        return parts[3].strip()
    return None


def parse_jsonl_line(line):
    """JSON Lines の1行から (レベル, 時刻, メッセージ) を取り出す。

    レベルが3種以外・キー欠落・JSON として不正な行は (OTHER, None, None) を返す。
    """
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return OTHER, None, None
    if not isinstance(record, dict):
        return OTHER, None, None
    if not all(key in record for key in ("timestamp", "level", "message")):
        return OTHER, None, None
    if record["level"] not in LEVELS:
        return OTHER, None, None
    parts = str(record["timestamp"]).split()
    time = parts[1] if len(parts) == 2 else None
    return record["level"], time, str(record["message"])


def count_levels(path, since=None, until=None, level=None):
    """レベル別件数と、絞り込み後のメッセージ別件数(OTHER 除く)を返す。

    level を指定するとメッセージ集計をそのレベルの行に限定する
    (レベル別件数には影響しない)。
    """
    is_jsonl = str(path).endswith(".jsonl")
    counts = Counter()
    messages = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            if is_jsonl:
                lv, time, message = parse_jsonl_line(line)
            else:
                lv, time, message = (
                    parse_level(line),
                    parse_time(line),
                    parse_message(line),
                )
            if since is not None or until is not None:
                if time is None:
                    continue  # 時刻を持たない行(OTHER)は範囲指定時は除外
                if since is not None and time < since:
                    continue
                if until is not None and time > until:
                    continue
            counts[lv] += 1
            if lv != OTHER and message is not None:
                if level is None or lv == level:
                    messages[message] += 1
    return counts, messages


def cmd_count(args):
    counts = Counter()
    messages = Counter()
    try:
        for logfile in args.logfile:
            file_counts, file_messages = count_levels(
                logfile, since=args.since, until=args.until, level=args.level
            )
            counts += file_counts
            messages += file_messages
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.level:
        print(f"{args.level} {counts[args.level]}")
    else:
        for level in LEVELS + [OTHER]:
            print(f"{level:<5} {counts[level]}")
        print(f"TOTAL {sum(counts.values())}")

    if args.top is not None:
        # most_common は同数のとき挿入順(=先に出現した順)を保つ
        for message, count in messages.most_common(args.top):
            print(f"{count} {message}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="loglens", description="ログ集計 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_count = subparsers.add_parser("count", help="レベル別の件数を集計する")
    p_count.add_argument(
        "logfile",
        nargs="+",
        help="対象のログファイル(複数指定時は合算して集計する)",
    )
    p_count.add_argument(
        "--level",
        choices=LEVELS + [OTHER],
        help="指定したレベルの件数だけを表示する",
    )
    p_count.add_argument(
        "--since",
        metavar="HH:MM:SS",
        help="この時刻以降の行だけを集計する(両端を含む)",
    )
    p_count.add_argument(
        "--until",
        metavar="HH:MM:SS",
        help="この時刻以前の行だけを集計する(両端を含む)",
    )
    p_count.add_argument(
        "--top",
        type=int,
        metavar="N",
        help="頻出メッセージの上位 N 件を集計の後に表示する",
    )
    p_count.set_defaults(func=cmd_count)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

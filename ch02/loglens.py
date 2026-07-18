#!/usr/bin/env python3
"""loglens: ログファイルのレベル別件数を集計する CLI。

使い方:
    python3 loglens.py count <ログファイル>

ログ行の形式:
    2026-07-18 09:12:03 INFO Server started on port 8080
    (日付 時刻 レベル メッセージ)
"""

import argparse
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


def count_levels(path):
    counts = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            counts[parse_level(line)] += 1
    return counts


def cmd_count(args):
    try:
        counts = count_levels(args.logfile)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.level:
        print(f"{args.level} {counts[args.level]}")
        return 0

    for level in LEVELS + [OTHER]:
        print(f"{level:<5} {counts[level]}")
    print(f"TOTAL {sum(counts.values())}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="loglens", description="ログ集計 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_count = subparsers.add_parser("count", help="レベル別の件数を集計する")
    p_count.add_argument("logfile", help="対象のログファイル")
    p_count.add_argument(
        "--level",
        choices=LEVELS + [OTHER],
        help="指定したレベルの件数だけを表示する",
    )
    p_count.set_defaults(func=cmd_count)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""loglens: ログファイルのレベル別件数を集計する CLI。

使い方:
    python3 loglens.py count <ログファイル>
    python3 loglens.py count <ログファイル> --since 09:00:00 --until 12:00:00

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


def parse_time(line):
    """ログ1行から時刻部分(HH:MM:SS)を取り出す。形式外の行は None を返す。"""
    parts = line.split(maxsplit=3)
    if len(parts) >= 3 and parts[2] in LEVELS:
        return parts[1]
    return None


def count_levels(path, since=None, until=None):
    counts = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            if since is not None or until is not None:
                time = parse_time(line)
                if time is None:
                    continue  # 時刻を持たない行(OTHER)は範囲指定時は除外
                if since is not None and time < since:
                    continue
                if until is not None and time > until:
                    continue
            counts[parse_level(line)] += 1
    return counts


def cmd_count(args):
    try:
        counts = count_levels(args.logfile, since=args.since, until=args.until)
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
    p_count.set_defaults(func=cmd_count)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

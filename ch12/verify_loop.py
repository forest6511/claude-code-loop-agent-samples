#!/usr/bin/env python3
"""loglens 検証ループ。

Agent SDK でエージェントループを回し、最終判定はエージェントの
自己申告ではなく、決定的ゲートの再実行で行う(exit 0/1 が CI の合否)。
"""
import argparse
import asyncio
import subprocess
import sys

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

GATE = [
    ["python3", "-m", "pytest", "-q"],
    ["python3", "-m", "ruff", "check", "."],
    ["python3", "-m", "pytest", "-q", "--cov=loglens",
     "--cov-fail-under=90"],
]

CHECK_PROMPT = """\
リポジトリの検証ゲート3点を実行してください。
1. python3 -m pytest -q
2. python3 -m ruff check .
3. python3 -m pytest -q --cov=loglens --cov-fail-under=90
失敗があれば、原因のファイルと行を特定し、修正方針を報告して
ください。ファイルは変更しないでください。
全て合格なら、3点の実行結果の要約行だけを報告してください。"""

FIX_PROMPT = """\
リポジトリの検証ゲート3点(pytest / ruff check / カバレッジ90%)を
実行し、失敗があれば原因を修正して、3点すべてが合格するまで
繰り返してください。既存テストの削除・弱体化は禁止します。
合格したら、3点の実行結果の要約行を報告してください。"""


async def run_agent(prompt: str, opts: ClaudeAgentOptions):
    """エージェントループを最後まで消費し、ResultMessage を返す。"""
    last = None
    try:
        async for message in query(prompt=prompt, options=opts):
            if isinstance(message, ResultMessage):
                last = message
    except Exception as error:
        # 単発の query() はエラー結果を yield した後に例外を投げる
        # (公式仕様)。ResultMessage は last に残っているので落とさない
        print(f"query() raised: {error}", file=sys.stderr)
    return last


def gate_passes() -> bool:
    """決定的ゲート。エージェントの報告とは独立に再実行する。"""
    for cmd in GATE:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"gate NG: {' '.join(cmd)}")
            print((r.stdout + r.stderr).strip().splitlines()[-1])
            return False
    return True


def build_options(fix: bool, max_turns: int,
                  max_budget: float) -> ClaudeAgentOptions:
    if fix:
        # ローカル修復モード: 編集を許可し、プロジェクト設定
        # (CLAUDE.md と Stop hook の完了ゲート)を読み込む
        return ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Grep", "Glob",
                           "Bash(python3 -m pytest *)",
                           "Bash(python3 -m ruff *)"],
            permission_mode="acceptEdits",
            setting_sources=["project"],
            max_turns=max_turns,
            max_budget_usd=max_budget,
        )
    # CI 検問モード: 読み取りとゲート実行だけ。
    # setting_sources=[] が遮断の要。None(未指定)は「読み込まない」
    # ではなく「CLI と同じ既定 = user/project/local を全部読む」
    return ClaudeAgentOptions(
        allowed_tools=["Read", "Grep", "Glob",
                       "Bash(python3 -m pytest *)",
                       "Bash(python3 -m ruff *)"],
        disallowed_tools=["Edit", "Write", "NotebookEdit"],
        setting_sources=[],
        max_turns=max_turns,
        max_budget_usd=max_budget,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="loglens verification loop")
    ap.add_argument("--fix", action="store_true",
                    help="失敗を修正するローカルモード(既定は検問のみ)")
    ap.add_argument("--max-turns", type=int, default=15)
    ap.add_argument("--max-budget", type=float, default=4.0)
    args = ap.parse_args()

    opts = build_options(args.fix, args.max_turns, args.max_budget)
    prompt = FIX_PROMPT if args.fix else CHECK_PROMPT
    result = asyncio.run(run_agent(prompt, opts))

    if result is not None:
        print(f"agent: subtype={result.subtype} "
              f"turns={result.num_turns} "
              f"cost=${result.total_cost_usd or 0:.2f} "
              f"time={result.duration_ms / 1000:.1f}s")
        if result.subtype == "success":
            print(result.result)
        elif result.subtype == "error_max_turns":
            print("ターン上限で停止。--max-turns を増やして再実行できます")
        elif result.subtype == "error_max_budget_usd":
            print("予算上限で停止。ここまでの消費は上の cost のとおりです")

    ok = gate_passes()
    print(f"deterministic gate: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

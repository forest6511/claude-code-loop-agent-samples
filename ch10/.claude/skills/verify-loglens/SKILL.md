---
description: loglens の検証ゲート。実装や修正の後に呼び、テスト・lint・
  カバレッジの3点で合否を判定する。不合格の間は修正と再実行を繰り返す。
argument-hint: [検証対象の説明]
allowed-tools: Bash(python3 -m pytest *) Bash(python3 -m ruff *)
disallowed-tools: AskUserQuestion
---

loglens の検証を実行します。検証対象: $ARGUMENTS

次の3点を順に実行し、すべて合格するまで修正と再実行を繰り返して
ください。

1. テスト: python3 -m pytest -q が全件成功すること
2. lint: python3 -m ruff check . が「All checks passed!」であること
3. カバレッジ: python3 -m pytest -q --cov=loglens --cov-fail-under=90
   が exit 0 であること（loglens.py の行カバレッジ 90% 以上）

ルール:

- 合格させるための既存テストの削除・弱体化は禁止（CLAUDE.md 準拠）
- 報告には3点それぞれの実行結果の要約行をそのまま含める
- 不合格の項目は、原因の特定 → 修正 → 3点の再実行の順で解消する

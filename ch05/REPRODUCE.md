# ch05 — Maker-Checker（checker サブエージェント・実測）

第5章終了時点の `loglens` の到達状態です。
（`README.md` は loglens 自体の使い方ドキュメント＝到達状態の一部なので、
章の説明と再現手順はこのファイルにあります）

- `loglens.py` — count + `--level` + `--since` / `--until` + JSON Lines
  入力 + 複数ファイル合算 + `--top N`（頻出メッセージ上位表示）
- `test_loglens.py` — pytest 39件（ch04 の31件 + top-messages 8件）
- `.claude/agents/checker.md` — 読み取り専用のレビュー担当
  （tools: Read, Grep, Glob / maxTurns: 15）
- `specs/top-messages.md` — --top N の仕様（毎回 checker の照合基準）
- `.claude/settings.json` — 常設ゲートは ch03 の2本のまま
  （command 型 verify.sh + prompt 型 README チェック）。agent 型は実測の
  結果、常設から外した（fail-open と毎ターン発火コストのため）
- `.claude/hooks/agent-gate-prompt.txt` — agent 型 Stop hook を試す
  場合の検証プロンプト（本文の絞り込み修正済み版）
- `feature_list.json` — 全5機能 passes: true（12章ロードマップの
  ch02-05 区間が完了）

## 実行

```bash
python3 -m pytest -q                          # 39 passed
python3 loglens.py count sample.log --top 3
python3 loglens.py count sample.log sample.jsonl --top 5
```

## 実測サマリ（v2.1.215 / Claude Fable 5 / サブスク認証）

- Run 1（実装）: `claude -p "specs/top-messages.md の仕様どおり…"`
  25ターン / 296.5秒 / $6.12。テスト31→39件。プロンプトに書いていない
  checker 呼び出しが description による自動委譲で発生（指摘なし）
- Run 2（自己レビュー）: `claude -p --resume <session-id> "…レビュー…"`
  1ターン / 68.8秒 / $2.35 →「指摘なし」
- Run 3（checker・green）: 新セッションから diff+仕様を checker に中継
  3ターン / 133.3秒 / $3.31 →「指摘なし」
- Run 4（checker・red）: 改変 diff（下記）に対して
  5ターン / 91.1秒 / $2.99 → 指摘2点（仕様違反+テスト弱体化）を検知
- Run 5（agent 型 Stop hook・素のプロンプト）: 6ターン / 89.7秒 / $1.98。
  hook は 50ターン上限で中断 = fail-open（ターン終了は許可された）
- Run 6（agent 型・絞ったプロンプト）: 9ターン / 67.1秒 / $2.20。
  2回発火・各ツール使用2〜5回・10〜14秒で完走
- 累計 $18.95

## red 経路の再現（checker の検知能力テスト）

コミットせずに次の2種類の改変を作り、checker に `git diff` を渡す:

1. `loglens.py` の `most_common(args.top)` を
   `sorted(messages.items(), key=lambda kv: (-kv[1], kv[0]))` に置換
   （同数タイが初出順→辞書順になる仕様違反）
2. これで落ちる4テストを弱体化（リスト完全一致→set 比較×3、
   内容検証→行数のみ×1）

pytest は 39 passed（全緑）・verify.sh は exit 0 で素通りするが、
checker は仕様違反とテスト弱体化の両方を指摘する。確認後は
`git restore loglens.py test_loglens.py` で破棄する。

## agent 型 Stop hook を試す場合

```bash
jq --rawfile p .claude/hooks/agent-gate-prompt.txt \
  '.hooks.Stop[0].hooks +=
     [{"type": "agent", "prompt": $p, "timeout": 180}]' \
  .claude/settings.json > /tmp/settings.json \
  && mv /tmp/settings.json .claude/settings.json
```

agent 型は experimental（公式）。調査の打ち切りをプロンプトに明示しない
と 50ターン上限まで完走せず、判定なしのままターン終了が許可される
（fail-open）点に注意。

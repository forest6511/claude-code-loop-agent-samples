# ch08 — worktree 並列（ループの複線化・実測）

第8章終了時点の `loglens` の到達状態です。
（`README.md` は loglens 自体の使い方ドキュメント＝到達状態の一部なので、
章の説明と再現手順はこのファイルにあります）

- `loglens.py` — count + これまでの全オプション + `--stats`（時間帯別集計・
  csv 併用は exit 2）+ `--output PATH`（ファイル書き出し・`wrote: PATH`）。
  マージの結果、`--stats` の出力もそのまま `--output` で書き出せる
- `test_loglens.py` — pytest 85件（ch07 の65件 + stats 13件 + output 7件。
  マージで1件も削っていない）
- `specs/stats.md` / `specs/output.md` — 並列開発した2機能の仕様
  （互いに言及しない=並列開発の前提）
- `feature_list.json` — 10機能すべて passes: true
- `.gitignore` — ch07 + `.claude/worktrees/`（公式推奨）
- `.claude/` — ch07 と同じ（常設ゲート2本・checker・verify-loglens スキル）

## 実行

```bash
python3 -m pytest -q                                   # 85 passed
python3 loglens.py count sample.log --stats
python3 loglens.py count sample.log --stats --output /tmp/merged.txt
```

## 実測サマリ（v2.1.216 / Claude Fable 5 / サブスク認証）

すべて `env -u ANTHROPIC_API_KEY` を付けて実行。origin はローカル bare
リポジトリ（`git init --bare ../loglens-origin.git` → remote add →
`git push -u origin master` → `git remote set-head origin master`）。

- 罠の実測: 仕様2本を**未 push**でコミット → `claude -p --worktree
  spec-check "ls specs/ と git log を報告"` → 3ターン・17.3秒・$1.34。
  worktree は origin/HEAD（c8f94cf）から切られ、未 push の仕様コミット
  （67ba84b）が存在しない（`git worktree list` で本体とのズレを確認）
- 並列実装: push 後、`claude -p --worktree stats-dev` と
  `claude -p --worktree output-dev` を `&` + `wait` で同時起動
  → stats 33ターン/227.1秒/$5.55（テスト78件）・output 28ターン/161.4秒/
  $4.79（テスト72件）。**壁時計 232秒**（直列なら合計 388.5秒ぶん）。
  各ブランチにコミット2個（実装 + README 検問による README 追記）
- マージ: `git merge worktree-stats-dev` = Fast-forward。
  `git merge worktree-output-dev` = 4ファイル CONFLICT（loglens.py /
  test_loglens.py / README.md / claude-progress.txt。feature_list.json は
  エントリ位置が離れていたため自動マージ成功）
- 衝突解消: `claude -p` に両仕様+テスト全残し+/verify-loglens 3点合格を
  指定 → 30ターン・174.5秒・$4.43。マージコミット `5d5befb`・テスト85件・
  カバレッジ 98.74%・`--stats` × `--output` の自然な合成まで導出
- 後片付け: `-p` の worktree は自動削除されず lock も残る
  （`fatal: cannot remove a locked working tree, lock reason: claude
  session stats-dev (pid ...)`）→ `git worktree unlock` してから
  `remove`、`git branch -d` で2ブランチ削除

`-p` 4本の費用合計は $16.11。

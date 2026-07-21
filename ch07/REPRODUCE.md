# ch07 — /goal（完了条件を渡して離席する・実測）

第7章終了時点の `loglens` の到達状態です。
（`README.md` は loglens 自体の使い方ドキュメント＝到達状態の一部なので、
章の説明と再現手順はこのファイルにあります）

- `loglens.py` — count + `--level` + `--since` / `--until` + JSON Lines
  入力 + 複数ファイル合算 + `--top N` + `--format text/json/csv` +
  `--regex`（メッセージの正規表現絞り込み。不正パターンは exit 2）
- `test_loglens.py` — pytest 65件（ch06 の53件 + regex 12件）
- `specs/regex.md` — 本章の機能仕様
- `feature_list.json` — 8機能すべて passes: true
- `.gitignore` — `.coverage` / `__pycache__/` / `logs/` /
  `logs-console.txt`（対話セッションの `/goal` と Run 3 のループ内で追加）
- `.claude/` — ch06 と同じ（常設ゲート2本・checker・verify-loglens スキル）

## 実行

```bash
python3 -m pytest -q                          # 65 passed
python3 loglens.py count sample.log --regex "timeout|refused"
python3 loglens.py count sample.log --regex "(" ; echo "exit=$?"   # exit 2
```

## 実測サマリ（v2.1.216 / Claude Fable 5 / サブスク認証）

すべて `env -u ANTHROPIC_API_KEY` を付けて実行（API キーが env に残っていると
`-p` はキー課金になる）。`/goal` は trust dialog 承認済みワークスペースが前提。

- Run 1（悪い条件・破棄）: `claude -p "/goal count に --regex オプションが
  追加されて動くこと"` `--allowedTools "Read,Write,Edit,Bash,Skill"`
  → 33ターン・272.0秒・$6.83。完走したが evaluator の差し戻し 0 回
  （ブロックは ch03 常設の README 検問1回のみ）。品質を支えたのは条件では
  なく CLAUDE.md の掟・常設フック・スキル。`git reset --hard` で破棄
- Run 2（良い条件・採用）: 条件 = specs/regex.md 準拠 + (1) /verify-loglens
  3点の実行結果の要約行が会話に出力され合格 (2) 既存テスト無変更
  (3) feature_list passes:true + git commit。or stop after 20 turns
  → 30ターン・200.9秒・$5.60。Skill 呼び出し {"skill": "verify-loglens"}
  が transcript に記録。実装 897e2b6 + README e05df4f。最終報告が
  「ゴール達成状況の再掲」（条件3項目の証拠列挙）になった
- Run 3（証拠が残せない条件）: `/goal loglens が本番環境で安定稼働している
  こと。or stop after 5 turns` → 23ターン・175.1秒・$4.12。evaluator が
  4回差し戻し（Stop hook feedback として transcript に記録。ターン数を
  数えながら「第1条件は不可能」）。モデルは周辺の仕事を発明（gitignore
  追加整理・README 終了コード追記・進捗記録の3コミット）し、5ターンの
  打ち切り条項で停止
- Run 3 別試行: 同じ条件で 10ターン・$2.06。「ローカルで確認できる範囲では
  満たしている」という再解釈を evaluator が初回判定で受理（判定は
  確率的で、曖昧な条件は挙動まで曖昧になる実例）
- 対話セッション（本文掲載分）: `claude --permission-mode default
  --allowedTools "Read,Bash"` で「pytest 全件成功の出力と --regex の
  実行結果が会話に出力されていること」の検証型ゴールを設定 →
  `◎ /goal active (7s)` → `✔ Goal achieved (17s · 1 turn · 714 tokens)` →
  `/goal`（引数なし）で達成状態の表示 → `/goal clear` → `No goal set`
- 対話セッション（本文非掲載）: .gitignore 整理のゴール
  （`✔ Goal achieved (33s · 1 turn · 1.8k tokens)`、コミット fc41f7e）。
  Run 3 の `.gitignore` 整理コミット（42afc5a）はこれへの追記

## 数字の読み方

`--output-format json` の `num_turns` は応答内部のツール実行サイクル数。
`/goal` と evaluator が数える「ターン」は応答の区切り（Stop）の数で、
打ち切り条項 `or stop after N turns` の N は後者。Run 3 は `num_turns` 23 に
対し evaluator の数えたターンは 5。

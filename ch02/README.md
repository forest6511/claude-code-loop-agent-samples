# ch02 — 検証を渡す（pytest・CLAUDE.md・feature list 導入）

第2章終了時点の `loglens` の到達状態です。

- `loglens.py` — count コマンド + `--level` フィルタ
- `test_loglens.py` — pytest 10件（count の固定4件 + `--level` の6件）
- `CLAUDE.md` — テスト・作法・落とし穴・進捗管理のルール
- `feature_list.json` — 機能リスト（`--level` のみ passes: true）
- `claude-progress.txt` — 進捗ログ
- `sample.log` — 第1章と同じ20行のサンプルログ

## 実行

```bash
python3 -m pytest -v                                # 10 passed
python3 loglens.py count sample.log                 # 全レベル集計
python3 loglens.py count sample.log --level ERROR   # ERROR 3
```

## 本文実行ログの再現方法

書籍の実行ログは、ch01 の到達状態（loglens.py + sample.log を置き
`git init` した作業ディレクトリ）で以下を順に実行して採取しました
（Claude Code v2.1.214 / Claude Fable 5 / pytest 9.1.1 /
Python 3.14.3）。生成されるコードは実行のたびに細部が変わります。

1回目（pytest 導入）:

```bash
claude -p "loglens.py の count コマンドの現在の動作を固定する\
テストを、test_loglens.py という名前で pytest 用に書いてください。\
sample.log は使わず、テストの中で一時ファイルにログ行を書いて検証\
してください。ERROR / WARN / INFO / OTHER の集計、TOTAL が空行以外\
の全行数と一致すること、存在しないファイルで終了コード 1 になる\
ことをカバーします。書き終えたら pytest を実行し、実行結果をそのまま\
見せてください。" \
  --allowedTools "Write,Bash" --output-format json
```

2回目（--level を検証込み1メッセージで。コミット後に実行）:

```bash
claude -p "loglens に --level オプションを追加してください。使い方は \
python3 loglens.py count sample.log --level ERROR で、指定したレベル\
（ERROR / WARN / INFO / OTHER のいずれか）の件数だけを「ERROR 3」の\
形式で1行表示します。実装したら test_loglens.py にこの機能のテストを\
追加し、pytest を実行して、全テストが通るまで修正してから報告して\
ください。報告には pytest の実行結果をそのまま含めてください。既存の\
テストは変更しないでください。" \
  --allowedTools "Write,Edit,Bash" --output-format json
```

3回目（CLAUDE.md・feature_list.json・claude-progress.txt を置いて
コミットした後、新規セッションで現在地把握。実装はさせない）:

```bash
claude -p "このディレクトリの CLAUDE.md、claude-progress.txt、\
feature_list.json を読んで現在の状態を把握してください。次に pytest \
を実行して、いまのコードが壊れていないことを確認してください。その\
うえで、feature_list.json の passes が false の機能から次に実装する\
べきものを1つ選び、選んだ理由と実装方針を報告してください。実装は\
まだ始めないでください。" \
  --allowedTools "Read,Bash" --output-format json
```

実測値（書籍掲載分）: 1回目 5ターン・45.8秒・$1.25 / 2回目 11ターン・
72.3秒・$1.78 / 3回目 5ターン・45.1秒・$1.13。ターン数・時間・費用は
`--output-format json` の `num_turns` / `duration_ms` /
`total_cost_usd` の値です。

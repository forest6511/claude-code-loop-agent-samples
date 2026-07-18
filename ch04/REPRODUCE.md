# ch04 — Ralph loop（外側ループ・停止条件3種・実測）

第4章終了時点の `loglens` の到達状態です。
（`README.md` は loglens 自体の使い方ドキュメント＝到達状態の一部なので、
章の説明と再現手順はこのファイルにあります）

- `loglens.py` — count + `--level` + `--since` / `--until` + JSON Lines
  入力（`.jsonl`）+ 複数ファイル合算
- `test_loglens.py` — pytest 31件（ch03 の16件 + jsonl-input 8件 +
  multi-file 7件）
- `sample.jsonl` — JSON Lines のテストデータ（12行。全レベル・不正行・
  空行を含む。1周目のループが生成）
- `PROMPT.md` — 毎周注入する夜間ループ指示書（1ループ1タスク）
- `specs/` — 毎周確定注入する仕様2件（jsonl.md / multi-file.md）
- `ralph.sh` — 外側ループ本体（停止条件3種 + jq 完了判定）
- `stub/claude` — ドライラン用の偽 claude（固定コスト JSON を返す）
- `.claude/` — ch03 の Stop hook 2本（command 型 verify.sh + prompt 型）
  をそのまま継続
- `CLAUDE.md` / `feature_list.json`（jsonl-input / multi-file: true）/
  `claude-progress.txt`

## 実行

```bash
python3 -m pytest -q                          # 31 passed
python3 loglens.py count sample.log sample.jsonl
python3 loglens.py count sample.jsonl --level ERROR
```

## ドライラン（Claude を起動せずに ralph.sh を検証）

git リポジトリであることが前提です（HEAD 比較を使うため）。

```bash
git init -q && git add -A && git commit -qm "arrival state"

# 無進捗停止（スタブはコミットしないため 2周で停止）
PATH="$PWD/stub:$PATH" bash ralph.sh

# 予算停止（$4.10/周 × 毎周コミットで 2周 $8.20 ≥ $8.00）
rm -rf logs
PATH="$PWD/stub:$PATH" STUB_COST=4.10 STUB_COMMIT=1 bash ralph.sh
```

ドライラン後は `git reset --hard` でスタブの空コミットを戻し、
`rm -rf logs` で掃除してください。

## 本文実行ログの再現方法

書籍の実行ログは、ch03 の到達状態に本章のファイル一式（PROMPT.md・
specs 2件・ralph.sh・stub/）を加えてコミットした作業ディレクトリで
採取しました（Claude Code v2.1.214 / Claude Fable 5 / pytest 9.1.1 /
Python 3.14.3）。再現するには `feature_list.json` の `jsonl-input` と
`multi-file` を `"passes": false` に戻し、`loglens.py` 等も ch03 の
状態から開始してください（このディレクトリは完了後の到達状態です）。

```bash
bash ralph.sh
```

実測のコンソール出力（2026-07-19）:

```text
iter=1 cost=$3.40479675 total=$3.40 stall=0
iter=2 cost=$3.4736870000000004 total=$6.87 stall=0
DONE: 対象の全機能が passes:true
```

- 1周目: 18ターン・139.8秒・$3.40 → jsonl-input を実装・コミット
- 2周目: 19ターン・114.7秒・$3.47 → multi-file を実装・コミット
- 3周目: jq の完了判定が feature_list.json を確認し、claude を起動
  せずに終了（$0）

生成されるコードは実行のたびに細部が変わります。答え合わせは
「同じ流れをたどれたか」「テスト全件パス・対象2件が passes:true に
なったか」で行ってください。

> 注意: 環境変数 `ANTHROPIC_API_KEY` が設定されていると、`claude -p` は
> サブスクリプションではなく常にその API キーで課金されます（公式仕様）。
> サブスクリプションで実行する場合は `env -u ANTHROPIC_API_KEY bash
> ralph.sh` のようにキーを外してください。夜間放置は `caffeinate -i`
> （macOS）や `nohup` を併用します。

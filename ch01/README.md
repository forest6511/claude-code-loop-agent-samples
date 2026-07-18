# ch01 — なぜLoop Agentか（loglens v0.1 手動開発）

第1章終了時点の `loglens` の到達状態です。

- `loglens.py` — v0.1。`count` コマンドで ERROR / WARN / INFO / OTHER を集計
- `sample.log` — 20行のサンプルログ（7〜8行目に形式外の Traceback 行を含む）

## 実行

```bash
python3 loglens.py count sample.log
```

期待出力:

```text
ERROR 3
WARN  4
INFO  11
OTHER 2
TOTAL 20
```

## 本文実行ログの再現方法

書籍の実行ログは、このディレクトリで以下のプロンプトを非対話モード
（`claude -p`）に与えて採取しました（Claude Code v2.1.214 / Claude Fable 5）。
対話モード（`claude`）で同じプロンプトを打っても流れは同じです。
生成されるコードは実行のたびに細部が変わります。

1回目（v0.1 生成。`sample.log` を置く前に実行）:

```bash
claude -p "loglens.py という名前で Python のログ集計 CLI をこの\
ディレクトリに作ってください。標準ライブラリだけを使います。使い方は \
python3 loglens.py count <ログファイル> で、ログの各行は\
「2026-07-18 09:12:03 INFO Server started on port 8080」のような\
「日付 時刻 レベル メッセージ」形式です。ERROR / WARN / INFO の\
件数を集計して表示してください。" \
  --allowedTools "Write" --output-format json
```

2回目（`sample.log` で TOTAL 18 を確認した後、同セッションを再開して修正依頼）:

```bash
claude -p --resume "<1回目の session_id>" \
  "sample.log で実行したら TOTAL 18 でした。ログは 20 行あります。\
Traceback のような形式外の行も OTHER として集計に含めて、TOTAL は\
ファイルの空行以外の全行数と一致するようにしてください。" \
  --allowedTools "Write,Edit,Read,Bash" --output-format json
```

ターン数・所要時間・費用は `--output-format json` の応答に含まれる
`num_turns` / `duration_ms` / `total_cost_usd` の実測値です。

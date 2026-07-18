# loglens

ログファイルのレベル別件数を集計する CLI。

## 使い方

    python3 loglens.py count app.log
    python3 loglens.py count app.log --level ERROR
    python3 loglens.py count app.log --since 09:00:00 --until 12:00:00
    python3 loglens.py count app.jsonl
    python3 loglens.py count a.log b.jsonl

`--level` は ERROR / WARN / INFO / OTHER のいずれかを指定します。
`--since` / `--until` は HH:MM:SS 形式で集計対象の時刻範囲を指定します。

ファイルは複数指定でき、全ファイルの件数を合算して1つの集計として
表示します（ファイル別の内訳は表示しません）。`.log` と `.jsonl` の
混在も可能で、形式はファイルごとに判定します。`--level` / `--since` /
`--until` はすべてのファイルに適用されます。

## 入力形式

拡張子が `.jsonl` のファイルは JSON Lines（1行 = 1 JSON オブジェクト）として
解釈します。各行のキーは `timestamp`（`2026-07-18 09:12:01` 形式）、
`level`（ERROR / WARN / INFO）、`message`（文字列）です。
レベルが3種以外・キー欠落・JSON として不正な行は OTHER に数えます。
空行はテキスト形式と同じくスキップします。
`--level` / `--since` / `--until` はテキスト形式と同じ挙動で併用できます。

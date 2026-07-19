# loglens

ログファイルのレベル別件数を集計する CLI。

## 使い方

    python3 loglens.py count app.log
    python3 loglens.py count app.log --level ERROR
    python3 loglens.py count app.log --since 09:00:00 --until 12:00:00
    python3 loglens.py count app.jsonl
    python3 loglens.py count a.log b.jsonl
    python3 loglens.py count app.log --top 3

`--level` は ERROR / WARN / INFO / OTHER のいずれかを指定します。
`--since` / `--until` は HH:MM:SS 形式で集計対象の時刻範囲を指定します。
`--top N` は頻出メッセージの上位 N 件を、レベル別集計の後に
「件数 メッセージ」の形式で1行1件表示します。同数のメッセージは
ログで先に出現した順に並び、OTHER に分類される行は集計対象に
含めません。`--level` / `--since` / `--until` / `.jsonl` 入力 /
複数ファイルと併用でき、絞り込み後の行を集計対象とします。

`sample.log` で `--top 3` を実行した例:

    $ python3 loglens.py count sample.log --top 3
    ERROR 3
    WARN  4
    INFO  11
    OTHER 2
    TOTAL 20
    1 Server started on port 8080
    1 User login succeeded user_id=1023
    1 GET /api/items 200 12ms

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

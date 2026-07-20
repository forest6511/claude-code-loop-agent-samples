# loglens

ログファイルのレベル別件数を集計する CLI。

## 使い方

    python3 loglens.py count app.log
    python3 loglens.py count app.log --level ERROR
    python3 loglens.py count app.log --since 09:00:00 --until 12:00:00
    python3 loglens.py count app.jsonl
    python3 loglens.py count a.log b.jsonl
    python3 loglens.py count app.log --top 3
    python3 loglens.py count app.log --format json
    python3 loglens.py count app.log --format csv

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

`--format` は text / json / csv のいずれかを指定します（既定は text で、
出力は従来と同じです）。`--format json` は集計結果をインデント2の
JSON 1オブジェクトで出力します。`--top N` 併用時は `top` キーが
最後に追加され、`--level` 指定時は `counts` にそのレベルだけが
入ります。他のオプション・`.jsonl` 入力・複数ファイルとも併用でき、
絞り込み・合算後の集計結果を出力します。

`sample.log` で `--format json --top 1` を実行した例:

    $ python3 loglens.py count sample.log --format json --top 1
    {
      "counts": {
        "ERROR": 3,
        "WARN": 4,
        "INFO": 11,
        "OTHER": 2
      },
      "total": 20,
      "top": [
        {
          "count": 1,
          "message": "Server started on port 8080"
        }
      ]
    }

`--format csv` は1行目にヘッダ `level,count`、以降に ERROR / WARN /
INFO / OTHER / TOTAL の順で「レベル,件数」を出力します。`--top N`
併用時は空行を1行おき、ヘッダ `count,message` に続けて上位順に
「件数,メッセージ」を出力します。メッセージにカンマや引用符が
含まれる場合は標準の CSV 引用ルール（ダブルクォート囲み）で
守ります。`--level` 指定時はそのレベルの1行だけを出力します。
他のオプション・`.jsonl` 入力・複数ファイルとも併用できます。

`sample.log` で `--format csv --top 3` を実行した例:

    $ python3 loglens.py count sample.log --format csv --top 3
    level,count
    ERROR,3
    WARN,4
    INFO,11
    OTHER,2
    TOTAL,20

    count,message
    1,Server started on port 8080
    1,User login succeeded user_id=1023
    1,GET /api/items 200 12ms

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

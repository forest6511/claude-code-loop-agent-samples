# loglens

ログファイルのレベル別件数を集計する CLI。

## 使い方

    python3 loglens.py count app.log
    python3 loglens.py count app.log --level ERROR
    python3 loglens.py count app.log --since 09:00:00 --until 12:00:00

`--level` は ERROR / WARN / INFO / OTHER のいずれかを指定します。
`--since` / `--until` は HH:MM:SS 形式で集計対象の時刻範囲を指定します。

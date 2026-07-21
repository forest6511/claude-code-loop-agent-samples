# 仕様: JSON 出力（id: format-json）

- count に --format オプションを追加する。値は text / json、既定は text
  例: python3 loglens.py count sample.log --format json
- --format json のとき、集計結果を次の形の JSON 1オブジェクトで
  標準出力に出す（インデント2・キーはこの順）
  {"counts": {"ERROR": 3, "WARN": 4, "INFO": 11, "OTHER": 2},
   "total": 20}
- --top N 併用時は "top" キーを最後に追加し、
  [{"count": 件数, "message": "メッセージ"}, ...] を上位順で入れる
- --format text（既定）の出力は現在と1文字も変えない
- --level / --since / --until / .jsonl 入力 / 複数ファイルと併用できる
  （絞り込み・合算後の集計結果を出力する）
- テストで挙動を固定する。既存のテストは変更しない

# 仕様: CSV 出力（id: format-csv）

- --format の選択肢に csv を追加する（text / json / csv）
  例: python3 loglens.py count sample.log --format csv
- --format csv のとき、1行目にヘッダ level,count、以降に
  ERROR / WARN / INFO / OTHER / TOTAL の順で「レベル,件数」を出す
- --top N 併用時は空行を1行おき、ヘッダ count,message に続けて
  上位順で「件数,メッセージ」を出す。メッセージにカンマや引用符が
  含まれる場合は標準の CSV 引用ルール（ダブルクォート囲み）で守る
- --format text / json の出力は変更しない
- --level / --since / --until / .jsonl 入力 / 複数ファイルと併用できる
- テストで挙動を固定する。既存のテストは変更しない

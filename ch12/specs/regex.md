# 仕様: 正規表現フィルタ（id: regex）

- count に --regex オプションを追加する。値は Python の正規表現パターン
  例: python3 loglens.py count sample.log --regex "timeout|refused"
- メッセージ部分がパターンに一致（re.search・大文字小文字は区別）する
  行だけを集計対象にする。レベル判定より後・集計より前の絞り込みとして働く
- 不正なパターン（re.error）のときは、パターンと理由を標準エラーに出して
  exit 2 で終了する
- --level / --since / --until / --top / --format json / --format csv /
  .jsonl 入力 / 複数ファイルと併用できる（すべての絞り込みの積で集計する）
- --regex を指定しないときの出力は現在と1文字も変えない
- テストで挙動を固定する。既存のテストは変更しない

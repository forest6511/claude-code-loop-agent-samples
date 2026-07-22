# 仕様: ファイル書き出し（id: output）

- count に --output PATH オプションを追加する
  例: python3 loglens.py count sample.log --output result.txt
- --output のとき、標準出力に出すはずの内容（--format text / json / csv
  すべて）をそのまま PATH のファイルに書き出し、標準出力には
  「wrote: PATH」を1行だけ出す
- 書き出しは UTF-8・末尾に改行あり。既存ファイルは上書きする
- PATH の親ディレクトリが存在しないときは error: を標準エラーに出して
  exit 2
- --output を指定しないときの出力は現在と1文字も変えない
- テストで挙動を固定する。既存のテストは変更しない

# 仕様: 時間帯別集計（id: stats）

- count に --stats フラグを追加する
  例: python3 loglens.py count sample.log --stats
- --stats のとき、通常の集計の後に空行を1行おき、行が1件以上ある
  時間帯だけを「HH時 N件」の形式で時刻順に出す（HH は 00〜23 の2桁）
- 対象は他の絞り込み（--level / --since / --until / --regex）適用後の行。
  タイムスタンプを持たない行（OTHER）は時間帯集計に含めない
- --format json との併用時は "stats" キー（{"HH": 件数} 形式・出現した
  時間帯のみ・時刻順）を最後に追加する
- --format csv との併用は非対応。error: を標準エラーに出して exit 2
- --stats を指定しないときの出力は現在と1文字も変えない
- テストで挙動を固定する。既存のテストは変更しない

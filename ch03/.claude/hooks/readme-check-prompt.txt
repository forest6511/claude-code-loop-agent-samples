開発セッションの終了判定を行います。次の JSON の
last_assistant_message を読んでください: $ARGUMENTS

判定基準: loglens.py の変更（機能追加・オプション追加・挙動変更）を
報告しているのに、README.md の更新に言及していない場合だけ
{"ok": false, "reason": "loglens.py の変更が README.md の使い方に
反映されているか確認し、必要なら更新してから終了してください"} を
返します。それ以外はすべて {"ok": true} を返します。

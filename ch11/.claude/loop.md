ops/incoming の新着ログを処理する定期メンテナンスです。

1. ops/incoming/*.log を確認する。無ければ「新着なし」と1行だけ
   報告して終わる
2. 各ファイルを python3 loglens.py count <file> で集計し、
   「HH:MM file ERROR n / WARN n / INFO n」形式の1行を
   ops/daily-report.txt に追記する
3. 処理したファイルは ops/processed/ へ移動する
4. ERROR が3件以上のファイルがあれば、報告の先頭に「要確認」と書く

このループでは新しい作業を始めない。ファイルの編集は
ops/daily-report.txt への追記だけ。コミット・push はしない。

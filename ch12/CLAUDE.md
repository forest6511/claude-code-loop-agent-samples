# loglens 開発ルール

## テスト（毎回）
- 変更後は python3 -m pytest を実行し、全テストが通ってから報告する
- 報告には pytest の実行結果をそのまま含める
- 既存のテストの削除・書き換えは禁止。仕様変更でテストの変更が
  必要なときは、理由を説明して人間の判断を待つ

## 作法
- 標準ライブラリのみ使う（依存の追加は人間に確認）
- argparse の subparsers 構造を維持する
- 1機能ずつ実装する。頼まれていない機能を足さない

## 落とし穴
- ログには形式外の行（Traceback 等）が混ざる。形式外の行は OTHER
  として集計し、TOTAL は空行以外の全行数と一致させる

## 進捗管理
- 作業開始時に claude-progress.txt と feature_list.json を読む
- feature_list.json は passes の値だけを変更してよい。項目の削除・
  文言の変更は禁止
- 機能を1つ完了するたびに claude-progress.txt に1行追記し、
  git commit する

## ガードプロファイル
- 維持ループ（無人運転・/loop・定期処理）は
  `claude --settings .claude/settings.maintenance.json` で起動する。
  テスト編集を機械的に拒否する PreToolUse deny が有効になる
- 人間が承認した仕様（SPEC.md）に基づく機能追加セッションは通常起動。
  既存テスト無変更の検問は /goal 条件と checker レビューで行う

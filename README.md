# Claude Codeで実践するAI駆動開発とLoop Agent — サンプルコード

書籍「Claude Codeで実践するAI駆動開発とLoop Agent: 手動プロンプトをやめて、開発を自律ループで回す12段階」（森川陽介）のサンプルリポジトリです。

本書では、ログ集計CLI「loglens」を12章かけて手動開発から完全自律開発へ育てていきます。各章のディレクトリに、その章時点の loglens のコード・ループ設定（hooks / skills / agents / スクリプト）・実行ログを収録しています。

## 構成

- `ch01/` なぜLoop Agentか（loglens v0.1 手動開発）
- `ch02/` 検証を渡す（pytest・CLAUDE.md・進捗ファイル）
- `ch03/` Stop hook（verify.sh・settings.json）
- `ch04/` Ralph loop（ralph.sh・PROMPT.md・停止条件）
- `ch05/` Maker-Checker（checker エージェント定義）
- `ch06/` 検証Skills（verify-loglens SKILL.md）
- `ch07/` /goal（完了条件の設計例）
- `ch08/` worktree並列（並列ループ設定）
- `ch09/` /loopと/schedule（loop.md・routine 設定）
- `ch10/` Agent SDK（Python ループスクリプト・GitHub Actions）
- `ch11/` 運用と安全（ガードレール設定集）
- `ch12/` 総仕上げ（SPEC.md → リリースの全記録）

## 動作環境

- Claude Code v2.1.202 以降（/goal は v2.1.139 以降）
- Python 3.12+

各章の詳細な手順は書籍本文を参照してください。

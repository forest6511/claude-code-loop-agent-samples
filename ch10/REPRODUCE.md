# ch10 — Agent SDK（検証ループのスクリプト化と GitHub Actions）

第10章終了時点の `loglens` の到達状態です。機能追加はなく、検証ループが
Agent SDK の Python スクリプトになり、PR を開くと GitHub Actions で走ります。

- `verify_loop.py` — SDK 検証ループ。check（読み取りチェック・既定）/ `--fix`
  （修復）の2モード。最終判定はエージェントの自己申告ではなく決定的ゲート
  （pytest / ruff / カバレッジ90%）の再実行で行い、exit 0/1 が CI の合否
- `.github/workflows/verify.yml` — `pull_request` で検証ループを実行。
  `timeout-minutes` がジョブ側の壁時計上限（SDK にセッションタイムアウトなし）
- その他のファイルは ch09 の到達状態と同じ（85テスト・10機能 passes:true）

本物のリポジトリ（GitHub Actions が実際に動く場所）:
https://github.com/forest6511/loglens

## セットアップ

```bash
python3 -m venv .venv
.venv/bin/pip install claude-agent-sdk   # 実測時 0.2.124（CLI 2.1.216 同梱）
```

## 実行（ローカル）

```bash
# チェックモード（読み取り専用・setting_sources=[] で遮断）
env -u ANTHROPIC_API_KEY .venv/bin/python verify_loop.py

# 修復モード（プロジェクト設定 = CLAUDE.md + Stop hook を読み込む）
env -u ANTHROPIC_API_KEY .venv/bin/python verify_loop.py --fix

# 予算上限の挙動確認（error_max_budget_usd + query() の例外）
env -u ANTHROPIC_API_KEY .venv/bin/python verify_loop.py --max-budget 0.05
```

## 本文実行ログの再現方法

書籍の実行ログは claude-agent-sdk 0.2.124（同梱 CLI 2.1.216）/
Claude Fable 5 / Python 3.14.3（CI は 3.12.13）/ サブスクリプション認証で
採取しました。生成される診断文は実行のたびに細部が変わります。

- 緑（master・遮断版）: 4ターン / $0.04 / 10.1秒 / gate PASS / exit 0
- 赤（`--since` 境界バグ・遮断版）: 5ターン / $0.37 / 38.0秒 /
  診断のみ・ファイル未変更 / gate FAIL / exit 1（2回目は 6ターン / $0.13）
- 修復（`--fix`）: 16ターン / $0.61 / 65.3秒 / loglens.py 1行 + README 2行 /
  Stop hook feedback 1回 / gate PASS / exit 0
- 予算停止: `--max-budget 0.05` で subtype=error_max_budget_usd /
  5ターン / $0.07（上限はターン境界で判定されるためわずかに超える）

赤の状態は `loglens.py` の時刻フィルタ（`--since` 側の比較）を
`time < since` から `time <= since` に変えると再現できます（8件失敗）。

### 「チェックが直してしまう」事故の再現（本文の v1 → v2 の物語）

`verify_loop.py` の check モードから `disallowed_tools` と
`setting_sources=[]` の2行を外すと v1 の状態になります。`setting_sources`
未指定（None）は「読み込まない」ではなく「CLI と同じ既定 = user / project /
local を全部読む」です。開発機のユーザー設定（`permissions.defaultMode` 等）
とプロジェクトの Stop hook が読み込まれ、読み取り専用のつもりのチェックが
バグを修正してターンを終えます（実測: 19ターン / $1.61 / Edit 2回 /
Stop hook feedback 2回）。

## CI（GitHub Actions）

```bash
claude setup-token   # ブラウザ承認 → 長期トークン（サブスク必須・表示は一度きり）
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <owner>/loglens
```

実測（forest6511/loglens）:

- 緑 PR #1（README 追記）: エージェント 6ターン / $0.20 / 16.8秒 →
  gate PASS → ジョブ success
- 赤 PR #2（境界バグ）: エージェント 9ターン / $0.14 / 34.4秒 →
  失敗8テスト名の列挙・`loglens.py` 107行目の特定・`--until` 側との
  非対称の指摘・ファイル未変更 → gate FAIL → exit 1 → ジョブ failure

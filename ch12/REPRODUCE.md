# 第12章 総仕上げ　再現手順

仕様書1枚からリリースまでの通し。本ディレクトリはマージ後の master 相当
（`alert` 実装済み・テスト 104 件・維持プロファイル・保存済みワークフロー入り）。

実測環境: Claude Code v2.1.216 / Fable 5 / サブスクリプション認証
（`env -u ANTHROPIC_API_KEY`。API キーがあると `-p` は常にキー課金）。

## 1. 仕様インタビュー（対話セッション）

公式テンプレート（best-practices「Let Claude interview you」）の日本語版を投げる。

```text
loglens に、ログのエラー件数がしきい値を超えたら知らせるアラート機能を
追加したい。AskUserQuestion ツールを使って、私に詳細なインタビューを
してください。技術的な実装、CLI の使い勝手、エッジケース、懸念、
トレードオフについて聞いてください。当たり前の質問はせず、私がまだ
考えていない難しい部分を掘ってください。すべてカバーしたと思えるまで
インタビューを続け、終わったら完全な仕様を SPEC.md に書いてください。
```

実測: 4ラウンド・16問 → SPEC.md 162行。人間レビューで「E2E 受け入れ手順が
ない」を差し戻し → 266行（本ディレクトリの SPEC.md がその完成形）。
セッション $8.68 / API 10m21s。

## 2. 三重ゲート実装（`-p` + `/goal`）

新セッション・新ブランチで。Stop hook（verify.sh 常設）+ `/goal` evaluator +
checker サブエージェントの三重ゲート。

```bash
git checkout -b alert-notify
env -u ANTHROPIC_API_KEY claude -p "/goal SPEC.md の alert サブコマンド
を実装する。完了条件: (1) SPEC.md の「受け入れ手順（E2E）」1〜7 を
すべて実行し、実際の出力と終了コードを会話に貼ること (2) /verify-loglens
を実行し、その要約行を会話に出力して全項目合格であること (3) checker
サブエージェントにレビューさせ、正確性の指摘がゼロであること。指摘が
あれば修正して再レビュー (4) git diff --stat を会話に貼り、既存テスト
の削除・書き換えがないこと (5) SPEC.md の実装作業一覧 1〜5 を完了し、
変更を1つのコミットにまとめること。or stop after 40 turns" \
  --output-format json
```

実測: 27T / 291.3s / $6.98・evaluator 差し戻し 0・checker「指摘なし」・
テスト 85→104 件（既存無変更）・1コミット。E2E 7ケースは手動再実行でも全一致:

```bash
python3 loglens.py alert sample.log --threshold 4   # OK: ERROR 3 < 4, exit 0
python3 loglens.py alert sample.log --threshold 3   # ALERT(境界), exit 3
python3 loglens.py alert sample.log sample.jsonl --threshold 5  # 合算6, exit 3
python3 loglens.py alert sample.log --threshold 0   # exit 2
python3 loglens.py alert no_such.log --threshold 1  # exit 1
```

## 3. マージ前レビュー（dynamic workflows）

対話セッションで自分の言葉で依頼（`-p`・scheduled task からは起動しない）。

```text
ワークフローを使って、master との差分（git diff master..HEAD に含まれる
変更）を1ファイル1エージェントで並列レビューしてください。観点は正確性
（SPEC.md との不一致・既存機能への影響・テストの妥当性）だけ。見つかった
指摘は敵対的に検証（本当に問題か反証を試みる）してから、1つのランク付き
サマリーにまとめてください。
```

実測: 8 agents（Review 7 + Verify 1）/ 2m26s / セッション $15.58。
指摘1件（medium）= 人間のガード削除コミットに「プロファイルの実体がない」。
`/workflows` → run 選択 → `s` でプロジェクトスコープに保存 →
`.claude/workflows/diff-review-per-file.js`（次回から `/diff-review-per-file`）。

## 4. 維持プロファイル（レビュー指摘対応）

テスト保護 deny は `.claude/settings.maintenance.json` に実体化。
維持ループはこれで起動する:

```bash
claude --settings .claude/settings.maintenance.json
```

deny 発火のプローブ実測: テスト追記を指示 → 3T / $1.62 / 30.6s で
「テストの編集は禁止です」と機械拒否・ファイル無変更。

## 5. PR → CI → マージ

```bash
git push -u origin alert-notify
gh pr create --title "feat: alert サブコマンド" --body "..."
gh pr checks 4        # verify-loop pass
gh pr merge 4 --merge --delete-branch
```

CI 実測: agent 5T/$0.18/16.9s + deterministic gate PASS。
注意: 初回の CI はローカル作業でサブスク限度枠を使い切った直後だったため
agent が 1T/$0.00 で走れず、決定的ゲート単独の PASS で green になった
（二層判定の防御が本番で再現）。完全なログは枠回復後の re-run。

一周の合計: 約 $33（仕様 $8.68 + 実装 $6.98 + レビュー $15.58 +
プローブ $1.62 + CI $0.18）・人間の判断点は仕様承認・レビュー方針・
マージの3点のみ。

# ch09 — /loop と /schedule（時間で動くループ・実測）

第9章終了時点の `loglens` の到達状態です。機能追加はありません（運用の章）。
（`README.md` は loglens 自体の使い方ドキュメント＝到達状態の一部なので、
章の説明と再現手順はこのファイルにあります）

- `loglens.py` / `test_loglens.py` — ch08 から変更なし
  （テスト85件・feature_list 10機能 passes: true）
- `loggen.sh` — 疑似ログ生成（COUNT 個を INTERVAL 秒おきに
  `ops/incoming/` へ置く。ログ着信の再現用・新規）
- `.claude/loop.md` — 引数なし `/loop` 用の無人運転指示書（新規）
- `.claude/settings.json` — 無人発火用の `permissions.allow` 6件を追加
  （Stop hook 2本は ch03 のまま）
- `.gitignore` — `ops/`（実行時データ）を追加

## 再現手順

```bash
mkdir -p ops/incoming ops/processed
env -u ANTHROPIC_API_KEY claude    # 対話セッション（manual mode で実測）
```

1. 固定間隔 — `/loop 2m ops/incoming の .log ファイルを確認してください。
   あれば各ファイルを python3 loglens.py count で集計して結果を1行に要約し、
   ops/daily-report.txt に追記してから ops/processed/ へ移動します。
   無ければ「新着なし」とだけ報告してください。` を設定し、
   別ターミナルで `bash loggen.sh` を1回 → 次の発火で処理される
2. スキル発火 — `/loop 2m /verify-loglens 定期健全性チェック`。
   初回に Skill 使用確認が出る（don't ask again を選ぶと以後無人）
3. 罠の再現 — `verify-loglens/SKILL.md` に
   `disable-model-invocation: true` を足してセッションを立て直し、
   同じ `/loop` を打つ → Skill ツールがエラーで拒否される。確認後は戻す
4. self-paced — `/loop <プロンプトのみ>`（Monitor 提案を承認）/
   「Monitor ツールは使わず」で ScheduleWakeup 型
5. 無人運転 — `bash loggen.sh 4 420 &` → `/loop 10m`（loop.md が走る）

## 実測サマリ（2026-07-21 / v2.1.216 / Claude Fable 5 / サブスク認証）

- 固定間隔 `/loop 2m`: cron `*/2 * * * *`・ジョブID d149f7c0。
  発火 (1:16pm) で新着1件処理（処理完了 13:17 = jitter）、
  発火 (1:18pm) は空振り7秒。CronList に `[session-only]` 表示
- スキル発火: 発火時に `❯ /verify-loglens 定期健全性チェック` が
  再投入されスキル実行（テスト 85 passed・lint 合格・カバレッジ 98.74%）
- disable-model-invocation: `Error: Skill verify-loglens cannot be used
  with Skill tool due to disable-model-invocation`（v2.1.196+）。
  その後モデルは SKILL.md を Read し同等チェックを手動実行
  （allowed-tools の保証は消える）
- self-paced（Monitor）: 反復1で Monitor を自分から提案
  （process_substitution 含みで権限確認）→ persistent 常駐 →
  13:30:48 投入 → 13:30:59 処理完了（11秒）
- self-paced（ScheduleWakeup）: 反復1空振り → 5分後を予約
  （CronList に one-shot 914694a5）→ 13:37 起床
  `Claude resuming /loop wakeup` → 2回連続空振りで自己終了
- ワンショット: 「8分後に…」→ `CronCreate(42 13 21 7 *)` →
  13:42:07 発火・報告後に自己削除
- 無人運転25分: `/loop 10m` + 着信7分おき4本 → 発火3回
  （1:51pm 空振り / 2:01pm 2件一括 / 2:11pm 1件）・計4件処理・
  権限による停止ゼロ
- セッション費用（/usage）: 壁時計 49分40秒で $10.26
  （Fable 5 $9.66 + Haiku $0.60 = prompt 型 Stop hook の判定分）・
  コード変更 0行
- `/schedule`: list = RemoteTrigger HTTP 200（0件）。作成会話は
  「リポジトリは GitHub 等にあるか」で停止（ローカル bare origin では
  routine を作れない → 第10章で GitHub 接続後に作成）

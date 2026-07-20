# ch06 — 検証Skills（/verify-loglens・実測）

第6章終了時点の `loglens` の到達状態です。
（`README.md` は loglens 自体の使い方ドキュメント＝到達状態の一部なので、
章の説明と再現手順はこのファイルにあります）

- `loglens.py` — count + `--level` + `--since` / `--until` + JSON Lines
  入力 + 複数ファイル合算 + `--top N` + `--format text/json/csv`
- `test_loglens.py` — pytest 53件（ch05 の39件 + format-json 8件 +
  format-csv 6件）
- `.claude/skills/verify-loglens/SKILL.md` — 検証スキル（テスト+lint+
  カバレッジの3点ゲート。619字・23行）
- `.claude/agents/checker.md` — ch05 の checker に `skills:
  [verify-loglens]` を追加（起動時にスキル全文をプリロード）
- `specs/format-json.md` / `specs/format-csv.md` — 2機能の仕様
- `feature_list.json` — 7機能すべて passes: true。ch06 から `verify`
  フィールドは `python3 -m pytest` でなくスキル名 `/verify-loglens`
- `.claude/settings.json` — 常設ゲートは ch03 の2本のまま

## 準備

```bash
python3 -m pip install ruff pytest-cov   # lint とカバレッジの導入
```

## 実行

```bash
python3 -m pytest -q                          # 53 passed
python3 -m ruff check .                       # All checks passed!
python3 -m pytest -q --cov=loglens --cov-fail-under=90
python3 loglens.py count sample.log --format json --top 1
python3 loglens.py count sample.log --format csv
```

## 実測サマリ（v2.1.216 / Claude Fable 5 / サブスク認証）

- Run 1（format-json 実装）: `claude -p "specs/format-json.md の仕様
  どおり…/verify-loglens format-json を呼んで3点すべて合格させて…"`
  `--allowedTools "Read,Write,Edit,Bash,Skill"`
  27ターン / 155.6秒 / $4.24。テスト39→47件。transcript に Skill ツール
  呼び出し {"skill": "verify-loglens", "args": "format-json"} が記録され、
  3点検証（47 passed / All checks passed! / カバレッジ98.04%）を1コマンド
  で実行。実装コミット後、ch03 の prompt 型 README 検問が発火して README
  追記まで実施
- Run 2（format-csv 実装・スキル使い回し）: 検証の指示は
  「検証は /verify-loglens format-csv で」の1句のみ。
  31ターン / 152.2秒 / $4.73。テスト47→53件。カバレッジ98.29%
- Run 3（checker プリロード・レビュー）: checker.md に skills フィールド
  追加後、diff 1e260fd..HEAD を checker に中継。3ターン / 144.3秒 /
  $3.52 →「指摘なし」。checker は起動直後の2通目ユーザーメッセージとして
  スキル全文（$ARGUMENTS は空欄展開）を受け取り、報告内で「実行ツールが
  与えられていないためコマンド実行による検証は行っていません（静的照合
  のみ）」と明示 = スキルは知識を運び、能力は tools が決める実測例
- 累計 $12.50

## スキル呼び出しの再現

```bash
env -u ANTHROPIC_API_KEY claude -p \
  "specs/format-json.md の仕様どおり、count に --format json を実装して
ください。テストを先に追加し、実装が終わったら /verify-loglens
format-json を呼んで3点すべて合格させてください。" \
  --allowedTools "Read,Write,Edit,Bash,Skill" --output-format json
```

`--allowedTools` に `Skill` が必要（スキル呼び出しは Skill ツールの
実行として扱われるため）。

## 注意

- `disable-model-invocation: true` を SKILL.md に付けると、maker の
  自動呼び出し・checker へのプリロード・スケジュール発火（v2.1.196+）の
  3経路が同時に閉じる（本文の落とし穴参照）
- スキルは指示でありゲートではない。常設の検問は `.claude/settings.json`
  の Stop hook（verify.sh）に置いたまま運用する

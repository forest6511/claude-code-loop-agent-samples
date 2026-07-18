# ch03 — Stop hook（完了ゲート・自己修復・prompt型）

第3章終了時点の `loglens` の到達状態です。
（`README.md` は loglens 自体の使い方ドキュメント＝到達状態の一部なので、
章の説明と再現手順はこのファイルにあります）

- `loglens.py` — count + `--level` + `--since` / `--until`
- `test_loglens.py` — pytest 16件（ch02 の10件 + time-range の6件）
- `.claude/settings.json` — Stop hook 2本（command 型 verify.sh + prompt 型）
- `.claude/hooks/verify.sh` — 完了ゲート（pytest → exit 0/2 変換）
- `.claude/hooks/readme-check-prompt.txt` — prompt 型の判定基準
- `README.md` — loglens の使い方（`--since` / `--until` 反映済み）
- `CLAUDE.md` / `feature_list.json`（time-range: true） / `claude-progress.txt`

## 実行

```bash
python3 -m pytest -q                                        # 16 passed
python3 loglens.py count sample.log --since 09:13:00 --until 09:15:00
echo '{"stop_hook_active": false}' | \
  CLAUDE_PROJECT_DIR="$PWD" bash .claude/hooks/verify.sh; echo "exit=$?"
```

## 本文実行ログの再現方法

書籍の実行ログは、ch02 の到達状態に `.claude/`（verify.sh + settings.json）を
加えて `git init` した作業ディレクトリで採取しました（Claude Code v2.1.214 /
Claude Fable 5 / pytest 9.1.1 / Python 3.14.3）。
生成されるコードは実行のたびに細部が変わります。

> 注意: 環境変数 `ANTHROPIC_API_KEY` が設定されていると、`claude -p` は
> サブスクリプションではなく常にその API キーで課金されます（公式仕様）。
> サブスクリプションで実行する場合は `env -u ANTHROPIC_API_KEY claude -p ...`
> のようにキーを外してください。

1回目（自己修復。`loglens.py` の `if not line.strip():` を `if not line:` に
書き換えてバグを仕込んでから実行）:

```bash
claude -p "sample.log で件数が最も多いレベルはどれですか。loglens で集計して\
答えてください。" \
  --allowedTools "Read,Edit,Bash" --output-format json
```

2回目（--since/--until を検証指示なしの1メッセージで。バグ修復コミット後）:

```bash
claude -p "loglens に --since と --until オプションを追加してください。使い方\
は python3 loglens.py count sample.log --since 09:12:05 --until 09:12:09 で、\
タイムスタンプの時刻部分が範囲内（両端を含む）の行だけを集計します。指定は\
片方だけでもかまいません。形式外の行（OTHER）は時刻を持たないため、--since \
/ --until 指定時は集計から除外します。--level との併用も動くようにして\
ください。" \
  --allowedTools "Read,Write,Edit,Bash" --output-format json
```

3回目（prompt 型。README.md を count/--level のみの古い状態で置き、
readme-check-prompt.txt を jq で settings.json に合流させた後）:

```bash
jq --rawfile p .claude/hooks/readme-check-prompt.txt \
  '.hooks.Stop[0].hooks += [{"type": "prompt", "prompt": $p}]' \
  .claude/settings.json > settings.tmp
mv settings.tmp .claude/settings.json

claude -p "loglens.py のモジュール docstring の使い方の節に、--since / \
--until を使う例を1行追加してください。" \
  --allowedTools "Read,Edit,Bash" --output-format json
```

# SPEC: alert サブコマンド（エラー件数しきい値アラート）

作成日: 2026-07-21
状態: インタビュー完了・実装前（人間承認済み仕様）

## 目的

ログのエラー件数がしきい値以上になったことを、終了コードと stderr で
呼び出し側（cron / CI / シェルスクリプト）に知らせる。

alert は「判定専用」のサブコマンドとする。集計の詳細表示は count の
仕事であり、発火後の調査は `loglens count` で行う2コマンド運用とする。

## CLI 仕様

```
python3 loglens.py alert <logfile>... --threshold N
    [--level {ERROR,WARN,INFO,OTHER}]
    [--since HH:MM:SS] [--until HH:MM:SS]
    [--regex PATTERN]
```

| 引数 | 必須 | 意味 |
|---|---|---|
| `logfile` (1個以上) | ○ | 対象ログ。count と同じく .log / .jsonl 混在可、複数指定は合算 |
| `--threshold N` | ○ | 発火しきい値。整数。デフォルト値なし（未指定は argparse エラー → exit 2） |
| `--level` | — | 判定対象レベル。単一指定のみ。未指定時は **ERROR** |
| `--since` / `--until` | — | count と同じ時刻範囲フィルタ（両端を含む） |
| `--regex` | — | count と同じメッセージフィルタ（re.search・大文字小文字区別） |

count の出力系オプション（`--format` / `--output` / `--top` / `--stats`）は
alert には**載せない**（初回スコープ外。将来必要になれば追加する）。

## 判定仕様

1. 全ファイルを count と同一のロジック（count_levels 再利用）で読み、
   `--since` / `--until` / `--regex` を適用したうえで、対象レベルの
   件数を**全ファイル合算**で求める。
2. **合算件数 >= threshold なら発火**（「以上で発火」。ちょうど N 件でも発火する）。
3. 発火単位はファイル毎ではなく合算のみ。ファイル毎に監視したい場合は
   alert をファイル毎に実行する運用で対応する。

## 出力仕様

正常時・発火時とも、stdout に**必ず1行サマリ**を出す（英語トークン形式）。

```
OK: ERROR 3 < 10          ← 非発火（exit 0）
ALERT: ERROR 12 >= 10     ← 発火（exit 3）
```

書式: `{OK|ALERT}: {LEVEL} {count} {<|>=} {threshold}`

- 先頭トークン（`OK:` / `ALERT:`）で grep できることを保証する。
- 発火時は**同一内容の行を stderr にも出す**（stdout はパイプで消費されても
  stderr 経由で気づけるようにするため）。
- 非発火時の stderr は無出力。

## 終了コード

| code | 意味 |
|---|---|
| 0 | 非発火（件数 < threshold） |
| 1 | ファイルエラー（存在しない・読めない等、count と同じ） |
| 2 | 引数エラー（下記バリデーション参照） |
| 3 | **発火**（件数 >= threshold）※新設 |

「発火（3）」と「壊れていて判定できなかった（1/2）」は必ず区別される。
ファイルが読めない場合に 0 や 3 を返してはならない。

## バリデーションとエラー処理（すべて exit 2）

判定より前に、以下を引数エラーとして拒否する。

1. `--threshold` 未指定（argparse required）。
2. `--threshold` が整数でない（argparse type=int）。
3. `--threshold` が **0 以下**。`>=` 方式では N=0 は「常時発火」となり
   誤設定と区別できないため拒否する。「1件でもあれば発火」は N=1 で表現する。
   エラー例: `error: --threshold は 1 以上を指定してください`
4. **死に組合せの拒否**: `--level OTHER` と `--regex` の併用、および
   `--level OTHER` と `--since` / `--until` の併用は exit 2。
   理由: 既存実装では --regex はメッセージを持たない OTHER 行を全除外し、
   --since/--until は時刻を持たない OTHER 行を全除外するため、これらの
   組合せは常に 0 件 =「永遠に発火しない監視」になる。設定段階で潰す
   （--stats × --format csv の拒否と同じ既存パターン）。
5. `--regex` が不正なパターン（count と同じ扱い・同形式のメッセージ）。

エラーチェックの順序: 引数バリデーション（exit 2）→ ファイル読み込み
（OSError → exit 1）→ 判定（exit 0 / 3）。

## エッジケースの規定

- 空ファイル・フィルタ後 0 件: `OK: ERROR 0 < N` で exit 0（正常）。
- OTHER 行の扱い: デフォルト（--level 未指定 = ERROR）では Traceback 等の
  OTHER 行は件数に**含めない**。Traceback 込みで監視したい場合は
  `--level OTHER` を別途実行する（フィルタ併用は上記のとおり不可）。
- .jsonl の不正行・キー欠落行は count と同じく OTHER として扱われる
  （= デフォルトでは判定対象外）。
- 複数ファイル中の1つでも読めなければ、判定せず exit 1（count と同じ
  fail-fast）。部分的な合算で判定してはならない。

## 実装方針

- `count_levels()` をそのまま再利用し、`counts[対象レベル]` を threshold と
  比較する薄い `cmd_alert()` を追加する。集計ロジックの複製は作らない。
- argparse の subparsers 構造を維持し、`alert` サブパーサーを追加する。
- 標準ライブラリのみ使用（依存追加なし）。

## 実装作業一覧

1. `loglens.py` に `alert` サブコマンドと `cmd_alert()` を追加する。
2. `test_loglens.py` にテストを追加する（既存テストの削除・書き換えは禁止）。
   最低限カバーするケース:
   - 非発火（exit 0・OK 行）／発火（exit 3・ALERT 行が stdout と stderr 両方）
   - 境界: ちょうど N 件で発火（>=）
   - --level 指定（WARN / OTHER 単独）／未指定時 ERROR
   - --since/--until/--regex 併用時のフィルタ後判定
   - 複数ファイル合算での発火（単体では超えないが合算で超えるケース）
   - .jsonl 入力・.log 混在
   - exit 2 系: --threshold 未指定・0・負数・非整数、OTHER×regex、
     OTHER×since/until、不正 regex
   - exit 1 系: 存在しないファイル（複数指定中の1つが欠けるケース含む）
3. **feature_list.json に以下のエントリを追加する**（本 SPEC が人間承認済み
   仕様であるため、この追加は承認済み作業に含まれる。これ以外の項目追加・
   削除・文言変更は従来どおり禁止、passes の更新のみ可）:

   ```json
   {
     "id": "alert-threshold",
     "description": "alert サブコマンドを追加し、指定レベルの件数がしきい値以上なら exit 3 と ALERT 行で知らせる",
     "verify": "/verify-loglens",
     "passes": false
   }
   ```

4. README.md に alert の使い方と終了コード表（3 = 発火）を追記する。
5. 完了時に claude-progress.txt へ1行追記し、git commit する。
6. 検証は /verify-loglens（テスト・lint・カバレッジ）合格を条件とする。

## スコープ外（将来拡張の候補）

- 率（エラー率 %）や時間窓（1時間バケット毎）での判定
- レベル毎の複数しきい値（ERROR=10,WARN=100 のような指定）
- 複数レベルの合算監視（ERROR+OTHER 等）
- --format json / --output 等の出力系オプション
- Webhook 等の外部通知（現状は終了コードを cron / CI 側で拾う設計）

## インタビューで確定した決定事項（記録）

| 論点 | 決定 |
|---|---|
| CLI 形状 | 新サブコマンド。名前は check ではなく **alert**（監視意図が名前から分かるように） |
| 対象レベル | 単一指定・デフォルト ERROR |
| 通知方法 | 終了コード + stderr（stdout には常に1行サマリ） |
| 判定単位 | フィルタ後の絶対件数・全ファイル合算 |
| フィルタ | count の全フィルタ（--level/--since/--until/--regex）対応 |
| 発火コード | 3（既存 0/1/2 は不変） |
| 境界 | count >= N で発火 |
| threshold | --threshold N・指定必須・デフォルトなし・N >= 1 強制 |
| 死に組合せ | OTHER×regex、OTHER×since/until は exit 2 で拒否 |
| サマリ形式 | 英語トークン形式（OK: / ALERT: 先頭） |
| feature_list.json | alert-threshold エントリ追加を実装作業として本 SPEC に明記（人間承認済み） |

## 受け入れ手順（E2E）

リポジトリ同梱の sample.log / sample.jsonl で機能が動くことを証明する。
前提となる実件数（`loglens count` で検証可能）:

- sample.log: ERROR 3 / WARN 4 / INFO 11 / OTHER 2
- sample.jsonl: ERROR 3 / WARN 2 / INFO 3 / OTHER 3
- 合算 ERROR: 6

各コマンドの直後に `echo $?` で終了コードを確認する。

### 1. 非発火（exit 0）

```
$ python3 loglens.py alert sample.log --threshold 4
OK: ERROR 3 < 4
$ echo $?
0
```

stderr は無出力であること。

### 2. 発火（exit 3・stderr にも同一行）

```
$ python3 loglens.py alert sample.log --threshold 2
ALERT: ERROR 3 >= 2
$ echo $?
3
```

stderr にも `ALERT: ERROR 3 >= 2` が出ること。確認例:

```
$ python3 loglens.py alert sample.log --threshold 2 2>err.txt >/dev/null; cat err.txt
ALERT: ERROR 3 >= 2
```

### 3. 境界（ちょうど N 件で発火）

```
$ python3 loglens.py alert sample.log --threshold 3
ALERT: ERROR 3 >= 3
$ echo $?
3
```

### 4. 複数ファイル合算（単体では超えず、合算で超える）

sample.log(3) も sample.jsonl(3) も単体では 5 未満だが、合算 6 で発火する。

```
$ python3 loglens.py alert sample.log sample.jsonl --threshold 5
ALERT: ERROR 6 >= 5
$ echo $?
3
```

### 5. フィルタ併用

--regex（sample.log の ERROR で "timeout" を含むのは 1 件のみ）:

```
$ python3 loglens.py alert sample.log --threshold 1 --regex timeout
ALERT: ERROR 1 >= 1
$ echo $?
3
```

--level WARN（sample.log の WARN は 4 件 < 5）:

```
$ python3 loglens.py alert sample.log --threshold 5 --level WARN
OK: WARN 4 < 5
$ echo $?
0
```

### 6. 引数エラー（exit 2）

いずれも判定を行わず exit 2 で終了し、stderr にエラーを出すこと。

```
$ python3 loglens.py alert sample.log --threshold 0        # 0 以下
$ echo $?
2
$ python3 loglens.py alert sample.log                      # --threshold 未指定
$ echo $?
2
$ python3 loglens.py alert sample.log --threshold 1 --level OTHER --regex x   # 死に組合せ
$ echo $?
2
```

### 7. ファイルエラー（exit 1・発火と区別できること）

```
$ python3 loglens.py alert no_such.log --threshold 1
$ echo $?
1
```

上記 1〜7 がすべて期待どおりであれば受け入れ完了とする。

# 仕様: JSON Lines 入力対応（id: jsonl-input）

- 拡張子が .jsonl のファイルは JSON Lines として解釈する
  （1行 = 1つの JSON オブジェクト）
- 各行のキー: "timestamp"（"2026-07-18 09:12:01" 形式）、
  "level"（ERROR / WARN / INFO のいずれか）、"message"（文字列）
- レベルが3種以外・キー欠落・JSON として不正な行は OTHER に数える
- 空行はテキスト形式と同じくスキップする
- --level / --since / --until はテキスト形式と同じ挙動で併用できる
- テストデータとして sample.jsonl（12行前後。全レベル・不正な行・
  空行を含む）を新規作成し、テストで挙動を固定する

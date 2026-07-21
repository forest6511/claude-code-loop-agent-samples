#!/bin/bash
# Stop hook 完了ゲート: pytest が全て通るまでターンを終了させない
INPUT=$(cat)
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

if OUTPUT=$(python3 -m pytest -q 2>&1); then
  exit 0  # 全テスト成功。ターン終了を許可する
fi

NOTE=""
if [ "$ACTIVE" = "true" ]; then
  NOTE="（Stop hook による継続中も、まだ失敗しています）"
fi

{
  echo "pytest が失敗しています${NOTE}。"
  echo "全テストが通るまで、このターンは終了できません。失敗内容:"
  echo "$OUTPUT" | tail -15
} >&2
exit 2

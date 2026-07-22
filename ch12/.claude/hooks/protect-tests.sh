#!/bin/bash
# PreToolUse ガード: テストファイルへの編集を拒否する
INPUT=$(cat)
FILE=$(echo "$INPUT" \
  | jq -r '.tool_input.file_path // .tool_input.notebook_path // ""')

case "$FILE" in
  *test_loglens.py|*/tests/*)
    REASON="テストの編集は禁止です。失敗ならコードを直してください。"
    jq -n --arg reason "$REASON" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $reason
      }
    }'
    ;;
esac
exit 0

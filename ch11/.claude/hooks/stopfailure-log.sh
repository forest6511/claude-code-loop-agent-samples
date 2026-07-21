#!/bin/bash
# StopFailure 観測: API エラーでターンが終わったら ops/ に1行残す
INPUT=$(cat)
ERROR=$(echo "$INPUT" | jq -r '.error')
DETAILS=$(echo "$INPUT" | jq -r '.error_details // "-"')
DIR="${CLAUDE_PROJECT_DIR:-.}"

mkdir -p "$DIR/ops"
echo "$(date '+%Y-%m-%d %H:%M:%S') error=$ERROR details=$DETAILS" \
  >> "$DIR/ops/stop-failure.log"
exit 0

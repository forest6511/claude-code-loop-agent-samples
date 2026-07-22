#!/bin/bash
# 疑似ログ生成: COUNT 個のログファイルを INTERVAL 秒おきに
# ops/incoming/ へ置く（アプリサーバからのログ着信を模す）
COUNT="${1:-1}"
INTERVAL="${2:-0}"
for i in $(seq 1 "$COUNT"); do
  ts="$(date '+%Y-%m-%d %H:%M')"
  f="ops/incoming/app-$(date +%H%M%S).log"
  {
    echo "$ts:01 INFO Server heartbeat ok"
    echo "$ts:05 INFO GET /api/items 200 11ms"
    echo "$ts:12 WARN Slow query detected duration_ms=$((RANDOM % 2000 + 500))"
    echo "$ts:20 INFO User login succeeded user_id=$((RANDOM % 9000 + 1000))"
    echo "$ts:31 ERROR Upstream timeout after 5000ms"
  } > "$f"
  echo "generated: $f"
  if [ "$i" -lt "$COUNT" ]; then sleep "$INTERVAL"; fi
done

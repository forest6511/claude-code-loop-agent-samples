#!/bin/bash
# ralph.sh: loglens 用の外側ループ（停止条件3種つき）
set -u
MAX_ITER=6        # 停止条件(1) 反復回数の上限
MAX_COST=8.00     # 停止条件(3) 予算上限（USD）
STALL_LIMIT=2     # 停止条件(2) 無進捗を許容する連続回数
TARGETS='["jsonl-input", "multi-file"]'
total=0.00; stall=0
mkdir -p logs
for i in $(seq 1 "$MAX_ITER"); do
  if jq -e --argjson t "$TARGETS" \
    '[.[] | select(.id as $x | $t | index($x))] | all(.passes)' \
    feature_list.json > /dev/null; then
    echo "DONE: 対象の全機能が passes:true"; break
  fi
  head_before=$(git rev-parse HEAD)
  claude -p "$(cat PROMPT.md specs/*.md)" \
    --allowedTools "Read,Write,Edit,Bash" \
    --output-format json > "logs/iter-$i.json" 2> "logs/iter-$i.err"
  cost=$(jq -r '.total_cost_usd // 0' "logs/iter-$i.json" 2>/dev/null)
  total=$(awk "BEGIN{printf \"%.2f\", $total + ${cost:-0}}")
  [ "$(git rev-parse HEAD)" = "$head_before" ] \
    && stall=$((stall + 1)) || stall=0
  echo "iter=$i cost=\$${cost:-0} total=\$$total stall=$stall"
  [ "$stall" -ge "$STALL_LIMIT" ] && { echo "STOP: 無進捗"; break; }
  awk "BEGIN{exit !($total >= $MAX_COST)}" \
    && { echo "STOP: 予算上限"; break; }
done

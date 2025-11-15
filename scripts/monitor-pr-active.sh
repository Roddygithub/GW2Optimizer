#!/usr/bin/env bash
# Active monitoring for PR checks with polling (avoids gh run watch lag)
# Usage: ./scripts/monitor-pr-active.sh <PR-number> [poll-interval-seconds] [max-duration-seconds]
set -euo pipefail
PR_NUMBER=${1:?"Usage: $0 <PR-number> [poll-interval] [max-seconds]"}
POLL_INTERVAL=${2:-30}
MAX_DURATION=${3:-3600}
mkdir -p reports
log(){ echo "[$(date +'%F %T')] $*" | tee -a reports/ci-monitoring.log; }
get_status(){ gh pr checks "$PR_NUMBER" --json name,status,conclusion,workflow 2>/dev/null || echo "[]"; }
log "🚀 ACTIVE monitor start - PR #$PR_NUMBER (interval=${POLL_INTERVAL}s, max=${MAX_DURATION}s)"
start=$(date +%s)
while :; do
  now=$(date +%s); elapsed=$((now-start))
  if [ "$elapsed" -ge "$MAX_DURATION" ]; then
    log "⏱️ TIMEOUT after ${MAX_DURATION}s"; exit 2
  fi
  status_json=$(get_status)
  inprog=$(echo "$status_json" | jq '[.[] | select(.status=="in_progress" or .status=="queued")] | length')
  if [ "$inprog" -gt 0 ]; then
    log "⏳ $inprog workflow(s) running... (${elapsed}s elapsed)"; sleep "$POLL_INTERVAL"; continue
  fi
  log "✅ All workflows completed (${elapsed}s)"
  failures=$(echo "$status_json" | jq -r '.[] | select(.conclusion=="failure") | .workflow')
  if [ -z "$failures" ]; then
    log "🎉 ALL GREEN"; exit 0
  else
    echo "$failures" | while read -r wf; do [ -n "$wf" ] && log "❌ Failure: $wf"; done
    exit 1
  fi
done

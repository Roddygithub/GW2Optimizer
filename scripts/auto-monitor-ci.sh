#!/usr/bin/env bash
# Minimal auto-monitor for CI workflows (ci.yml, frontend-ci.yml)
# Usage: ./scripts/auto-monitor-ci.sh <PR-number>
set -euo pipefail
PR=${1:-}
if [[ -z "$PR" ]]; then echo "Usage: $0 <PR-number>"; exit 1; fi
BRANCH=$(gh pr view "$PR" --json headRefName -q .headRefName)
mkdir -p reports
log(){ echo "[$(date +'%F %T')] $*" | tee -a reports/ci-monitoring.log; }
watch(){ local wf=$1; local id; id=$(gh run list --workflow "$wf" --branch "$BRANCH" --limit 1 --json databaseId --jq '.[0].databaseId' || true); [[ -z "${id:-}" ]] && { log "$wf: no recent run"; return 0; }; log "Watching $wf #$id"; gh run watch "$id" || true; concl=$(gh run view "$id" --json conclusion -q .conclusion); log "$wf concluded: $concl"; }
log "AUTO-MONITOR START - PR #$PR (branch: $BRANCH)"
watch ci.yml
watch frontend-ci.yml
log "AUTO-MONITOR END"

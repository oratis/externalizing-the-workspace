#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"  # launchd minimal PATH lacks node
# Advance every arm by ONE day. Idempotent per day via runs/state.json.
# Intended to be run once/day by launchd (or manually to accelerate).
#
#   ./tick.sh            # run the next day for all arms
#   MAX_DAYS=21 ./tick.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_DAYS="${MAX_DAYS:-21}"
# COHORTS = space list; "main" = flat runs/, "c1 c2 ..." = runs/c1 runs/c2.
# One tick advances EVERY listed cohort by one day (so a single daily launchd
# fire keeps all parallel cohorts in lock-step).
COHORTS="${COHORTS:-main}"
ARMS="$(node -e "process.stdout.write(Object.keys(JSON.parse(require('fs').readFileSync('$HERE/arms.json','utf8')).arms).join(' '))")"
OVERALL=0

for COH in $COHORTS; do
  if [ "$COH" = "main" ]; then RUNS="$HERE/runs"; else RUNS="$HERE/runs/$COH"; fi
  STATE="$RUNS/state.json"; LOG="$RUNS/tick.log"
  mkdir -p "$RUNS"
  [ -f "$STATE" ] || echo '{"nextDay":0}' > "$STATE"
  DAY="$(node -e "process.stdout.write(String(JSON.parse(require('fs').readFileSync('$STATE','utf8')).nextDay))")"

  if [ "$DAY" -ge "$MAX_DAYS" ]; then
    echo "$(date -u +%FT%TZ) [$COH] all $MAX_DAYS days complete" | tee -a "$LOG"; continue
  fi
  echo "$(date -u +%FT%TZ) [$COH] === tick day $DAY ===" | tee -a "$LOG"

  FAILED=0
  for arm in $ARMS; do
    echo "$(date -u +%FT%TZ) [$COH] -> $arm day $DAY" | tee -a "$LOG"
    if ! COHORT="$COH" node "$HERE/drive-day.mjs" "$arm" "$DAY" >>"$LOG" 2>&1; then
      echo "$(date -u +%FT%TZ) [$COH] !! $arm day $DAY FAILED" | tee -a "$LOG"
      FAILED=$((FAILED + 1))
    fi
  done

  # Advance a cohort ONLY if every arm succeeded, else retry it next tick.
  if [ "$FAILED" -eq 0 ]; then
    NEXT=$((DAY + 1)); echo "{\"nextDay\":$NEXT}" > "$STATE"
    echo "$(date -u +%FT%TZ) [$COH] === day $DAY done; nextDay=$NEXT ===" | tee -a "$LOG"
  else
    echo "$(date -u +%FT%TZ) [$COH] === day $DAY had $FAILED failed arm(s); NOT advanced ===" | tee -a "$LOG"
    OVERALL=1
  fi
done
exit $OVERALL

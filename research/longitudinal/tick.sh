#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"  # launchd minimal PATH lacks node
# Advance every arm by ONE day. Idempotent per day via runs/state.json.
# Intended to be run once/day by launchd (or manually to accelerate).
#
#   ./tick.sh            # run the next day for all arms
#   MAX_DAYS=21 ./tick.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNS="$HERE/runs"
STATE="$RUNS/state.json"
LOG="$RUNS/tick.log"
MAX_DAYS="${MAX_DAYS:-21}"

mkdir -p "$RUNS"
[ -f "$STATE" ] || echo '{"nextDay":0}' > "$STATE"
DAY="$(node -e "process.stdout.write(String(JSON.parse(require('fs').readFileSync('$STATE','utf8')).nextDay))")"

if [ "$DAY" -ge "$MAX_DAYS" ]; then
  echo "$(date -u +%FT%TZ) all $MAX_DAYS days complete; nothing to do" | tee -a "$LOG"
  exit 0
fi

echo "$(date -u +%FT%TZ) === tick day $DAY ===" | tee -a "$LOG"
ARMS="$(node -e "process.stdout.write(Object.keys(JSON.parse(require('fs').readFileSync('$HERE/arms.json','utf8')).arms).join(' '))")"

FAILED=0
for arm in $ARMS; do
  echo "$(date -u +%FT%TZ) -> $arm day $DAY" | tee -a "$LOG"
  if ! node "$HERE/drive-day.mjs" "$arm" "$DAY" >>"$LOG" 2>&1; then
    echo "$(date -u +%FT%TZ) !! $arm day $DAY FAILED" | tee -a "$LOG"
    FAILED=$((FAILED + 1))
  fi
done

# Advance ONLY if every arm succeeded; otherwise leave state at DAY so the
# next tick retries it (drive-day.mjs clears the day's partial rows first).
if [ "$FAILED" -eq 0 ]; then
  NEXT=$((DAY + 1))
  echo "{\"nextDay\":$NEXT}" > "$STATE"
  echo "$(date -u +%FT%TZ) === day $DAY done; nextDay=$NEXT ===" | tee -a "$LOG"
else
  echo "$(date -u +%FT%TZ) === day $DAY had $FAILED failed arm(s); state NOT advanced (will retry) ===" | tee -a "$LOG"
  exit 1
fi

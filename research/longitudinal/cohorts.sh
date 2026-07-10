#!/usr/bin/env bash
# Roll out N independent parallel cohorts for real-deployment statistics.
# Each cohort = the same 5 arms seeded from the same founding soul, with a
# per-cohort incidental-workload rotation (pressure timing held fixed).
#
#   ./cohorts.sh c1 c2 c3            # seed + fix-keys + run day 0 for each
#   LISA_AUTH_TOKEN=… ./cohorts.sh c1 c2   # use coding-plan bearer instead of key
#
# After this, add the cohorts to the daily launchd tick by setting COHORTS in
# the plist, e.g. COHORTS="main c1 c2 c3" — one fire advances all in lock-step.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ "$#" -ge 1 ] || { echo "usage: ./cohorts.sh c1 [c2 ...]"; exit 2; }

for COH in "$@"; do
  echo "=== cohort $COH: seed ==="
  COHORT="$COH" node "$HERE/seed-arms.mjs" --force
done
echo "=== fix-keys (all cohorts) ==="
bash "$HERE/fix-keys.sh"
echo "=== run day 0 for cohorts: $* ==="
COHORTS="$*" bash "$HERE/tick.sh"
echo "=== done. To automate daily, set COHORTS=\"main $*\" in the launchd plist."
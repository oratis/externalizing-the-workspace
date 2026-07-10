#!/bin/bash
export PATH="$HOME/.local/bin:/usr/bin:$PATH"
export SEED_HOME=~/.lisa
export TURN_TIMEOUT_MS=180000
cd ~/ew/research/longitudinal || exit 1
ST=~/run_status.txt; echo "SEED $(date -u)" > $ST
rm -rf runs; node seed-arms.mjs --force >>~/seed.log 2>&1
for c in c1 c2 c3 c4; do COHORT=$c node seed-arms.mjs --force >>~/seed.log 2>&1; done
n=0
while IFS= read -r s; do d=$(dirname "$s"); printf 'LISA_BASE_URL=http://localhost:8000/v1\nLISA_MODEL=Qwen/Qwen2.5-7B-Instruct\nLISA_API_KEY=vllm\n' > "$d/config.env"; n=$((n+1)); done < <(find runs -type d -name soul)
echo "CONFIGURED $n arms $(date -u)" >> $ST
mkdir -p ~/armlogs
run_arm(){ local coh=$1 arm=$2; for d in $(seq 0 20); do COHORT=$coh node drive-day.mjs "$arm" "$d" >>~/armlogs/${coh}_${arm}.log 2>&1 || { echo "FAIL $coh/$arm d$d $(date -u)" >> $ST; return; }; done; echo "DONE $coh/$arm $(date -u)" >> $ST; }
echo "RUN START $(date -u) maxjobs=8" >> $ST
for coh in main c1 c2 c3 c4; do for arm in full no_examen no_git no_broadcast no_soul; do
  run_arm "$coh" "$arm" &
  sleep 3
  while [ "$(jobs -r | wc -l)" -ge 8 ]; do sleep 3; done
done; done
wait
echo "ALL DONE $(date -u)" >> $ST
python3 analyze_cohorts.py >>$ST 2>&1
echo "ANALYZE DONE $(date -u)" >> $ST

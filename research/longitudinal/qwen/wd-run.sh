#!/bin/bash
export PATH="$HOME/.local/bin:/usr/bin:$PATH"
export WREPRO_MODEL="Qwen/Qwen2.5-7B-Instruct"
cd ~/ew/research/longitudinal
pkill -9 -f vllm.entrypoints 2>/dev/null; pkill -9 -f EngineCore 2>/dev/null
nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | xargs -r sudo kill -9 2>/dev/null
sleep 8
echo "WD START $(date -u) gpu_free=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader)" > ~/wd_status.txt
python3 wd_real.py >> ~/wd_status.txt 2>&1
echo "WD ALLDONE $(date -u)" >> ~/wd_status.txt

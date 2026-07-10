#!/bin/bash
pkill -9 -f vllm.entrypoints 2>/dev/null; sleep 2
sudo rm -rf /usr/local/lib/python3.10/dist-packages/torchaudio* /usr/local/lib/python3.10/dist-packages/torchvision* 2>/dev/null
rm -rf ~/.local/lib/python3.10/site-packages/torchaudio* ~/.local/lib/python3.10/site-packages/torchvision* 2>/dev/null
python3 -c "import torchaudio" 2>&1 | tail -1   # should now be ModuleNotFound
exec python3 -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-7B-Instruct --dtype bfloat16 --port 8000 --max-model-len 16384 --gpu-memory-utilization 0.90 --enable-auto-tool-choice --tool-call-parser hermes

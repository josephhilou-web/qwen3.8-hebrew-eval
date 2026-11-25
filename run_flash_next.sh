#!/bin/zsh
# All runs for Qwen3.8-Flash-Next (unsloth UD-Q4_K_XL GGUF) through llama.cpp's llama-server. Resumable.
# GGUF: path to the first shard of unsloth/Qwen3.8-Flash-Next-GGUF, UD-Q4_K_XL
set -e
PY=${PY:-python3}
G=${GGUF:-models/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf}
PORT=${PORT:-8197}
mkdir -p logs
llama-server -m $G --host 127.0.0.1 --port $PORT -np 8 -c 163840 -ngl 999 --jinja \
  --reasoning-format deepseek > logs/llama_server.log 2>&1 &
SRV=$!
trap "kill $SRV 2>/dev/null" EXIT
until curl -sf http://127.0.0.1:$PORT/props 2>/dev/null | grep -q Flash-Next; do
  kill -0 $SRV 2>/dev/null || { echo "llama-server died"; tail -30 logs/llama_server.log; exit 1; }
  sleep 5
done
echo "server ready"
A=(--backend server --host http://127.0.0.1:$PORT --name qwen38-flash-next --parallel 8)
$PY run.py $A --items items/language.jsonl --mode nothink --max-tokens 3000
$PY run.py $A --items items/writing.jsonl --mode nothink --max-tokens 4000
$PY run.py $A --items items/language.jsonl --mode think
$PY run.py $A --items items/reasoning.jsonl --mode think

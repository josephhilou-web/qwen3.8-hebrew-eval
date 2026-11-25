#!/bin/zsh
# Tuned settings (thinking off, temp 0.3, min_p 0.05, Hebrew system prompt) for both models, one after the other,
# on the language and writing sets. Resumable. Same env vars as run_27b.sh / run_flash_next.sh.
set -e
PY=${PY:-python3}
M=${MODEL:-models/Qwen3.8-27B-8bit}
G=${GGUF:-models/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf}
PORT=${PORT:-8197}
mkdir -p logs
llama-server -m $G --host 127.0.0.1 --port $PORT -np 8 -c 163840 -ngl 999 --jinja \
  --reasoning-format deepseek > logs/llama_server_tuned.log 2>&1 &
SRV=$!
trap "kill $SRV 2>/dev/null" EXIT
until curl -sf http://127.0.0.1:$PORT/props 2>/dev/null | grep -q Flash-Next; do
  kill -0 $SRV 2>/dev/null || { echo "llama-server died"; tail -30 logs/llama_server_tuned.log; exit 1; }
  sleep 5
done
echo "server ready"
A=(--backend server --host http://127.0.0.1:$PORT --name qwen38-flash-next --parallel 8 --mode tuned)
$PY run.py $A --items items/language.jsonl --max-tokens 3000
$PY run.py $A --items items/writing.jsonl --max-tokens 4000
kill $SRV; wait $SRV 2>/dev/null || true
echo "MoE done, server stopped"
sleep 5
$PY run.py --backend mlx --model $M --name qwen38-27b --items items/language.jsonl --mode tuned --max-tokens 3000
$PY run.py --backend mlx --model $M --name qwen38-27b --items items/writing.jsonl --mode tuned --max-tokens 4000
echo "TUNED DONE"

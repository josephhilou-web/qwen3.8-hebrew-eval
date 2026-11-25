#!/bin/zsh
# Document-reading runs for the three models, one after another (resumable). Run from the repository root.
#   VPY       python with mlx-vlm (tested with mlx-vlm 0.8.1)
#   GEMMA     MLX weights of Gemma-4-26B-A4B (mlx-community/gemma-4-26b-a4b-it-8bit, vision tower included)
#   QWEN_HF   original Qwen/Qwen3.8-27B weights; converted here to an 8-bit MLX model that keeps the vision tower
#             (the 8-bit model used for the text tests was converted with mlx-lm, which drops it)
#   GGUF, MMPROJ  Qwen3.8-Flash-Next UD-Q4_K_XL and its mmproj-F16.gguf, served by llama-server
set -e
VPY=${VPY:-python3}
GEMMA=${GEMMA:-models/gemma-4-26B-A4B-it-8bit}
QWEN_HF=${QWEN_HF:-models/Qwen3.8-27B}
QWEN_VLM=${QWEN_VLM:-models/Qwen3.8-27B-vlm-8bit}
G=${GGUF:-models/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf}
MMPROJ=${MMPROJ:-models/Qwen3.8-Flash-Next-GGUF/mmproj-F16.gguf}
PORT=${PORT:-8197}
mkdir -p logs

# Gemma 4 at its default image budget (280 tokens per image) and at the largest one (1120)
$VPY vision/run_vision.py --backend mlxvlm --model $GEMMA --name gemma4-26b-a4b
$VPY vision/run_vision.py --backend mlxvlm --model $GEMMA --name gemma4-26b-a4b-1120tok --max-soft-tokens 1120

# Qwen3.8-27B (dense) at native resolution
[ -d $QWEN_VLM ] || $VPY -m mlx_vlm.convert --hf-path $QWEN_HF --mlx-path $QWEN_VLM -q --q-bits 8
$VPY vision/run_vision.py --backend mlxvlm --model $QWEN_VLM --name qwen38-27b

# Qwen3.8-Flash-Next (MoE) through llama.cpp; --image-max-tokens 4096 so an A4 page is not shrunk
llama-server -m $G --mmproj $MMPROJ --image-max-tokens 4096 --host 127.0.0.1 --port $PORT -np 1 -c 32768 -ngl 999 \
  --jinja --reasoning-format deepseek > logs/llama_server_vision.log 2>&1 &
SRV=$!
trap "kill $SRV 2>/dev/null" EXIT
until curl -sf http://127.0.0.1:$PORT/props 2>/dev/null | grep -q Flash-Next; do
  kill -0 $SRV 2>/dev/null || { echo "llama-server died"; tail -30 logs/llama_server_vision.log; exit 1; }
  sleep 5
done
echo "server ready"
$VPY vision/run_vision.py --backend server --host http://127.0.0.1:$PORT --name qwen38-flash-next
kill $SRV; wait $SRV 2>/dev/null || true
echo "VISION DONE"

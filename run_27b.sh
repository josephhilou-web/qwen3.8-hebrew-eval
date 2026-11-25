#!/bin/zsh
# All runs for Qwen3.8-27B (MLX 8-bit), one after another. Resumable: items already answered are skipped.
# MODEL: path to the MLX 8-bit weights, e.g. made with: mlx_lm.convert --hf-path Qwen/Qwen3.8-27B -q --q-bits 8
set -e
PY=${PY:-python3}
M=${MODEL:-models/Qwen3.8-27B-8bit}
$PY run.py --backend mlx --model $M --name qwen38-27b --items items/language.jsonl --mode nothink --max-tokens 3000
$PY run.py --backend mlx --model $M --name qwen38-27b --items items/writing.jsonl --mode nothink --max-tokens 4000
$PY run.py --backend mlx --model $M --name qwen38-27b --items items/language.jsonl --mode think
$PY run.py --backend mlx --model $M --name qwen38-27b --items items/reasoning.jsonl --mode think

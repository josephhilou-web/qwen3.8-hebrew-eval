#!/bin/zsh
# All runs for Gemma-4-26B-A4B (MLX 8-bit, mlx-community/gemma-4-26b-a4b-it-8bit), one after another. Resumable.
# think / nothink use Google's recommended sampling (--sampling gemma); tuned is identical for every model.
# --batch 1 (one prompt at a time): mlx_lm 0.32.2's batched generator slowed to under 1 token/s per sequence on
# Gemma 4 once answers passed ~2,400 tokens. For Gemma-4-26B-A4B the no-think runs, the thinking-on language run and
# the first 16 reasoning items were made batched (batch 8) before that was noticed.
# GEMMA: path to the MLX weights; NAME: results name (default gemma4-26b-a4b)
set -e
PY=${PY:-python3}
M=${GEMMA:-models/gemma-4-26B-A4B-it-8bit}
A=(--backend mlx --model $M --name ${NAME:-gemma4-26b-a4b} --sampling gemma --batch ${BATCH:-1})
$PY run.py $A --items items/language.jsonl --mode nothink --max-tokens 3000
$PY run.py $A --items items/writing.jsonl --mode nothink --max-tokens 4000
$PY run.py $A --items items/language.jsonl --mode think
$PY run.py $A --items items/reasoning.jsonl --mode think
$PY run.py $A --items items/language.jsonl --mode tuned --max-tokens 3000
$PY run.py $A --items items/writing.jsonl --mode tuned --max-tokens 4000
echo "GEMMA DONE ${NAME:-gemma4-26b-a4b}"

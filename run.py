"""Run one model over one item file in one mode -> results/{name}__{section}__{mode}.jsonl (resumable).

Modes (sampling = Qwen's own recommendation for each mode, identical for both models):
  think    thinking on, reasoning_effort=medium, temp 1.0, top_p 0.95, top_k 20, min_p 0, presence 0
  nothink  enable_thinking=False,                temp 0.7, top_p 0.80, top_k 20, min_p 0, presence 1.5
No system prompt: this measures the models out of the box.

Backends:
  mlx     local MLX model through mlx_lm's BatchGenerator (groups of --batch prompts, no slot refill:
          refilling slots crashes Metal with Qwen3.8's linear attention on mlx_lm 0.32.2)
  server  OpenAI-compatible /v1/chat/completions (llama.cpp llama-server), --parallel requests at once
Usage:
  python run.py --backend mlx --model ../../models/mlx/Qwen3.8-27B-8bit --name qwen38-27b --items items/reasoning.jsonl --mode think
  python run.py --backend server --host http://127.0.0.1:8197 --name qwen38-flash-next --items items/reasoning.jsonl --mode think
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LET = "אבגד"
TAIL_MCQ = "בחר את התשובה הנכונה. ענה בעברית. בשורה האחרונה של התשובה כתוב בדיוק: \"התשובה: \" ואחריו האות בלבד (א, ב, ג או ד)."
TAIL_NUM = "פתור שלב אחר שלב. ענה בעברית. בשורה האחרונה של התשובה כתוב בדיוק: \"התשובה: \" ואחריו המספר בלבד."
MODES = {
    "think": dict(temp=1.0, top_p=0.95, top_k=20, min_p=0.0, presence=0.0,
                  kwargs={"enable_thinking": True, "reasoning_effort": "medium"}),
    "nothink": dict(temp=0.7, top_p=0.80, top_k=20, min_p=0.0, presence=1.5, kwargs={"enable_thinking": False}),
}


def prompt(it):
    if it["kind"] == "mcq":
        opts = "\n".join(f"{LET[i]}. {o}" for i, o in enumerate(it["options"]))
        return f"{it['question']}\n\n{opts}\n\n{TAIL_MCQ}"
    if it["kind"] == "number":
        return f"{it['question']}\n\n{TAIL_NUM}"
    return it["question"]


def split_think(text):
    if "</think>" in text:
        th, ans = text.split("</think>", 1)
        return th.replace("<think>", "").strip(), ans.strip(), True
    if "<think>" in text:  # never closed: the whole output was thinking
        return text.replace("<think>", "").strip(), "", False
    return "", text.strip(), True


def run_server(a, m, jobs):
    import requests

    def one(it):
        t0 = time.time()
        r = requests.post(f"{a.host}/v1/chat/completions", timeout=7200, json={
            "messages": [{"role": "user", "content": prompt(it)}], "max_tokens": a.max_tokens,
            "temperature": m["temp"], "top_p": m["top_p"], "top_k": m["top_k"], "min_p": m["min_p"],
            "presence_penalty": m["presence"], "chat_template_kwargs": m["kwargs"], "seed": 0}).json()
        if "error" in r:
            raise RuntimeError(r["error"])
        msg, ch = r["choices"][0]["message"], r["choices"][0]
        th, ans = (msg.get("reasoning_content") or "").strip(), (msg.get("content") or "").strip()
        if not th and "<think>" in ans:
            th, ans, _ = split_think(ans)
        tm = r.get("timings", {})
        return it, {"answer": ans, "thinking": th, "gen_tokens": r["usage"]["completion_tokens"],
                    "seconds": round(time.time() - t0, 1), "decode_tok_s": round(tm.get("predicted_per_second", 0), 1),
                    "truncated": ch.get("finish_reason") == "length"}

    with ThreadPoolExecutor(a.parallel) as ex:
        yield from ex.map(one, jobs)


def run_mlx(a, m, jobs):
    import gc

    import mlx.core as mx
    from mlx_lm import load
    from mlx_lm.generate import BatchGenerator
    from mlx_lm.sample_utils import make_logits_processors, make_sampler

    mx.random.seed(0)
    model, tok = load(a.model)
    sampler = make_sampler(temp=m["temp"], top_p=m["top_p"], top_k=m["top_k"], min_p=m["min_p"])
    procs = make_logits_processors(presence_penalty=m["presence"] or None, presence_context_size=4096)
    for b in range(0, len(jobs), a.batch):
        part = jobs[b: b + a.batch]
        gen = BatchGenerator(model, stop_tokens=[[t] for t in tok.eos_token_ids], sampler=sampler,
                             logits_processors=procs or None, completion_batch_size=a.batch, prefill_batch_size=a.batch)
        prompts = [tok.apply_chat_template([{"role": "user", "content": prompt(it)}], add_generation_prompt=True,
                                           tokenize=True, **m["kwargs"]) for it in part]
        uids = gen.insert(prompts, [a.max_tokens] * len(prompts))
        meta = {u: (it, p) for u, it, p in zip(uids, part, prompts)}
        toks = {u: [] for u in uids}
        t0, step = time.time(), 0
        while responses := gen.next_generated():
            step += 1
            if step % 256 == 0:
                mx.clear_cache()
            for r in responses:
                if r.finish_reason != "stop":
                    toks[r.uid].append(int(r.token))
                if r.finish_reason is None:
                    continue
                it, p = meta[r.uid]
                ids = toks.pop(r.uid)
                text = tok.decode(ids)
                tail = tok.decode(p[-8:])  # the template opens <think> itself in thinking mode
                if tail.rfind("<think>") > tail.rfind("</think>") and "<think>" not in text:
                    text = "<think>" + text
                th, ans, _ = split_think(text)
                el = time.time() - t0
                yield it, {"answer": ans, "thinking": th, "gen_tokens": len(ids), "seconds": round(el, 1),
                           "decode_tok_s": round(len(ids) / max(el, 1e-9), 1), "truncated": r.finish_reason == "length"}
        gen.close()
        del gen, responses
        gc.collect()
        mx.clear_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["mlx", "server"], required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("--name", required=True)
    ap.add_argument("--host", default="http://127.0.0.1:8090")
    ap.add_argument("--items", required=True)
    ap.add_argument("--mode", choices=list(MODES), required=True)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--parallel", type=int, default=4)
    a = ap.parse_args()
    m = MODES[a.mode]

    items = [json.loads(l) for l in open(a.items, encoding="utf-8")]
    section = items[0]["section"]
    out = Path(f"results/{a.name}__{section}__{a.mode}.jsonl")
    out.parent.mkdir(exist_ok=True)
    done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
    jobs = [it for it in items if it["id"] not in done]
    print(f"{out.name}: {len(jobs)} to run ({len(done)} done)", flush=True)
    t_start, n, toks = time.time(), 0, 0
    with open(out, "a", encoding="utf-8") as f:
        for it, r in (run_mlx if a.backend == "mlx" else run_server)(a, m, jobs):
            f.write(json.dumps({"id": it["id"], "section": section, "part": it["part"], "kind": it["kind"],
                                "model": a.name, "mode": a.mode, "question": it["question"], "gold": it["gold"], **r},
                               ensure_ascii=False) + "\n")
            f.flush()
            n, toks = n + 1, toks + r["gen_tokens"]
            el = time.time() - t_start
            print(f"  {n}/{len(jobs)}  {it['id']}  {r['gen_tokens']} tok  {toks / el:.0f} tok/s total  "
                  f"ETA {el / n * (len(jobs) - n) / 60:.0f} min", flush=True)
    print("DONE", out, f"{(time.time() - t_start) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()

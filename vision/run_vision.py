"""Run one vision model over vision/items.jsonl -> vision/results/{name}.jsonl (resumable)

Every model gets the same Hebrew prompts, no system prompt, thinking off, greedy decoding (temperature 0).
  ocr  "copy all the text in the image exactly, in reading order; tables one row per line, cells separated by |"
  qa   the question + "answer from the document, only the answer"
Backends:
  mlxvlm  mlx-vlm (Gemma 4, Qwen3.8-27B). --max-soft-tokens sets Gemma 4's image token budget (default 280).
  server  llama.cpp llama-server with --mmproj (Qwen3.8-Flash-Next), OpenAI-style image_url
Usage:
  python vision/run_vision.py --backend mlxvlm --model ../../models/mlx/gemma-4-26B-A4B-it-8bit --name gemma4-26b-a4b
  python vision/run_vision.py --backend mlxvlm --model ... --name gemma4-26b-a4b-1120tok --max-soft-tokens 1120
  python vision/run_vision.py --backend server --host http://127.0.0.1:8197 --name qwen38-flash-next
"""
import argparse
import base64
import json
import time
from pathlib import Path

HERE = Path(__file__).parent
OCR = ("העתק את כל הטקסט שבתמונה בדיוק כפי שהוא כתוב, מההתחלה ועד הסוף, לפי סדר הקריאה. "
       "אל תתרגם, אל תתקן ואל תוסיף הסברים. בטבלאות כתוב כל שורה של הטבלה בשורה נפרדת, והפרד בין התאים בסימן |.")
QA = "{q}\nענה על סמך המסמך שבתמונה. כתוב רק את התשובה, בלי הסברים."


def prompt(it):
    return OCR if it["kind"] == "ocr" else QA.format(q=it["question"])


def strip_think(t):
    for op, cl in [("<think>", "</think>"), ("<|channel>thought", "<channel|>")]:
        if cl in t:
            t = t.split(cl, 1)[1]
    return t.replace("<turn|>", "").strip()


def run_server(a, jobs):
    import requests
    for it in jobs:
        img = base64.b64encode((HERE / it["image"]).read_bytes()).decode()
        mime = "image/png" if it["image"].endswith(".png") else "image/jpeg"
        t0 = time.time()
        r = requests.post(f"{a.host}/v1/chat/completions", timeout=3600, json={
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img}"}},
                {"type": "text", "text": prompt(it)}]}],
            "max_tokens": a.max_tokens if it["kind"] == "ocr" else 300, "temperature": 0.0,
            "chat_template_kwargs": {"enable_thinking": False}, "seed": 0}).json()
        if "error" in r:
            raise RuntimeError(r["error"])
        ch = r["choices"][0]
        yield it, {"answer": strip_think(ch["message"].get("content") or ""), "gen_tokens": r["usage"]["completion_tokens"],
                   "prompt_tokens": r["usage"]["prompt_tokens"], "seconds": round(time.time() - t0, 1),
                   "truncated": ch.get("finish_reason") == "length"}


def run_mlxvlm(a, jobs):
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template
    model, processor = load(a.model)
    if a.max_soft_tokens:
        ip = processor.image_processor
        for attr in ["max_soft_tokens", "image_seq_length"]:
            if hasattr(ip, attr):
                setattr(ip, attr, a.max_soft_tokens)
        if hasattr(processor, "image_seq_length"):
            processor.image_seq_length = a.max_soft_tokens
    for it in jobs:
        p = apply_chat_template(processor, model.config, prompt(it), num_images=1, enable_thinking=False)
        t0 = time.time()
        r = generate(model, processor, p, image=[str(HERE / it["image"])], verbose=False, temperature=0.0,
                     max_tokens=a.max_tokens if it["kind"] == "ocr" else 300)
        yield it, {"answer": strip_think(r.text), "gen_tokens": r.generation_tokens, "prompt_tokens": r.prompt_tokens,
                   "seconds": round(time.time() - t0, 1), "truncated": r.finish_reason == "length"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["mlxvlm", "server"], required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("--name", required=True)
    ap.add_argument("--host", default="http://127.0.0.1:8197")
    ap.add_argument("--max-tokens", type=int, default=2500)
    ap.add_argument("--max-soft-tokens", type=int, default=0, help="Gemma 4 image token budget (default: model's own)")
    ap.add_argument("--only", default="", help="comma-separated item ids (for smoke tests)")
    a = ap.parse_args()
    items = [json.loads(l) for l in open(HERE / "items.jsonl", encoding="utf-8")]
    if a.only:
        items = [i for i in items if i["id"] in a.only.split(",")]
    out = HERE / "results" / f"{a.name}.jsonl"
    out.parent.mkdir(exist_ok=True)
    done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
    jobs = [it for it in items if it["id"] not in done]
    print(f"{out.name}: {len(jobs)} to run ({len(done)} done)", flush=True)
    t0 = time.time()
    with open(out, "a", encoding="utf-8") as f:
        for n, (it, r) in enumerate((run_mlxvlm if a.backend == "mlxvlm" else run_server)(a, jobs), 1):
            f.write(json.dumps({"id": it["id"], "model": a.name, **r}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {n}/{len(jobs)} {it['id']} {r['gen_tokens']} tok {r['seconds']} s", flush=True)
    print("DONE", out.name, f"{(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()

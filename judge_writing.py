"""Blind judging of the 16 writing tasks.

  build  -> <dir>/writing_blind.txt: every task with all models' answers labelled A, B, C, ... (model names hidden).
            Each model gets each label about equally often, in a seeded random order. The key goes to <dir>/key.json.
  tally  -> reads <dir>/scores_*.json (one file per independent judge) and writes results/writing_summary_<dir name>.json:
            Hebrew errors per 100 words (overall and by type), fluency 1-5, task success 1-5, first places and mean rank
Judge output, one object per task (see judge/JUDGE_PROMPT.md):
  {"task": id, "A": {"errors": [{"type", "text", "fix"}], "fluency": 1-5, "task": 1-5}, "B": {...}, ...,
   "rank": ["B", "A", ...] (best first), "best": "B" | "tie", "why": "..."}
The first, two-model pass (judge/qwen_pairwise/) used labels X / Y and a "prefer" field instead of rank / best.
error types: spelling, agreement, invented_word, preposition_or_collocation, unnatural_or_literal,
             wrong_word_in_context, foreign_word, niqqud, other
Usage:
  python judge_writing.py build --mode nothink --dir judge/nothink
  python judge_writing.py tally --dir judge/nothink      (the run mode and models are read from key.json)
"""
import argparse
import json
import random
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

MODELS = ["qwen38-27b", "qwen38-flash-next", "gemma4-26b-a4b"]


def load(m, mode):
    return {r["id"]: r for r in map(json.loads, open(f"results/{m}__writing__{mode}.jsonl", encoding="utf-8"))}


def build(a):
    J, models = Path(a.dir), a.models
    ans = {m: load(m, a.mode) for m in models}
    items = {i["id"]: i for i in map(json.loads, open("items/writing.jsonl", encoding="utf-8"))}
    labels = "ABCDEFGH"[:len(models)]
    perms = list(permutations(range(len(models))))
    orders = (perms * (len(items) // len(perms) + 1))[:len(items)]
    random.Random(16).shuffle(orders)  # every model sits in every position about equally often
    J.mkdir(parents=True, exist_ok=True)
    key, out = {"_mode": a.mode}, []
    for tid, order in zip(items, orders):
        shown = [models[k] for k in order]
        key[tid] = dict(zip(labels, shown))
        out += [f"################ task {tid}", f"משימה: {items[tid]['question']}"]
        if items[tid]["gold"]:
            out.append(f"(תשובת ייחוס: {items[tid]['gold']})")
        for lab, m in zip(labels, shown):
            r = ans[m][tid]
            out += [f"-------- {lab}:", (r["answer"] or "(ריק)") + ("\n[נקטע באמצע: הגיע למגבלת האורך]" if r["truncated"] else "")]
        out.append("")
    (J / "writing_blind.txt").write_text("\n".join(out), encoding="utf-8")
    (J / "key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    pos = {m: Counter(lab for t, k in key.items() if t != "_mode" for lab, mm in k.items() if mm == m) for m in models}
    print(len(items), "tasks ->", J / "writing_blind.txt", "| label counts:", {m: dict(sorted(c.items())) for m, c in pos.items()})


def tally(a):
    J = Path(a.dir)
    key = json.loads((J / "key.json").read_text())
    mode = key.pop("_mode", "nothink")
    models = sorted({m for k in key.values() for m in k.values()}, key=lambda m: MODELS.index(m) if m in MODELS else 99)
    words = {m: {t: len((r["answer"] or "").split()) for t, r in load(m, mode).items()} for m in models}
    per = {m: {"errors": 0, "words": 0, "types": Counter(), "fluency": [], "task": [], "rank": []} for m in models}
    best = Counter()
    judges = sorted(J.glob("scores_*.json"))
    examples = defaultdict(list)
    for jf in judges:
        rows = json.loads(jf.read_text(encoding="utf-8"))
        assert len(rows) == len(key), f"{jf}: {len(rows)} tasks, expected {len(key)}"
        for s in rows:
            k = key[s["task"]]
            for lab, m in k.items():
                e = s[lab]["errors"]
                per[m]["errors"] += len(e)
                per[m]["types"].update(x["type"] for x in e)
                per[m]["words"] += words[m][s["task"]]
                per[m]["fluency"].append(s[lab]["fluency"])
                per[m]["task"].append(s[lab]["task"])
                examples[m] += [{"task": s["task"], "judge": jf.stem, **x} for x in e]
            if "rank" in s:
                assert sorted(s["rank"]) == sorted(k), f"{jf} {s['task']}: bad rank {s['rank']}"
                for i, lab in enumerate(s["rank"]):
                    per[k[lab]]["rank"].append(i + 1)
            win = s.get("best", s.get("prefer"))
            best[k[win] if win in k else "tie"] += 1
    res = {"mode": mode, "judges": len(judges), "models": models, "first_place": dict(best), "per_model": {}}
    for m, d in per.items():
        res["per_model"][m] = {
            "errors_per_100_words": round(100 * d["errors"] / max(d["words"], 1), 2),
            "errors": d["errors"], "words_judged": d["words"], "error_types": dict(d["types"].most_common()),
            "fluency_mean": round(sum(d["fluency"]) / len(d["fluency"]), 2),
            "task_mean": round(sum(d["task"]) / len(d["task"]), 2),
            **({"mean_rank": round(sum(d["rank"]) / len(d["rank"]), 2)} if d["rank"] else {})}
    res["error_examples"] = examples
    out = Path(f"results/writing_summary_{J.name}.json")
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(out, json.dumps({k: v for k, v in res.items() if k != "error_examples"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "tally"])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--mode", default="nothink", help="run mode whose writing answers are judged (build only)")
    ap.add_argument("--models", nargs="+", default=MODELS, help="build only")
    a = ap.parse_args()
    {"build": build, "tally": tally}[a.cmd](a)

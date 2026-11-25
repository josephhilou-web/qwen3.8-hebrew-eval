"""Blind judging of the 16 writing tasks (thinking off).

  build  -> judge/writing_blind.txt: every task with the two models' answers as "X" and "Y" in random order
            (model names hidden); the key goes to judge/key.json
  tally  -> reads judge/scores_*.json (one file per independent judge) and writes results/writing_summary.json:
            Hebrew errors per 100 words (overall and by type), fluency 1-5, task success 1-5, and preference wins
Judge output, one object per task:
  {"task": id, "X": {"errors": [{"type", "text", "fix"}], "fluency": 1-5, "task": 1-5},
               "Y": {...}, "prefer": "X" | "Y" | "tie", "why": "..."}
error types: spelling, agreement, invented_word, preposition_or_collocation, unnatural_or_literal,
             wrong_word_in_context, foreign_word, niqqud, other
Usage: python judge_writing.py build | python judge_writing.py tally
"""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

MODELS = ["qwen38-27b", "qwen38-flash-next"]
J = Path("judge")


def load(m):
    return {r["id"]: r for r in map(json.loads, open(f"results/{m}__writing__nothink.jsonl", encoding="utf-8"))}


def build():
    a, b = (load(m) for m in MODELS)
    items = {i["id"]: i for i in map(json.loads, open("items/writing.jsonl", encoding="utf-8"))}
    flips = [0, 1] * (len(items) // 2) + [0] * (len(items) % 2)
    random.Random(16).shuffle(flips)  # each model is "X" in half of the tasks, in random order
    J.mkdir(exist_ok=True)
    key, out = {}, []
    for tid, flip in zip(items, flips):
        pair = [(MODELS[0], a[tid]), (MODELS[1], b[tid])]
        if flip:
            pair.reverse()
        key[tid] = {"X": pair[0][0], "Y": pair[1][0]}
        out += [f"################ task {tid}", f"משימה: {items[tid]['question']}"]
        if items[tid]["gold"]:
            out.append(f"(תשובת ייחוס: {items[tid]['gold']})")
        for lab, (_, r) in zip("XY", pair):
            out += [f"-------- {lab}:", (r["answer"] or "(ריק)") + ("\n[נקטע באמצע: הגיע למגבלת האורך]" if r["truncated"] else "")]
        out.append("")
    (J / "writing_blind.txt").write_text("\n".join(out), encoding="utf-8")
    (J / "key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print(len(key), "tasks ->", J / "writing_blind.txt")


def tally():
    key = json.loads((J / "key.json").read_text())
    words = {m: {t: len((r["answer"] or "").split()) for t, r in load(m).items()} for m in MODELS}
    per = {m: {"errors": 0, "words": 0, "types": Counter(), "fluency": [], "task": []} for m in MODELS}
    pref = Counter()
    judges = sorted(J.glob("scores_*.json"))
    examples = defaultdict(list)
    for jf in judges:
        for s in json.loads(jf.read_text(encoding="utf-8")):
            k = key[s["task"]]
            for lab in "XY":
                m = k[lab]
                e = s[lab]["errors"]
                per[m]["errors"] += len(e)
                per[m]["types"].update(x["type"] for x in e)
                per[m]["words"] += words[m][s["task"]]
                per[m]["fluency"].append(s[lab]["fluency"])
                per[m]["task"].append(s[lab]["task"])
                examples[m] += [{"task": s["task"], "judge": jf.stem, **x} for x in e]
            pref[k[s["prefer"]] if s["prefer"] in "XY" else "tie"] += 1
    res = {"judges": len(judges), "preference": dict(pref), "per_model": {}}
    for m, d in per.items():
        res["per_model"][m] = {
            "errors_per_100_words": round(100 * d["errors"] / max(d["words"], 1), 2),
            "errors": d["errors"], "words_judged": d["words"], "error_types": dict(d["types"].most_common()),
            "fluency_mean": round(sum(d["fluency"]) / len(d["fluency"]), 2),
            "task_mean": round(sum(d["task"]) / len(d["task"]), 2)}
    res["error_examples"] = examples
    Path("results/writing_summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "error_examples"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"build": build, "tally": tally}[sys.argv[1]]()

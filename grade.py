"""Grade the auto-gradable runs and summarise thinking behaviour -> results/summary.json (+ printed tables).

  accuracy      per model x section x mode x part (multiple choice: letter after "התשובה:"; numbers: exact value)
  paired        per section/mode and pair of models: items only A got right vs only B, two-sided sign test
  thinking      generated tokens (median / p90), truncated runs, seconds per item, decode speed,
                and the script of the thinking text: share of Hebrew / Latin / CJK letters
  answer purity answers that contain CJK, Cyrillic or Arabic letters, or Latin words (writing translation task excluded)
Usage: python grade.py
"""
import json
import re
import statistics as st
from collections import defaultdict
from itertools import combinations
from fractions import Fraction
from math import comb
from pathlib import Path

R = Path("results")
MODELS = ["qwen38-27b", "qwen38-flash-next", "gemma4-26b-a4b"]
HEB, LAT = re.compile(r"[א-ת]"), re.compile(r"[A-Za-z]")
CJK, CYR, ARA = re.compile(r"[぀-ヿ一-鿿가-힯]"), re.compile(r"[Ѐ-ӿ]"), re.compile(r"[؀-ۿ]")
LATWORD = re.compile(r"\b[A-Za-z]{3,}\b")


def letter(ans):
    m = re.findall(r"התשובה\s*[:：]?\s*\**\s*\(?([אבגד])", ans)
    return m[-1] if m else None


def number(ans):
    m = re.findall(r"התשובה\s*[:：]?\s*\**\s*\$?\\?(?:boxed\{)?\s*(-?[\d,]*\.?\d+(?:\s*/\s*\d+)?)", ans)
    if not m:
        return None
    s = m[-1].replace(",", "").replace(" ", "")
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        return None


def correct(r):
    if r["kind"] == "mcq":
        return letter(r["answer"]) == r["gold"]
    if r["kind"] == "number":
        v = number(r["answer"])
        return v is not None and v == Fraction(r["gold"])
    return None


def sign(w, l):
    n = w + l
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(w, l) + 1)) / 2 ** n)


def script_mix(text):
    h, l, c = len(HEB.findall(text)), len(LAT.findall(text)), len(CJK.findall(text))
    t = h + l + c or 1
    return {"hebrew": h / t, "latin": l / t, "cjk": c / t}


def main():
    runs = defaultdict(dict)  # (section, mode) -> model -> {id: row}
    for p in sorted(R.glob("*__*__*.jsonl")):
        model, section, mode = p.stem.split("__")
        rows = {r["id"]: r for r in map(json.loads, open(p, encoding="utf-8"))}
        if rows:  # skip a run that has not written anything yet
            runs[(section, mode)][model] = rows

    summary = {"accuracy": {}, "paired": {}, "thinking": {}, "purity": {}}
    print("\n=== accuracy ===")
    for (section, mode), by_model in sorted(runs.items()):
        if section == "writing":
            continue
        for model, rows in by_model.items():
            parts = defaultdict(list)
            for r in rows.values():
                parts[r["part"]].append(correct(r))
                parts["ALL"].append(correct(r))
            acc = {p: {"correct": sum(v), "n": len(v), "pct": round(100 * sum(v) / len(v), 1)} for p, v in parts.items()}
            summary["accuracy"][f"{model}|{section}|{mode}"] = acc
            print(f"{model:20s} {section:9s} {mode:8s} " + "  ".join(f"{p} {a['correct']}/{a['n']}" for p, a in sorted(acc.items())))
        for ma, mb in combinations([m for m in MODELS if m in by_model], 2):
            a, b = by_model[ma], by_model[mb]
            ids = sorted(set(a) & set(b))
            ca, cb = [correct(a[i]) for i in ids], [correct(b[i]) for i in ids]
            oa = sum(x and not y for x, y in zip(ca, cb))
            ob = sum(y and not x for x, y in zip(ca, cb))
            summary["paired"][f"{section}|{mode}|{ma}|{mb}"] = {
                "a": ma, "b": mb, "n": len(ids), "only_a": oa, "only_b": ob,
                "both": sum(x and y for x, y in zip(ca, cb)), "neither": sum(not x and not y for x, y in zip(ca, cb)),
                "sign_p": round(sign(oa, ob), 3)}

    print("\n=== thinking / speed ===")
    for (section, mode), by_model in sorted(runs.items()):
        for model, rows in by_model.items():
            rs = list(rows.values())
            toks = sorted(r["gen_tokens"] for r in rs)
            th = [r["thinking"] for r in rs if r["thinking"]]
            mix = [script_mix(t) for t in th]
            d = {"n": len(rs), "median_tokens": st.median(toks), "p90_tokens": toks[int(0.9 * (len(toks) - 1))],
                 "truncated": sum(r["truncated"] for r in rs), "empty_answer": sum(not r["answer"] for r in rs),
                 "mean_seconds": round(st.mean(r["seconds"] for r in rs), 1),
                 "decode_tok_s": round(st.median(r["decode_tok_s"] for r in rs), 1)}
            if mix:
                d["thinking_script"] = {k: round(st.mean(m[k] for m in mix), 3) for k in mix[0]}
                d["thinking_mostly_hebrew"] = sum(m["hebrew"] > 0.5 for m in mix)
                d["thinking_n"] = len(mix)
            summary["thinking"][f"{model}|{section}|{mode}"] = d
            print(f"{model:20s} {section:9s} {mode:8s} {json.dumps(d, ensure_ascii=False)}")

    print("\n=== answer purity (foreign script inside Hebrew answers) ===")
    for (section, mode), by_model in sorted(runs.items()):
        for model, rows in by_model.items():
            rs = [r for r in rows.values() if r["part"] != "translate_he_en"]
            bad = {"cjk": [], "cyrillic": [], "arabic": [], "latin_words": []}
            for r in rs:
                a = r["answer"]
                for k, rx in [("cjk", CJK), ("cyrillic", CYR), ("arabic", ARA)]:
                    if rx.search(a):
                        bad[k].append(r["id"])
                words = [w for w in LATWORD.findall(a) if w.lower() not in {"the", "and"}]
                if words and r["section"] != "reasoning":  # math/STEM answers legitimately use Latin symbols
                    bad["latin_words"].append(f"{r['id']}: {' '.join(words[:5])}")
            summary["purity"][f"{model}|{section}|{mode}"] = {"n": len(rs), **bad}
            print(f"{model:20s} {section:9s} {mode:8s} " + "  ".join(f"{k} {len(v)}" for k, v in bad.items()))

    (R / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\npaired:", json.dumps(summary["paired"], indent=1))


if __name__ == "__main__":
    main()

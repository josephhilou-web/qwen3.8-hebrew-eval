"""Markdown tables for the report from results/summary.json and results/writing_summary.json -> results/tables.md
Usage: python grade.py && python judge_writing.py tally && python make_tables.py
"""
import json
from pathlib import Path

M = ["qwen38-27b", "qwen38-flash-next"]
NAME = {"qwen38-27b": "Qwen3.8-27B", "qwen38-flash-next": "Qwen3.8-Flash-Next"}
s = json.loads(Path("results/summary.json").read_text(encoding="utf-8"))
w = json.loads(Path("results/writing_summary.json").read_text(encoding="utf-8")) if Path("results/writing_summary.json").exists() else None
out = []


def acc(model, section, mode, part="ALL"):
    a = s["accuracy"].get(f"{model}|{section}|{mode}", {}).get(part)
    return f"{a['correct']}/{a['n']} ({a['pct']:.0f}%)" if a else "–"


def table(head, rows):
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    out.extend("| " + " | ".join(map(str, r)) + " |" for r in rows)
    out.append("")


out.append("### Reasoning in Hebrew (thinking on, effort medium)\n")
parts = [("math_he", "Math word problems"), ("include_logic", "Native Hebrew logic / verbal reasoning (INCLUDE)"),
         ("gmmlu_stem", "STEM, human-translated (Global-MMLU)"), ("include_driving", "Israeli driving theory (INCLUDE)"),
         ("ALL", "**All reasoning**")]
table(["Part"] + [NAME[m] for m in M], [[label] + [acc(m, "reasoning", "think", p) for m in M] for p, label in parts])

out.append("### Hebrew language knowledge (28 questions)\n")
cats = ["numerals", "agreement", "construct_state", "prepositions", "verb_forms", "roots", "homographs", "idioms", "spelling", "ALL"]
table(["Category"] + [f"{NAME[m]} no-think" for m in M] + [f"{NAME[m]} think" for m in M],
      [[("**All**" if c == "ALL" else c)] + [acc(m, "language", md, c) for md in ["nothink", "think"] for m in M] for c in cats])

out.append("### Paired comparison (same items)\n")
table(["Set", "n", f"only {NAME[M[0]]} right", f"only {NAME[M[1]]} right", "both", "neither", "sign test p"],
      [[k.replace("|", ", "), v["n"], v[f"only_{M[0]}"], v[f"only_{M[1]}"], v["both"], v["neither"], v["sign_p"]] for k, v in s["paired"].items()])

out.append("### Thinking behaviour\n")
rows = []
for key, d in s["thinking"].items():
    model, section, mode = key.split("|")
    if mode != "think":
        continue
    sc = d.get("thinking_script", {})
    rows.append([NAME[model], section, round(d["median_tokens"]), d["p90_tokens"], d["truncated"],
                 f"{100 * sc.get('hebrew', 0):.0f}% / {100 * sc.get('latin', 0):.0f}% / {100 * sc.get('cjk', 0):.0f}%",
                 f"{d.get('thinking_mostly_hebrew', 0)}/{d.get('thinking_n', 0)}"])
table(["Model", "Set", "median tokens", "p90 tokens", "hit 16k cap", "thinking letters: Hebrew / Latin / CJK",
       "traces mostly in Hebrew"], rows)

out.append("### Foreign script leaking into Hebrew answers\n")
rows = []
for key, d in s["purity"].items():
    model, section, mode = key.split("|")
    rows.append([NAME[model], section, mode, d["n"], len(d["cjk"]), len(d["cyrillic"]), len(d["arabic"]), len(d["latin_words"])])
table(["Model", "Set", "Mode", "answers", "with CJK", "with Cyrillic", "with Arabic", "with Latin words"], rows)

if w:
    out.append(f"### Writing quality (16 tasks, thinking off, blind, {w['judges']} judges)\n")
    pm = w["per_model"]
    table(["Metric"] + [NAME[m] for m in M], [
        ["Hebrew errors per 100 words (lower is better)"] + [pm[m]["errors_per_100_words"] for m in M],
        ["Errors found / words judged"] + [f"{pm[m]['errors']} / {pm[m]['words_judged']}" for m in M],
        ["Fluency 1-5"] + [pm[m]["fluency_mean"] for m in M],
        ["Task success 1-5"] + [pm[m]["task_mean"] for m in M],
        ["Preferred by judges (tasks x judges)"] + [w["preference"].get(m, 0) for m in M]])
    types = sorted({t for m in M for t in pm[m]["error_types"]})
    table(["Error type"] + [NAME[m] for m in M], [[t] + [pm[m]["error_types"].get(t, 0) for m in M] for t in types])
    out.append(f"Ties: {w['preference'].get('tie', 0)}\n")

Path("results/tables.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))

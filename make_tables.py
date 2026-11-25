"""Markdown tables for the report from results/summary.json and results/writing_summary_*.json -> results/tables.md
Usage: python grade.py && python judge_writing.py tally --dir judge/<pass> && python make_tables.py
"""
import json
from pathlib import Path

M = ["qwen38-27b", "qwen38-flash-next", "gemma4-26b-a4b"]
NAME = {"qwen38-27b": "Qwen3.8-27B (dense)", "qwen38-flash-next": "Qwen3.8-Flash-Next (MoE)",
        "gemma4-26b-a4b": "Gemma-4-26B-A4B (MoE)", "gemma4-26b-a4b-1120tok": "Gemma-4-26B-A4B, 1120 image tokens",
        "qwen38-27b-bf16": "Qwen3.8-27B BF16", "qwen38-flash-next-min1024": "Qwen3.8-Flash-Next, min 1024 image tokens"}
s = json.loads(Path("results/summary.json").read_text(encoding="utf-8"))
M = [m for m in M if any(k.startswith(m + "|") for k in s["accuracy"])]  # models that have results


def wsum(name):
    p = Path(f"results/writing_summary_{name}.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


W = {name: wsum(name) for name in ["nothink", "tuned", "qwen_pairwise"]}
out = []


def acc(model, section, mode, part="ALL"):
    a = s["accuracy"].get(f"{model}|{section}|{mode}", {}).get(part)
    return f"{a['correct']}/{a['n']} ({a['pct']:.0f}%)" if a else "–"


def table(head, rows):
    out.append("| " + " | ".join(head) + " |")
    out.append("|" + "---|" * len(head))
    out.extend("| " + " | ".join(map(str, r)) + " |" for r in rows)
    out.append("")


def writing_rows(w, models):
    pm = w["per_model"]
    rows = [["Hebrew errors per 100 words (lower is better)"] + [pm[m]["errors_per_100_words"] for m in models],
            ["Errors found / words judged"] + [f"{pm[m]['errors']} / {pm[m]['words_judged']}" for m in models],
            ["Fluency 1-5"] + [pm[m]["fluency_mean"] for m in models],
            ["Task success 1-5"] + [pm[m]["task_mean"] for m in models],
            ["Best answer (tasks x judges)"] + [w["first_place"].get(m, 0) for m in models]]
    if all("mean_rank" in pm[m] for m in models):
        rows.append([f"Mean rank (1 = best of {len(models)})"] + [pm[m]["mean_rank"] for m in models])
    return rows


out.append("### Reasoning in Hebrew (thinking on)\n")
parts = [("math_he", "Math word problems"), ("include_logic", "Native Hebrew logic / verbal reasoning (INCLUDE)"),
         ("gmmlu_stem", "STEM, human-translated (Global-MMLU)"), ("include_driving", "Israeli driving theory (INCLUDE)"),
         ("ALL", "**All reasoning**")]
table(["Part"] + [NAME[m] for m in M], [[label] + [acc(m, "reasoning", "think", p) for m in M] for p, label in parts])

out.append("### Hebrew language knowledge (28 questions)\n")
cats = ["numerals", "agreement", "construct_state", "prepositions", "verb_forms", "roots", "homographs", "idioms", "spelling", "ALL"]
for md, title in [("nothink", "thinking off"), ("think", "thinking on")]:
    out.append(f"**{title}**\n")
    table(["Category"] + [NAME[m] for m in M],
          [[("**All**" if c == "ALL" else c)] + [acc(m, "language", md, c) for m in M] for c in cats])

out.append("### Paired comparison (same items)\n")
table(["Set", "A", "B", "n", "only A right", "only B right", "both", "neither", "sign test p"],
      [[", ".join(k.split("|")[:2]), NAME[v["a"]], NAME[v["b"]], v["n"], v["only_a"], v["only_b"], v["both"],
        v["neither"], v["sign_p"]] for k, v in s["paired"].items() if v["a"] in M and v["b"] in M])

out.append("### Thinking behaviour\n")
rows = []
for key, d in s["thinking"].items():
    model, section, mode = key.split("|")
    if mode != "think" or model not in M:
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
    if model in M:
        rows.append([NAME[model], section, mode, d["n"], len(d["cjk"]), len(d["cyrillic"]), len(d["arabic"]), len(d["latin_words"])])
table(["Model", "Set", "Mode", "answers", "with CJK", "with Cyrillic", "with Arabic", "with Latin words"], rows)

for name, title in [("nothink", "default settings, thinking off"), ("tuned", "tuned settings")]:
    w = W[name]
    if not w:
        continue
    wm = [m for m in M if m in w["per_model"]]
    out.append(f"### Writing quality, {title} (16 tasks, blind, {w['judges']} judges, all answers side by side)\n")
    table(["Metric"] + [NAME[m] for m in wm], writing_rows(w, wm))
    types = sorted({t for m in wm for t in w["per_model"][m]["error_types"]})
    table(["Error type"] + [NAME[m] for m in wm], [[t] + [w["per_model"][m]["error_types"].get(t, 0) for m in wm] for t in types])
    out.append(f"Ties for best answer: {w['first_place'].get('tie', 0)}\n")

def writing_pairs(name):  # per task: which model the two judges ranked higher on average
    from itertools import combinations

    from grade import sign
    J = Path("judge") / name
    key = json.loads((J / "key.json").read_text())
    key.pop("_mode", None)
    pos = {}
    for jf in sorted(J.glob("scores_*.json")):
        for t in json.loads(jf.read_text(encoding="utf-8")):
            for i, lab in enumerate(t["rank"]):
                pos.setdefault(t["task"], {}).setdefault(key[t["task"]][lab], []).append(i + 1)
    rows = []
    for a, b in combinations([m for m in M if all(m in p for p in pos.values())], 2):
        wa = sum(sum(p[a]) < sum(p[b]) for p in pos.values())
        wb = sum(sum(p[b]) < sum(p[a]) for p in pos.values())
        rows.append([NAME[a], NAME[b], wa, wb, len(pos) - wa - wb, round(sign(wa, wb), 3)])
    return rows


for name, title in [("nothink", "default settings"), ("tuned", "tuned settings")]:
    if W[name]:
        out.append(f"### Writing, task by task ({title}): which answer the judges ranked higher\n")
        table(["A", "B", "tasks A ranked higher", "tasks B ranked higher", "level", "sign test p"], writing_pairs(name))

if W["qwen_pairwise"]:
    w = W["qwen_pairwise"]
    wm = [m for m in M if m in w["per_model"]]
    out.append(f"### Writing quality, first pass (two Qwen models only, default settings, {w['judges']} judges)\n")
    table(["Metric"] + [NAME[m] for m in wm], writing_rows(w, wm))

if any(f"{m}|language|tuned" in s["accuracy"] for m in M):
    def leaks(model, mode):  # answers (language + writing) with CJK, Cyrillic or Arabic letters
        ids = set()
        for section in ["language", "writing"]:
            d = s["purity"].get(f"{model}|{section}|{mode}", {})
            ids |= {f"{section}:{i}" for k in ["cjk", "cyrillic", "arabic"] for i in d.get(k, [])}
        n = sum(s["purity"].get(f"{model}|{sec}|{mode}", {}).get("n", 0) for sec in ["language", "writing"])
        return f"{len(ids)} / {n}" if n else "–"

    def words(model, mode):
        p = Path(f"results/{model}__writing__{mode}.jsonl")
        if not p.exists():
            return "–"
        ws = sorted(len(json.loads(l)["answer"].split()) for l in open(p, encoding="utf-8"))
        return ws[len(ws) // 2]

    def wv(mode, model, field):
        w = W[mode]
        return w["per_model"][model][field] if w and model in w["per_model"] else "–"

    cols = [(m, md) for m in M for md in ["nothink", "tuned"]]
    head = ["Thinking off"] + [f"{NAME[m]} {'default' if md == 'nothink' else 'tuned'}" for m, md in cols]
    rows = [["Grammar questions (28)"] + [acc(m, "language", md) for m, md in cols],
            ["Answers with Arabic / Chinese / Cyrillic letters"] + [leaks(m, md) for m, md in cols],
            ["Median writing answer length (words)"] + [words(m, md) for m, md in cols],
            ["Writing: Hebrew errors per 100 words"] + [wv(md, m, "errors_per_100_words") for m, md in cols],
            ["Writing: fluency 1-5"] + [wv(md, m, "fluency_mean") for m, md in cols],
            ["Writing: task success 1-5"] + [wv(md, m, "task_mean") for m, md in cols]]
    out.append("### Default vs tuned settings (thinking off)\n")
    table(head, rows)

V = Path("vision/results/summary.json")
if V.exists():
    v = json.loads(V.read_text(encoding="utf-8"))
    vm = [m for m in ["qwen38-27b", "qwen38-27b-bf16", "qwen38-flash-next", "qwen38-flash-next-min1024",
                      "gemma4-26b-a4b", "gemma4-26b-a4b-1120tok"] if m in v]
    o = lambda m, ver, k: v[m]["ocr"].get(ver, {}).get(k, "–")
    out.append("### Reading Hebrew documents from images (12 pages, clean and scanned; 42 questions on the scans)\n")
    table(["Metric"] + [NAME[m] for m in vm], [
        ["Word F1, clean pages (higher is better)"] + [o(m, "clean", "word_f1_mean") for m in vm],
        ["Word F1, scanned pages"] + [o(m, "scan", "word_f1_mean") for m in vm],
        ["Character error rate, clean (lower is better)"] + [f"{100 * o(m, 'clean', 'cer_mean'):.1f}%" for m in vm],
        ["Character error rate, scanned"] + [f"{100 * o(m, 'scan', 'cer_mean'):.1f}%" for m in vm],
        ["Questions answered correctly (scans)"] + [f"{v[m]['qa']['all']['correct']}/{v[m]['qa']['all']['n']}" for m in vm],
        ["Pages (of 24) with reversed words or numbers"] + [sum(x["pages_with_reversed"] for x in v[m]["ocr"].values()) for m in vm],
        ["Reversed words / reversed numbers"] + [f"{sum(x['reversed_words'] for x in v[m]['ocr'].values())} / "
                                                 f"{sum(x['reversed_numbers'] for x in v[m]['ocr'].values())}" for m in vm],
        ["Transcriptions with Arabic / CJK / Cyrillic"] + [sum(x["foreign"] for x in v[m]["ocr"].values()) for m in vm],
        ["Transcriptions cut off at 2,500 tokens"] + [sum(x["truncated"] for x in v[m]["ocr"].values()) for m in vm],
        ["Mean seconds per item"] + [v[m]["seconds_mean"] for m in vm]])
    docs = sorted({k.split("|")[0] for m in vm for k in v[m]["per_doc"]})
    for ver in ["clean", "scan"]:
        out.append(f"**Word F1 per document, {ver}**\n")
        table(["Document"] + [NAME[m] for m in vm],
              [[d] + [v[m]["per_doc"].get(f"{d}|{ver}", {}).get("word_f1", "–") for m in vm] for d in docs])
    out.append("**Questions per document (scans)**\n")
    table(["Document"] + [NAME[m] for m in vm],
          [[d] + [f"{sum(v[m]['per_doc'].get(d + '|qa', []))}/{len(v[m]['per_doc'].get(d + '|qa', []))}" for m in vm]
           for d in docs])

Path("results/tables.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))

"""Score the document-reading runs -> vision/results/summary.json (+ printed tables)

ocr  CER       character error rate against the known page text, after normalising both sides: markdown, table
               pipes, checkbox marks, quote/dash variants and niqqud removed, whitespace collapsed. Order-sensitive,
               so a wrong reading order (e.g. a table read left to right) costs here.
     word F1   the same text as a bag of words: order-free, so it isolates misread / invented / missing words
     niqqud    for the niqqud page, CER with the vowel marks kept as well
     foreign   outputs with Arabic, CJK or Cyrillic letters
     reversed  Hebrew words (3+ letters) and numbers (3+ digits) written backwards: the output word is not in the page
               but its mirror image is ("םיכמסמ" for "מסמכים", "71402" for "20417"), a right-to-left ordering failure
qa   exact match after normalisation: num (any number in the answer equals the gold), id (gold digits appear in the
     answer's digits), date (d/m/y in any common format), text (gold appears in the answer; an answer written with
     niqqud must match the vocalized gold, so "יָרָק" (vegetable) does not pass for "יָרֹק" (green))
Word F1 is the main reading score; CER also depends on the order in which side-by-side fields are read.
Usage: python vision/grade_vision.py
"""
import json
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
NIQ = re.compile(r"[֑-ׇֽֿׁׂׅׄ]")
FOREIGN = re.compile(r"[؀-ۿ぀-ヿ一-鿿가-힯Ѐ-ӿ]")
MONTHS = {m: i for i, m in enumerate(["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר",
                                       "אוקטובר", "נובמבר", "דצמבר"], 1)}
NUMWORDS = {w: i for i, ws in enumerate([[], ["אחד", "אחת"], ["שניים", "שתיים", "שני", "שתי"], ["שלושה", "שלוש"],
                                         ["ארבעה", "ארבע"], ["חמישה", "חמש"], ["שישה", "שש"], ["שבעה", "שבע"],
                                         ["שמונה"], ["תשעה", "תשע"], ["עשרה", "עשר"]]) for w in ws}
NUMWORDS.update({"ארבעה עשר": 14, "ארבע עשרה": 14, "ארבעה-עשר": 14})


def lev(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    bb = np.frombuffer(b.encode("utf-32-le"), dtype=np.uint32)
    prev = np.arange(len(b) + 1)
    idx = np.arange(len(b) + 1)
    for i, ca in enumerate(a, 1):
        cur = np.empty_like(prev)
        cur[0] = i
        cur[1:] = np.minimum(prev[:-1] + (bb != ord(ca)), prev[1:] + 1)
        prev = np.minimum.accumulate(cur - idx) + idx  # insertions
    return int(prev[-1])


def norm(t, keep_niqqud=False):
    t = re.sub(r"```[a-z]*", "", t or "")
    lines = []
    for ln in t.splitlines():
        if re.match(r"^\s*\|?\s*:?-{3,}", ln):  # markdown table separator
            continue
        ln = re.sub(r"^\s*(#+|[-*•])\s+", "", ln)
        lines.append(ln)
    t = "\n".join(lines)
    t = re.sub(r"\*\*|__|`", "", t)
    t = re.sub(r"\[[ xX✓]\]|[☐☒☑✓✔✗]", " ", t)
    t = t.replace("|", " ")
    t = re.sub(r"[“”„״″]", '"', t)
    t = re.sub(r"[‘’׳′]", "'", t)
    t = re.sub(r"[–—־‐]", "-", t)
    t = re.sub(r"[‎‏‪-‮]", "", t)
    if not keep_niqqud:
        t = NIQ.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def words(t):
    return Counter(w for w in (x.strip(".,:;!?()\"'") for x in t.split()) if w)


def word_f1(pred, gold):
    p, g = words(pred), words(gold)
    tp = sum((p & g).values())
    if not tp:
        return 0.0, 0.0, 0.0
    pr, rc = tp / sum(p.values()), tp / sum(g.values())
    return pr, rc, 2 * pr * rc / (pr + rc)


def reversed_tokens(pred, gold):
    gw = set(norm(gold).split())
    heb = [w.strip(".,:;!?()\"'") for w in norm(pred).split()]
    rw = sum(1 for w in heb if len(re.findall("[א-ת]", w)) >= 3 and w not in gw and w[::-1] in gw)
    gnum = set(re.findall(r"\d{3,}", gold))
    rn = sum(1 for n in re.findall(r"\d{3,}", pred) if n not in gnum and n[::-1] in gnum)
    return rw, rn


def numbers(ans):
    out = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", ans)]
    a = norm(ans)
    out += [v for w, v in NUMWORDS.items() if re.search(rf"(^|[\sו]){w}($|[\s.,])", a)]
    return out


def dates(ans):
    out = [(int(d), int(m), int(y) + ((2000 if int(y) < 50 else 1900) if len(y) == 2 else 0))
           for d, m, y in re.findall(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4}|\d{2})", ans)]
    for d, mon, y in re.findall(r"(\d{1,2})\s+ב?(" + "|".join(MONTHS) + r")\s+(\d{4})", ans):
        out.append((int(d), MONTHS[mon], int(y)))
    return out


def qa_ok(it, ans):
    m, g = it["match"], it["gold"]
    if m == "num":
        return any(abs(x - g) < 1e-6 for x in numbers(ans))
    if m == "id":
        return g in re.sub(r"\D", "", ans)
    if m == "date":
        return tuple(g) in dates(ans)
    if m == "text":
        if it.get("gold_niqqud") and NIQ.search(ans):  # a vocalized answer must carry the right vowels
            return norm(it["gold_niqqud"], keep_niqqud=True) in norm(ans, keep_niqqud=True)
        a = re.sub(r"[\"'.,:;!?()-]", "", norm(ans))
        return any(re.sub(r"[\"'.,:;!?()-]", "", norm(x)) in a for x in g)
    raise ValueError(m)


def main():
    items = {i["id"]: i for i in map(json.loads, open(HERE / "items.jsonl", encoding="utf-8"))}
    summary = {}
    for p in sorted((HERE / "results").glob("*.jsonl")):
        rows = [json.loads(l) for l in open(p, encoding="utf-8")]
        if not rows:
            continue
        name = p.stem
        ocr, qa = defaultdict(list), defaultdict(list)
        per_doc = {}
        for r in rows:
            it = items[r["id"]]
            if it["kind"] == "ocr":
                pred, gold = norm(r["answer"]), norm(it["gold"])
                cer = lev(pred, gold) / len(gold)
                pr, rc, f1 = word_f1(pred, gold)
                rw, rn = reversed_tokens(r["answer"], it["gold"])
                d = {"cer": round(cer, 4), "word_precision": round(pr, 3), "word_recall": round(rc, 3),
                     "word_f1": round(f1, 3), "foreign": bool(FOREIGN.search(r["answer"])), "truncated": r["truncated"],
                     "reversed_words": rw, "reversed_numbers": rn}
                if it["doc"] == "niqqud":
                    g2 = norm(it["gold"], keep_niqqud=True)
                    d["cer_with_niqqud"] = round(lev(norm(r["answer"], keep_niqqud=True), g2) / len(g2), 4)
                ocr[it["version"]].append(d)
                per_doc[f"{it['doc']}|{it['version']}"] = d
            else:
                ok = qa_ok(it, r["answer"])
                qa["all"].append(ok)
                qa[it["match"]].append(ok)
                per_doc.setdefault(f"{it['doc']}|qa", []).append(ok)
        s = {"n": len(rows), "ocr": {}, "qa": {}, "per_doc": per_doc,
             "seconds_mean": round(st.mean(r["seconds"] for r in rows), 1)}
        for ver, ds in ocr.items():
            s["ocr"][ver] = {"n": len(ds), "cer_mean": round(st.mean(d["cer"] for d in ds), 4),
                             "cer_median": round(st.median(d["cer"] for d in ds), 4),
                             "word_f1_mean": round(st.mean(d["word_f1"] for d in ds), 3),
                             "word_precision_mean": round(st.mean(d["word_precision"] for d in ds), 3),
                             "foreign": sum(d["foreign"] for d in ds), "truncated": sum(d["truncated"] for d in ds),
                             "reversed_words": sum(d["reversed_words"] for d in ds),
                             "reversed_numbers": sum(d["reversed_numbers"] for d in ds),
                             "pages_with_reversed": sum(d["reversed_words"] + d["reversed_numbers"] > 0 for d in ds)}
        for k, v in qa.items():
            s["qa"][k] = {"correct": sum(v), "n": len(v)}
        summary[name] = s
        o = s["ocr"]
        print(f"{name:32s} CER clean {o.get('clean', {}).get('cer_mean', '-'):>7} scan {o.get('scan', {}).get('cer_mean', '-'):>7} | "
              f"word F1 clean {o.get('clean', {}).get('word_f1_mean', '-'):>5} scan {o.get('scan', {}).get('word_f1_mean', '-'):>5} | "
              f"QA {s['qa'].get('all', {}).get('correct', 0)}/{s['qa'].get('all', {}).get('n', 0)} | "
              f"foreign {sum(x['foreign'] for x in o.values())}")
    (HERE / "results" / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

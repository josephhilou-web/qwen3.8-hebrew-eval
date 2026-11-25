"""Build the quick Hebrew test set -> items/{reasoning,language,writing}.jsonl

reasoning (36, thinking on, auto-graded): sampled with a fixed seed from
  - math_he          12  multi-step Hebrew word problems, answers verified in Python
  - include_logic    12  INCLUDE-base-44 Hebrew "Logic" (native Israeli academic-exam questions)
  - gmmlu_stem        6  Global-MMLU Hebrew, human-checked translations (math / physics / statistics)
  - include_driving   6  INCLUDE-base-44 Hebrew driving-theory questions (Israeli local knowledge)
language (28, run with thinking off AND on, auto-graded): multiple-choice questions written for this test:
  numerals, gender/number agreement, construct state, prepositions, verb forms and binyanim, roots,
  unvocalized homographs, idioms, spelling (Academy full spelling)
writing (16, thinking off, graded blind by an LLM judge for Hebrew errors, fluency and task success)

Source pool for reasoning and the 12 open_he writing tasks: ../../data/hebrew_eval/items.jsonl, built in the parent
project from the public CohereLabs datasets plus hand-written math problems and writing tasks. The pool is not part
of this repository; the built items/*.jsonl are, so you do not need to run this. Run: python3 build_items.py
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
POOL = HERE.parent.parent / "data/hebrew_eval/items.jsonl"
LET = "אבגד"

# (category, question, options, index of the correct option)
LANG = [
    ("numerals", "השלם את החסר: בכיתה של נועה יש ___ תלמידות חדשות.", ["שלוש", "שלושה", "שלושת", "שלושתן"], 0),
    ("numerals", "השלם את החסר: הזמנתי ___ ספרים מהחנות.", ["חמישה", "חמש", "חמשת", "חמישית"], 0),
    ("numerals", "השלם את החסר: המחיר הוא ___ שקלים.", ["עשרים ואחד", "עשרים ואחת", "עשרים ושתיים", "עשרים ואחת־עשרה"], 0),
    ("numerals", "השלם את החסר: הישיבה תתקיים בעוד ___ שבועות.", ["שני", "שתי", "שניים", "שתיים"], 0),
    ("agreement", "השלם את החסר: הממשלה ___ אתמול על תוכנית חדשה.", ["החליטה", "החליט", "מחליטים", "החליטו"], 0),
    ("agreement", "השלם את החסר: השולחנות במשרד ___.", ["חדשים", "חדשות", "חדשה", "חדש"], 0),
    ("agreement", "השלם את החסר: העיניים שלה ___ מאוד.", ["יפות", "יפים", "יפה", "יופי"], 0),
    ("agreement", "השלם את החסר: כל הדרכים בצפון ___ בגלל השלג.", ["חסומות", "חסומים", "חסום", "חסומה"], 0),
    ("construct_state", "איזו צורה תקנית?", ["בית הספר החדש", "הבית ספר החדש", "הבית הספר החדש", "בית ספר החדש"], 0),
    ("construct_state", "מהו הריבוי התקני של הצירוף \"חדר אוכל\"?", ["חדרי אוכל", "חדרים אוכל", "חדר אוכלים", "חדרי אוכלים"], 0),
    ("prepositions", "איזה משפט תקני?", ["הוא השתמש במחשב", "הוא השתמש את המחשב", "הוא השתמש עם המחשב", "הוא השתמש על המחשב"], 0),
    ("prepositions", "איזה משפט תקני?", ["אני מחכה לתשובה", "אני מחכה על התשובה", "אני מחכה את התשובה", "אני מחכה בתשובה"], 0),
    ("prepositions", "איזה משפט תקני?", ["אני רוצה שתבוא אליי מחר", "אני רוצה שתבוא עליי מחר", "אני רוצה שתבוא לאצלי מחר", "אני רוצה שתבוא בי מחר"], 0),
    ("verb_forms", "השלם בצורה התקנית: מחר אני ___ את החשבון.", ["אשלם", "ישלם", "אשלום", "תשלם"], 0),
    ("verb_forms", "מהי צורת הציווי התקנית של הפועל \"לשבת\" בנקבה יחידה?", ["שבי", "תשבי", "ישבי", "שבת"], 0),
    ("verb_forms", "באיזה בניין הפועל \"הוכנס\"?", ["הופעל", "פיעל", "התפעל", "נפעל"], 0),
    ("verb_forms", "באיזה בניין הפועל \"נשבר\"?", ["נפעל", "פעל (קל)", "פועל", "הפעיל"], 0),
    ("roots", "מהו השורש של המילה \"התכתבנו\"?", ["כ-ת-ב", "ת-כ-ב", "ת-ב-נ", "כ-ת-נ"], 0),
    ("roots", "מהו השורש של המילה \"הצטלמתי\"?", ["צ-ל-מ", "צ-ט-ל", "ט-ל-מ", "ס-ל-מ"], 0),
    ("roots", "מהו השורש של המילה \"השתכרתי\" (במובן: קיבלתי משכורת)?", ["ש-כ-ר", "ש-ת-כ", "ת-כ-ר", "כ-ר-ת"], 0),
    ("homographs", "במשפט \"הספר גזר לי את השיער\", מה פירוש המילה \"הספר\"?", ["מי שמספר שיער כמקצוע", "ספר קריאה", "אזור הגבול", "מי שסופר ומונה דברים"], 0),
    ("homographs", "במשפט \"הוא שם את המפתחות על השולחן\", מה פירוש המילה \"שם\"?", ["הניח", "כינוי של אדם", "במקום ההוא", "שמע"], 0),
    ("idioms", "מה פירוש הביטוי \"נפל בין הכיסאות\"?", ["לא טופל, כי אף גורם לא לקח עליו אחריות", "נכשל בגלל עצלות", "הגיע באיחור לאירוע", "עבר בין מקומות עבודה רבים"], 0),
    ("idioms", "מה פירוש הביטוי \"עבר לסדר היום\"?", ["התעלם מהעניין והמשיך כרגיל", "דן בנושא בהרחבה", "קבע פגישה חדשה", "שינה את סדרי העדיפויות"], 0),
    ("idioms", "מה פירוש הביטוי \"לא דובים ולא יער\"?", ["אין שום אמת בדבר", "המצב מסוכן", "הדבר רחוק מכאן", "אין מה לעשות"], 0),
    ("idioms", "מה פירוש הביטוי \"שבר את הכלים\"?", ["פרש בכעס ממסגרת או מהסכם", "הרס רכוש", "הצליח מעבר למצופה", "עבד קשה מאוד"], 0),
    ("spelling", "איזה איות נכון לפי כללי הכתיב המלא של האקדמיה ללשון העברית (כללי 2017)?", ["תוכנית", "תכנית", "תוכניית", "תכניית"], 0),
    ("spelling", "איזה איות נכון לפי האקדמיה ללשון העברית?", ["לחלופין", "לחילופין", "לחילופים", "לחליפין"], 0),
]

EXTRA_WRITING = [
    ("translate_he_en", "תרגם לאנגלית טבעית (לא מילולית): \"אחרי שהבקשה שלו נדחתה פעמיים, הוא החליט לא לוותר ולפנות לנציב תלונות הציבור.\"", None),
    ("summary", "סכם בשני משפטים את הפסקה הבאה:\n\"ישראל היא אחת המדינות המובילות בעולם בהתפלת מי ים. בשנים האחרונות הוקמו לאורך החוף כמה מתקני התפלה גדולים, "
                "שמספקים כיום את רוב המים לשתייה ולשימוש ביתי. ההתפלה צמצמה מאוד את התלות במי הגשמים ובכנרת, ואפשרה אפילו להזרים מים "
                "מותפלים לכנרת בשנים שחונות. מצד שני, התהליך צורך הרבה אנרגיה, ויש חשש מפגיעה בסביבה הימית בגלל התמלחת שמוחזרת לים.\"", None),
    ("register", "כתוב הודעת וואטסאפ קלילה וקצרה לקבוצת החברים, שבה אתה מזמין אותם למנגל ביום שישי בצהריים אצלך, ומבקש מכל אחד להביא משהו.", None),
    ("niqqud", "כתוב את המשפט הבא בניקוד מלא: \"הילדים שיחקו בחצר עד שירד הגשם.\"",
     "הַיְלָדִים שִׂחֲקוּ בֶּחָצֵר עַד שֶׁיָּרַד הַגֶּשֶׁם."),
]


def main():
    pool = [json.loads(l) for l in open(POOL, encoding="utf-8")]
    rng = random.Random(38)
    out = HERE / "items"
    out.mkdir(exist_ok=True)

    reasoning = []
    for part, n in [("math_he", 12), ("include_logic", 12), ("gmmlu_stem", 6), ("include_driving", 6)]:
        cand = sorted((i for i in pool if i["part"] == part), key=lambda i: i["id"])
        reasoning += [{**i, "section": "reasoning"} for i in rng.sample(cand, n)]

    language = []
    for k, (cat, q, opts, gold) in enumerate(LANG):
        order = list(range(4))
        rng.shuffle(order)  # spread the correct answer over א-ד
        language.append({"id": f"lang-{k:02d}", "section": "language", "part": cat, "kind": "mcq", "question": q,
                         "options": [opts[j] for j in order], "gold": LET[order.index(gold)]})

    writing = [{"id": i["id"], "section": "writing", "part": "open_he", "kind": "open", "question": i["question"],
                "gold": None} for i in pool if i["part"] == "open_he"]
    writing += [{"id": f"write-{part}", "section": "writing", "part": part, "kind": "open", "question": q, "gold": g}
                for part, q, g in EXTRA_WRITING]

    for name, rows in [("reasoning", reasoning), ("language", language), ("writing", writing)]:
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(name, len(rows))


if __name__ == "__main__":
    main()

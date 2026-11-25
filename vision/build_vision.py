"""Build the Hebrew document-reading test -> vision/images/*.png + vision/items.jsonl

12 synthetic Hebrew documents (all names, companies, numbers and addresses are made up). Each document is written
as HTML, rendered by headless Chrome at A4 width (1240 px, about 150 dpi; right-to-left layout and tables are
handled by the browser), and saved twice:
  clean  the rendered page, as from a digital PDF
  scan   the same page made to look scanned: grey paper, 0.6-1.4 degree tilt, blur, noise, lower resolution, JPEG
Items:
  ocr  transcribe the whole page (both versions)     -> character error rate and word F1 against the known text
  qa   short questions about the scanned version     -> exact match (numbers, ids, dates, short text)
Run: python3 vision/build_vision.py   (needs Google Chrome, Pillow and numpy)
"""
import html
import io
import json
import random
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W = 1240

# ---------------------------------------------------------------- documents
# blocks: ("h1"|"h2"|"p"|"right"|"small", text), ("kv", [(label, value)]), ("table", header, rows),
#         ("ol", [items]), ("check", [(checked, label)]), ("cols", [blocks]), ("niqqud", [lines])
# qa: (question, match, gold[, gold_niqqud]) where match is num | id | date | text; text gold is a list of options;
#     gold_niqqud: the required vocalized form when an answer is written with niqqud
DOCS = [
    dict(id="invoice", font="Arial Hebrew", size=22, blocks=[
        ("h1", "נגרות העמק בע\"מ"),
        ("p", "רחוב הנפחים 12, אזור התעשייה הצפוני | ח.פ. 514382917 | טלפון: 04-9590123"),
        ("h2", "חשבונית מס / קבלה מס' 20417"),
        ("kv", [("תאריך", "14/03/2026"), ("לכבוד", "דנה כהן-לוי, רחוב הזית 7, קריית אורנים")]),
        ("table", ["תיאור", "כמות", "מחיר ליחידה", "סה\"כ"], [
            ["ארון מטבח עליון, אלון", "3", "1,250.00", "3,750.00"],
            ["מדף צף 80 ס\"מ", "4", "185.00", "740.00"],
            ["התקנה והובלה", "1", "450.00", "450.00"],
            ["ידיות נירוסטה", "12", "22.50", "270.00"]]),
        ("kv", [("סה\"כ לפני מע\"מ", "5,210.00"), ("מע\"מ 18%", "937.80"), ("סה\"כ לתשלום", "6,147.80 ש\"ח")]),
        ("p", "התשלום התקבל בהעברה בנקאית ביום 16/03/2026. תודה שבחרתם בנו!")],
        qa=[("מהו הסכום הכולל לתשלום בחשבונית?", "num", 6147.80),
            ("מה מספר החשבונית?", "id", "20417"),
            ("כמה מדפים צפים הוזמנו?", "num", 4),
            ("מה סכום המע\"מ בחשבונית?", "num", 937.80),
            ("מה מספר ח.פ. של העסק?", "id", "514382917")]),

    dict(id="form", font="Tahoma", size=21, blocks=[
        ("h1", "עיריית נווה ברושים – אגף החניה"),
        ("h2", "טופס בקשה לתו חניה לתושב"),
        ("h2", "חלק א' – פרטי המבקש"),
        ("kv", [("שם פרטי", "אביטל"), ("שם משפחה", "רוזנברג"), ("מספר זהות", "058471236"),
                ("תאריך לידה", "07/11/1988"), ("כתובת", "רחוב השקד 23, דירה 5"),
                ("טלפון נייד", "052-7419630"), ("דואר אלקטרוני", "avital.r@example.co.il")]),
        ("h2", "חלק ב' – פרטי הרכב"),
        ("kv", [("מספר רישוי", "82-417-63"), ("יצרן ודגם", "טויוטה קורולה"), ("שנת ייצור", "2021"), ("צבע", "כסוף")]),
        ("h2", "חלק ג' – סוג הבקשה"),
        ("check", [(False, "תו חדש"), (True, "חידוש תו קיים"), (False, "החלפת רכב")]),
        ("p", "אני מצהיר/ה כי הפרטים שמסרתי בטופס זה נכונים ומלאים."),
        ("kv", [("תאריך", "02/02/2026"), ("חתימה", "____________")])],
        qa=[("מה מספר הזהות של המבקשת?", "id", "058471236"),
            ("מה מספר הרישוי של הרכב?", "id", "8241763"),
            ("איזה סוג בקשה סומן בטופס?", "text", ["חידוש"]),
            ("מה תאריך הלידה של המבקשת?", "date", (7, 11, 1988)),
            ("מה מספר הטלפון הנייד?", "id", "0527419630")]),

    dict(id="letter", font="Times New Roman", size=23, blocks=[
        ("h1", "אופק ירוק – חברה לביטוח בע\"מ"),
        ("right", "12 במרץ 2026"),
        ("p", "לכבוד מר יואב פרידמן, רחוב הרימון 14, מודיעין"),
        ("h2", "הנדון: דרישה להשלמת מסמכים – תביעה מס' 7729-26"),
        ("p", "שלום רב, בהמשך לתביעה שהגשת בגין נזקי מים בדירתך, ולאחר בדיקה ראשונית של שמאי החברה, "
              "הוערך הנזק בסך של 12,400 ש\"ח. על מנת שנוכל להמשיך בטיפול בתביעה ולהעביר את התשלום, "
              "עליך להשלים את המסמכים הבאים:"),
        ("ol", ["צילום פוליסת הביטוח בתוקף ליום האירוע.",
                "הצעת מחיר או חשבונית מאת בעל מקצוע מורשה לתיקון הנזק.",
                "אישור ניהול חשבון בנק על שמך, לצורך העברת התשלום."]),
        ("p", "את המסמכים יש להעביר עד ליום 15 באפריל 2026. אם המסמכים לא יתקבלו עד מועד זה, "
              "התביעה תיסגר, וניתן יהיה לפתוח אותה מחדש בפנייה בכתב."),
        ("p", "לשאלות ניתן לפנות למוקד התביעות בטלפון 03-7654321, בימים א'–ה' בין השעות 08:00 ל-17:00."),
        ("p", "בכבוד רב,"),
        ("p", "מיכל ששון, מחלקת תביעות רכוש")],
        qa=[("מה מספר התביעה?", "id", "772926"),
            ("עד איזה תאריך יש להעביר את המסמכים?", "date", (15, 4, 2026)),
            ("באיזה סכום הוערך הנזק?", "num", 12400),
            ("מי חתומה על המכתב?", "text", ["מיכל ששון"])]),

    dict(id="statement", font="Arial", size=19, blocks=[
        ("h1", "בנק הדוגמה בע\"מ – סניף 512"),
        ("h2", "תדפיס חשבון עובר ושב"),
        ("kv", [("שם בעל החשבון", "נועם ושירה אלמוג"), ("מספר חשבון", "512-384920/61"),
                ("תקופה", "01/02/2026 – 28/02/2026")]),
        ("table", ["תאריך", "תיאור", "חובה", "זכות", "יתרה"], [
            ["01/02/2026", "יתרת פתיחה", "", "", "8,412.35"],
            ["02/02/2026", "הוראת קבע – ועד בית", "250.00", "", "8,162.35"],
            ["05/02/2026", "משכורת – חברת אורביט מערכות", "", "14,860.00", "23,022.35"],
            ["09/02/2026", "חברת החשמל – תשלום חשבון", "612.40", "", "22,409.95"],
            ["11/02/2026", "משיכת מזומן – כספומט", "1,000.00", "", "21,409.95"],
            ["15/02/2026", "העברה לפיקדון לזמן קצוב", "5,000.00", "", "16,409.95"],
            ["20/02/2026", "החזר מס הכנסה", "", "1,284.00", "17,693.95"],
            ["27/02/2026", "כרטיס אשראי – חיוב חודשי", "7,915.62", "", "9,778.33"]]),
        ("kv", [("יתרת סגירה", "9,778.33")]),
        ("small", "המידע בתדפיס זה נכון למועד הפקתו ואינו מהווה אישור יתרה.")],
        qa=[("מהי יתרת הסגירה בחשבון?", "num", 9778.33),
            ("כמה שולם לחברת החשמל?", "num", 612.40),
            ("באיזה תאריך נכנסה המשכורת?", "date", (5, 2, 2026)),
            ("מה סכום החיוב החודשי של כרטיס האשראי?", "num", 7915.62)]),

    dict(id="procedure", font="Arial Hebrew", size=20, blocks=[
        ("h1", "נוהל מס' 4.12 – טיפול בפניות ותלונות לקוחות"),
        ("kv", [("גרסה", "3"), ("בתוקף מיום", "01/01/2026"), ("גורם אחראי", "אגף שירות הלקוחות")]),
        ("h2", "1. מטרה"),
        ("p", "נוהל זה קובע את אופן קבלת הפניות והתלונות של לקוחות החברה, תיעודן והטיפול בהן, "
              "כדי להבטיח מענה מהיר, הוגן ואחיד."),
        ("h2", "2. הגדרות"),
        ("p", "2.1 \"פנייה\" – כל בקשה, שאלה או הערה של לקוח, בכתב או בעל פה."),
        ("p", "2.2 \"תלונה\" – פנייה שבה הלקוח טוען כי נפגע מפעולה או ממחדל של החברה."),
        ("h2", "3. תהליך הטיפול"),
        ("p", "3.1 כל פנייה תתועד במערכת ניהול הפניות תוך יום עסקים אחד ממועד קבלתה."),
        ("p", "3.2 הלקוח יקבל מענה ראשוני תוך 3 ימי עסקים, הכולל את מספר הפנייה ואת שם הנציג המטפל."),
        ("p", "3.3 תלונה מורכבת תועבר לממונה על פניות הציבור, והטיפול בה יסתיים תוך 14 ימי עסקים לכל היותר."),
        ("p", "3.4 תלונה שעניינה חיוב כספי שגוי תטופל בעדיפות עליונה, וההחזר יבוצע תוך 5 ימי עסקים מיום ההחלטה."),
        ("h2", "4. אישור"),
        ("p", "הנוהל אושר על ידי מנהל אגף שירות הלקוחות ונכנס לתוקף במועד הנקוב לעיל.")],
        qa=[("תוך כמה ימי עסקים הלקוח יקבל מענה ראשוני?", "num", 3),
            ("תוך כמה ימי עסקים לכל היותר יסתיים הטיפול בתלונה מורכבת?", "num", 14),
            ("מה מספר הגרסה של הנוהל?", "num", 3),
            ("מי אישר את הנוהל?", "text", ["שירות הלקוחות", "שירות לקוחות"])]),

    dict(id="pricelist", font="Arial", size=21, blocks=[
        ("h1", "מרפאת השיניים \"חיוך רחב\" – מחירון טיפולים 2026"),
        ("p", "המחירים בש\"ח וכוללים מע\"מ. מחיר למנויים בתוקף למנויי התוכנית המשפחתית בלבד."),
        ("table", ["טיפול", "מחיר רגיל", "מחיר למנויים", "משך משוער (דקות)"], [
            ["בדיקה תקופתית וצילום", "180", "120", "20"],
            ["ניקוי אבנית", "320", "240", "40"],
            ["סתימה לבנה – משטח אחד", "450", "360", "45"],
            ["טיפול שורש – שן קדמית", "1,650", "1,390", "60"],
            ["עקירה פשוטה", "390", "310", "30"],
            ["כתר חרסינה", "3,200", "2,750", "90"],
            ["הלבנת שיניים במרפאה", "1,400", "1,150", "75"],
            ["שתל כולל מבנה", "5,900", "5,100", "120"]]),
        ("small", "המחירון אינו כולל טיפולים בהרדמה כללית. ייתכנו שינויים לאחר בדיקה.")],
        qa=[("מה המחיר הרגיל של כתר חרסינה?", "num", 3200),
            ("מה המחיר למנויים של ניקוי אבנית?", "num", 240),
            ("כמה דקות נמשך בערך טיפול שורש בשן קדמית?", "num", 60)]),

    dict(id="mixed", font="Arial", size=21, blocks=[
        ("h1", "הוראות התחברות לרשת ה-VPN של המשרד"),
        ("p", "ההוראות מתאימות ל-Windows 11 ול-macOS 15 ומעלה. יש להשתמש בתוכנת SecureLink בגרסה 5.2.1 ומעלה."),
        ("ol", ["פתחו את התוכנה ובחרו Settings > Network > VPN.",
                "בשדה Server Address הקלידו: vpn2.example-office.co.il",
                "בשדה Port הקלידו 4433, ובשדה Protocol בחרו IKEv2.",
                "הזינו את שם המשתמש הארגוני שלכם (למשל d.levi) ואת הסיסמה.",
                "אשרו את הבקשה באפליקציית האימות בטלפון תוך 60 שניות."]),
        ("p", "אם מופיעה השגיאה Error 809, ודאו שאינכם מחוברים לרשת Wi-Fi ציבורית שחוסמת את הפורט."),
        ("p", "לתמיכה: helpdesk@example-office.co.il או בטלפון 4721*, בימים א'–ה' 08:30–18:00.")],
        qa=[("איזה מספר פורט יש להקליד?", "num", 4433),
            ("מה כתובת השרת?", "text", ["vpn2.example-office.co.il"]),
            ("מהי הגרסה המינימלית של התוכנה?", "text", ["5.2.1"]),
            ("איזו שגיאה מופיעה ברשת Wi-Fi ציבורית?", "num", 809)]),

    dict(id="niqqud", font="Arial Hebrew Scholar", size=30, blocks=[
        ("h1", "הַפַּרְפַּר הַקָּטָן"),
        ("niqqud", ["הַיֶּלֶד הָלַךְ לַגַּן עִם אִמָּא שֶׁלּוֹ.",
                    "בַּגַּן הָיוּ פְּרָחִים אֲדֻמִּים וּצְהֻבִּים.",
                    "הוּא רָאָה פַּרְפַּר קָטָן עַל עָלֶה יָרֹק.",
                    "הַפַּרְפַּר עָף גָּבוֹהַּ אֶל הַשָּׁמַיִם הַכְּחֻלִּים.",
                    "הַיֶּלֶד צָחַק וְאָמַר: \"לְהִתְרָאוֹת, פַּרְפַּר!\""])],
        qa=[("מה צבע העלה שעליו עמד הפרפר?", "text", ["ירוק", "ירק"], "יָרֹק"),
            ("עם מי הלך הילד לגן?", "text", ["אמא", "אימא", "אמו", "אימו"])]),

    dict(id="article", font="Times New Roman", size=21, blocks=[
        ("h1", "מתקן ההתפלה החדש בדרום יספק מים לחצי מיליון תושבים"),
        ("p", "מאת: עידו ברק | 18 בפברואר 2026"),
        ("cols", [
            ("p", "מתקן ההתפלה החדש, שהוקם סמוך לחוף הדרומי, החל השבוע לפעול באופן מלא. לפי נתוני החברה המפעילה, "
                  "המתקן יספק כ-90 מיליון מטרים מעוקבים של מים בשנה, כמות המספיקה לכחצי מיליון תושבים."),
            ("p", "הקמת המתקן נמשכה ארבע שנים ועלתה כ-1.8 מיליארד ש\"ח. לדברי מנהלת הפרויקט, ד\"ר רותם גל, "
                  "המתקן צורך כ-20% פחות אנרגיה ממתקנים קודמים, בזכות משאבות חדשות ומערכת להשבת אנרגיה."),
            ("p", "ארגוני סביבה בירכו על החיסכון באנרגיה, אך הביעו דאגה מהשפעת התמלחת המוחזרת לים על בעלי החיים "
                  "באזור. החברה הודיעה כי תפרסם דוח ניטור ימי פעמיים בשנה."),
            ("p", "בחודשים הקרובים צפוי להתחיל גם חיבור המתקן למוביל הארצי, כך שבשנים שחונות ניתן יהיה "
                  "להעביר מים מותפלים גם לאזורים בצפון.")])],
        qa=[("כמה מים בשנה יספק המתקן?", "num", 90),
            ("כמה עלתה הקמת המתקן?", "num", 1.8),
            ("מי מנהלת הפרויקט?", "text", ["רותם גל"])]),

    dict(id="smallprint", font="Arial", size=14, blocks=[
        ("h2", "תנאי שימוש ומדיניות ביטולים – אתר \"שוק הבית\""),
        ("p", "1. השימוש באתר מותר למי שמלאו לו 18 שנים ובידו כרטיס אשראי בתוקף שהונפק בישראל."),
        ("p", "2. הזמנה תיחשב כמאושרת רק לאחר קבלת הודעת אישור בדואר האלקטרוני. החברה רשאית לסרב להזמנה, "
              "בין היתר אם המוצר אזל מהמלאי או אם נפלה טעות קולמוס במחיר."),
        ("p", "3. ניתן לבטל עסקה תוך 14 ימים מיום קבלת המוצר, בתנאי שהמוצר לא נפתח ולא נעשה בו שימוש. "
              "בביטול עסקה ייגבו דמי ביטול בשיעור של 5% ממחיר המוצר או 100 ש\"ח, לפי הנמוך מביניהם."),
        ("p", "4. מוצרי מזון טריים, מוצרים שיוצרו במיוחד עבור הלקוח ומוצרי היגיינה אישית אינם ניתנים להחזרה."),
        ("p", "5. משלוח חינם בהזמנה מעל 350 ש\"ח. בהזמנה בסכום נמוך יותר ייגבו דמי משלוח של 29.90 ש\"ח."),
        ("p", "6. זמן האספקה הוא עד 3 ימי עסקים באזור המרכז ועד 6 ימי עסקים בשאר הארץ, למעט ערבי חג ומועד."),
        ("p", "7. החברה אינה אחראית לעיכוב באספקה שנגרם בשל כוח עליון, לרבות שביתות, מלחמה או תקלות "
              "במערכות התקשורת."),
        ("p", "8. על תנאי שימוש אלה יחולו דיני מדינת ישראל, ומקום השיפוט הבלעדי הוא בבתי המשפט במחוז תל אביב.")],
        qa=[("תוך כמה ימים ניתן לבטל עסקה?", "num", 14),
            ("מעל איזה סכום המשלוח חינם?", "num", 350),
            ("כמה ימי עסקים נמשכת האספקה באזור המרכז?", "num", 3)]),

    dict(id="receipt", font="Courier New", size=20, width=560, blocks=[
        ("h2", "סופר השכונה"),
        ("p", "רחוב הגפן 3, כפר הדרים"),
        ("p", "קופה 4 | 23/01/2026 | 18:42"),
        ("table", ["פריט", "כמות", "סכום"], [
            ["חלב 3% קרטון", "2", "12.80"],
            ["לחם אחיד פרוס", "1", "8.30"],
            ["עגבניות (ק\"ג)", "1.250", "11.25"],
            ["גבינה לבנה 5%", "3", "17.70"],
            ["ביצים L תבנית 12", "1", "13.90"],
            ["שמן זית כתית 750 מ\"ל", "1", "39.90"],
            ["שקית", "2", "0.20"]]),
        ("kv", [("סה\"כ לתשלום", "104.05"), ("אשראי", "כרטיס המסתיים ב-4821")]),
        ("p", "תודה ולהתראות!")],
        qa=[("מה הסכום הכולל לתשלום בקבלה?", "num", 104.05),
            ("כמה עלה שמן הזית?", "num", 39.90),
            ("מהן ארבע הספרות האחרונות של כרטיס האשראי?", "id", "4821")]),

    dict(id="note", font="Corsiva Hebrew", size=34, width=900, blocks=[
        ("p", "שירה, הטכנאי יגיע מחר (יום שלישי) בין 10:00 ל-12:00."),
        ("p", "תשאירי לו את המפתח אצל השכנה מדירה 6."),
        ("p", "אם יש בעיה תתקשרי אליו: 054-3318207"),
        ("p", "וגם – לא לשכוח לקנות חלב ונרות לשבת!"),
        ("p", "אוהבת, אמא")],
        qa=[("מה מספר הטלפון של הטכנאי?", "id", "0543318207"),
            ("אצל מי יש להשאיר את המפתח?", "text", ["שכנה", "דירה 6"])]),
]

CSS = """
body {{ margin:0; background:#fff; }}
.page {{ width:{w}px; box-sizing:border-box; padding:60px 70px; direction:rtl; font-family:'{font}'; font-size:{size}px;
        line-height:1.5; color:#111; }}
h1 {{ font-size:1.55em; margin:0 0 .5em; }} h2 {{ font-size:1.2em; margin:.9em 0 .4em; }}
p {{ margin:.35em 0; }} .right {{ text-align:left; }} .small {{ font-size:.8em; color:#333; }}
table {{ border-collapse:collapse; width:100%; margin:.6em 0; }}
td, th {{ border:1px solid #555; padding:.25em .5em; text-align:right; }} th {{ background:#e8e8e8; }}
.kv {{ display:grid; grid-template-columns:1fr 1fr; gap:.2em 2em; margin:.4em 0; }}
.cols {{ column-count:2; column-gap:40px; text-align:justify; }}
.check span {{ margin-left:2em; }}
.niq {{ font-size:1.1em; line-height:2.1; }}
"""


def render_block(b):
    """-> (html, ground-truth lines)"""
    t, *rest = b
    e = html.escape
    if t in ("h1", "h2"):
        return f"<{t}>{e(rest[0])}</{t}>", [rest[0]]
    if t in ("p", "right", "small"):
        cls = f' class="{t}"' if t != "p" else ""
        return f"<p{cls}>{e(rest[0])}</p>", [rest[0]]
    if t == "kv":
        items = rest[0]
        return ('<div class="kv">' + "".join(f"<div><b>{e(k)}:</b> {e(v)}</div>" for k, v in items) + "</div>",
                [f"{k}: {v}" for k, v in items])
    if t == "table":
        head, rows = rest
        h = "<tr>" + "".join(f"<th>{e(c)}</th>" for c in head) + "</tr>"
        r = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in row) + "</tr>" for row in rows)
        return f"<table>{h}{r}</table>", [" | ".join(head)] + [" | ".join(c for c in row if c) for row in rows]
    if t == "ol":
        return ("<ol>" + "".join(f"<li>{e(x)}</li>" for x in rest[0]) + "</ol>",
                [f"{i}. {x}" for i, x in enumerate(rest[0], 1)])
    if t == "check":
        return ('<p class="check">' + "".join(f"<span>{'☒' if c else '☐'} {e(x)}</span>" for c, x in rest[0]) + "</p>",
                [" ".join(f"{'☒' if c else '☐'} {x}" for c, x in rest[0])])
    if t == "cols":
        parts = [render_block(x) for x in rest[0]]
        return '<div class="cols">' + "".join(p[0] for p in parts) + "</div>", [l for p in parts for l in p[1]]
    if t == "niqqud":
        return '<div class="niq">' + "".join(f"<p>{e(x)}</p>" for x in rest[0]) + "</div>", list(rest[0])
    raise ValueError(t)


def shoot(page_html, out, width, tmp):
    src = Path(tmp) / "doc.html"
    src.write_text(page_html, encoding="utf-8")
    raw = Path(tmp) / "shot.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--user-data-dir={tmp}/profile", f"--window-size={width},2600", f"--screenshot={raw}",
                    src.as_uri()], check=True, capture_output=True)
    im = Image.open(raw).convert("RGB")
    a = np.asarray(im.convert("L"))
    rows = np.where((a < 245).any(axis=1))[0]
    im = im.crop((0, 0, width, min(a.shape[0], rows.max() + 60)))
    im.save(out)
    return im


def scan(im, seed):
    rng = random.Random(seed)
    g = im.convert("L")
    w, h = g.size
    g = g.resize((int(w * 0.8), int(h * 0.8)), Image.BILINEAR)  # lower resolution, about 120 dpi
    g = g.rotate(rng.choice([-1, 1]) * rng.uniform(0.6, 1.4), resample=Image.BICUBIC, expand=True, fillcolor=255)
    g = g.filter(ImageFilter.GaussianBlur(0.7))
    a = np.asarray(g).astype(np.float32)
    a = a * 0.86 + 22  # grey paper, weaker ink
    a += np.random.default_rng(seed).normal(0, 9, a.shape)
    g = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    g.save(buf, "JPEG", quality=55)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def main():
    img_dir = HERE / "images"
    img_dir.mkdir(exist_ok=True)
    items = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, d in enumerate(DOCS):
            parts = [render_block(b) for b in d["blocks"]]
            width = d.get("width", W)
            page = (f"<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'><style>"
                    f"{CSS.format(w=width, font=d['font'], size=d['size'])}</style></head><body><div class='page'>"
                    + "".join(p[0] for p in parts) + "</div></body></html>")
            gt = "\n".join(l for p in parts for l in p[1])
            clean = shoot(page, img_dir / f"{d['id']}_clean.png", width, tmp)
            scan(clean, k).save(img_dir / f"{d['id']}_scan.jpg", quality=95)
            for ver, ext in [("clean", "png"), ("scan", "jpg")]:
                items.append({"id": f"ocr-{d['id']}-{ver}", "doc": d["id"], "version": ver, "kind": "ocr",
                              "image": f"images/{d['id']}_{ver}.{ext}", "font": d["font"], "gold": gt})
            for j, (q, match, gold, *niq) in enumerate(d["qa"]):
                items.append({"id": f"qa-{d['id']}-{j}", "doc": d["id"], "version": "scan", "kind": "qa",
                              "image": f"images/{d['id']}_scan.jpg", "question": q, "match": match, "gold": gold,
                              **({"gold_niqqud": niq[0]} if niq else {})})
            print(d["id"], clean.size, len(gt), "chars")
    with open(HERE / "items.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(len(items), "items:", sum(i["kind"] == "ocr" for i in items), "ocr,", sum(i["kind"] == "qa" for i in items), "qa")


if __name__ == "__main__":
    main()

# How good are open models at Hebrew? Qwen3.8 (dense and MoE) vs Gemma 4

A hands-on test of Hebrew in three open models, run locally on one Mac:

| Model | Type | Parameters |
|---|---|---|
| **Qwen3.8-27B** | dense | 27B, all active |
| **Qwen3.8-Flash-Next** | MoE preview | 125B, 6B active per token, plus a 51B n-gram embedding table |
| **Gemma-4-26B-A4B** | MoE | 26B, about 4B active per token |

The test covers six things:

- writing quality, judged blind;
- Hebrew grammar and vocabulary;
- reasoning in Hebrew with thinking on;
- how each model *thinks*: in which language, and for how long;
- reading Hebrew documents from images: invoices, forms, letters, tables, scans;
- how much a Hebrew system prompt and a lower temperature help.

## TL;DR

- **Writing, out of the box: the two MoE models are far better than the dense 27B.**
  - Errors per 100 words: Gemma 0.93, Flash-Next 1.22, Qwen3.8-27B 3.22.
  - Both MoE models beat the 27B on 14–15 of 16 tasks (sign test p = 0.001). Gemma vs Flash-Next is 9–4 for Gemma,
    which is not significant.
- **Tuned settings help a lot, and help Qwen most.** The settings are a short Hebrew system prompt, temperature 0.3
  and min_p 0.05, with thinking off.
  - Qwen3.8-27B: errors drop by half (3.22 → 1.65 per 100 words), and the Arabic and Chinese letters disappear.
  - Qwen3.8-Flash-Next: errors drop to 0.56 per 100 words. It becomes the best writer: preferred over Gemma on 14
    of 16 tasks (p = 0.001).
  - Gemma barely changes: 0.93 → 0.85.
  - Grammar questions with tuned settings: Flash-Next 28/28, Gemma 27/28, 27B 26/28.
- **Foreign letters inside Hebrew words.**
  - The 27B mixes Arabic and Chinese letters into Hebrew: "ריבית שנائية", "זהו פازل קלאסי", "לאדם另".
  - Gemma sometimes mixes in English fragments: "עכשYLE השמש", "עובדים rested (נחים)".
  - Flash-Next never did either.
- **Reasoning: a tie.** All three solved every math word problem and every translated STEM question. All three get
  only about half of the native Israeli logic and verbal-reasoning exam questions right. Overall: 29, 28 and 29 of 36.
- **All three think in English**, even when everything they are given is in Hebrew. Gemma thinks about twice as long
  as the Qwen models.
- **Reading Hebrew documents from images: Gemma is far ahead.**
  - On 12 Hebrew documents (invoice, form, letter, bank statement, procedure, small print, receipt and more), clean and
    scanned, Gemma transcribed 95–98% of the words correctly and answered 40–41 of 42 questions.
  - Qwen3.8-27B read 82% of the words on clean pages and 64% on scans, and answered 33 of 42 questions. Flash-Next
    did worse: 59% and 46%, and 32 of 42.
  - **Both Qwen models sometimes write Hebrew backwards** ("םיכמסמ" for "מסמכים") and reverse numbers ("71402" for
    20417, "26/30/1411" for 14/03/2026). Gemma never did. The 27B's original BF16 weights gave the same result, so
    this is not caused by quantization.
- **Niqqud fails out of the box.** No model vocalized the test sentence correctly with default settings. With tuned
  settings, Flash-Next got it right apart from one dagesh that many texts accept.
- **None of them knows the idiom "לא דובים ולא יער".** In a multiple-choice question they all pick the right meaning.
  In free writing they all explain it wrongly and invent a source for it: a Hasidic tale, a Spanish saying, a
  Russian proverb, a Mishnah quote.

## What was tested

| Part | Items | Mode | Graded by |
|---|---|---|---|
| **Writing** | 16 open tasks: explanation for a child, formal letter, persuasive text, rhyming lines, advice, finance explanation, idiom, EN→HE and HE→EN translation, legal-to-plain rewrite, verb conjugation, grammar correction, logic puzzle, summary, casual WhatsApp register, full niqqud | thinking off, default and tuned settings | 2 blind LLM judges |
| **Language** | 28 multiple-choice questions written for this test: numerals and gender, agreement, construct state (סמיכות), prepositions, verb forms and binyanim, roots, unvocalized homographs, idioms, spelling | thinking off, thinking on, tuned | exact answer |
| **Reasoning** | 36: 12 multi-step math word problems, 12 native Israeli logic / verbal-reasoning exam questions, 6 STEM questions (human-translated), 6 Israeli driving-theory questions | thinking on | exact answer |
| **Documents** | 12 synthetic Hebrew document images, each clean and "scanned": transcribe the page (24), and 42 short questions about the scans | thinking off | text comparison, exact answer |

An independent reviewer checked the language questions before the runs, and two items were fixed.

## Setup

| | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| Weights | `Qwen/Qwen3.8-27B`, MLX 8-bit | `unsloth/Qwen3.8-Flash-Next-GGUF` UD-Q4_K_XL (~4.5 bits per weight, 104 GiB) | `mlx-community/gemma-4-26b-a4b-it-8bit` |
| Runtime, text | mlx-lm 0.32.2 | llama.cpp 1.0.0 (`llama-server`) | mlx-lm 0.32.2 |
| Runtime, images | mlx-vlm 0.8.1 (8-bit conversion with the vision tower) | llama.cpp with `mmproj-F16.gguf` | mlx-vlm 0.8.1 |
| Decode speed per stream | ~6 tokens/s (8 at once) | ~11 tokens/s (8 at once) | ~42 tokens/s (1 at a time) |
| Hardware | Apple M5 Max, 128 GB | same | same |

All models got exactly the same prompts. Sampling:

- **Default settings** use each maker's own recommended sampling, with no system prompt:
  - Qwen, thinking: temperature 1.0, top_p 0.95, top_k 20, `reasoning_effort=medium`, at most 16k tokens.
  - Qwen, no thinking: temperature 0.7, top_p 0.8, top_k 20, presence penalty 1.5.
  - Gemma, both modes: temperature 1.0, top_p 0.95, top_k 64.
- **Tuned settings** are the same for every model: thinking off, temperature 0.3, top_p 0.95, top_k 20, min_p 0.05,
  and the short Hebrew system prompt in [`system_he.txt`](system_he.txt). The prompt asks for correct, natural
  Hebrew: Academy full spelling, gender and number agreement, native prepositions, no foreign or invented words.
  It came from earlier tests on another project, where these settings cut Hebrew errors a lot.
- **Document reading:** greedy decoding (temperature 0), thinking off, no system prompt.

Each item was run once. The models are quantized differently: the Flash-Next does not fit in 128 GB at 8-bit. The
speeds come from different runtimes and batch sizes, so they are only a rough guide.

## Results

### Writing quality, default settings (16 tasks, blind, 2 judges)

Each task's three answers were shown side by side as "A", "B" and "C", in a shuffled order. Each model got each label
about equally often, and the judges did not know which model was which.

For every answer, the judges listed each Hebrew error (with the exact text and a fix) and rated fluency and task
success from 1 to 5. Then they ranked the three answers. One judge read the tasks first to last, the other last to
first.

| Metric | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| Hebrew errors per 100 words (lower is better) | 3.22 | 1.22 | **0.93** |
| Errors found / words judged (both judges together) | 212 / 6590 | 74 / 6044 | 51 / 5478 |
| Fluency 1–5 | 2.72 | 3.97 | **4.25** |
| Task success 1–5 | 3.16 | 3.88 | **4.12** |
| Best answer (16 tasks × 2 judges, 2 ties) | 1 | 9 | **20** |
| Mean rank (1 = best of 3) | 2.84 | 1.75 | **1.41** |

| Error type | Qwen3.8-27B | Qwen3.8-Flash-Next | Gemma-4-26B-A4B |
|---|---|---|---|
| wrong word in context | 59 | 10 | 5 |
| spelling | 32 | 15 | 7 |
| unnatural / literal | 31 | 11 | 10 |
| other grammar (binyan, tense, syntax) | 25 | 10 | 13 |
| invented word | 22 | 10 | 2 |
| agreement (gender / number) | 17 | 12 | 5 |
| preposition or collocation | 10 | 2 | 1 |
| foreign word or script | 10 | **0** | 6 |
| niqqud | 6 | 4 | 2 |

Task by task, using the average of the two judges' ranks:

| | tasks won | sign test p |
|---|---|---|
| Flash-Next vs 27B | 14 vs 1 (1 level) | **0.001** |
| Gemma vs 27B | 15 vs 1 | **0.001** |
| Gemma vs Flash-Next | 9 vs 4 (3 level) | 0.27 |

A first pass of this test judged only the two Qwen models against each other (blind, two judges). It gave the same
picture: 3.66 vs 1.47 errors per 100 words, and the MoE preferred on 14 of 16 tasks. That pass is kept in
[`judge/qwen_pairwise/`](judge/qwen_pairwise).

### Default vs tuned settings (thinking off)

| | Qwen3.8-27B default | Qwen3.8-27B tuned | Flash-Next default | Flash-Next tuned | Gemma default | Gemma tuned |
|---|---|---|---|---|---|---|
| Grammar questions (28) | 25 | 26 | 27 | **28** | 24 | 27 |
| Answers with Arabic / Chinese letters (43 answers) | 4 | **0** | 0 | 0 | 0 | 0 |
| Writing: Hebrew errors per 100 words | 3.22 | 1.65 | 1.22 | **0.56** | 0.93 | 0.85 |
| Writing: fluency 1–5 | 2.72 | 3.53 | 3.97 | **4.47** | 4.25 | 4.25 |
| Writing: task success 1–5 | 3.16 | 3.53 | 3.88 | **4.25** | 4.12 | 3.72 |
| Median writing answer (words) | 168 | 55 | 140 | 64 | 158 | 162 |

With tuned settings, the three answers per task were again judged blind side by side, in a separate pass:

| Tuned settings | Qwen3.8-27B | Qwen3.8-Flash-Next | Gemma-4-26B-A4B |
|---|---|---|---|
| Best answer (16 tasks × 2 judges, 1 tie) | 3 | **25** | 3 |
| Mean rank (1 = best of 3) | 2.56 | **1.31** | 2.12 |

| Task by task, tuned | tasks won | sign test p |
|---|---|---|
| Flash-Next vs 27B | 12 vs 3 (1 level) | **0.035** |
| Flash-Next vs Gemma | 14 vs 1 (1 level) | **0.001** |
| Gemma vs 27B | 12 vs 4 | 0.08 |

What changes with tuned settings:

- **The Qwen models write much shorter answers** (median 55–64 words instead of 140–168), with far fewer errors. Task
  success still went up, so the shorter answers did not cost completeness on these tasks.
- **The 27B's foreign-script leaks stop**, and it makes half as many errors. It is still the weakest writer of the three.
- **Gemma's writing hardly changes.** Its task success drops a little: with tuned settings it often offered several
  versions where one was asked for (three translations, two WhatsApp messages), and the judges marked that down.
- One Gemma answer under tuned settings contains Cyrillic. It is not a leak: Gemma invented a "Russian proverb" as
  the source of "לא דובים ולא יער" and quoted it in Russian.

The default and tuned numbers come from separate judging passes (same rubric, different judge runs), so compare
them with some care. The rankings inside each pass are the more reliable comparison.

### Hebrew language knowledge (28 multiple-choice questions)

| Category | 27B off | Flash-Next off | Gemma off | 27B think | Flash-Next think | Gemma think |
|---|---|---|---|---|---|---|
| numerals | 3/4 | 4/4 | 3/4 | 4/4 | 3/4 | 4/4 |
| agreement | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| construct state | 1/2 | 2/2 | 2/2 | 1/2 | 2/2 | 2/2 |
| prepositions | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| verb forms / binyanim | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| roots | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| homographs | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| idioms | 3/4 | 4/4 | 3/4 | 4/4 | 4/4 | 3/4 |
| spelling | 2/2 | 1/2 | 0/2 | 2/2 | 2/2 | 1/2 |
| **All** | **25/28** | **27/28** | **24/28** | **27/28** | **27/28** | **26/28** |

What each model got wrong:

- **27B:** an ungrammatical construct form in every mode ("בית ספר החדש", "הבית הספר החדש"); "עשרים ושתיים שקלים"
  with thinking off; it read "שבר את הכלים" literally, as "destroyed property".
- **Flash-Next:** "לחילופין" instead of the Academy's "לחלופין" with thinking off; "שתי שבועות" with thinking on
  (see below). With tuned settings it got all 28 right.
- **Gemma:** "חמש ספרים" instead of "חמישה ספרים" with thinking off; the Academy spellings "תכנית" and "לחילופין";
  and in every mode it read "עבר לסדר היום" as "changed its priorities" (it means "ignored the matter and carried on").

None of the differences is significant on 28 items: the paired sign tests give p ≥ 0.25. See
[`results/tables.md`](results/tables.md).

### Reasoning in Hebrew (thinking on)

| Part | Qwen3.8-27B | Qwen3.8-Flash-Next | Gemma-4-26B-A4B |
|---|---|---|---|
| Math word problems | 12/12 | 12/12 | 12/12 |
| Native Hebrew logic / verbal reasoning (INCLUDE) | 6/12 | 5/12 | 7/12 |
| STEM, human-translated (Global-MMLU) | 6/6 | 6/6 | 6/6 |
| Israeli driving theory (INCLUDE) | 5/6 | 5/6 | 4/6 |
| **All reasoning** | **29/36** | **28/36** | **29/36** |

The models fail on mostly the same items. 6 items were missed by all three: 5 native Israeli logic and
verbal-reasoning questions and 1 driving-theory question.
Math and translated STEM are easy for all three. Reasoning that depends on Hebrew itself is where they struggle.

### How they think

| Model | Set | median thinking+answer tokens | p90 tokens | hit 16k cap | letters in thinking: Hebrew / Latin | traces mostly Hebrew |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | language | 404 | 943 | 0 | 16% / 84% | 0/28 |
| Qwen3.8-Flash-Next | language | 434 | 871 | 0 | 15% / 85% | 0/28 |
| Gemma-4-26B-A4B | language | 766 | 2056 | 0 | 24% / 76% | 0/28 |
| Qwen3.8-27B | reasoning | 711 | 2109 | 0 | 5% / 95% | 0/36 |
| Qwen3.8-Flash-Next | reasoning | 729 | 1712 | 0 | 4% / 96% | 0/36 |
| Gemma-4-26B-A4B | reasoning | 1718 | 4806 | 0 | 18% / 82% | 0/36 |

- All three models reason in English, even though the prompt is entirely Hebrew. The Hebrew in their thinking is
  mostly words quoted from the question.
- Gemma thinks about twice as long, and has the longest tail (up to ~9k tokens on logic questions). Gemma has no
  effort setting; the Qwen models ran at medium effort.
- Chinese almost never shows up in the thinking: 2 characters in all of the 27B's traces, none in the others'.

### Foreign script inside Hebrew answers

Counted automatically over all answers with default settings (HE→EN translation excluded):

| Model | Answers checked | With Chinese/Japanese/Korean | With Arabic | With Cyrillic |
|---|---|---|---|---|
| Qwen3.8-27B | 107 | 2 | 6 | 0 |
| Qwen3.8-Flash-Next | 107 | **0** | **0** | **0** |
| Gemma-4-26B-A4B | 107 | **0** | **0** | **0** |

Gemma's failure is different: English fragments inside Hebrew sentences, in 2 of its 16 writing answers. The
automatic check cannot tell these from normal English terms, so they are counted by the judges instead (the
"foreign word" row of the writing table).

## Reading Hebrew documents from images

12 Hebrew documents were written for this test: an invoice, a government-style form with check boxes, a formal
letter, a bank statement, an internal procedure with numbered clauses, a price list, IT instructions mixing Hebrew,
English and numbers, a vocalized children's text, a two-column news article, small-print terms of use, a narrow
supermarket receipt, and a note in a handwriting-style font. All names, companies and numbers are made up.

Each document was rendered by Chrome at A4 width (about 150 dpi) and saved twice:

- **clean**, as from a digital PDF;
- **scanned**: grey paper, a 0.6–1.4° tilt, blur, noise, lower resolution and JPEG compression.

Each model transcribed all 24 pages and answered 42 short questions about the scanned pages: amounts, ID numbers,
dates, names. The prompts were in Hebrew, with thinking off and greedy decoding. The Qwen models read the images at
native resolution (an A4 page is about 900 image tokens). Gemma 4 ran twice: at its default image budget of 280
tokens per image, and at its maximum, 1120.

[See the pages](vision/images): for example, [a scanned invoice](vision/images/invoice_scan.jpg) and
[the small print](vision/images/smallprint_clean.png).

| | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B, 280 image tokens | Gemma-4-26B-A4B, 1120 image tokens |
|---|---|---|---|---|
| Word F1, clean pages (higher is better) | 0.82 | 0.59 | 0.96 | **0.98** |
| Word F1, scanned pages | 0.64 | 0.46 | 0.95 | **0.98** |
| Questions answered correctly (scans) | 33/42 | 32/42 | 40/42 | **41/42** |
| Pages (of 24) with Hebrew written backwards | 5 | 12 | **0** | **0** |
| Reversed words / reversed numbers | 51 / 3 | 168 / 20 | 0 / 0 | 0 / 0 |
| Seconds per item (Mac) | 11.8 | 5.3 | 2.8 | 5.4 |

Word F1 compares the words of the transcription with the words of the page, in any order. It is the main score
here, because the order in which side-by-side fields are read is often a matter of taste. The character error rate
(which also counts order) and per-document scores are in [`results/tables.md`](results/tables.md).

**Is it the 8-bit conversion? No.** The same test with Qwen3.8-27B's original BF16 weights gave the same result:
word F1 0.80 on clean pages and 0.66 on scans, 33 of 42 questions, and Hebrew written backwards on the same 5 pages
(15 words, 5 numbers). The 8-bit run had 0.82 / 0.64 and 33 of 42.

What the numbers mean:

- **Gemma reads Hebrew documents far better than both Qwen models.** Even at its default 280 image tokens it
  transcribes about 95% of the words correctly on scans, and it answered 40 of 42 questions. It never wrote Hebrew
  backwards.
- **Both Qwen models sometimes write Hebrew backwards**, letter by letter, and reverse the digits of numbers. From
  the scanned letter, Qwen3.8-27B wrote "התודעה: השריה תמלשמה םיכמסמ" (for "הנדון: דרישה להשלמת מסמכים"). From the
  clean invoice, Flash-Next wrote invoice number "71402" for 20417, date "26/30/1411" for 14/03/2026, and phone
  "32109590-04" for 04-9590123. The 27B wrote clause numbers backwards in the procedure: "1.2" for 2.1, "1.3" for
  3.1.
- **The Qwen models also invent text.** The 27B turned the made-up town "עיריית נווה ברושים" into a real city,
  "עיריית נתניה". Given the parking-permit form, Flash-Next transcribed a different document altogether: "הודעת ביטול
  חוזה – חוזה שכירות", with names that are not on the page.
- **Scans hurt Qwen much more.** From clean to scanned, the 27B drops from 0.82 to 0.64 word F1. Gemma drops from
  0.96 to 0.95.
- **Small print is the hardest page.** At 280 tokens Gemma reads 84% of it, at 1120 tokens 98%. For dense pages,
  raise Gemma's image budget (`max_soft_tokens`). The 27B read only 15% of the clean small print.
- **Gemma's weak spot is reading order.** At 1120 tokens it read the scanned two-column article's paragraphs in the
  wrong order. Every word was right, but the text was out of sequence.
- **Flash-Next with more image tokens:** a second run with llama.cpp's `--image-min-tokens 1024` gave the same
  picture (word F1 0.54 / 0.49, 32/42). Flash-Next's vision ran only through llama.cpp, because mlx-vlm does not
  support its architecture yet; part of its weakness may come from llama.cpp's support for this new model.

## What the mistakes look like

**1. Arabic and Chinese letters inside Hebrew words (Qwen3.8-27B).** All from the 27B's final answers:

- language question, thinking off: "כדי להשלים את המשפט **بشكل** תקינתי"
- language question, thinking on: "המילה "שקלים" היא **בذكورية**"
- writing, finance explanation: "**ריבית שנائية:** 4.5%"
- writing, logic puzzle: "זהו **פازل** קלאסי"
- writing, study advice: "...למגע הקרוב ביותר **לאדם另**?"

**2. English fragments inside Hebrew (Gemma).**

- "**עכשYLE** השמש שולחת..." (explanation for a child)
- "עובדים **rested** (נחים)" and "שיעורי שחיקה **מתק advancing**" (persuasive paragraph)

**3. Invented and wrong words.**

- 27B: "הכחול **נפוזר** לכל הכיוונים" (מתפזר); "ממתינים **לישראון** מידיכם... **חג שמח!**" in a WhatsApp invitation to a
  Friday barbecue.
- Flash-Next: "**מדעי המחדרה**" (three times, for מדעי המחשב); "**פסידות** כפולה".
- Qwen3.8-27B with tuned settings, too: "ריבית משתנה (או **מובטלת**)" ("unemployed") and "בעיית **הגלשן**" in
  the wolf, goat and cabbage puzzle.

**4. A grammar rule made up during thinking (Flash-Next, language question).** Asked to fill in "בעוד ___ שבועות",
the MoE reasoned in English:

> "שבוע" (week) is a masculine noun. However, its plural form "שבועות" has a feminine-looking ending (ות). In
> Hebrew, when a noun is in the plural form ending with "ות", it is treated as feminine plural…

It answered "שתי שבועות", which is wrong. With thinking off, and with tuned settings, it got this item right.

**5. Niqqud.** The reference is "הַיְלָדִים שִׂחֲקוּ בֶּחָצֵר עַד שֶׁיָּרַד הַגֶּשֶׁם".

- With default settings every model vocalized "בחצר" wrongly (בַּחֲצֵר or בַּחָצֵר). The 27B also wrote
  "שֶׁחִקּוּ" (shin instead of sin), with an explanation that makes no sense ("יש דגש בצירוי החולם המופחת").
- With tuned settings, Flash-Next wrote "הַיְּלָדִים שִׂחֲקוּ בֶּחָצֵר עַד שֶׁיָּרַד הַגֶּשֶׁם", which differs from the
  reference only by the dagesh in הַיְּלָדִים. The other two were still wrong.

**6. Knowing the answer in a quiz but not in writing.** In the multiple-choice question, all three picked the right
meaning of "לא דובים ולא יער": the story is entirely made up. Asked in free writing to explain the idiom and its
source, all got it wrong, under both settings. They said it means "confusion" or "a double loss", and invented
sources: a Hasidic parable about a poor man hunting bears, a Spanish saying ("Ni perros ni gatos"), a Russian
proverb quoted in Cyrillic, and a quote from Mishnah Avot. The real source is the Talmud (Sotah 47a).

## Why a 125B MoE runs on a 128 GB Mac

Memory depends on the **total** number of parameters, because every expert must be loaded. Speed depends on the
**active** ones, because each token uses only a few experts.

- Qwen3.8-Flash-Next has about 180B parameters in all: 125B in the main model (6B active per token), a 51B n-gram
  embedding table and 4B for multi-token prediction. In BF16 the files are about 330 GiB; in 8-bit about 175 GiB.
- At ~4.5 bits per weight (unsloth's UD-Q4_K_XL) it is 104 GiB. On a Mac the GPU shares the 128 GB of unified
  memory with the CPU, so the whole model fits on one machine. It runs at ~11 tokens/s per stream because only 6B
  parameters are active per token.
- On 80 GB GPUs, BF16 or FP8 weights need several cards. Quantizing to 4 bits, or keeping the n-gram table in CPU
  memory, cuts the number of cards needed.
- Qwen3.8-27B (dense) is 54 GB in BF16 and fits on one 80 GB GPU. Gemma-4-26B-A4B is about 50 GB in BF16, also one
  card, and with ~4B active parameters it is much faster per token than the dense 27B.

## Limitations

- **Small sample.** 16 writing tasks, 28 language questions, 36 reasoning items, 12 documents, one sample each.
  Differences of a few items are noise; the sign tests say which differences hold up.
- **LLM judges.** The writing scores come from independent Claude (Anthropic) instances, not native-speaker raters.
  They were blind, and each pass had two judges reading in opposite orders, but read the raw answers in `results/`
  if you want to check. One writing task (grammar correction) contains "שתבוא אצלי", which has Mishnaic precedent;
  the judges treated it as an error to fix.
- **Different quantization and runtimes.** The 27B and Gemma run at 8-bit, the Flash-Next at ~4.5-bit. In production
  (BF16 or FP8 on GPUs) all three may do slightly better.
- **Medium effort.** Qwen's thinking ran at `reasoning_effort=medium`; the default `xhigh` thinks longer and may
  score higher on reasoning.
- **Gemma batching.** mlx-lm 0.32.2's batched generator slowed to under 1 token/s per sequence on Gemma 4 once
  answers passed ~2,400 tokens. Gemma's later runs went one prompt at a time, with the same sampling. This changes
  speed, not results.
- **Synthetic documents.** The document images are rendered from HTML, then degraded to look scanned. Real scans,
  photos and handwriting are harder.

## Reproduce

```bash
pip install mlx-lm==0.32.2 requests        # plus llama.cpp's llama-server for Flash-Next
MODEL=path/to/Qwen3.8-27B-8bit ./run_27b.sh                  # Qwen3.8-27B via mlx-lm
GGUF=path/to/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf ./run_flash_next.sh
GEMMA=path/to/gemma-4-26b-a4b-it-8bit ./run_gemma.sh          # all Gemma runs, including tuned
MODEL=... GGUF=... ./run_tuned.sh                            # tuned settings for the two Qwen models
python grade.py                         # accuracy, thinking stats, foreign-script check -> results/summary.json
python judge_writing.py build --mode nothink --dir judge/nothink   # blind file + key for the judges
#   judges follow judge/JUDGE_PROMPT.md and write judge/nothink/scores_*.json
python judge_writing.py tally --dir judge/nothink                  # -> results/writing_summary_nothink.json
#   same for --mode tuned --dir judge/tuned

pip install mlx-vlm==0.8.1               # in a separate environment: it upgrades transformers
python3 vision/build_vision.py           # renders the documents (needs Google Chrome) -> vision/images, items.jsonl
VPY=... GEMMA=... QWEN_HF=path/to/Qwen/Qwen3.8-27B GGUF=... MMPROJ=path/to/mmproj-F16.gguf ./vision/run_vision_all.sh
python3 vision/grade_vision.py           # -> vision/results/summary.json
python make_tables.py                    # -> results/tables.md
```

Run one model at a time: two of them together do not fit in 128 GB. The runs are resumable, so items that already have
an answer are skipped. The items are already built in `items/` and `vision/`.

Files:

- `results/<model>__<section>__<mode>.jsonl`: every prompt, answer, full thinking trace, token count and timing.
- `results/summary.json`: auto-graded accuracy, paired tests, thinking stats and foreign-script check.
- `results/writing_summary_<pass>.json`: judge totals and every error found, with its fix.
- `results/tables.md`: every table, generated.
- `judge/<pass>/`: the blind file, both judges' raw scores and the label key. `judge/JUDGE_PROMPT.md` is the rubric.
- `vision/`: the document images, the known text of each page, the questions, every model's output and the scores.

## Sources and licence

- Reasoning items `include_logic` and `include_driving`:
  [CohereLabs/include-base-44](https://huggingface.co/datasets/CohereLabs/include-base-44) (Apache-2.0).
- `gmmlu_stem`: [CohereLabs/Global-MMLU](https://huggingface.co/datasets/CohereLabs/Global-MMLU), human-checked
  Hebrew translations only (Apache-2.0).
- Math problems, language questions, writing tasks and the documents were written for this test. All names,
  companies, numbers and addresses in the documents are made up. The math answers were checked in Python.
- Code and results: MIT.

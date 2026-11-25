# How good is Qwen3.8 at Hebrew? Qwen3.8-27B vs Qwen3.8-Flash-Next

A quick, hands-on test of Hebrew in two open Qwen3.8 models, run locally on one Mac:

- **Qwen3.8-27B**: dense, 27B parameters.
- **Qwen3.8-Flash-Next**: the new MoE preview. It has 125B parameters, 6B of them active per token, plus a 51B
  n-gram embedding table.

The test covers four things:

- reasoning in Hebrew with thinking on;
- Hebrew grammar and vocabulary;
- writing quality;
- how each model *thinks*: in which language, and for how long.

## TL;DR

- **Writing: the MoE is much better.**
  - Two blind judges both preferred the MoE's answer on **14 of 16** writing tasks (sign test p = 0.004).
  - The MoE made **2.5× fewer Hebrew errors**: 1.5 per 100 words vs 3.7 for the 27B.
  - Fluency was 4.0/5 for the MoE vs 2.7/5 for the 27B.
- **The 27B mixes foreign letters into Hebrew words; the MoE never did.**
  - **8** of the 27B's Hebrew answers contain Arabic or Chinese characters, often in the middle of a word:
    "ריבית שנائية", "זהו פازل קלאסי", "בذكورية", "לאדם另".
  - The MoE did this in **0** of its answers.
- **Grammar knowledge: both are good and close.**
  - Both models answered 27 of 28 multiple-choice grammar questions correctly with thinking on.
  - With thinking off, the MoE got 27/28 and the 27B got 25/28.
  - Neither difference is significant on this small set.
- **Reasoning: a tie, and the weak spot is native Hebrew.**
  - Both models solved every math word problem (12/12) and every translated STEM question (6/6).
  - Both got only about half of the native Israeli logic and verbal-reasoning exam questions right: 6/12 for the
    27B, 5/12 for the MoE.
  - Overall: 29/36 for the 27B, 28/36 for the MoE.
- **Both models think in English, even when everything they are given is in Hebrew.**
  - **0 of 128** thinking traces were mostly Hebrew. Hebrew makes up only 4–16% of the letters in the thinking,
    mostly quotes from the question.
  - The final answers are in Hebrew.
  - The thinking is short at medium effort: a median of 400–730 tokens. No answer hit the length cap.
- **Neither model can write Hebrew vowel marks (niqqud) correctly.**
- **Recognizing is not the same as knowing.** Both models picked the right meaning of the idiom "לא דובים ולא
  יער" in a multiple-choice question. Asked to explain the same idiom in free writing, both got its meaning wrong
  and made up a source for it.

## What was tested

80 items, all in Hebrew, in three parts:

| Part | Items | Mode | Graded by |
|---|---|---|---|
| **Reasoning** | 36: 12 multi-step math word problems, 12 native Israeli logic / verbal-reasoning exam questions, 6 STEM questions (human-translated), 6 Israeli driving-theory questions | thinking on | exact answer |
| **Language** | 28 multiple-choice questions written for this test: numerals and gender, agreement, construct state (סמיכות), prepositions, verb forms and binyanim, roots, unvocalized homographs, idioms, spelling | thinking off **and** on | exact answer |
| **Writing** | 16 open tasks: explanation for a child, formal letter, persuasive text, rhyming lines, advice questions, finance explanation, idiom, EN→HE and HE→EN translation, legal-to-plain rewrite, verb conjugation, grammar correction, logic puzzle, summary, casual WhatsApp register, full niqqud | thinking off | 2 blind LLM judges |

An independent reviewer checked the language questions. Two items were fixed:

- One option that was arguably also correct ("שתבוא אצלי", which has Mishnaic usage) was replaced.
- One spelling question now names the 2017 Academy rules.

Both models were graded on the final versions.

## Setup

| | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|
| Weights | `Qwen/Qwen3.8-27B`, MLX 8-bit | `unsloth/Qwen3.8-Flash-Next-GGUF` UD-Q4_K_XL (~4.5 bits per weight, 104 GiB) |
| Runtime | mlx-lm 0.32.2, batches of 8 | llama.cpp 1.0.0 (`llama-server`, 8 parallel slots) |
| Decode speed per stream (8 at once) | ~6 tokens/s | ~11 tokens/s |
| Hardware | Apple M5 Max, 128 GB | same |

Both models got exactly the same prompts, with Qwen's own recommended sampling for each mode:

- **Thinking:** `reasoning_effort=medium`, temperature 1.0, top_p 0.95, top_k 20, presence penalty 0, at most 16k
  tokens.
- **No thinking:** `enable_thinking=false`, temperature 0.7, top_p 0.8, top_k 20, presence penalty 1.5.

There is no system prompt, so this measures the models out of the box. Each item was run once.

The two models are quantized differently (8-bit vs ~4.5-bit), because the MoE does not fit in 128 GB at 8-bit.
The speeds come from two different runtimes and are only a rough guide.

## Results

### Writing quality (16 tasks, thinking off, blind, 2 judges)

Each model's answer was shown to two judges as "X" or "Y", in random order. Each model was "X" in exactly half of
the tasks, and the judges did not know which model was which.

For every answer, the judges listed each Hebrew error (with the exact text and a fix) and rated fluency and task
success from 1 to 5. Then they picked the better answer. One judge read the tasks first to last, the other last to
first. They agreed on the preferred answer in all 16 tasks.

| Metric | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|
| Hebrew errors per 100 words (lower is better) | 3.66 | **1.47** |
| Errors found / words judged (both judges together) | 241 / 6590 | 89 / 6044 |
| Fluency 1–5 | 2.69 | **3.97** |
| Task success 1–5 | 3.16 | **3.81** |
| Preferred (16 tasks × 2 judges) | 4 | **28** |

| Error type | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|
| wrong word in context | 68 | 15 |
| unnatural / literal | 44 | 15 |
| other grammar (binyan, tense, syntax) | 34 | 5 |
| spelling | 25 | 18 |
| invented word | 21 | 11 |
| agreement (gender / number) | 21 | 16 |
| preposition or collocation | 11 | 5 |
| foreign word or script | 11 | **0** |
| niqqud | 6 | 4 |

The 27B was preferred on only two tasks:

- **The rhyming lines.** The MoE's lines did not rhyme.
- **The HE→EN translation.** The 27B wrote "Ombudsman", where the MoE wrote "Public Complaints Commissioner".

Per-task scores are in [`judge/`](judge), and every error the judges found, with its fix, is in
[`results/writing_summary.json`](results/writing_summary.json).

### Hebrew language knowledge (28 multiple-choice questions)

| Category | 27B no-think | MoE no-think | 27B think | MoE think |
|---|---|---|---|---|
| numerals | 3/4 | 4/4 | 4/4 | 3/4 |
| agreement | 4/4 | 4/4 | 4/4 | 4/4 |
| construct state | 1/2 | 2/2 | 1/2 | 2/2 |
| prepositions | 3/3 | 3/3 | 3/3 | 3/3 |
| verb forms / binyanim | 4/4 | 4/4 | 4/4 | 4/4 |
| roots | 3/3 | 3/3 | 3/3 | 3/3 |
| homographs | 2/2 | 2/2 | 2/2 | 2/2 |
| idioms | 3/4 | 4/4 | 4/4 | 4/4 |
| spelling | 2/2 | 1/2 | 2/2 | 2/2 |
| **All** | **25/28** | **27/28** | **27/28** | **27/28** |

What each model got wrong:

- **27B, both modes:** it picked an ungrammatical construct form ("בית ספר החדש" with thinking off, "הבית הספר
  החדש" with thinking on).
- **27B, thinking off:**
  - "עשרים ושתיים שקלים": a feminine numeral with a masculine noun.
  - It read "שבר את הכלים" literally, as "destroyed property".
- **MoE, thinking off:** "לחילופין" instead of the Academy's "לחלופין".
- **MoE, thinking on:** "שתי שבועות". See the example below.

### Reasoning in Hebrew (thinking on, effort medium)

| Part | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|
| Math word problems | 12/12 | 12/12 |
| Native Hebrew logic / verbal reasoning (INCLUDE) | 6/12 | 5/12 |
| STEM, human-translated (Global-MMLU) | 6/6 | 6/6 |
| Israeli driving theory (INCLUDE) | 5/6 | 5/6 |
| **All reasoning** | **29/36** | **28/36** |

The two models fail on the same items:

- 28 items were solved by both, and 7 were missed by both.
- 6 of those 7 shared misses are native Israeli verbal-reasoning questions: analogies, sentence completion,
  analysing an argument, and a passage in classical Hebrew.

Math and translated STEM are easy for both. Reasoning that depends on Hebrew itself is where they struggle.

### Paired comparison (same items)

| Set | n | only 27B right | only MoE right | both | neither | sign test p |
|---|---|---|---|---|---|---|
| language, no-think | 28 | 1 | 3 | 24 | 0 | 0.63 |
| language, think | 28 | 1 | 1 | 26 | 0 | 1.0 |
| reasoning, think | 36 | 1 | 0 | 28 | 7 | 1.0 |
| writing, judge preference | 16 | 2 | 14 | – | – | **0.004** |

### How they think

| Model | Set | median thinking+answer tokens | p90 tokens | hit 16k cap | letters in thinking: Hebrew / Latin | traces mostly Hebrew |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | language | 404 | 943 | 0 | 16% / 84% | 0/28 |
| Qwen3.8-Flash-Next | language | 435 | 871 | 0 | 15% / 85% | 0/28 |
| Qwen3.8-27B | reasoning | 711 | 2109 | 0 | 5% / 95% | 0/36 |
| Qwen3.8-Flash-Next | reasoning | 729 | 1712 | 0 | 4% / 96% | 0/36 |

- Both models always reason in English, even though the prompt is entirely Hebrew.
- The Hebrew in their thinking is mostly words quoted from the question.
- Chinese almost never showed up in the thinking: 2 characters in all 64 of the 27B's traces, and none in the
  MoE's.
- At medium effort, the two models think for about the same length.

### Foreign script inside Hebrew answers

Answers are counted if they contain Chinese/Japanese/Korean, Cyrillic or Arabic letters. The HE→EN translation is
excluded.

| Model | Answers checked | With Chinese/Japanese/Korean | With Arabic | With Cyrillic |
|---|---|---|---|---|
| Qwen3.8-27B | 107 | 2 | 6 | 0 |
| Qwen3.8-Flash-Next | 107 | **0** | **0** | **0** |

## What the mistakes look like

**1. Arabic and Chinese letters inside Hebrew words (27B only).** All of these are from the 27B's final answers:

- language question, thinking off: "כדי להשלים את המשפט **بشكل** תקינתי"
- language question, thinking on: "המילה "שקלים" היא **בذكورية**"
- language question, thinking on: "הפועל "לחכות" יוצא **עם介** התחרי "ל""
- writing, finance explanation: "**ריבית שנائية:** 4.5%"
- writing, logic puzzle: "זהו **פازل** קלאסי"
- writing, study advice: "...למגע הקרוב ביותר **לאדם另**?"

Note that "תקינתי" in the first example is also an invented word.

**2. Invented words (both models, the 27B about twice as often).**

27B:

- "הכחול **נפוזר** לכל הכיוונים" (should be מתפזר)
- "שעות פחותות... **בתוצרתיות**"
- "(**גזרה קלילה**)" for גזרת השלמים
- a WhatsApp invitation that ends "ממתינים **לישראון** מידיכם עד רביעי! **חג שמח!**" (for a Friday barbecue)

MoE:

- "**מדעי המחדרה**" (three times, for מדעי המחשב)
- "**פסידות** כפולה"
- "**שמשונו** משקפת"

**3. A grammar rule made up during thinking (MoE, language question).** Asked to fill in "בעוד ___ שבועות", the
MoE reasoned in English:

> "שבוע" (week) is a masculine noun. However, its plural form "שבועות" has a feminine-looking ending (ות). In
> Hebrew, when a noun is in the plural form ending with "ות", it is treated as feminine plural…

It answered "שתי שבועות", which is wrong. The 27B got this item right, with a correct explanation. With thinking
off, the MoE also got it right.

**4. Niqqud: both fail.** The reference is "הַיְלָדִים שִׂחֲקוּ בֶּחָצֵר עַד שֶׁיָּרַד הַגֶּשֶׁם".

- The 27B wrote "הַיְּלָדִים **שֶׁחִקּוּ בַּחֲצֵר**…". "שֶׁחִקּוּ" is a different word from שִׂחֲקוּ. It added an
  explanation that makes no sense ("יש דגש בצירוי החולם המופחת").
- The MoE spent about 450 words contradicting itself ("לא… לא… למעשה…") before writing "הַיְּלָדִים שִׂיחֲקוּ
  **בַּחָצֵר**…". That is closer to the reference, but still wrong.

**5. Knowing the answer in a quiz but not in writing.**

- In the multiple-choice question, both models picked the right meaning of "לא דובים ולא יער": the story is
  entirely made up.
- Asked in free writing to explain the idiom and its source, both got it wrong:
  - The 27B said it describes "בלבול, אי-בהירות".
  - The MoE said it means "פסידות כפולה" and invented a "Hasidic parable" about a poor man hunting bears.
- The real source is the Talmud (Sotah 47a).

## Limitations

- **Small sample.**
  - This is a quick test: 36 reasoning items and 28 language items, one sample each.
  - Differences of a few items are noise; the sign test says which differences hold up. The writing gap holds up
    (p = 0.004); the accuracy gaps do not.
- **Different quantization.** The 27B runs at 8-bit and the MoE at ~4.5-bit. If anything, this should handicap
  the MoE, and it still writes better.
- **Medium effort.** Thinking ran at `reasoning_effort=medium` to keep the run short. The default is `xhigh`,
  which thinks longer and may score higher on reasoning.
- **LLM judges.**
  - The writing scores come from two independent Claude (Anthropic) instances, not from native-speaker raters.
  - They were blind and agreed with each other on every task, but read the raw answers in `results/` if you
    want to check.
  - One writing task (grammar correction) contains "שתבוא אצלי", which has Mishnaic precedent. The judges treated
    it as an error to fix, which slightly lowered the 27B's task score on that item.
- **No system prompt.** A Hebrew system prompt and a lower temperature may reduce errors, especially the
  foreign-script leaks.

## Reproduce

```bash
pip install mlx-lm==0.32.2 requests       # plus llama.cpp's llama-server for the MoE
MODEL=path/to/Qwen3.8-27B-8bit ./run_27b.sh                 # Qwen3.8-27B via mlx-lm
GGUF=path/to/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf ./run_flash_next.sh
python grade.py                        # accuracy, thinking stats, foreign-script check -> results/summary.json
python judge_writing.py build          # blind file for the writing judges -> judge/writing_blind.txt + key.json
#   judges follow judge/JUDGE_PROMPT.md and write judge/scores_*.json
python judge_writing.py tally          # -> results/writing_summary.json
python make_tables.py                  # -> results/tables.md
```

Run one model at a time: both together do not fit in 128 GB. The runs are resumable, so items that already have an
answer are skipped. The items are already built in `items/`; `build_items.py` documents how they were sampled.

Files:

- `results/<model>__<section>__<mode>.jsonl`: every prompt, answer, full thinking trace, token count and timing.
- `results/summary.json`: auto-graded accuracy, paired tests, thinking stats and foreign-script check.
- `results/writing_summary.json`: judge totals and every error found.
- `judge/`: the blind file, the judge instructions, both judges' raw scores, and the X/Y key.

## Sources and licence

- Reasoning items `include_logic` and `include_driving`:
  [CohereLabs/include-base-44](https://huggingface.co/datasets/CohereLabs/include-base-44) (Apache-2.0).
- `gmmlu_stem`: [CohereLabs/Global-MMLU](https://huggingface.co/datasets/CohereLabs/Global-MMLU), human-checked
  Hebrew translations only (Apache-2.0).
- Math problems, language questions and writing tasks were written for this test. The math answers were checked in
  Python.
- Code and results: MIT.

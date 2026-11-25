### Reasoning in Hebrew (thinking on)

| Part | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| Math word problems | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) |
| Native Hebrew logic / verbal reasoning (INCLUDE) | 6/12 (50%) | 5/12 (42%) | 7/12 (58%) |
| STEM, human-translated (Global-MMLU) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| Israeli driving theory (INCLUDE) | 5/6 (83%) | 5/6 (83%) | 4/6 (67%) |
| **All reasoning** | 29/36 (81%) | 28/36 (78%) | 29/36 (81%) |

### Hebrew language knowledge (28 questions)

**thinking off**

| Category | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| numerals | 3/4 (75%) | 4/4 (100%) | 3/4 (75%) |
| agreement | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| construct_state | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) |
| prepositions | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| verb_forms | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| roots | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| homographs | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| idioms | 3/4 (75%) | 4/4 (100%) | 3/4 (75%) |
| spelling | 2/2 (100%) | 1/2 (50%) | 0/2 (0%) |
| **All** | 25/28 (89%) | 27/28 (96%) | 24/28 (86%) |

**thinking on**

| Category | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| numerals | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) |
| agreement | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| construct_state | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) |
| prepositions | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| verb_forms | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| roots | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| homographs | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| idioms | 4/4 (100%) | 4/4 (100%) | 3/4 (75%) |
| spelling | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) |
| **All** | 27/28 (96%) | 27/28 (96%) | 26/28 (93%) |

### Paired comparison (same items)

| Set | A | B | n | only A right | only B right | both | neither | sign test p |
|---|---|---|---|---|---|---|---|---|
| language, nothink | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | 28 | 1 | 3 | 24 | 0 | 0.625 |
| language, nothink | Qwen3.8-27B (dense) | Gemma-4-26B-A4B (MoE) | 28 | 4 | 3 | 21 | 0 | 1.0 |
| language, nothink | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) | 28 | 3 | 0 | 24 | 1 | 0.25 |
| language, think | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | 28 | 1 | 1 | 26 | 0 | 1.0 |
| language, think | Qwen3.8-27B (dense) | Gemma-4-26B-A4B (MoE) | 28 | 2 | 1 | 25 | 0 | 1.0 |
| language, think | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) | 28 | 2 | 1 | 25 | 0 | 1.0 |
| language, tuned | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | 28 | 0 | 2 | 26 | 0 | 0.5 |
| language, tuned | Qwen3.8-27B (dense) | Gemma-4-26B-A4B (MoE) | 28 | 1 | 2 | 25 | 0 | 1.0 |
| language, tuned | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) | 28 | 1 | 0 | 27 | 0 | 1.0 |
| reasoning, think | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | 36 | 1 | 0 | 28 | 7 | 1.0 |
| reasoning, think | Qwen3.8-27B (dense) | Gemma-4-26B-A4B (MoE) | 36 | 1 | 1 | 28 | 6 | 1.0 |
| reasoning, think | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) | 36 | 1 | 2 | 27 | 6 | 1.0 |

### Thinking behaviour

| Model | Set | median tokens | p90 tokens | hit 16k cap | thinking letters: Hebrew / Latin / CJK | traces mostly in Hebrew |
|---|---|---|---|---|---|---|
| Gemma-4-26B-A4B (MoE) | language | 766 | 2056 | 0 | 24% / 76% / 0% | 0/28 |
| Qwen3.8-27B (dense) | language | 404 | 943 | 0 | 16% / 84% / 0% | 0/28 |
| Qwen3.8-Flash-Next (MoE) | language | 434 | 871 | 0 | 15% / 85% / 0% | 0/28 |
| Gemma-4-26B-A4B (MoE) | reasoning | 1718 | 4806 | 0 | 18% / 82% / 0% | 0/36 |
| Qwen3.8-27B (dense) | reasoning | 711 | 2109 | 0 | 5% / 95% / 0% | 0/36 |
| Qwen3.8-Flash-Next (MoE) | reasoning | 729 | 1712 | 0 | 4% / 96% / 0% | 0/36 |

### Foreign script leaking into Hebrew answers

| Model | Set | Mode | answers | with CJK | with Cyrillic | with Arabic | with Latin words |
|---|---|---|---|---|---|---|---|
| Gemma-4-26B-A4B (MoE) | language | nothink | 28 | 0 | 0 | 0 | 2 |
| Qwen3.8-27B (dense) | language | nothink | 28 | 0 | 0 | 1 | 1 |
| Qwen3.8-Flash-Next (MoE) | language | nothink | 28 | 0 | 0 | 0 | 1 |
| Gemma-4-26B-A4B (MoE) | language | think | 28 | 0 | 0 | 0 | 2 |
| Qwen3.8-27B (dense) | language | think | 28 | 1 | 0 | 3 | 2 |
| Qwen3.8-Flash-Next (MoE) | language | think | 28 | 0 | 0 | 0 | 0 |
| Gemma-4-26B-A4B (MoE) | language | tuned | 28 | 0 | 0 | 0 | 2 |
| Qwen3.8-27B (dense) | language | tuned | 28 | 0 | 0 | 0 | 1 |
| Qwen3.8-Flash-Next (MoE) | language | tuned | 28 | 0 | 0 | 0 | 1 |
| Gemma-4-26B-A4B (MoE) | reasoning | think | 36 | 0 | 0 | 0 | 0 |
| Qwen3.8-27B (dense) | reasoning | think | 36 | 0 | 0 | 0 | 0 |
| Qwen3.8-Flash-Next (MoE) | reasoning | think | 36 | 0 | 0 | 0 | 0 |
| Gemma-4-26B-A4B (MoE) | writing | nothink | 15 | 0 | 0 | 0 | 6 |
| Qwen3.8-27B (dense) | writing | nothink | 15 | 1 | 0 | 2 | 2 |
| Qwen3.8-Flash-Next (MoE) | writing | nothink | 15 | 0 | 0 | 0 | 1 |
| Gemma-4-26B-A4B (MoE) | writing | tuned | 15 | 0 | 1 | 0 | 4 |
| Qwen3.8-27B (dense) | writing | tuned | 15 | 0 | 0 | 0 | 0 |
| Qwen3.8-Flash-Next (MoE) | writing | tuned | 15 | 0 | 0 | 0 | 1 |

### Writing quality, default settings, thinking off (16 tasks, blind, 2 judges, all answers side by side)

| Metric | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| Hebrew errors per 100 words (lower is better) | 3.22 | 1.22 | 0.93 |
| Errors found / words judged | 212 / 6590 | 74 / 6044 | 51 / 5478 |
| Fluency 1-5 | 2.72 | 3.97 | 4.25 |
| Task success 1-5 | 3.16 | 3.88 | 4.12 |
| Best answer (tasks x judges) | 1 | 9 | 20 |
| Mean rank (1 = best of 3) | 2.84 | 1.75 | 1.41 |

| Error type | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| agreement | 17 | 12 | 5 |
| foreign_word | 10 | 0 | 6 |
| invented_word | 22 | 10 | 2 |
| niqqud | 6 | 4 | 2 |
| other | 25 | 10 | 13 |
| preposition_or_collocation | 10 | 2 | 1 |
| spelling | 32 | 15 | 7 |
| unnatural_or_literal | 31 | 11 | 10 |
| wrong_word_in_context | 59 | 10 | 5 |

Ties for best answer: 2

### Writing quality, tuned settings (16 tasks, blind, 2 judges, all answers side by side)

| Metric | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| Hebrew errors per 100 words (lower is better) | 1.65 | 0.56 | 0.85 |
| Errors found / words judged | 79 / 4788 | 27 / 4844 | 37 / 4350 |
| Fluency 1-5 | 3.53 | 4.47 | 4.25 |
| Task success 1-5 | 3.53 | 4.25 | 3.72 |
| Best answer (tasks x judges) | 3 | 25 | 3 |
| Mean rank (1 = best of 3) | 2.56 | 1.31 | 2.12 |

| Error type | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) |
|---|---|---|---|
| agreement | 0 | 5 | 4 |
| invented_word | 0 | 0 | 2 |
| niqqud | 6 | 2 | 2 |
| other | 20 | 2 | 7 |
| preposition_or_collocation | 8 | 2 | 3 |
| spelling | 5 | 6 | 0 |
| unnatural_or_literal | 19 | 6 | 11 |
| wrong_word_in_context | 21 | 4 | 8 |

Ties for best answer: 1

### Writing, task by task (default settings): which answer the judges ranked higher

| A | B | tasks A ranked higher | tasks B ranked higher | level | sign test p |
|---|---|---|---|---|---|
| Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | 1 | 14 | 1 | 0.001 |
| Qwen3.8-27B (dense) | Gemma-4-26B-A4B (MoE) | 1 | 15 | 0 | 0.001 |
| Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) | 4 | 9 | 3 | 0.267 |

### Writing, task by task (tuned settings): which answer the judges ranked higher

| A | B | tasks A ranked higher | tasks B ranked higher | level | sign test p |
|---|---|---|---|---|---|
| Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) | 3 | 12 | 1 | 0.035 |
| Qwen3.8-27B (dense) | Gemma-4-26B-A4B (MoE) | 4 | 12 | 0 | 0.077 |
| Qwen3.8-Flash-Next (MoE) | Gemma-4-26B-A4B (MoE) | 14 | 1 | 1 | 0.001 |

### Writing quality, first pass (two Qwen models only, default settings, 2 judges)

| Metric | Qwen3.8-27B (dense) | Qwen3.8-Flash-Next (MoE) |
|---|---|---|
| Hebrew errors per 100 words (lower is better) | 3.66 | 1.47 |
| Errors found / words judged | 241 / 6590 | 89 / 6044 |
| Fluency 1-5 | 2.69 | 3.97 |
| Task success 1-5 | 3.16 | 3.81 |
| Best answer (tasks x judges) | 4 | 28 |

### Default vs tuned settings (thinking off)

| Thinking off | Qwen3.8-27B (dense) default | Qwen3.8-27B (dense) tuned | Qwen3.8-Flash-Next (MoE) default | Qwen3.8-Flash-Next (MoE) tuned | Gemma-4-26B-A4B (MoE) default | Gemma-4-26B-A4B (MoE) tuned |
|---|---|---|---|---|---|---|
| Grammar questions (28) | 25/28 (89%) | 26/28 (93%) | 27/28 (96%) | 28/28 (100%) | 24/28 (86%) | 27/28 (96%) |
| Answers with Arabic / Chinese / Cyrillic letters | 4 / 43 | 0 / 43 | 0 / 43 | 0 / 43 | 0 / 43 | 1 / 43 |
| Median writing answer length (words) | 168 | 55 | 140 | 64 | 158 | 162 |
| Writing: Hebrew errors per 100 words | 3.22 | 1.65 | 1.22 | 0.56 | 0.93 | 0.85 |
| Writing: fluency 1-5 | 2.72 | 3.53 | 3.97 | 4.47 | 4.25 | 4.25 |
| Writing: task success 1-5 | 3.16 | 3.53 | 3.88 | 4.25 | 4.12 | 3.72 |

### Reading Hebrew documents from images (12 pages, clean and scanned; 42 questions on the scans)

| Metric | Qwen3.8-27B (dense) | Qwen3.8-27B BF16 | Qwen3.8-Flash-Next (MoE) | Qwen3.8-Flash-Next, min 1024 image tokens | Gemma-4-26B-A4B (MoE) | Gemma-4-26B-A4B, 1120 image tokens |
|---|---|---|---|---|---|---|
| Word F1, clean pages (higher is better) | 0.823 | 0.804 | 0.585 | 0.539 | 0.959 | 0.983 |
| Word F1, scanned pages | 0.639 | 0.658 | 0.455 | 0.493 | 0.946 | 0.975 |
| Character error rate, clean (lower is better) | 11.9% | 12.5% | 32.1% | 30.8% | 3.5% | 4.2% |
| Character error rate, scanned | 20.8% | 19.2% | 38.5% | 36.8% | 5.7% | 8.3% |
| Questions answered correctly (scans) | 33/42 | 33/42 | 32/42 | 32/42 | 40/42 | 41/42 |
| Pages (of 24) with reversed words or numbers | 5 | 5 | 12 | 7 | 0 | 0 |
| Reversed words / reversed numbers | 51 / 3 | 15 / 5 | 168 / 20 | 243 / 9 | 0 / 0 | 0 / 0 |
| Transcriptions with Arabic / CJK / Cyrillic | 0 | 0 | 0 | 1 | 0 | 0 |
| Transcriptions cut off at 2,500 tokens | 0 | 0 | 0 | 0 | 0 | 0 |
| Mean seconds per item | 11.8 | 18.1 | 5.3 | 6.6 | 2.8 | 5.4 |

**Word F1 per document, clean**

| Document | Qwen3.8-27B (dense) | Qwen3.8-27B BF16 | Qwen3.8-Flash-Next (MoE) | Qwen3.8-Flash-Next, min 1024 image tokens | Gemma-4-26B-A4B (MoE) | Gemma-4-26B-A4B, 1120 image tokens |
|---|---|---|---|---|---|---|
| article | 0.824 | 0.79 | 0.5 | 0.534 | 0.954 | 0.966 |
| form | 0.969 | 0.957 | 0.321 | 0.289 | 0.975 | 0.988 |
| invoice | 0.936 | 0.936 | 0.761 | 0.727 | 0.968 | 1.0 |
| letter | 0.928 | 0.936 | 0.629 | 0.518 | 0.966 | 0.985 |
| mixed | 0.989 | 0.989 | 0.494 | 0.517 | 0.971 | 0.989 |
| niqqud | 0.903 | 0.903 | 0.871 | 0.645 | 0.951 | 1.0 |
| note | 0.892 | 0.831 | 0.545 | 0.462 | 0.97 | 0.97 |
| pricelist | 0.942 | 0.942 | 0.643 | 0.64 | 0.965 | 0.977 |
| procedure | 0.944 | 0.941 | 0.642 | 0.479 | 0.98 | 0.993 |
| receipt | 0.667 | 0.667 | 0.73 | 0.748 | 0.974 | 0.948 |
| smallprint | 0.153 | 0.168 | 0.111 | 0.111 | 0.84 | 0.982 |
| statement | 0.732 | 0.591 | 0.773 | 0.802 | 0.99 | 1.0 |

**Word F1 per document, scan**

| Document | Qwen3.8-27B (dense) | Qwen3.8-27B BF16 | Qwen3.8-Flash-Next (MoE) | Qwen3.8-Flash-Next, min 1024 image tokens | Gemma-4-26B-A4B (MoE) | Gemma-4-26B-A4B, 1120 image tokens |
|---|---|---|---|---|---|---|
| article | 0.664 | 0.639 | 0.338 | 0.27 | 0.962 | 0.966 |
| form | 0.587 | 0.59 | 0.164 | 0.695 | 0.975 | 0.988 |
| invoice | 0.91 | 0.91 | 0.624 | 0.4 | 0.987 | 1.0 |
| letter | 0.132 | 0.355 | 0.514 | 0.469 | 0.933 | 0.985 |
| mixed | 0.846 | 0.864 | 0.581 | 0.48 | 0.966 | 0.977 |
| niqqud | 0.387 | 0.355 | 0.355 | 0.233 | 0.885 | 0.935 |
| note | 0.909 | 0.909 | 0.531 | 0.393 | 0.97 | 0.97 |
| pricelist | 0.919 | 0.919 | 0.181 | 0.793 | 0.953 | 0.965 |
| procedure | 0.476 | 0.491 | 0.277 | 0.498 | 0.95 | 0.99 |
| receipt | 0.897 | 0.914 | 0.966 | 0.983 | 0.966 | 0.983 |
| smallprint | 0.426 | 0.447 | 0.339 | 0.129 | 0.817 | 0.938 |
| statement | 0.51 | 0.5 | 0.585 | 0.575 | 0.99 | 1.0 |

**Questions per document (scans)**

| Document | Qwen3.8-27B (dense) | Qwen3.8-27B BF16 | Qwen3.8-Flash-Next (MoE) | Qwen3.8-Flash-Next, min 1024 image tokens | Gemma-4-26B-A4B (MoE) | Gemma-4-26B-A4B, 1120 image tokens |
|---|---|---|---|---|---|---|
| article | 1/3 | 1/3 | 2/3 | 2/3 | 3/3 | 3/3 |
| form | 4/5 | 4/5 | 4/5 | 4/5 | 5/5 | 5/5 |
| invoice | 5/5 | 5/5 | 5/5 | 4/5 | 5/5 | 5/5 |
| letter | 2/4 | 2/4 | 2/4 | 2/4 | 4/4 | 4/4 |
| mixed | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| niqqud | 2/2 | 2/2 | 2/2 | 2/2 | 1/2 | 2/2 |
| note | 2/2 | 2/2 | 1/2 | 1/2 | 2/2 | 1/2 |
| pricelist | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| procedure | 3/4 | 3/4 | 1/4 | 2/4 | 4/4 | 4/4 |
| receipt | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| smallprint | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| statement | 1/4 | 1/4 | 4/4 | 2/4 | 3/4 | 4/4 |

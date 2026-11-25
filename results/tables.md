### Reasoning in Hebrew (thinking on, effort medium)

| Part | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|
| Math word problems | 12/12 (100%) | 12/12 (100%) |
| Native Hebrew logic / verbal reasoning (INCLUDE) | 6/12 (50%) | 5/12 (42%) |
| STEM, human-translated (Global-MMLU) | 6/6 (100%) | 6/6 (100%) |
| Israeli driving theory (INCLUDE) | 5/6 (83%) | 5/6 (83%) |
| **All reasoning** | 29/36 (81%) | 28/36 (78%) |

### Hebrew language knowledge (28 questions)

| Category | Qwen3.8-27B no-think | Qwen3.8-Flash-Next no-think | Qwen3.8-27B think | Qwen3.8-Flash-Next think |
|---|---|---|---|---|
| numerals | 3/4 (75%) | 4/4 (100%) | 4/4 (100%) | 3/4 (75%) |
| agreement | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| construct_state | 1/2 (50%) | 2/2 (100%) | 1/2 (50%) | 2/2 (100%) |
| prepositions | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| verb_forms | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| roots | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| homographs | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| idioms | 3/4 (75%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| spelling | 2/2 (100%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) |
| **All** | 25/28 (89%) | 27/28 (96%) | 27/28 (96%) | 27/28 (96%) |

### Paired comparison (same items)

| Set | n | only Qwen3.8-27B right | only Qwen3.8-Flash-Next right | both | neither | sign test p |
|---|---|---|---|---|---|---|
| language, nothink | 28 | 1 | 3 | 24 | 0 | 0.625 |
| language, think | 28 | 1 | 1 | 26 | 0 | 1.0 |
| reasoning, think | 36 | 1 | 0 | 28 | 7 | 1.0 |

### Thinking behaviour

| Model | Set | median tokens | p90 tokens | hit 16k cap | thinking letters: Hebrew / Latin / CJK | traces mostly in Hebrew |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | language | 404 | 943 | 0 | 16% / 84% / 0% | 0/28 |
| Qwen3.8-Flash-Next | language | 434 | 871 | 0 | 15% / 85% / 0% | 0/28 |
| Qwen3.8-27B | reasoning | 711 | 2109 | 0 | 5% / 95% / 0% | 0/36 |
| Qwen3.8-Flash-Next | reasoning | 729 | 1712 | 0 | 4% / 96% / 0% | 0/36 |

### Foreign script leaking into Hebrew answers

| Model | Set | Mode | answers | with CJK | with Cyrillic | with Arabic | with Latin words |
|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | language | nothink | 28 | 0 | 0 | 1 | 1 |
| Qwen3.8-Flash-Next | language | nothink | 28 | 0 | 0 | 0 | 1 |
| Qwen3.8-27B | language | think | 28 | 1 | 0 | 3 | 2 |
| Qwen3.8-Flash-Next | language | think | 28 | 0 | 0 | 0 | 0 |
| Qwen3.8-27B | reasoning | think | 36 | 0 | 0 | 0 | 0 |
| Qwen3.8-Flash-Next | reasoning | think | 36 | 0 | 0 | 0 | 0 |
| Qwen3.8-27B | writing | nothink | 15 | 1 | 0 | 2 | 2 |
| Qwen3.8-Flash-Next | writing | nothink | 15 | 0 | 0 | 0 | 1 |

### Writing quality (16 tasks, thinking off, blind, 2 judges)

| Metric | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|
| Hebrew errors per 100 words (lower is better) | 3.66 | 1.47 |
| Errors found / words judged | 241 / 6590 | 89 / 6044 |
| Fluency 1-5 | 2.69 | 3.97 |
| Task success 1-5 | 3.16 | 3.81 |
| Preferred by judges (tasks x judges) | 4 | 28 |

| Error type | Qwen3.8-27B | Qwen3.8-Flash-Next |
|---|---|---|
| agreement | 21 | 16 |
| foreign_word | 11 | 0 |
| invented_word | 21 | 11 |
| niqqud | 6 | 4 |
| other | 34 | 5 |
| preposition_or_collocation | 11 | 5 |
| spelling | 25 | 18 |
| unnatural_or_literal | 44 | 15 |
| wrong_word_in_context | 68 | 15 |

Ties: 0

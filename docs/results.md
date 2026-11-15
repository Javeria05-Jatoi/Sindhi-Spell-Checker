# Results

All numbers below were printed by the scripts named next to them, run on 2026-10-30 on a
12-core Windows laptop with 7.4 GB RAM and no GPU. "Before" is the original Day-15 code
(git commit `ec34d1f`) run on the **same** test cases (`scripts/eval_baseline.py`).

## Spelling correction: isolated words
`python scripts/evaluate.py` · test split of `data/test_words.json` (80 %, never used for tuning)

| | Before | After |
|---|---|---|
| Correct word ranked 1st | 41.6 % | **75.9 %** |
| Correct word in top 3 (what the UI shows) | 57.7 % | **90.2 %** |
| Correct word in top 5 | 63.6 % | **93.6 %** |
| Misspellings detected | 100 % | 100 % |
| Correctly spelled words missing from the lexicon (inflections, names) wrongly flagged | 100 % | **0 %**\* |
| Time per suggestion | 2.48 s | **7–15 ms** |

\*These 80 test words are corpus words seen ≥ 20 times, so the corpus check accepts them by
construction. The real point is that the lexicon lists base forms only, so the old checker
flagged every inflected word (`ماڻهن`, `ٿيندو`, `ڪيائين`, ...).

Top-1 / top-3 by error type (after):

| error type | n | top-1 | top-3 | top-5 |
|---|---|---|---|---|
| deletion | 115 | 34.8% | 62.6% | 71.3% |
| insertion | 119 | 83.2% | 96.6% | 98.3% |
| phonetic substitution | 109 | 95.4% | 100.0% | 100.0% |
| random substitution | 115 | 49.6% | 77.4% | 86.1% |
| transposition | 114 | 92.1% | 100.0% | 100.0% |
| visual substitution (dots) | 115 | 93.0% | 99.1% | 100.0% |
| weak letter (ا و ي) | 109 | 84.4% | 96.3% | 100.0% |

Deletions are the hardest case: removing a letter from a short word often lands one edit away
from many real words, and without context there's no way to choose.

## Spelling correction: words inside real sentences
Test split of `data/test_context.json`: 400 sentences from held-out Wikipedia articles that are
excluded from the corpus counts.

| | Before | After, no context | After, with bigram context |
|---|---|---|---|
| Top-1 | 39.3 % | 81.2 % | **93.8 %** |
| Top-3 | 57.0 % | 94.2 % | **97.5 %** |

## Real-word errors (`مهمن نواز` → `مهمان نواز`)
`python scripts/eval_real_word.py` · 400 held-out Wikipedia segments

| threshold (log-prob gain / frequency ratio) | false alarms on clean words | swaps caught |
|---|---|---|
| 4 / 5 | 2.7 % | 64.6 % |
| 6 / 20 | 1.2 % | 57.6 % |
| 8 / 50 (shipped, plus no 1-letter words) | **0.8 %** | **43.0 %** |

The shipped setting favours not nagging: it flags about 1 in 125 correct words.

## Tuning (dev split only)
`python scripts/tune.py` · 304 dev misspellings

| | top-1 | top-3 |
|---|---|---|
| hand-picked costs and weights | 79.6 % | 92.8 % |
| tuned costs (structural 0.6, phonetic 0.5, weak-letter 0.7, transposition 0.6) | 83.9 % | 94.7 % |
| + tuned weights (distance 0.8, frequency 0.2, context 0.2) | 83.9 % | 95.1 % |

## Translation (NLLB-200 distilled 600M, CTranslate2 int8, CPU)
`python scripts/eval_translation.py --n 1012` · all 1,012 sentences of FLORES-200 devtest

| direction | chrF++ | BLEU | CPU time |
|---|---|---|---|
| Sindhi → English | 59.9 | 36.7 | 1.7 s / sentence |
| English → Sindhi | 46.0 | 20.7 | 2.4 s / sentence |

(Timings were re-measured on 20 sentences with the CPU otherwise idle; a short sentence takes ~0.6 s.
On the first 200 sentences only, the scores were 60.6 / 36.3 and 46.7 / 20.6.)

## Speed
`python scripts/benchmark.py`

| | Before | After |
|---|---|---|
| `suggest()` mean | 1,635 ms | 8–15 ms (SymSpell + re-scoring) |
| startup | 1.3 s | ~8 s (lexicon + 323k-word corpus stats; the SymSpell index is cached) |

## Caveats
- The spelling test sets are **synthetic** (`scripts/make_test_set.py`, seed 13). They include
  error types the cost model favours (visual/phonetic substitutions) and ones it doesn't (random
  substitution, insertion, deletion). Real user typos would be a better test.
- CC-100 is a web crawl and may include copies of Wikipedia pages, so the held-out sentences may
  not be perfectly unseen by the bigram model.

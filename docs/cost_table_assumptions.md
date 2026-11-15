# Substitution Cost Table -- Assumptions Log

Status: **project assumption, tuned on synthetic data**. This is not a verified Sindhi typo/confusion study.

## What's implemented (`src/sindhi_cost_model.py`, `src/edit_distance.py`)

| Edit | Cost | Why |
|---|---|---|
| Substitution within a **structural group** (same undotted base shape: ب ٻ ڀ پ ت ٿ ٽ ٺ ث / ج ڄ ڃ چ ڇ ح خ / د ڌ ڏ ڊ ڍ ڎ ذ / ر ڙ ز / ن ڻ / ه ھ ...) | 0.6 | letters that differ only by dots are easy to mistype or misread |
| Substitution within a **phonetic group** (س ص ث, ز ذ ض ظ, ت ط, ح ه, ع ا ء, ق ڪ, plain vs implosive ب/ٻ ج/ڄ د/ڏ گ/ڳ) | 0.5 | Arabic loanwords are spelled by sound |
| Insert/delete a **weak letter** (ا و ي ء ئ ه ھ) | 0.7 | long vowels are often dropped or added |
| Adjacent **transposition** | 0.6 | common keyboard slip (Damerau) |
| Any other substitution / insertion / deletion | 1.0 | |

## Why these numbers
The v1 table (Day 6) was a hand-picked 0.5. In Phase 2 every cost was grid-searched on the
**dev split** (20 %) of a synthetic, seeded test set (`scripts/make_test_set.py`,
`scripts/tune.py`), maximising top-1 accuracy. They were then reported once on the untouched
test split (`docs/results.md`).

Dev-split top-1: 79.6 % with the hand-picked values → 83.9 % with the tuned ones.

## Caveat: the evaluation is partly circular
The synthetic errors include visual and phonetic substitutions drawn from these same groups, so
the cost model scores well on them by design. To keep this honest, the test set also has error
types that the model does **not** favour (random substitution, random insertion, deletion), and
`docs/results.md` reports each type separately.

## What would validate or change this
- A real corpus of Sindhi typos / OCR errors, showing which substitutions actually occur most often.
- Native-speaker review of which letters are confused on common Sindhi keyboard layouts.

## Log of changes
- v1 (Day 6): initial structural groups, cost 0.5 within group / 1.0 across. No corpus validation yet.
- v2 (Phase 1): added the missing Sindhi letters (ڙ ڻ ڌ ڍ ڎ ڃ ...), phonetic groups,
  cheaper weak-letter insert/delete, transpositions.
- v3 (Phase 2): all four costs tuned on the dev split (0.6 / 0.5 / 0.7 / 0.6).

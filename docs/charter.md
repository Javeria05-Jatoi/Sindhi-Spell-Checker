# Project Charter

## Objective
Build a working Sindhi-English dictionary + Sindhi spell-checker prototype
using edit-distance algorithms, over a 15-day plan (see the full PDF guide).

## In scope
- Sindhi Unicode normalization and tokenization
- Dictionary lookup (Sindhi -> English)
- Spelling error detection against the dictionary
- Ranked correction suggestions using weighted edit distance
- A simple UI (Streamlit) for testing

## Out of scope (for this 15-day version)
- Full Sindhi grammar / syntax checking
- Morphological analysis (inflection generation, not just lookup)
- Mobile app
- Roman-Sindhi (Latin script) support -- Perso-Arabic script only

## Success criteria (Day 15)
- [ ] `pytest` passes
- [ ] `python main.py` runs end to end on a real Sindhi sentence
- [ ] `streamlit run src/app.py` works interactively
- [ ] `python scripts/evaluate.py` reports accuracy/precision/recall/top-K
- [ ] README has working install + run instructions

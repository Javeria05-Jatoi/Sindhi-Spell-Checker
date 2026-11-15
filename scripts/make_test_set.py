# scripts/make_test_set.py  (Phase 2)
#
# Builds a reproducible synthetic evaluation set:
#   data/test_words.json        isolated words: 1,000 misspellings + 100 correct
#                               words that are NOT in the lexicon
#   data/test_context.json      500 misspellings inside real sentences taken from
#                               the HELD-OUT Wikipedia articles (never counted in
#                               data/frequencies.tsv / bigrams.tsv.gz)
# Each case has a "split": "dev" (20 %, used for tuning) or "test" (80 %).
#
# Error types deliberately include ones the cost model does NOT favour
# (random substitution, random insertion), so the eval isn't circular.

import json
import random
import sys

sys.path.insert(0, ".")
from scripts.build_corpus_stats import WIKI_PATH, _SEGMENT_BREAK, iter_wikipedia  # noqa: E402
from src.dictionary import Dictionary  # noqa: E402
from src.normalization import lookup_key, to_grapheme_clusters  # noqa: E402
from src.sindhi_cost_model import PHONETIC_GROUPS, STRUCTURAL_GROUPS, WEAK_LETTERS  # noqa: E402
from src.tokenizer import tokenize_with_spans  # noqa: E402

SEED = 13
N_WORDS = 1000
N_UNKNOWN_CORRECT = 100
N_CONTEXT = 500
DEV_FRACTION = 0.2

SINDHI_LETTERS = list("اٻبڀپتٿٽٺثجڄڃچڇحخدڌڏڊڍذرڙزسشصضطظعغفڦقڪکگڳڱلمنڻوهءيئ")
ERROR_TYPES = ["visual_substitution", "phonetic_substitution", "random_substitution",
               "deletion", "insertion", "transposition", "weak_letter"]


def _neighbours(ch, groups):
    out = set()
    for g in groups:
        if ch in g:
            out |= g
    out.discard(ch)
    return sorted(out)


def corrupt(word, error_type, rng):
    letters = to_grapheme_clusters(word)
    n = len(letters)
    if error_type in ("visual_substitution", "phonetic_substitution"):
        groups = STRUCTURAL_GROUPS if error_type == "visual_substitution" else PHONETIC_GROUPS
        spots = [i for i, ch in enumerate(letters) if _neighbours(ch, groups)]
        if not spots:
            return None
        i = rng.choice(spots)
        letters[i] = rng.choice(_neighbours(letters[i], groups))
    elif error_type == "random_substitution":
        i = rng.randrange(n)
        letters[i] = rng.choice([c for c in SINDHI_LETTERS if c != letters[i]])
    elif error_type == "deletion":
        del letters[rng.randrange(n)]
    elif error_type == "insertion":
        letters.insert(rng.randrange(n + 1), rng.choice(SINDHI_LETTERS))
    elif error_type == "transposition":
        spots = [i for i in range(n - 1) if letters[i] != letters[i + 1]]
        if not spots:
            return None
        i = rng.choice(spots)
        letters[i], letters[i + 1] = letters[i + 1], letters[i]
    elif error_type == "weak_letter":
        spots = [i for i, ch in enumerate(letters) if ch in WEAK_LETTERS]
        if spots and rng.random() < 0.5:
            del letters[rng.choice(spots)]
        else:
            letters.insert(rng.randrange(1, n + 1), rng.choice("اوي"))
    return "".join(letters)


def assign_splits(cases, rng):
    rng.shuffle(cases)
    cut = int(len(cases) * DEV_FRACTION)
    for i, case in enumerate(cases):
        case["split"] = "dev" if i < cut else "test"
    return cases


def main():
    rng = random.Random(SEED)
    d = Dictionary()

    # isolated words: lexicon words that real writers use, weighted by usage
    pool = [(k, e["frequency"]) for k, e in d._entries.items()
            if e["frequency"] >= 3 and len(to_grapheme_clusters(k)) >= 3]
    words = [w for w, _ in pool]
    weights = [f ** 0.5 for _, f in pool]  # sqrt: common words, but not only "جي/۾"

    cases, seen = [], set()
    while len(cases) < N_WORDS:
        word = rng.choices(words, weights)[0]
        error_type = ERROR_TYPES[len(cases) % len(ERROR_TYPES)]
        bad = corrupt(word, error_type, rng)
        if not bad or bad in seen or d.status(bad) != "unknown":
            continue  # real-word errors can't be caught by a dictionary checker
        seen.add(bad)
        cases.append({"correct": word, "misspelled": bad, "error_type": error_type})

    # correctly spelled words the lexicon lacks (inflections, names): tests false alarms
    oov = [(w, c) for w, c in d._frequencies.items()
           if c >= 20 and d.lookup(w) is None and len(w) >= 3]
    rng.shuffle(oov)
    for w, _ in oov[:N_UNKNOWN_CORRECT]:
        cases.append({"correct": None, "misspelled": w, "error_type": "unknown_not_misspelled"})
    assign_splits(cases, rng)
    with open("data/test_words.json", "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(cases)} cases to data/test_words.json")

    # in-context cases from held-out articles
    context_cases = []
    for text in iter_wikipedia(WIKI_PATH, holdout=True):
        for segment in _SEGMENT_BREAK.split(text):
            toks = [t for t, _, _, sindhi in tokenize_with_spans(segment) if sindhi]
            if len(toks) < 5:
                continue
            i = rng.randrange(1, len(toks) - 1)
            key = lookup_key(toks[i])
            if key not in d._entries or len(to_grapheme_clusters(key)) < 3:
                continue
            error_type = rng.choice(ERROR_TYPES)
            bad = corrupt(key, error_type, rng)
            if not bad or d.status(bad) != "unknown":
                continue
            context_cases.append({"correct": key, "misspelled": bad, "error_type": error_type,
                                  "prev": toks[i - 1], "next": toks[i + 1],
                                  "sentence": " ".join(toks)})
            break  # at most one case per article
        if len(context_cases) >= N_CONTEXT:
            break
    assign_splits(context_cases, rng)
    with open("data/test_context.json", "w", encoding="utf-8") as f:
        json.dump(context_cases, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(context_cases)} cases to data/test_context.json")


if __name__ == "__main__":
    main()

# scripts/tune.py  (Phase 2)
# Grid-searches the cost model + ranking weights on the DEV split only
# (data/test_words.json + data/test_context.json, split == "dev").
# Prints the best settings; copy them into src/sindhi_cost_model.py,
# src/edit_distance.py and src/ranking.py, then report on the test split.
import itertools
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src import edit_distance, sindhi_cost_model  # noqa: E402
from src.normalization import lookup_key  # noqa: E402
from src.ranking import rank_candidates  # noqa: E402
from src.spellchecker import SpellChecker  # noqa: E402


def load_dev():
    cases = []
    for path in ["data/test_words.json", "data/test_context.json"]:
        with open(path, encoding="utf-8") as f:
            cases += [c for c in json.load(f) if c["split"] == "dev" and c["correct"]]
    return cases


def prepare(checker, cases):
    """Candidate terms + context scores don't depend on the costs: compute once."""
    from symspellpy import Verbosity

    prepared = []
    for c in cases:
        key = lookup_key(c["misspelled"])
        items = checker._index._sym.lookup(key, Verbosity.ALL, max_edit_distance=2)
        items.sort(key=lambda it: (it.distance, -it.count))
        terms = [it.term for it in items[:60]]
        ctx = None
        if c.get("prev") or c.get("next"):
            prev = lookup_key(c["prev"]) if c.get("prev") else None
            nxt = lookup_key(c["next"]) if c.get("next") else None
            ctx = {t: checker.context.context_score(t, prev, nxt) for t in terms}
        prepared.append((key, c["correct"], terms, ctx))
    return prepared


def score(checker, prepared, w_freq, w_ctx, max_distance=2.0):
    top1 = top3 = 0
    for key, correct, terms, ctx in prepared:
        cands = [(t, d) for t in terms
                 if (d := edit_distance.weighted_edit_distance(key, t)) <= max_distance]
        ranked = rank_candidates(cands, checker.dictionary, max_distance, 3,
                                 w_dist=1 - w_freq, w_freq=w_freq, context_scores=ctx, w_ctx=w_ctx)
        words = [r["word"] for r in ranked]
        top1 += words[:1] == [correct]
        top3 += correct in words
    return top1 / len(prepared), top3 / len(prepared)


def main():
    checker = SpellChecker()
    prepared = prepare(checker, load_dev())
    print(f"{len(prepared)} dev misspellings")
    base = score(checker, prepared, 0.3, 0.3)
    print(f"current settings: top-1 {base[0]:.1%}  top-3 {base[1]:.1%}")

    best = (base, None)
    for structural, phonetic, weak, transposition in itertools.product(
            [0.3, 0.4, 0.5, 0.6], [0.5, 0.6, 0.8], [0.5, 0.7, 0.9], [0.6, 0.8, 1.0]):
        sindhi_cost_model.configure(structural, phonetic, weak)
        edit_distance.TRANSPOSITION_COST = transposition
        s = score(checker, prepared, 0.3, 0.3)
        if s > best[0]:
            best = (s, (structural, phonetic, weak, transposition))
    print("best costs (structural, phonetic, weak-indel, transposition):", best[1],
          f"top-1 {best[0][0]:.1%} top-3 {best[0][1]:.1%}")
    if best[1]:
        sindhi_cost_model.configure(*best[1][:3])
        edit_distance.TRANSPOSITION_COST = best[1][3]

    best_w = (best[0], (0.3, 0.3))
    for w_freq, w_ctx in itertools.product([0.1, 0.2, 0.3, 0.4, 0.5, 0.6], [0.0, 0.2, 0.3, 0.5, 0.8, 1.2]):
        s = score(checker, prepared, w_freq, w_ctx)
        if s > best_w[0]:
            best_w = (s, (w_freq, w_ctx))
    print("best weights (w_freq, w_ctx):", best_w[1],
          f"top-1 {best_w[0][0]:.1%} top-3 {best_w[0][1]:.1%}")


if __name__ == "__main__":
    main()

# scripts/export_rerank_input.py  (Phase 3b)
# Writes data/kaggle_rerank_input.json for kaggle/03_xlmr_context_rerank.ipynb:
# the TEST split of data/test_context.json with the app's top-10 candidates.
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src.normalization import lookup_key  # noqa: E402
from src.spellchecker import SpellChecker  # noqa: E402


def main():
    checker = SpellChecker(top_n=10)
    with open("data/test_context.json", encoding="utf-8") as f:
        cases = [c for c in json.load(f) if c["split"] == "test"]
    out = []
    for c in cases:
        cands = checker.suggest(c["misspelled"], c["prev"], c["next"])
        if lookup_key(c["correct"]) not in [s["word"] for s in cands]:
            continue  # re-ranking can't help if the right word wasn't generated
        out.append({"misspelled": c["misspelled"], "correct": lookup_key(c["correct"]),
                    "prev": c["prev"], "next": c["next"], "candidates": cands})
    with open("data/kaggle_rerank_input.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(out)} cases to data/kaggle_rerank_input.json")


if __name__ == "__main__":
    main()

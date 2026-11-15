# scripts/build_seed_dictionary.py
#
# Creates a tiny data/dictionary.json (a handful of common words) so you can
# run the pipeline end-to-end on Day 1-2 BEFORE the full Sindhi Open Lexicon
# download (scripts/download_lexicon.py) is set up. Replace with the real
# dataset as soon as it's available -- this seed is not meant to be the
# final dictionary.

import json

SEED_ENTRIES = [
    {"word": "\u06AA\u062A\u0627\u0628", "meanings": ["book"], "pos": "noun",
     "frequency": 50, "variants": [], "source": "seed (manual)"},
    {"word": "\u067E\u0627\u0621\u06CC", "meanings": ["water"], "pos": "noun",
     "frequency": 80, "variants": [], "source": "seed (manual)"},
    {"word": "\u06AF\u0647\u0631", "meanings": ["house"], "pos": "noun",
     "frequency": 70, "variants": [], "source": "seed (manual)"},
]


def build(out_path: str = "data/dictionary.json"):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(SEED_ENTRIES, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(SEED_ENTRIES)} SEED entries to {out_path} (replace with real data ASAP)")


if __name__ == "__main__":
    build()

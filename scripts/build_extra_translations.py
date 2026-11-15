# scripts/build_extra_translations.py  (Phase 2)
#
# Extracts modern English glosses for Sindhi (Perso-Arabic script) words from
# the Wiktionary dump at data/external/kaikki_sindhi.jsonl (kaikki.org,
# Wiktionary content, CC BY-SA 4.0) into data/extra_translations.json.
# Dictionary loads that file automatically and shows these glosses first
# (the lexicon's English glosses are mostly 19th-century Mewaram entries).

import json
import re
import sys
from collections import defaultdict

sys.path.insert(0, ".")
from src.normalization import lookup_key  # noqa: E402

SOURCE = "data/external/kaikki_sindhi.jsonl"
OUT = "data/extra_translations.json"
_ARABIC = re.compile(r"[؀-ۿ]")


def main():
    glosses_by_key = defaultdict(list)
    with open(SOURCE, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            forms = []
            if _ARABIC.search(entry.get("word", "")):
                forms.append(entry["word"])
            for form in entry.get("forms", []):
                if "Perso-Arabic" in form.get("tags", []) and _ARABIC.search(form.get("form", "")):
                    forms.append(form["form"])
            glosses = []
            for sense in entry.get("senses", []):
                for gloss in sense.get("glosses", []):
                    gloss = gloss.strip()
                    if gloss and gloss not in glosses and len(gloss) < 160:
                        glosses.append(gloss)
            for form in forms:
                key = lookup_key(form)
                for gloss in glosses:
                    if key and gloss not in glosses_by_key[key]:
                        glosses_by_key[key].append(gloss)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(glosses_by_key, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(glosses_by_key)} words with Wiktionary glosses to {OUT}")


if __name__ == "__main__":
    main()

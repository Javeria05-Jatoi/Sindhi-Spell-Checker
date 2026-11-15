
import json
import csv
import re
import sys
from pathlib import Path
from collections import Counter

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.normalization import normalize

SOURCE = Path("data/external/kaikki_sindhi.jsonl")
DICTIONARY = Path("data/dictionary.json")
REPORT = Path("data/external/kaikki_translation_candidates.csv")


def has_arabic_script(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))


def get_english_glosses(entry):
    glosses = []
    for sense in entry.get("senses", []):
        for gloss in sense.get("glosses", []):
            if isinstance(gloss, str) and gloss.strip():
                glosses.append(gloss.strip())

    # Remove duplicate glosses while preserving order.
    return list(dict.fromkeys(glosses))


if not SOURCE.exists():
    raise SystemExit(f"Source file not found: {SOURCE}")

if not DICTIONARY.exists():
    raise SystemExit(f"Dictionary not found: {DICTIONARY}")

with DICTIONARY.open(encoding="utf-8") as f:
    dictionary = json.load(f)

# Index existing entries using the project's own normalization.
existing = {}
for entry in dictionary:
    existing[normalize(entry["word"])] = entry
    for variant in entry.get("variants", []):
        existing.setdefault(normalize(variant), entry)

stats = Counter()
candidates = {}
seen_source_words = set()

with SOURCE.open(encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        stats["source_rows"] += 1

        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            stats["invalid_json_rows"] += 1
            continue

        if item.get("lang_code") != "sd":
            continue

        stats["sindhi_rows"] += 1

        word = item.get("word", "").strip()
        if not word or not has_arabic_script(word):
            stats["excluded_non_arabic_headwords"] += 1
            continue

        glosses = get_english_glosses(item)
        if not glosses:
            stats["without_glosses"] += 1
            continue

        stats["arabic_headwords_with_glosses"] += 1
        key = normalize(word)

        if not key:
            continue

        seen_source_words.add(key)
        target = existing.get(key)

        if target is None:
            stats["not_in_current_dictionary"] += 1
            continue

        stats["matched_current_dictionary"] += 1
        current_translations = target.get("translations", [])

        if current_translations:
            stats["matches_already_translated"] += 1
            continue

        stats["matches_missing_translation"] += 1

        # Keep source glosses separate for review. Do not merge yet.
        candidate = candidates.setdefault(
            key,
            {
                "sindhi_word": target["word"],
                "kaikki_word": word,
                "english_glosses": [],
                "current_meanings": " | ".join(
                    target.get("meanings", [])
                ),
            },
        )

        for gloss in glosses:
            if gloss not in candidate["english_glosses"]:
                candidate["english_glosses"].append(gloss)

REPORT.parent.mkdir(parents=True, exist_ok=True)

with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "sindhi_word",
            "kaikki_word",
            "english_glosses",
            "current_meanings",
        ],
    )
    writer.writeheader()

    for candidate in candidates.values():
        writer.writerow({
            "sindhi_word": candidate["sindhi_word"],
            "kaikki_word": candidate["kaikki_word"],
            "english_glosses": " | ".join(
                candidate["english_glosses"]
            ),
            "current_meanings": candidate["current_meanings"],
        })

print("\n=== Kaikki translation coverage analysis ===")
for label, key in [
    ("Source rows", "source_rows"),
    ("Sindhi rows", "sindhi_rows"),
    ("Arabic-script headwords with English glosses",
     "arabic_headwords_with_glosses"),
    ("Matched existing dictionary entries",
     "matched_current_dictionary"),
    ("Matches already having translations",
     "matches_already_translated"),
    ("Matches missing translations",
     "matches_missing_translation"),
    ("Words absent from current dictionary",
     "not_in_current_dictionary"),
    ("Rows without English glosses", "without_glosses"),
    ("Invalid JSON rows", "invalid_json_rows"),
]:
    print(f"{label}: {stats[key]}")

total = len(dictionary)
with_translation = sum(
    bool(entry.get("translations")) for entry in dictionary
)
new_candidates = len(candidates)
projected = with_translation + new_candidates

print(f"\nCurrent entries: {total}")
print(f"Currently translated: {with_translation}")
print(f"Current coverage: {with_translation / total * 100:.2f}%")

print(f"\nCandidate words for review: {new_candidates}")
print(
    "Projected coverage if every candidate is approved: "
    f"{projected / total * 100:.2f}%"
)
print(f"\nReview report: {REPORT}")
print("No dictionary entries were changed.")

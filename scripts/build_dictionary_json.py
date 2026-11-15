# scripts/build_dictionary_json.py
#
# Converts data/raw/sindhi_open_lexicon_master_223342.csv (from
# scripts/download_lexicon.py) into this project's dictionary.json schema.
#
# The source CSV columns are:
#   lexical_id, entry_id, word, word_with_airab_or_variant, part_of_speech,
#   domain, definition, language_direction, source_dictionary,
#   normalized_word, normalized_definition, extra
#
# We keep two kinds of rows:
#   1. Pure Sindhi words  (source_dictionary == "\u062c\u0627\u0645\u0639 \u0633\u0646\u068a\u064a \u0644\u063a\u0627\u062a")
#      -> used for SPELLING coverage (Days 4-9), meanings may be empty.
#   2. English <-> Sindhi entries (language_direction contains "English")
#      -> used for the TRANSLATION feature (Day 10).
#
# Everything else (Arabic->Sindhi, Hindi->Sindhi, Trade/Haematology jargon, etc.)
# is skipped by default to keep the prototype dictionary a manageable size;
# change KEEP_SOURCES / KEEP_DIRECTIONS below if you want to include more.




import csv
import json
import os
import sys

sys.path.insert(0, ".")

from src.normalization import normalize

RAW_CSV = "data/raw/sindhi_open_lexicon_master_223342.csv"
OUT_JSON = "data/dictionary.json"

PURE_SINDHI_SOURCE = "جامع سنڌي لغات"
SINDHI_ENGLISH_SOURCES = {
    "Devanagari/Sindhi → English",
    "Mewaram لغت",
}
ENGLISH_SINDHI_SOURCE = "English→ Sindhi"

ATTRIBUTION = (
    "SindhiLanguage.org (curated by Amar Fayaz Buriro), CC BY 4.0"
)


def build(csv_path=RAW_CSV, out_path=OUT_JSON, limit=None):
    entries = {}

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break

            word = normalize(row.get("word") or "")
            if not word:
                continue

            source = (row.get("source_dictionary") or "").strip()
            direction = (row.get("language_direction") or "").strip().lower()
            definition = (row.get("definition") or "").strip()

            is_sindhi_dictionary = source == PURE_SINDHI_SOURCE
            is_sindhi_english = (
                source in SINDHI_ENGLISH_SOURCES
                and direction in {"sindhi", "sindhi-english"}
            )
            is_english_sindhi = (
                source == ENGLISH_SINDHI_SOURCE
                and direction == "english"
            )

            if not (
                is_sindhi_dictionary
                or is_sindhi_english
                or is_english_sindhi
            ):
                continue

            entry = entries.setdefault(
                word,
                {
                    "word": word,
                    "meanings": [],
                    "translations": [],
                    "pos": None,
                    "frequency": 0,
                    "variants": [],
                    "source": source,
                },
            )

            if definition:
                if is_sindhi_english:
                    field = "translations"
                else:
                    field = "meanings"

                if definition not in entry[field]:
                    entry[field].append(definition)

            if not entry["pos"]:
                entry["pos"] = (
                    row.get("part_of_speech") or ""
                ).strip() or None

            variant = (
                row.get("word_with_airab_or_variant") or ""
            ).strip()

            if variant and normalize(variant) != word:
                if variant not in entry["variants"]:
                    entry["variants"].append(variant)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            list(entries.values()),
            f,
            ensure_ascii=False,
            indent=2,
        )

    translated = sum(
        bool(entry["translations"]) for entry in entries.values()
    )

    print(f"Wrote {len(entries)} unique entries to {out_path}")
    print(f"Entries with English translations: {translated}")
    print(f"Attribution: {ATTRIBUTION}")


if __name__ == "__main__":
    build()

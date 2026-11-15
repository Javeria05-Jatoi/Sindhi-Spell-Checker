# scripts/download_lexicon.py
#
# Downloads the "Sindhi Open Lexicon" master dataset from Hugging Face and saves
# it under data/raw/. This replaces hand-typing 150-300 dictionary entries.
#
# Source:      SindhiLanguageorg/Sindhi-Open-Lexicon (Hugging Face Datasets)
# Publisher:   SindhiLanguage.org
# Curated by:  Amar Fayaz Buriro
# License:     CC BY 4.0 -- you MUST keep the attribution below anywhere this
#              data (or anything built from it) is used, shown, or submitted.
# Size:        223,342 entries total, ~341 MB across CSV/JSONL/SQLite.
#
# REQUIRED ATTRIBUTION (keep this in your README and report):
#   "SindhiLanguage.org -- https://sindhilanguage.org/
#    Prepared and curated by Amar Fayaz Buriro (امر فياض ٻرڙو)"
#
# NOTE: this script needs a real internet connection. It will NOT run inside a
# sandboxed/offline environment. Run it once, locally, on your own machine.

import os

RAW_DIR = "data/raw"
REPO_ID = "SindhiLanguageorg/Sindhi-Open-Lexicon"
REPO_TYPE = "dataset"

# The full 223k-entry CSV is large (hundreds of MB). For a 15-day student
# prototype you likely only need the CSV (not the SQLite/JSONL duplicates).
FILES_TO_FETCH = [
    "data/sindhi_open_lexicon_master_223342.csv",
    # "data/sample_1000_entries.csv",   # <- uncomment for a small preview file
]


def download():
    from huggingface_hub import hf_hub_download

    os.makedirs(RAW_DIR, exist_ok=True)
    for filename in FILES_TO_FETCH:
        print(f"Downloading {filename} ...")
        local_path = hf_hub_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            filename=filename,
        )
        dest = os.path.join(RAW_DIR, os.path.basename(filename))
        if not os.path.exists(dest):
            os.symlink(local_path, dest) if hasattr(os, "symlink") else None
        print(f"  -> cached at: {local_path}")
        print(f"  -> use path: {dest if os.path.exists(dest) else local_path}")


if __name__ == "__main__":
    print("This will download the Sindhi Open Lexicon dataset (CC BY 4.0).")
    print("Remember to keep the SindhiLanguage.org attribution in your report.\n")
    download()

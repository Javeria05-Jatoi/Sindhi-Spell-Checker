# src/data_files.py
# The three large data files ship compressed in data/packed/ (xz) to keep the
# project zip small. On first use they are unpacked to their normal locations:
#   data/packed/dictionary.json.xz -> data/dictionary.json
#   data/packed/frequencies.tsv.xz -> data/frequencies.tsv
#   data/packed/bigrams.tsv.xz     -> data/bigrams.tsv.gz
# Files that already exist are never overwritten. Runs automatically when any
# src module is imported (see src/__init__.py), and from setup.bat / setup.sh.

import gzip
import lzma
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKED = os.path.join(ROOT, "data", "packed")
FILES = [
    ("dictionary.json.xz", "dictionary.json", "plain"),
    ("frequencies.tsv.xz", "frequencies.tsv", "plain"),
    ("bigrams.tsv.xz", "bigrams.tsv.gz", "gzip"),
]


def ensure_data(verbose=False):
    for packed_name, target_name, mode in FILES:
        src = os.path.join(PACKED, packed_name)
        dest = os.path.join(ROOT, "data", target_name)
        if os.path.exists(dest) or not os.path.exists(src):
            continue
        if verbose:
            print(f"  unpacking data/{target_name}")
        tmp = dest + ".part"
        with lzma.open(src, "rb") as fin:
            opener = gzip.open if mode == "gzip" else open
            with opener(tmp, "wb") as fout:
                shutil.copyfileobj(fin, fout, 1 << 20)
        os.replace(tmp, dest)


if __name__ == "__main__":
    ensure_data(verbose=True)
    print("Data files ready.")

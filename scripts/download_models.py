# scripts/download_models.py  (Phase 2/3)
#
# Downloads everything that is too big for git:
#   models/nllb-200-distilled-600M-ct2-int8/   offline translator (~630 MB)   [--translator]
#   data/external/wikipedia/sd-20231101.parquet Sindhi Wikipedia (18 MB)     [--corpus]
#   data/external/cc100/sd.txt.xz               CC-100 Sindhi (70 MB)        [--corpus]
#   data/external/flores/flores200_dataset.tar.gz  FLORES-200 (26 MB)        [--flores]
# With no flags, downloads the translator only (the corpus stats are already
# committed as data/frequencies.tsv + data/bigrams.tsv.gz).
#
# Usage: python scripts/download_models.py [--translator] [--corpus] [--flores] [--all]

import argparse
import os
import urllib.request

NLLB_REPO = "JustFrederik/nllb-200-distilled-600M-ct2-int8"
NLLB_DIR = "models/nllb-200-distilled-600M-ct2-int8"
NLLB_FILES = ["config.json", "model.bin", "sentencepiece.bpe.model", "shared_vocabulary.txt",
              "special_tokens_map.json", "tokenizer_config.json"]
URLS = {
    "corpus": [
        ("https://huggingface.co/datasets/wikimedia/wikipedia/resolve/main/20231101.sd/train-00000-of-00001.parquet",
         "data/external/wikipedia/sd-20231101.parquet"),
        ("https://data.statmt.org/cc-100/sd.txt.xz", "data/external/cc100/sd.txt.xz"),
    ],
    "flores": [
        ("https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz",
         "data/external/flores/flores200_dataset.tar.gz"),
    ],
}


def fetch(url, dest):
    if os.path.exists(dest):
        print(f"  have {dest}")
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"  downloading {url}")
    urllib.request.urlretrieve(url, dest + ".part", reporthook=_progress)
    print()
    os.replace(dest + ".part", dest)


def _progress(blocks, block_size, total):
    done = blocks * block_size
    if total > 0:
        print(f"\r    {min(done, total) / 1e6:7.1f} / {total / 1e6:.1f} MB", end="", flush=True)


def main():
    parser = argparse.ArgumentParser()
    for flag in ("translator", "corpus", "flores", "all"):
        parser.add_argument(f"--{flag}", action="store_true")
    args = parser.parse_args()
    if not (args.translator or args.corpus or args.flores or args.all):
        args.translator = True

    if args.translator or args.all:
        print("NLLB-200 600M (CTranslate2 int8), CC BY-NC 4.0")
        for name in NLLB_FILES:
            fetch(f"https://huggingface.co/{NLLB_REPO}/resolve/main/{name}", os.path.join(NLLB_DIR, name))
    for group in ("corpus", "flores"):
        if getattr(args, group) or args.all:
            print(group)
            for url, dest in URLS[group]:
                fetch(url, dest)


if __name__ == "__main__":
    main()

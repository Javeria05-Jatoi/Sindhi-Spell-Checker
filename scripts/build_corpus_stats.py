# scripts/build_corpus_stats.py  (Phase 2)
#
# Counts word unigrams + bigrams in real Sindhi text, producing:
#   data/frequencies.tsv        word<TAB>count      (ranking + "known word" check)
#   data/bigrams.tsv.gz         "w1 w2"<TAB>count  (context re-ranking)
#   data/review/oov_candidates.tsv  frequent corpus words missing from the lexicon
#
# Sources (download first, see docs/dataset_sources.md):
#   data/external/wikipedia/sd-20231101.parquet   Sindhi Wikipedia (CC BY-SA 4.0)
#   data/external/cc100/sd.txt.xz                 CC-100 Sindhi web crawl
#
# Usage: python scripts/build_corpus_stats.py [--max-cc100-lines N]

import argparse
import gzip
import lzma
import os
import re
import sys
from collections import Counter

sys.path.insert(0, ".")
from src.normalization import lookup_key  # noqa: E402
from src.tokenizer import tokenize_with_spans  # noqa: E402

WIKI_PATH = "data/external/wikipedia/sd-20231101.parquet"
CC100_PATH = "data/external/cc100/sd.txt.xz"
FREQ_OUT = "data/frequencies.tsv"
BIGRAM_OUT = "data/bigrams.tsv.gz"
OOV_OUT = "data/review/oov_candidates.tsv"

MIN_UNIGRAM = 3
MIN_BIGRAM = 3
PRUNE_AT = 4_000_000  # bigram dict size that triggers dropping singletons (RAM guard)

_SEGMENT_BREAK = re.compile(r"[\n.،؛؟۔!?:;()\[\]\"“”|=*#<>]+")


HOLDOUT_EVERY = 20  # every 20th article is kept out of the counts for evaluation


def iter_wikipedia(path, holdout=False):
    """Yield article texts. holdout=False skips the held-out articles,
    holdout=True yields ONLY them (scripts/make_test_set.py)."""
    import pyarrow.parquet as pq

    table = pq.ParquetFile(path)
    i = 0
    for batch in table.iter_batches(columns=["text"], batch_size=500):
        for text in batch.column(0).to_pylist():
            if (i % HOLDOUT_EVERY == 0) == holdout:
                yield text
            i += 1


def iter_cc100(path, max_lines=None):
    with lzma.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        try:
            for i, line in enumerate(f):
                if max_lines and i >= max_lines:
                    break
                yield line
        except EOFError:
            print("  (CC-100 file is truncated -- counted what was there)")


def count(texts, unigrams, bigrams):
    docs = 0
    for text in texts:
        docs += 1
        for segment in _SEGMENT_BREAK.split(text):
            prev = None
            for token, _, _, is_sindhi in tokenize_with_spans(segment):
                key = lookup_key(token) if is_sindhi else None
                if not key or len(key) > 25:
                    prev = None
                    continue
                unigrams[key] += 1
                if prev:
                    bigrams[f"{prev} {key}"] += 1
                prev = key
        if len(bigrams) > PRUNE_AT:
            for pair in [p for p, c in bigrams.items() if c < 2]:
                del bigrams[pair]
    return docs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cc100-lines", type=int, default=None)
    parser.add_argument("--no-cc100", action="store_true")
    args = parser.parse_args()

    unigrams, bigrams = Counter(), Counter()
    if os.path.exists(WIKI_PATH):
        print("Sindhi Wikipedia articles:", count(iter_wikipedia(WIKI_PATH), unigrams, bigrams))
    if os.path.exists(CC100_PATH) and not args.no_cc100:
        print("CC-100 lines:", count(iter_cc100(CC100_PATH, args.max_cc100_lines), unigrams, bigrams))
    if not unigrams:
        sys.exit("No corpus found -- download the sources listed at the top of this file.")

    print(f"Tokens: {sum(unigrams.values()):,}  distinct words: {len(unigrams):,}")
    with open(FREQ_OUT, "w", encoding="utf-8") as f:
        for word, c in unigrams.most_common():
            if c < MIN_UNIGRAM:
                break
            f.write(f"{word}\t{c}\n")
    kept = [(p, c) for p, c in bigrams.items() if c >= MIN_BIGRAM]
    kept.sort(key=lambda pc: -pc[1])
    with gzip.open(BIGRAM_OUT, "wt", encoding="utf-8") as f:
        for pair, c in kept:
            f.write(f"{pair}\t{c}\n")
    print(f"Wrote {FREQ_OUT} and {BIGRAM_OUT} ({len(kept):,} bigrams)")

    from src.dictionary import Dictionary

    d = Dictionary(frequencies_path="")
    os.makedirs(os.path.dirname(OOV_OUT), exist_ok=True)
    with open(OOV_OUT, "w", encoding="utf-8") as f:
        f.write("word\tcount\tguessed_base_form\n")
        written = 0
        for word, c in unigrams.most_common():
            if written >= 5000:
                break
            if d.lookup(word) is None:
                base = d.base_form(word)
                f.write(f"{word}\t{c}\t{base['word'] if base else ''}\n")
                written += 1
    print(f"Wrote {OOV_OUT}")


if __name__ == "__main__":
    main()

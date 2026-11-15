# Dataset Sources

## Primary dataset: Sindhi Open Lexicon (used)

- **What:** Sindhi Open Lexicon Master Dataset
- **Publisher:** SindhiLanguage.org
- **Curated by:** Amar Fayaz Buriro (\u0627\u0645\u0631 \u0641\u064A\u0627\u0636 \u0628\u0631\u0691\u0648)
- **Where:** https://huggingface.co/datasets/SindhiLanguageorg/Sindhi-Open-Lexicon
- **License:** CC BY 4.0 (attribution required -- keep the line above in the
  README and the final report, anywhere this data is used or shown)
- **Size used:** ~223,342 total entries available; this project filters down to
  (a) the pure-Sindhi subset ("\u062C\u0627\u0645\u0639 \u0633\u0646\u068A\u064A \u0644\u063A\u0627\u062A", 80,588 entries)
  for spelling coverage, and (b) the English<->Sindhi subset (21,726 entries)
  for translation. See `scripts/build_dictionary_json.py` for the exact filter.
- **Format:** CSV (also available as JSONL / SQLite)
- **Fields kept:** word, definition, part_of_speech, source_dictionary
- **NOT provided by this dataset:** word frequency. Since Phase 2 frequencies
  come from the two corpora below (`scripts/build_corpus_stats.py`).

## Required attribution (copy verbatim wherever this data is used)

> SindhiLanguage.org -- https://sindhilanguage.org/
> Prepared and curated by Amar Fayaz Buriro (\u0627\u0645\u0631 \u0641\u064A\u0627\u0636 \u0628\u0631\u0691\u0648)

## Added in Phase 2/3

### Sindhi Wikipedia (used: frequencies, bigrams, held-out test sentences)
- **Where:** https://huggingface.co/datasets/wikimedia/wikipedia, config `20231101.sd`
  (`data/external/wikipedia/sd-20231101.parquet`, 17.6 MB, 16,928 articles)
- **License:** CC BY-SA 4.0 (Wikipedia contributors)
- **Used for:** word counts + bigram counts; every 20th article is held out and used
  only to build `data/test_context.json`.

### CC-100 Sindhi (used: frequencies, bigrams)
- **Where:** https://data.statmt.org/cc-100/sd.txt.xz (70 MB, 1.4M lines)
- **Citation:** Conneau et al., "Unsupervised Cross-lingual Representation Learning at
  Scale" (ACL 2020); Wenzek et al., "CCNet" (LREC 2020).
- **License:** Common Crawl terms of use; only aggregate counts are redistributed here.
- Together with Wikipedia: 53.1M tokens, 323k distinct words
  (`data/frequencies.tsv`, `data/bigrams.tsv.gz`).

### Wiktionary via kaikki.org (used: modern English glosses)
- **Where:** https://kaikki.org/dictionary/Sindhi/ (`data/external/kaikki_sindhi.jsonl`)
- **License:** CC BY-SA 4.0 (Wiktionary contributors)
- **Used for:** `data/extra_translations.json` -- 1,332 words with short modern glosses,
  shown before the 19th-century Mewaram glosses.

### FLORES-200 (used: translation evaluation only)
- **Where:** https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz
- **License:** CC BY-SA 4.0 (Meta AI)
- **Used for:** chrF++/BLEU of the translator (`scripts/eval_translation.py`). Never trained on.

### NLLB-200 distilled 600M (used: sentence translation)
- **Where:** https://huggingface.co/facebook/nllb-200-distilled-600M, CTranslate2 int8
  conversion from https://huggingface.co/JustFrederik/nllb-200-distilled-600M-ct2-int8
- **License:** CC BY-NC 4.0 (non-commercial; fine for a university project)
- **Citation:** NLLB Team, "No Language Left Behind" (2022).

## Fallback / development seed

`scripts/build_seed_dictionary.py` creates a tiny 3-word dictionary so the
pipeline can be run and tested before the real dataset is downloaded. This is
NOT a real data source and must not be cited as one in the final report.

## Datasets considered but not used

- **IEEE DataPort "Sindhi Open Lexicon Dataset"** -- same underlying dataset,
  but requires an IEEE DataPort subscription. The Hugging Face copy above is
  the same data, free, so it was used instead.
- **SiNER dataset** (github.com/AliWazir/SiNER-dataset) -- a Sindhi Named
  Entity Recognition corpus (news articles), not a dictionary. Could be a
  future source of real word-frequency counts (see Day 13/8 limitation
  above) but was not used for this version.
- **Kaggle "sindhi_language_corpus"** -- a large raw-text corpus, not a
  structured dictionary; same potential future use as SiNER for frequency
  estimation.

If a different or additional dataset is added later, log it here in the same
format: name, publisher, URL, license, what was kept, and required attribution.

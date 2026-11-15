# scripts/eval_translation.py  (Phase 3a)
# Scores the offline NLLB translator on FLORES-200 devtest (Sindhi <-> English)
# with chrF++ and BLEU (sacrebleu). Writes docs/translation_results.json.
#
# FLORES-200: https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz (CC BY-SA 4.0)
# Usage: python scripts/eval_translation.py [--n 200]
import argparse
import json
import os
import sys
import tarfile
import time

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src.translator import Translator  # noqa: E402

FLORES_TAR = "data/external/flores/flores200_dataset.tar.gz"
MEMBERS = {"sd": "./flores200_dataset/devtest/snd_Arab.devtest",
           "en": "./flores200_dataset/devtest/eng_Latn.devtest"}


def read_flores():
    out = {}
    with tarfile.open(FLORES_TAR) as tar:
        for lang, name in MEMBERS.items():
            out[lang] = tar.extractfile(name).read().decode("utf-8").splitlines()
    return out


def main():
    import sacrebleu

    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200, help="sentences per direction (devtest has 1012)")
    args = parser.parse_args()

    data = read_flores()
    translator = Translator()
    report = {"model": os.path.basename(translator.model_dir), "sentences": args.n}
    for src, tgt in (("sd", "en"), ("en", "sd")):
        sources, refs = data[src][:args.n], data[tgt][:args.n]
        t0 = time.time()
        hyps = [translator.translate(s, src, tgt) for s in sources]
        secs = (time.time() - t0) / len(sources)
        chrf = sacrebleu.corpus_chrf(hyps, [refs], word_order=2).score
        bleu = sacrebleu.corpus_bleu(hyps, [refs]).score
        report[f"{src}-{tgt}"] = {"chrf++": round(chrf, 1), "bleu": round(bleu, 1),
                                  "seconds_per_sentence": round(secs, 2)}
        print(f"{src}->{tgt}: chrF++ {chrf:.1f}  BLEU {bleu:.1f}  ({secs:.2f} s/sentence)")
        print("  e.g.", sources[0][:80], "->", hyps[0][:100])
    with open("docs/translation_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()

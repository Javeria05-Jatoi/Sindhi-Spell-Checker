# src/translator.py  (Phase 3a)
# Sentence-level Sindhi <-> English translation with Meta's NLLB-200
# (distilled 600M), run through CTranslate2 int8 so it works on a laptop CPU
# with no PyTorch install. Optional: if the model folder or the packages are
# missing, `Translator.available` is False and the UI falls back to
# word-by-word dictionary glosses.
#
# Model: facebook/nllb-200-distilled-600M (CC BY-NC 4.0), CTranslate2 int8
# conversion from huggingface.co/JustFrederik/nllb-200-distilled-600M-ct2-int8

import os
import re
import threading

MODEL_DIR = os.environ.get("NLLB_MODEL_DIR", "models/nllb-200-distilled-600M-ct2-int8")
LANG_CODES = {"sd": "snd_Arab", "en": "eng_Latn"}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?؟۔])\s+|\n+")


class Translator:
    def __init__(self, model_dir: str = MODEL_DIR, threads: int = 0):
        self.model_dir = model_dir
        self.threads = threads or max(1, (os.cpu_count() or 2) // 2)
        self._model = None
        self._sp = None
        self._lock = threading.Lock()
        self.error = None

    @property
    def available(self) -> bool:
        return os.path.exists(os.path.join(self.model_dir, "model.bin")) and \
            os.path.exists(os.path.join(self.model_dir, "sentencepiece.bpe.model"))

    def _load(self):
        if self._model is None:
            import ctranslate2
            import sentencepiece

            self._sp = sentencepiece.SentencePieceProcessor(
                model_file=os.path.join(self.model_dir, "sentencepiece.bpe.model"))
            self._model = ctranslate2.Translator(self.model_dir, device="cpu",
                                                 compute_type="int8",
                                                 intra_threads=self.threads)

    def translate(self, text: str, source: str = "sd", target: str = "en",
                  beam_size: int = 4) -> str:
        """Translate `text` (several sentences are fine) between 'sd' and 'en'."""
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text or "") if s.strip()]
        if not sentences:
            return ""
        src, tgt = LANG_CODES[source], LANG_CODES[target]
        with self._lock:
            self._load()
            batch = [[src] + self._sp.encode(s, out_type=str) + ["</s>"] for s in sentences]
            results = self._model.translate_batch(
                batch, target_prefix=[[tgt]] * len(batch), beam_size=beam_size,
                max_decoding_length=256, repetition_penalty=1.1)
        out = []
        for result in results:
            tokens = [t for t in result.hypotheses[0] if t != tgt]
            out.append(self._sp.decode(tokens))
        return " ".join(out)

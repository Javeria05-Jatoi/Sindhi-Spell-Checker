# src/api.py  (Phase 2/3: web backend)
# Run with:  python -m uvicorn src.api:app --port 8000     (then open http://localhost:8000)
# Serves the JSON API under /api and the web front end from web/.

import bisect
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)  # data/ paths are relative to the project root

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from src.normalization import lookup_key  # noqa: E402
from src.spellchecker import SpellChecker  # noqa: E402
from src.translator import Translator  # noqa: E402

app = FastAPI(title="Sindhi Spell-Checker & Translator API")
checker = SpellChecker()
translator = Translator()
_vocab_sorted = sorted(checker._vocab)
_ARABIC = re.compile(r"[؀-ۿ]")
METRICS_PATH = "docs/results.json"


class TextIn(BaseModel):
    text: str


class TranslateIn(BaseModel):
    text: str
    source: str = "sd"
    target: str = "en"


class WordIn(BaseModel):
    word: str


def _entry_json(entry, query=None):
    if entry is None:
        return None
    return {
        "word": entry["word"],
        "key": entry["key"],
        "forms": entry["forms"][:6],
        "pos": entry.get("pos"),
        "translations": entry["translations"][:8],
        "meanings": entry["meanings"][:4],
        "sources": entry["sources"],
        "frequency": checker.dictionary.frequency(entry["key"]),
        "query": query,
    }


_NON_LATIN = re.compile(r"[؀-ۿऀ-ॿ]+")


def _short_gloss(word):
    """First clause of the first English gloss, without embedded Devanagari/Arabic."""
    entry = checker.dictionary.base_form(word, need_translation=True)
    for gloss in (entry or {}).get("translations", []):
        gloss = _NON_LATIN.sub("", gloss)
        gloss = re.split(r"(?<=[a-z])\.\s|;", gloss)[0]
        gloss = re.sub(r"\s+", " ", gloss).strip(" .,")
        if len(gloss) > 1:
            return gloss[:60]
    return None


@app.get("/api/health")
def health():
    return {"entries": len(checker.dictionary), "vocabulary": len(checker._vocab),
            "context_model": checker.context.available, "translator": translator.available}


@app.post("/api/check")
def check(body: TextIn):
    if len(body.text) > 20_000:
        raise HTTPException(413, "Text too long (max 20,000 characters).")
    tokens = checker.check_text(body.text)
    for t in tokens:
        for s in t["suggestions"]:
            s["gloss"] = _short_gloss(s["word"])
    sindhi = [t for t in tokens if t["status"] != "skip"]
    return {
        "tokens": tokens,
        "stats": {"words": len(sindhi), "unknown": sum(not t["known"] for t in sindhi)},
    }


@app.get("/api/suggest")
def suggest(word: str, prev: str = None, next: str = None):
    out = checker.suggest(word, prev, next)
    for s in out:
        s["gloss"] = _short_gloss(s["word"])
    return {"word": word, "known": checker.dictionary.is_known(word), "suggestions": out}


@app.get("/api/lookup")
def lookup(q: str):
    q = q.strip()
    if not q:
        return {"mode": "empty"}
    if not _ARABIC.search(q):  # English -> Sindhi
        results = checker.dictionary.reverse_lookup(q, limit=24)
        return {"mode": "english", "query": q, "results": [_entry_json(e) for e in results]}
    entry = checker.dictionary.lookup(q)
    base = None
    if entry is None:
        base = checker.dictionary.base_form(q)
    suggestions = [] if entry else checker.suggest(q)
    for s in suggestions:
        s["gloss"] = _short_gloss(s["word"])
    return {
        "mode": "sindhi",
        "query": q,
        "status": checker.dictionary.status(q),
        "entry": _entry_json(entry, q),
        "base_form": _entry_json(base, q),
        "suggestions": suggestions,
    }


@app.get("/api/autocomplete")
def autocomplete(prefix: str, limit: int = 8):
    key = lookup_key(prefix)
    if not key:
        return []
    i = bisect.bisect_left(_vocab_sorted, key)
    matches = []
    while i < len(_vocab_sorted) and _vocab_sorted[i].startswith(key) and len(matches) < 400:
        matches.append(_vocab_sorted[i])
        i += 1
    matches.sort(key=lambda w: (-checker.dictionary.frequency(w), len(w)))
    return [{"word": w, "gloss": _short_gloss(w)} for w in matches[:limit]]


@app.get("/api/word-of-the-day")
def word_of_the_day():
    pool = [e for e in checker.dictionary._entries.values()
            if e["translations"] and e.get("frequency", 0) >= 50 and len(e["key"]) >= 3]
    pool.sort(key=lambda e: e["key"])
    if not pool:
        return None
    day = datetime.date.today().toordinal()
    return _entry_json(pool[(day * 7919) % len(pool)])


@app.post("/api/translate")
def translate(body: TranslateIn):
    if body.source not in ("sd", "en") or body.target not in ("sd", "en") or body.source == body.target:
        raise HTTPException(400, "source/target must be 'sd' and 'en'.")
    if len(body.text) > 3000:
        raise HTTPException(413, "Text too long (max 3,000 characters).")
    glosses = []
    if body.source == "sd":
        for t in checker.check_text(body.text):
            if t["status"] != "skip":
                glosses.append({"word": t["token"], "gloss": _short_gloss(t["token"])})
    translation, engine, error = None, "dictionary", None
    if translator.available:
        try:
            translation = translator.translate(body.text, body.source, body.target)
            engine = "nllb"
        except Exception as exc:  # missing package / broken model: fall back to glosses
            error = str(exc)
    if translation is None and body.source == "sd":
        translation = " ".join(g["gloss"].split(",")[0].rstrip(".") if g["gloss"] else f"[{g['word']}]"
                               for g in glosses)
    if translation is None:
        results = [checker.dictionary.reverse_lookup(w, limit=1) for w in body.text.split()]
        translation = " ".join(r[0]["word"] if r else w for r, w in zip(results, body.text.split()))
    return {"translation": translation, "engine": engine, "glosses": glosses, "error": error}


@app.post("/api/user-words")
def add_user_word(body: WordIn):
    added = checker.dictionary.add_user_word(body.word)
    return {"word": body.word, "added": added}


@app.get("/api/metrics")
def metrics():
    out = {}
    for key, path in (("spelling", METRICS_PATH), ("translation", "docs/translation_results.json"),
                      ("real_word", "docs/real_word_results.json")):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                out[key] = json.load(f)
    spelling = out.pop("spelling", {})
    out.update({k: v for k, v in spelling.items() if k in ("words", "context")})
    return out


@app.middleware("http")
async def no_stale_static(request, call_next):
    # the front end is edited often; make browsers revalidate instead of caching
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/static", StaticFiles(directory=os.path.join(ROOT, "web")), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(ROOT, "web", "index.html"))

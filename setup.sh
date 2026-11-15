#!/usr/bin/env bash
# One-time setup on macOS / Linux: creates .venv, installs packages, downloads the translator.
set -e
cd "$(dirname "$0")"
echo "=== Sindhi Spell-Checker: setup ==="

PY=""
for candidate in python3.12 python3.13 python3.11 python3.14 python3; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,14) else 1)'; then
    PY="$candidate"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.11-3.14 not found. Install Python 3.12 (https://www.python.org/downloads/) and run ./setup.sh again."
  exit 1
fi
echo "Using: $PY"

[ -x .venv/bin/python ] || "$PY" -m venv .venv
echo "[2/3] Installing packages (a few minutes the first time)"
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt
echo "Unpacking the data files"
.venv/bin/python -c "import src; print('Data files ready.')"
echo "[3/3] Downloading the offline translator model (about 630 MB)"
.venv/bin/python scripts/download_models.py ||
  echo "Translator download failed; the app still works with dictionary glosses. Run ./setup.sh again to retry."
echo "=== Setup finished. Start the app with ./run.sh ==="

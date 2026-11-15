#!/usr/bin/env bash
# Starts the web app and opens http://localhost:8000 in the browser.
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Run ./setup.sh first."
  exit 1
fi
exec .venv/bin/python scripts/serve.py

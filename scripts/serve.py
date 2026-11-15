# scripts/serve.py -- start the web app and open it in the browser.
# Used by run.bat / run.sh. Same as `python -m uvicorn src.api:app --port 8000`,
# but waits until the dictionary has loaded before opening the page.
import os
import sys
import threading
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
PORT = int(os.environ.get("PORT", "8000"))

print("Loading the dictionary and corpus statistics (the first start takes about 20 seconds)...")
import uvicorn  # noqa: E402
from src.api import app, translator  # noqa: E402

if not translator.available:
    print("Note: translator model not found, so the Translate tab will use dictionary glosses.")
    print("      Run: python scripts/download_models.py")
url = f"http://localhost:{PORT}"
print(f"\nReady: {url}   (press Ctrl+C to stop)\n")
if "--no-browser" not in sys.argv:
    threading.Timer(1.5, webbrowser.open, [url]).start()
uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")

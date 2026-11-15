# Setup on a new laptop

**Made by Sneha Haseja and Javeria Jatoi.**

You need:
- **Python 3.12** (3.11 and 3.13 also work). Download it from <https://www.python.org/downloads/>.
  On Windows, tick **"Add python.exe to PATH"** on the first install screen.
- An internet connection for the first setup. It downloads about 1 GB: packages plus the 630 MB translator.
- About 2.5 GB of free disk space.

After setup, the app runs **fully offline**.

---

## VS Code (recommended)

1. Unzip `Sindhi-Spell-Checker.zip`.
2. In VS Code: **File → Open Folder…** and pick the unzipped `Sindhi-Spell-Checker` folder.
   If VS Code asks *"Do you trust the authors?"*, click **Yes**. If it offers to install the
   recommended **Python** extension, click **Install**.
3. Open the terminal with **Terminal → New Terminal** (`` Ctrl+` ``) and run setup once:

   ```powershell
   .\setup.bat
   ```

   (macOS/Linux: `bash setup.sh`.) Wait for *Setup finished*, then press any key.
4. Start the app in the same terminal:

   ```powershell
   .venv\Scripts\python.exe scripts\serve.py
   ```

   (macOS/Linux: `.venv/bin/python scripts/serve.py`.) The browser opens http://localhost:8000.
   To stop it, click in the terminal and press `Ctrl+C`.

**Shortcuts that are already set up:**
- **Run and Debug panel** (`Ctrl+Shift+D`): choose **Run Sindhi web app** and press **F5**.
  It also has **Run tests** and **Spell-check a sentence (CLI)**.
- **Terminal → Run Task…**: **1. Setup (first time only)**, **2. Run the app**, **Run tests**.

**If you see a red error saying *"running scripts is disabled on this system"*:** that's
PowerShell refusing `.venv\Scripts\activate`. You don't need to activate anything. The commands
above call `.venv\Scripts\python.exe` directly. Or switch the terminal to Command Prompt: click
the **⌄** next to the **+** in the terminal panel and choose **Command Prompt**.

If VS Code shows the wrong Python, press `Ctrl+Shift+P`, run **Python: Select Interpreter** and pick
the one in `.venv`.

---

## Windows: the easy way

1. Unzip `Sindhi-Spell-Checker.zip`, for example to your Desktop.
2. Open the unzipped folder and double-click **`setup.bat`**. Wait until it says *Setup finished*
   (about 5–15 minutes, depending on your internet).
3. Double-click **`run.bat`**. The app opens in your browser at <http://localhost:8000>.
   The first start takes about 20 seconds.

To stop the app, close the black window (or press `Ctrl+C` in it). Next time, just double-click `run.bat`.

## Windows: typing the commands yourself

Open **Command Prompt** (not PowerShell) in the unzipped folder (in File Explorer, click the address bar, type `cmd` and press Enter), then run:

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\download_models.py
python scripts\serve.py
```

If `py` is not found, use `python -m venv .venv` in the first line instead.

## macOS / Linux

Open a Terminal in the unzipped folder, then:

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

Or the same thing by hand:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/download_models.py
python scripts/serve.py
```

On Ubuntu, install `venv` support first if needed: `sudo apt install python3.12-venv`.

---

## Other things you can run

First activate the environment: `.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on macOS/Linux.

| Command | What it does |
|---|---|
| `python scripts/serve.py` | Start the web app (same as `run.bat`) |
| `python -m uvicorn src.api:app --port 8000` | Start the web app without opening the browser |
| `pytest` | Run the 31 automated tests |
| `python main.py "سنڌى ٻولي"` | Spell-check a sentence in the terminal |
| `python main.py --file input.txt --fix` | Spell-check a text file and print the corrected text |
| `streamlit run src/app.py` | The original simple Streamlit interface |
| `python scripts/evaluate.py` | Re-measure spelling accuracy on the test set |
| `python scripts/benchmark.py` | Measure suggestion speed |
| `python scripts/download_models.py --flores` then `python scripts/eval_translation.py --n 1012` | Re-score the translator (slow on a CPU: about 1 hour) |

To rebuild the corpus statistics from scratch (optional; they are already included):

```bash
python scripts/download_models.py --corpus
python scripts/build_corpus_stats.py
```

## Problems?

| Problem | Fix |
|---|---|
| `Python ... was not found` | Install Python 3.12 and tick "Add python.exe to PATH", then run setup again. |
| `pip install` fails | Check the internet connection and run `setup.bat` again. It continues where it stopped. |
| Translate tab says "dictionary" instead of translating | The model didn't download. Run `python scripts/download_models.py` again. |
| `address already in use` / port 8000 busy | Close the other app, or start on another port: `set PORT=8010` (Windows) or `export PORT=8010` (macOS/Linux), then `python scripts/serve.py`. |
| Browser didn't open | Open <http://localhost:8000> yourself. |

## Credits

Dictionary data: **SindhiLanguage.org**, prepared and curated by **Amar Fayaz Buriro**, CC BY 4.0.
Translation model: Meta NLLB-200 (CC BY-NC 4.0, non-commercial use). Full list in `docs/dataset_sources.md`.

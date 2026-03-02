"""Copysight -- Video insight extractor for macOS.

PyWebView entry point: opens a native macOS window with WebKit WebView,
serving the HTML/CSS/JS frontend from ui/ folder. Python API is exposed
to JavaScript via the pywebview bridge.

Backend modules (downloader, transcriber, analyzer, vault) are unchanged.
"""

import warnings
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")

import os

# ── Ensure Homebrew binaries (ffmpeg, ffprobe) are on PATH ──
# macOS .app bundles don't inherit shell PATH, so /opt/homebrew/bin is missing.
_BREW_PATHS = ["/opt/homebrew/bin", "/usr/local/bin"]
_current_path = os.environ.get("PATH", "")
for _p in _BREW_PATHS:
    if _p not in _current_path:
        os.environ["PATH"] = _p + ":" + _current_path
        _current_path = os.environ["PATH"]

import webview
import threading
import json
import re
import time
from datetime import datetime

import downloader
import transcriber
import analyzer
import vault

# ── Paths ──

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
TRANSCRIPTS_DIR = os.path.join(DOWNLOADS_DIR, "transcripts")
ANALYSES_DIR = os.path.join(DOWNLOADS_DIR, "analyses")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
UI_DIR = os.path.join(BASE_DIR, "ui")

# Ensure output directories exist
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(ANALYSES_DIR, exist_ok=True)

# ── Default analysis prompt (3-paragraph editorial structure) ──

DEFAULT_ANALYSIS_PROMPT = """\
Wyciagnij z tej transkrypcji wideo dokladnie 9 insightow w formacie 3x3.

## Praktyczne tipy

Podaj 3 konkretne, actionable wskazowki -- co moge zrobic od razu po obejrzeniu.
Kazdy tip: **tytul** (max 8 slow), potem 1-2 zdania wyjasnienia.

## Inspiracje

Podaj 3 pomysly, referencje lub sposoby myslenia, ktore warto zapamietac.
Kazda inspiracja: **tytul**, potem 1-2 zdania kontekstu.

## Obserwacje

Podaj 3 krytyczne spostrzezenia -- co naprawde dziala, co jest przesadzone, co pominieto.
Kazda obserwacja: **tytul**, potem 1-2 zdania analizy.

Zasady:
- Pisz po polsku, zwiezle, bez wstepow i podsumowan.
- Nie powtarzaj tresci -- wyciagaj esencje.
- Format: markdown z naglowkami ## i boldowanymi tytulami insightow.
- Kazdy insight to tytul + body, nic wiecej. Lacznie 9 punktow."""


def _versioned_path(base_path, suffix="", output_dir=None):
    """Generate a versioned file path: <dir>/<name><suffix>_YYYYMMDD_HHmm.txt"""
    name = os.path.splitext(os.path.basename(base_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{name}{suffix}_{timestamp}.txt"
    if output_dir:
        return os.path.join(output_dir, filename)
    return os.path.join(os.path.dirname(base_path), filename)


# ══════════════════════════════════════════
#  Python API exposed to JavaScript
# ══════════════════════════════════════════

class Api:
    """Backend API for the Copysight WebView frontend.

    All public methods are callable from JavaScript via:
        window.pywebview.api.method_name(args)
    """

    def __init__(self):
        self._pipeline_status = {
            "step": "idle",
            "stamps": [],
            "progress": 0,
            "error": None,
            "done": False,
        }
        self._current_transcript = ""
        self._current_analysis = ""
        self._last_mp3 = ""
        self._is_processing = False

    # ── Pipeline ──

    def start_pipeline(self, url):
        """One-click pipeline: Download -> Transcribe -> Analyze.
        Runs in a background thread. Poll get_pipeline_status() for updates.
        """
        if self._is_processing:
            return {"started": False, "reason": "Already processing"}

        url = (url or "").strip()
        if not url:
            return {"started": False, "reason": "No URL"}

        self._is_processing = True
        self._pipeline_status = {
            "step": "connecting",
            "stamps": [],
            "progress": 0,
            "error": None,
            "done": False,
        }
        self._current_transcript = ""
        self._current_analysis = ""

        settings = self._load_prefs()

        def work():
            try:
                # Step 1: Download
                self._add_stamp("Connecting...")

                download_log = []

                def on_progress(pct, msg):
                    if self._pipeline_status["stamps"]:
                        if msg:
                            self._pipeline_status["stamps"][-1] = msg

                def on_log(msg):
                    if msg:
                        download_log.append(str(msg))

                mp3 = downloader.download_audio_as_mp3(
                    url,
                    output_path=DOWNLOADS_DIR,
                    log_fn=on_log,
                    progress_fn=on_progress,
                )
                if not mp3:
                    self._pipeline_status["step"] = "error"
                    # Find most informative log entry
                    detail = "Unknown error"
                    for entry in reversed(download_log):
                        if "error" in entry.lower() or "not found" in entry.lower():
                            detail = entry
                            break
                    if detail == "Unknown error" and download_log:
                        detail = download_log[-1]
                    self._pipeline_status["error"] = detail
                    self._add_stamp(f"Error: {detail[:80]}")
                    return
                self._last_mp3 = mp3
                self._add_stamp("Downloading... done.")
                self._pipeline_status["step"] = "transcribing"

                # Step 2: Transcribe
                self._add_stamp("Transcribing...")
                lang_val = settings.get("language", "auto")
                if lang_val == "auto":
                    lang_val = None
                ctx = settings.get("context", "").strip() or None
                model = settings.get("model", "turbo")

                def on_phase(msg):
                    if self._pipeline_status["stamps"]:
                        self._pipeline_status["stamps"][-1] = f"Transcribing... {msg}"

                text = transcriber.transcribe_audio(
                    mp3,
                    language=lang_val,
                    model_size=model,
                    initial_prompt=ctx,
                    phase_fn=on_phase,
                )
                if not text:
                    self._pipeline_status["step"] = "error"
                    self._pipeline_status["error"] = "Transcription failed"
                    self._add_stamp("Error: Transcription failed")
                    return
                self._current_transcript = text
                self._add_stamp("Transcribing... done.")

                # Auto-save transcript
                txt_path = _versioned_path(mp3, output_dir=TRANSCRIPTS_DIR)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)

                # Step 3: Analyze (if API key available)
                api_key = vault.load_key()
                if api_key:
                    self._pipeline_status["step"] = "analyzing"
                    self._add_stamp("Analyzing...")
                    prompt = settings.get("analysis_prompt", "").strip()
                    if not prompt:
                        prompt = DEFAULT_ANALYSIS_PROMPT

                    result = analyzer.analyze_text(text, prompt, api_key)
                    if result:
                        self._current_analysis = result
                        self._add_stamp("Analyzing... done.")
                        # Auto-save analysis
                        path = _versioned_path(mp3, "_analiza", output_dir=ANALYSES_DIR)
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(result)
                    else:
                        self._add_stamp("Analysis: API error (transcript saved)")
                else:
                    self._add_stamp("No API key -- transcript only.")

                self._pipeline_status["step"] = "done"
                self._pipeline_status["done"] = True

            except Exception as exc:
                self._pipeline_status["step"] = "error"
                self._pipeline_status["error"] = str(exc)[:120]
                self._add_stamp(f"Error: {str(exc)[:80]}")
            finally:
                self._is_processing = False

        threading.Thread(target=work, daemon=True).start()
        return {"started": True}

    def get_pipeline_status(self):
        """Returns current pipeline status for JS polling."""
        return self._pipeline_status

    def get_result(self):
        """Returns the current transcript and/or analysis text."""
        return {
            "transcript": self._current_transcript,
            "analysis": self._current_analysis,
        }

    def _add_stamp(self, text):
        self._pipeline_status["stamps"].append(text)

    # ── Settings ──

    def load_settings(self):
        """Load all settings (API key from vault, rest from settings.json)."""
        prefs = self._load_prefs()
        return {
            "api_key": vault.load_key(),
            "language": prefs.get("language", "auto"),
            "model": prefs.get("model", "turbo"),
            "context": prefs.get("context", ""),
            "analysis_prompt": prefs.get("analysis_prompt", ""),
        }

    def save_settings(self, data):
        """Save settings. API key goes to .env, rest to settings.json."""
        if not data:
            return {"saved": False}

        # API key -> vault
        api_key = data.get("api_key", "").strip()
        if api_key:
            if api_key.startswith("sk-or-"):
                vault.save_key(api_key)
            else:
                return {"saved": False, "error": "API key must start with sk-or-"}

        # Other prefs -> settings.json
        prefs = self._load_prefs()
        for key in ("language", "model", "context", "analysis_prompt"):
            if key in data:
                prefs[key] = data[key]
        self._save_prefs(prefs)

        return {"saved": True}

    def _load_prefs(self):
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_prefs(self, prefs):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)

    # ── Library ──

    def get_library(self, bracket="fresh"):
        """Scan analyses/ folder, filter by age bracket.
        Returns list of {title, date_str, path, bracket}.
        """
        entries = []
        if not os.path.exists(ANALYSES_DIR):
            return entries

        now = datetime.now()
        for filename in os.listdir(ANALYSES_DIR):
            if not filename.endswith(".txt"):
                continue
            filepath = os.path.join(ANALYSES_DIR, filename)
            try:
                mtime = datetime.fromtimestamp(os.stat(filepath).st_mtime)
            except OSError:
                continue

            age_days = (now - mtime).days
            file_bracket = (
                "fresh" if age_days <= 7
                else "recent" if age_days <= 30
                else "settled" if age_days <= 180
                else "gold"
            )

            if bracket and file_bracket != bracket:
                continue

            # Parse title from filename
            title = filename
            title = re.sub(r"_analiza_\d{8}_\d{4}\.txt$", "", title)
            title = re.sub(r"_\d{8}_\d{4}\.txt$", "", title)
            title = title.replace("_", " ")

            entries.append({
                "title": title,
                "date_str": mtime.strftime("%d %b"),
                "path": filepath,
                "bracket": file_bracket,
            })

        entries.sort(key=lambda x: os.stat(x["path"]).st_mtime, reverse=True)
        return entries

    def get_entry(self, path):
        """Read a library entry file and return its content."""
        try:
            # Security: only allow reading from ANALYSES_DIR or TRANSCRIPTS_DIR
            real_path = os.path.realpath(path)
            allowed = [os.path.realpath(ANALYSES_DIR), os.path.realpath(TRANSCRIPTS_DIR)]
            if not any(real_path.startswith(d) for d in allowed):
                return {"error": "Access denied"}
            with open(path, "r", encoding="utf-8") as f:
                return {"content": f.read()}
        except (OSError, IOError) as exc:
            return {"error": str(exc)}

    # ── Actions ──

    def export_txt(self, text, suffix=""):
        """Export text to a versioned .txt file."""
        if not text or not self._last_mp3:
            return {"exported": False, "error": "Nothing to export"}
        out_dir = ANALYSES_DIR if suffix else TRANSCRIPTS_DIR
        path = _versioned_path(self._last_mp3, suffix, output_dir=out_dir)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return {"exported": True, "filename": os.path.basename(path)}

    def has_api_key(self):
        """Check if an API key is saved (for first-run detection)."""
        return bool(vault.load_key())


# ══════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════

if __name__ == "__main__":
    api = Api()
    window = webview.create_window(
        "Copysight",
        url=os.path.join(UI_DIR, "index.html"),
        width=800,
        height=600,
        resizable=False,
        js_api=api,
    )
    webview.start()

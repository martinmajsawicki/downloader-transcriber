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

import subprocess
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
Napisz fiszke z tej transkrypcji wideo. Trzy sekcje, kazda to jeden spojny akapit editorial.

## Praktyczne tipy

Jeden akapit: 3 konkretne, actionable wskazowki -- co moge zrobic od razu po obejrzeniu.
Kazdy tip zacznij od **boldowanego tytulu** (max 8 slow) inline, potem plynnie kontynuuj
zdaniem wyjasnienia. Caly akapit ma sie czytac jako ciagly tekst, nie lista.

## Inspiracje

Jeden akapit: 3 pomysly, referencje lub sposoby myslenia warte zapamietania.
Kazda inspiracja zaczyna sie od **boldowanego tytulu** inline, potem kontekst.
Plynny, esejowy styl -- nie lista punktowa.

## Obserwacje

Jeden akapit: 3 krytyczne spostrzezenia -- co naprawde dziala, co przesadzone, co pominieto.
Kazda obserwacja zaczyna sie od **boldowanego tytulu** inline, potem analiza.
Ton: rzeczowy, bez ogladania sie.

Zasady:
- Pisz po polsku, zwiezle, bez wstepow i podsumowan.
- Nie powtarzaj tresci -- wyciagaj esencje.
- Format: markdown z naglowkami ## i boldowanymi tytulami inline.
- Kazda sekcja to JEDEN ciagly akapit, nie lista. Lacznie 9 insightow w 3 akapitach."""


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
        self._lock = threading.Lock()
        self._cancel = threading.Event()
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
        self._video_meta = {}
        self._current_entry_path = ""
        self._is_processing = False

    # ── Pipeline ──

    def start_pipeline(self, url):
        """One-click pipeline: Download -> Transcribe -> Analyze.
        Runs in a background thread. Poll get_pipeline_status() for updates.
        """
        with self._lock:
            if self._is_processing:
                return {"started": False, "reason": "Already processing"}

            url = (url or "").strip()
            if not url:
                return {"started": False, "reason": "No URL"}

            self._is_processing = True
            self._cancel.clear()
            self._pipeline_status = {
                "step": "connecting",
                "stamps": [],
                "progress": 0,
                "error": None,
                "done": False,
            }
            self._current_transcript = ""
            self._current_analysis = ""
            self._video_meta = {}
            self._current_entry_path = ""

        settings = self._load_prefs()

        def work():
            try:
                # Step 1: Download
                self._add_stamp("Connecting...")

                download_log = []

                def on_progress(pct, msg):
                    with self._lock:
                        if self._pipeline_status["stamps"] and msg:
                            self._pipeline_status["stamps"][-1] = msg

                def on_log(msg):
                    if msg:
                        download_log.append(str(msg))

                dl_result = downloader.download_audio_as_mp3(
                    url,
                    output_path=DOWNLOADS_DIR,
                    log_fn=on_log,
                    progress_fn=on_progress,
                )
                if not dl_result:
                    # Find most informative log entry
                    detail = "Unknown error"
                    for entry in reversed(download_log):
                        if "error" in entry.lower() or "not found" in entry.lower():
                            detail = entry
                            break
                    if detail == "Unknown error" and download_log:
                        detail = download_log[-1]
                    self._set_status(step="error", error=detail)
                    self._add_stamp(f"Error: {detail[:80]}")
                    return
                mp3 = dl_result["mp3"]
                self._last_mp3 = mp3
                self._video_meta = dl_result.get("meta", {})
                self._add_stamp("Downloading... done.")

                if self._cancel.is_set():
                    self._add_stamp("Cancelled.")
                    self._set_status(step="idle")
                    return

                self._set_status(step="transcribing")

                # Step 2: Transcribe
                self._add_stamp("Transcribing...")
                lang_val = settings.get("language", "auto")
                if lang_val == "auto":
                    lang_val = None
                ctx = settings.get("context", "").strip() or None
                model = settings.get("model", "turbo")

                def on_phase(msg):
                    with self._lock:
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
                    self._set_status(step="error", error="Transcription failed")
                    self._add_stamp("Error: Transcription failed")
                    return
                self._current_transcript = text
                self._add_stamp("Transcribing... done.")

                if self._cancel.is_set():
                    self._add_stamp("Cancelled.")
                    self._set_status(step="idle")
                    return

                # Auto-save transcript
                txt_path = _versioned_path(mp3, output_dir=TRANSCRIPTS_DIR)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                self._current_entry_path = txt_path

                # Step 3: Analyze (if API key available)
                api_key = vault.load_key()
                if api_key:
                    self._set_status(step="analyzing")
                    self._add_stamp("Analyzing...")
                    prompt = settings.get("analysis_prompt", "").strip()
                    if not prompt:
                        prompt = DEFAULT_ANALYSIS_PROMPT

                    result = analyzer.analyze_text(text, prompt, api_key)
                    if result:
                        self._current_analysis = result
                        self._add_stamp("Analyzing... done.")
                        # Auto-save analysis with source header
                        path = _versioned_path(mp3, "_analiza", output_dir=ANALYSES_DIR)
                        with open(path, "w", encoding="utf-8") as f:
                            meta = self._video_meta
                            if meta.get("url"):
                                f.write(f"<!-- source: {meta['url']} -->\n")
                            f.write(result)
                        self._current_entry_path = path
                    else:
                        self._add_stamp("Analysis: API error (transcript saved)")
                else:
                    self._add_stamp("No API key -- transcript only.")

                self._set_status(step="done", done=True)

            except Exception as exc:
                self._set_status(step="error", error=str(exc)[:120])
                self._add_stamp(f"Error: {str(exc)[:80]}")
            finally:
                with self._lock:
                    self._is_processing = False

        threading.Thread(target=work, daemon=True).start()
        return {"started": True}

    def get_pipeline_status(self):
        """Returns current pipeline status for JS polling."""
        with self._lock:
            status = self._pipeline_status.copy()
            status["stamps"] = list(status["stamps"])
            return status

    def get_result(self):
        """Returns the current transcript and/or analysis text + metadata."""
        return {
            "transcript": self._current_transcript,
            "analysis": self._current_analysis,
            "meta": self._video_meta,
        }

    def cancel_pipeline(self):
        """Request cancellation of the running pipeline."""
        self._cancel.set()
        return {"cancelled": True}

    def _add_stamp(self, text):
        with self._lock:
            self._pipeline_status["stamps"].append(text)

    def _set_status(self, **kwargs):
        with self._lock:
            self._pipeline_status.update(kwargs)

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
        """Scan analyses/ and transcripts/ folders, filter by age bracket.
        Returns list of {title, date_str, path, bracket, kind}.
        kind: "analysis" or "transcript".
        """
        entries = []
        now = datetime.now()

        # Scan both directories
        dirs = [
            (ANALYSES_DIR, "analysis"),
            (TRANSCRIPTS_DIR, "transcript"),
        ]
        # Track analysis base names to avoid duplicating transcripts
        analysis_bases = set()

        for scan_dir, kind in dirs:
            if not os.path.exists(scan_dir):
                continue
            for filename in os.listdir(scan_dir):
                if not filename.endswith(".txt"):
                    continue
                filepath = os.path.join(scan_dir, filename)
                try:
                    mtime = datetime.fromtimestamp(os.stat(filepath).st_mtime)
                except OSError:
                    continue

                # Parse base name (video title without suffix/timestamp)
                base = filename
                base = re.sub(r"_analiza_\d{8}_\d{4}\.txt$", "", base)
                base = re.sub(r"_\d{8}_\d{4}\.txt$", "", base)

                if kind == "analysis":
                    analysis_bases.add(base)
                elif kind == "transcript" and base in analysis_bases:
                    # Skip transcript if analysis exists for same video
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

                title = base.replace("_", " ")

                entries.append({
                    "title": title,
                    "date_str": mtime.strftime("%d %b"),
                    "path": filepath,
                    "bracket": file_bracket,
                    "kind": kind,
                })

        entries.sort(key=lambda x: os.stat(x["path"]).st_mtime, reverse=True)
        return entries

    def get_entry(self, path):
        """Read a library entry file and return its content.
        Also sets current entry path for export context.
        """
        try:
            # Security: only allow reading from ANALYSES_DIR or TRANSCRIPTS_DIR
            real_path = os.path.realpath(path)
            allowed = [os.path.realpath(ANALYSES_DIR), os.path.realpath(TRANSCRIPTS_DIR)]
            if not any(real_path.startswith(d) for d in allowed):
                return {"error": "Access denied"}
            self._current_entry_path = path
            with open(path, "r", encoding="utf-8") as f:
                return {"content": f.read()}
        except (OSError, IOError) as exc:
            return {"error": str(exc)}

    # ── Actions ──

    def reveal_in_finder(self):
        """Open Finder with the current entry file selected."""
        path = self._current_entry_path
        if not path or not os.path.exists(path):
            return {"revealed": False, "error": "No saved file"}
        subprocess.Popen(["open", "-R", path])
        return {"revealed": True, "filename": os.path.basename(path)}

    def get_library_counts(self):
        """Return entry count per bracket for all tabs."""
        counts = {"fresh": 0, "recent": 0, "settled": 0, "gold": 0}
        all_entries = self.get_library(bracket=None)
        for entry in all_entries:
            b = entry.get("bracket")
            if b in counts:
                counts[b] += 1
        return counts

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

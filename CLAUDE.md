# Copysight — Claude Code Instructions

## What this is

A macOS desktop app (PyWebView + vanilla HTML/CSS/JS) that extracts structured insights from online videos. Runs locally on Apple Silicon. No frameworks, no bundlers.

## How to run

```bash
venv/bin/python app.py
```

Opens a native 800x600 macOS window. For frontend-only testing, serve `ui/` via any HTTP server (fonts need a server, not `file://`).

## Architecture

**Python backend** (PyWebView bridge):
- `app.py` — Entry point, `Api` class exposed to JS via `window.pywebview.api.*`
- `downloader.py` — yt-dlp wrapper, returns `{mp3, meta}` dict
- `transcriber.py` — mlx-whisper, Apple Silicon GPU
- `analyzer.py` — OpenRouter API (Gemini 2.0 Flash) via OpenAI SDK
- `vault.py` — API key storage in `.env`

**Frontend** (vanilla, no frameworks):
- `ui/index.html` — SPA with 4 screens + settings overlay
- `ui/app.js` — All logic: navigation, pipeline polling, typewriter, reader, library
- `ui/styles.css` — Complete visual theme

**Bridge pattern**: JS calls Python methods via `window.pywebview.api.method_name()` which returns a Promise. Pipeline runs in a background thread; JS polls `get_pipeline_status()` every 500ms.

## Key conventions

### Python
- All public `Api` methods return dicts (JSON-serializable for the bridge)
- Shared state protected by `threading.Lock` — always use `self._lock`
- File paths: `DOWNLOADS_DIR`, `TRANSCRIPTS_DIR`, `ANALYSES_DIR` constants in app.py
- Versioned filenames: `Name_suffix_YYYYMMDD_HHMM.txt`

### JavaScript
- Vanilla JS only — no frameworks, no modules, no build step
- `var` not `const`/`let` (legacy consistency — don't mix styles)
- All pywebview calls must have `.catch()` handler
- DOM refs declared at top of app.js as `const` (exception to var rule — these are stable refs)

### CSS
- CSS variables defined in `:root` — use them, don't hardcode colors
- Font stack loaded via `<link>` in HTML `<head>` (not `@import` in CSS — causes silent failures)
- `user-select: none` on body, `user-select: text` on `.reader-content`

## Brand guidelines

**Read `brand/guidelines.md` before making visual changes.** Key rules:

- **Aesthetic**: "Minimalist Archive" — manila paper, editorial typography, subtle textures
- **Colors**: `--base` #F7E9C1, `--red` #D1344B, `--blue` #4A89C5, `--gold` #E5B742, `--ink` #2B2B2B
- **Fonts**: Playfair Display (brand title only), IBM Plex Sans/Condensed (UI/headers), Georgia/Charter (reading), IBM Plex Mono (stamps/metadata)
- **Tone**: Precise, calm, empowering. No emoji, no exclamation marks, no gamification
- **Analysis format**: 3 editorial paragraphs, not bullet lists. Each paragraph has 3 insights with **bold titles** inline

## What NOT to do

- Don't add frameworks (React, Vue, etc.) — the app is intentionally vanilla
- Don't change brand colors/fonts without checking `brand/guidelines.md`
- Don't add security hardening (path traversal, CORS, etc.) — this is a local desktop app
- Don't use `@import` in CSS for fonts — use `<link>` in HTML
- Don't use `let`/`const` for variables in app.js (except DOM refs at top)
- Don't add npm, webpack, or any build toolchain

## File output format

Analysis files saved with source URL header:
```
<!-- source: https://youtube.com/watch?v=... -->
## Praktyczne tipy
...
```

## Testing without pywebview

Open `ui/index.html` via HTTP server. The JS has a fallback path (`if (!window.pywebview)`) that simulates stamp typing. Reader can be tested by calling `populateReader(text, meta)` from browser console.

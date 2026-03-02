# Copysight — Technical Documentation

Version: 2.0 (PyWebView)
Platform: macOS (Apple Silicon)
Last updated: 2 March 2026

---

## Overview

Copysight is a local-first macOS desktop app that extracts structured insights from YouTube videos. One-click pipeline: paste a URL, get a 3x3 editorial analysis in under 2 minutes.

The app runs entirely on your machine. Video audio is downloaded via yt-dlp, transcribed locally using mlx-whisper on Apple Silicon GPU, and analyzed through OpenRouter API (Gemini 2.0 Flash). Results are saved as plain text files.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Native macOS window (pywebview + WebKit)        │
│  800x600, non-resizable, titlebar = 32px         │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  ui/index.html  — Single Page Application   │ │
│  │  ui/styles.css  — Minimalist Archive theme   │ │
│  │  ui/app.js      — Navigation + bridge logic  │ │
│  └──────────────────┬──────────────────────────┘ │
│                     │ pywebview JS↔Python bridge  │
│                     │ window.pywebview.api.*()    │
│  ┌──────────────────┴──────────────────────────┐ │
│  │  app.py  — Api class (pipeline, settings,   │ │
│  │            library, export)                  │ │
│  └──────────────────┬──────────────────────────┘ │
│                     │                             │
│  ┌─────────┬────────┴───┬──────────┬───────────┐ │
│  │download │transcriber │ analyzer │  vault    │ │
│  │er.py    │.py         │ .py      │  .py      │ │
│  │(yt-dlp) │(mlx-whisper│ (OpenAI  │  (.env    │ │
│  │         │ Apple GPU) │  SDK →   │   r/w)    │ │
│  │         │            │  OpenRtr)│           │ │
│  └─────────┴────────────┴──────────┴───────────┘ │
└─────────────────────────────────────────────────┘
```

### Component Map

| File | Role | Lines | Dependencies |
|------|------|-------|-------------|
| `app.py` | Entry point + Api class | ~371 | pywebview, all backend modules |
| `downloader.py` | YouTube audio download | ~142 | yt-dlp |
| `transcriber.py` | Local speech-to-text | ~129 | mlx-whisper, ffprobe |
| `analyzer.py` | LLM analysis via API | ~57 | openai SDK (OpenRouter) |
| `vault.py` | API key storage | ~27 | (stdlib only) |
| `ui/index.html` | SPA — 3 screens + settings overlay | ~162 | — |
| `ui/styles.css` | Unified CSS (Minimalist Archive) | ~892 | Google Fonts CDN |
| `ui/app.js` | Navigation, pipeline bridge, library | ~691 | pywebview bridge |
| `build_app.sh` | macOS .app bundle builder | ~100 | iconutil (system) |
| `build_icon.py` | App icon generator (.icns) | ~182 | Pillow |

### Project File Tree

```
copysight/
├── app.py                  # PyWebView entry point + Api class
├── downloader.py           # yt-dlp wrapper (YouTube → MP3)
├── transcriber.py          # mlx-whisper (Apple Silicon GPU, fp16)
├── analyzer.py             # OpenRouter API client (Gemini 2.0 Flash)
├── vault.py                # API key read/write (.env)
├── requirements.txt        # Python dependencies
├── settings.json           # User preferences (auto-created)
├── .env                    # API key (gitignored)
├── build_app.sh            # Bundle builder → dist/Copysight.app
├── build_icon.py           # Icon generator (Pillow → .icns)
├── ui/
│   ├── index.html          # Single Page Application (3 screens)
│   ├── styles.css          # Minimalist Archive visual theme
│   └── app.js              # Navigation, pipeline bridge, library
├── brand/
│   └── guidelines.md       # Brand guidelines v0.3
├── prototypes/
│   └── screen-*.html       # Original HTML/CSS mockups
├── downloads/              # Output directory (gitignored)
│   ├── *.mp3
│   ├── transcripts/*.txt
│   └── analyses/*.txt
└── dist/                   # Build output (gitignored)
    └── Copysight.app       # macOS application bundle
```

---

## Pipeline Flow

```
User pastes URL → clicks red button
    │
    ▼
1. CONNECTING
   downloader.download_audio_as_mp3(url)
   yt-dlp fetches audio, converts to MP3 via FFmpeg
   Progress callbacks update stamp text in real-time
    │
    ▼
2. TRANSCRIBING
   transcriber.transcribe_audio(mp3_path)
   mlx-whisper runs on Apple Silicon GPU (fp16)
   Models: tiny/base/small/medium/large/turbo
   Auto-saves transcript → downloads/transcripts/
    │
    ▼
3. ANALYZING (if API key present)
   analyzer.analyze_text(transcript, prompt, api_key)
   OpenRouter API → Gemini 2.0 Flash
   Default prompt: 3x3 format (9 insights)
   Auto-saves analysis → downloads/analyses/
    │
    ▼
4. READER
   Auto-transition to Screen 3 (after 800ms fade)
   Markdown parsed into editorial HTML by populateReader()
   Copy / Export .txt available
```

### Pipeline Status Model

The `Api._pipeline_status` dict is polled by JavaScript every 500ms:

```python
{
    "step": "idle|connecting|transcribing|analyzing|done|error",
    "stamps": ["Connecting...", "Downloading... done.", ...],
    "progress": 0,        # reserved for future use
    "error": None,         # error message string or None
    "done": False          # True when pipeline completes
}
```

Stamps are appended as new pipeline phases start. The last stamp can be updated in-place by progress/phase callbacks (e.g., "Transcribing... loading model" → "Transcribing... 2:30 (turbo)"). The JS polling logic (`pollPipelineStatus()`) detects both new stamps and in-place text updates.

---

## Screen System

The app has 3 screens + a settings overlay, managed as a SPA. Screens use `display: none` / `display: flex` toggling via `.active` class. Transitions use a `fadeIn` CSS animation (0.3s ease-out).

### Screen 1+2: Input Desk + Stamping

Combined into one screen (`#screen-input`). The red "nipple button" triggers the full pipeline. Stamps appear below the URL input with a typewriter effect.

**Layout architecture:**
- `.input-content` is a flex column (`align-items: center`, `justify-content: center`)
- `.brand-title` and `.input-row` are centered by the flex parent
- `.input-row` is 400px wide (matches URL slot width)
- `.nipple-btn` is `position: absolute` inside `.input-row`, placed at `left: calc(100% + 20px)` — this takes it outside the flow so it doesn't affect centering
- `.stamp-area` is below the input row, starts empty

**Critical CSS for centering:**
- `.brand-title` `letter-spacing: 5.7px` — calibrated so title width = URL slot width (400px)
- `.input-content` `padding: 32px 60px 0` — calibrated for vertical centering in 800x600 pywebview window (viewport = 800x568 after 32px titlebar)
- The button must remain `position: absolute` — if changed to `relative` or `static`, it re-enters the flow, inflates `.input-row` height by 76px, and pushes the visual group ~38px above viewport center

**Element details:**
- URL input: `IBM Plex Mono`, recessed slot with inset shadow, 400px wide
- Brand title: `Playfair Display 900`, 54px, uppercase, letter-spacing 5.7px
- Stamps: `IBM Plex Mono 500`, 18px, typewriter animation (see Typewriter Engine)
- Nipple button: radial gradient red, 76px circle, 3D shadow, `position: absolute`
- Watercolor gears: SVG paths, `mix-blend-mode: multiply`, blurred, decorative only
- Sound wave: 5 bars, CSS animation during processing (bottom-right)
- Settings gear: bottom-left corner, opens overlay

### Screen 3: Reader

Clean editorial reading experience. Content is the AI analysis parsed from markdown into styled HTML by `populateReader()`.

- Section headers (`## Title`): `IBM Plex Sans Condensed 700`, 10px, uppercase, red, with bottom border
- Insight titles (`**Title**`): `IBM Plex Sans 700`, 15px
- Insight body: `Georgia`, 16px, line-height 1.72
- Date stamp: red border, `IBM Plex Mono`, rotated -2deg
- Action bar (bottom): `← New`, `Copy`, `Export .txt` — buttons with border, opacity 0.65
- Scrollable content area (`.reader-content` with `min-height: 0` for flexbox overflow fix)
- Custom thin scrollbar (6px, subtle)

### Screen 4: Library

Age-based filing system. Scans `downloads/analyses/` folder via Python API.

- Sidebar tabs: Fresh (black), Recent (blue), Settled (red), Gold (gold)
- Tab labels: vertical text (`writing-mode: vertical-rl`, rotated 180deg)
- File list: title (`IBM Plex Sans Condensed 700`) + date (`IBM Plex Mono`)
- Search bar: client-side filtering (JS `renderLibrary()` re-filters on input)
- Click entry → loads content via `get_entry()` → opens in Reader

### Age Brackets

| Tab | Age | Color | Hex |
|-----|-----|-------|-----|
| Fresh | 0-7 days | Ink Black | `#2B2B2B` |
| Recent | 8-30 days | Archive Blue | `#4A89C5` |
| Settled | 1-6 months | Accent Red | `#D1344B` |
| Gold | 6+ months | Dusty Gold | `#E5B742` |

### Navigation

| From → To | Method |
|-----------|--------|
| Input → Stamping | Click red button / Enter key |
| Stamping → Reader | Automatic (pipeline done, 800ms delay) |
| Reader → Library | Arrow Left / click nav hint (left edge) |
| Library → Reader | Arrow Right / click file entry |
| Any → Input | Escape key / `← New` button |
| Any → Settings | Click gear icon (⚙, bottom-left) |

---

## Typewriter Engine

Stamps use a character-by-character typing animation with queue management.

### Functions (in `app.js`)

| Function | Role |
|----------|------|
| `queueStampTypewriter(text)` | Adds text to queue, starts processing if idle |
| `processStampQueue()` | Dequeues next text, creates DOM element, starts typing |
| `typeText(el, text, idx, callback)` | Types one character at a time (28-50ms per char) |
| `startDots(el, base)` | After typing "Connecting...", cycles dots (`.` → `..` → `...`) every 380ms |
| `stopDots()` | Clears the cycling dots interval |
| `updateLastStampText(text)` | Updates the last stamp in-place (for progress callbacks) |
| `fadeStamps()` | Fades all stamps to opacity 0 before transitioning to Reader |

### Typing behavior

1. New stamp text enters the queue
2. If not already typing, `processStampQueue()` picks up the next item
3. A new `.stamp-line.typing` div is created (CSS adds a blinking cursor via `::after`)
4. `typeText()` writes characters one at a time with random 28-50ms delay (organic feel)
5. After typing completes, `.typing` class is removed (cursor disappears)
6. If text ends with `...`, `startDots()` begins cycling 1/2/3 dots
7. When next stamp arrives, `stopDots()` halts the current cycling
8. Pipeline progress callbacks can update the last stamp text in-place via `updateLastStampText()`

---

## Settings

Stored in two locations:
- **API key** → `.env` file (via `vault.py`)
- **Preferences** → `settings.json`

### Settings Fields

| Field | Storage | Default | Notes |
|-------|---------|---------|-------|
| OpenRouter API Key | `.env` | — | Must start with `sk-or-` |
| Language | `settings.json` | `auto` | `auto`, `pl`, `en` |
| Model | `settings.json` | `turbo` | Whisper model size |
| Context Hint | `settings.json` | — | Initial prompt for Whisper |
| Analysis Prompt | `settings.json` | (built-in 3x3) | Custom LLM prompt |

### First Run

If no API key is saved, the settings overlay opens automatically on app launch (checked in `init()` via `has_api_key()`). The pipeline will still transcribe without a key (transcript-only mode), but analysis requires the key.

---

## File Output

All output goes to `downloads/`:

```
downloads/
├── *.mp3                           # Downloaded audio files
├── transcripts/
│   └── Video_Title_20260301_2214.txt   # Raw transcriptions
└── analyses/
    └── Video_Title_analiza_20260301_2214.txt  # AI analyses
```

Filename format: `{video_title}{suffix}_{YYYYMMDD}_{HHMM}.txt`

---

## Python↔JavaScript Bridge

The `Api` class in `app.py` exposes methods to JavaScript via pywebview:

```javascript
// From ui/app.js:
window.pywebview.api.start_pipeline(url)      // → {started: bool, reason?: str}
window.pywebview.api.get_pipeline_status()     // → {step, stamps[], done, error}
window.pywebview.api.get_result()              // → {transcript, analysis}
window.pywebview.api.load_settings()           // → {api_key, language, model, ...}
window.pywebview.api.save_settings(data)       // → {saved: bool, error?: str}
window.pywebview.api.get_library(bracket)      // → [{title, date_str, path}, ...]
window.pywebview.api.get_entry(path)           // → {content} or {error}
window.pywebview.api.export_txt(text, suffix)  // → {exported: bool, filename}
window.pywebview.api.has_api_key()             // → bool
```

All calls are async (return Promises in JS). The bridge is available after the `pywebviewready` event fires.

---

## Default Analysis Prompt

The built-in 3x3 format extracts exactly 9 insights:

```
## Praktyczne tipy        (3 actionable tips)
## Inspiracje             (3 ideas/references)
## Obserwacje             (3 critical observations)
```

Each insight: `**Title** (max 8 words) + 1-2 sentences.`
Language: Polish. No introductions, no summaries.

The prompt can be fully customized in Settings. The markdown output is parsed by `populateReader()` in app.js into styled HTML.

---

## Markdown → HTML Parser

`populateReader()` in `app.js` converts LLM markdown output into editorial HTML. It processes the text line by line with the following rules (evaluated in order):

| Markdown Pattern | HTML Output | CSS Class |
|-----------------|-------------|-----------|
| `## Header` (1-3 `#`) | `<h4>` | `.section-header` |
| `**Title** body text` | `<div>` with `<span>` + `<span>` | `.insight` → `.insight-title` + `.insight-body` |
| `- **Title** body` | Same as above (bullet variant) | `.insight` |
| `1. **Title** body` | Same as above (numbered variant) | `.insight` |
| `- plain text` | `<p>` | (inherits `.article p`) |
| Plain text lines | `<p>` (consecutive lines merged) | `.article p` |
| Inline `**bold**` | `<strong>` within `<p>` | — |

**Multi-line insight bodies:** After a `**Title** body` line, the parser collects continuation lines (lines that aren't headers, new insights, bullets, or empty) and appends them to the body.

---

## Visual Design: Minimalist Archive

Brand guidelines: `brand/guidelines.md` (v0.3)

### Color Palette

| Token | Hex | CSS Variable | Usage |
|-------|-----|-------------|-------|
| BASE | `#F7E9C1` | `--base` | Manila paper background |
| RED | `#D1344B` | `--red` | Nipple button, date stamp, Settled tab |
| BLUE | `#4A89C5` | `--blue` | Recent tab |
| GOLD | `#E5B742` | `--gold` | Gold tab |
| INK | `#2B2B2B` | `--ink` | Text, Fresh tab |
| GEAR | `#C4AA78` | `--gear-color` | Watercolor gear stains |

### Typography

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| Branding | Playfair Display | 900 | "COPYSIGHT" title (54px, letter-spacing 5.7px) |
| Headers | IBM Plex Sans Condensed | 700 | Section headers (10px uppercase), file titles |
| Body | Georgia | 400 | Reader article text (16-17px, line-height 1.72-1.74) |
| UI/Meta | IBM Plex Mono | 400-500 | Stamps, dates, inputs, buttons, settings |
| Insights | IBM Plex Sans | 700 | Insight titles (15px) |

### Texture Layers

1. **Manila gradient** — multi-stop radial + linear gradient on `.window`
2. **Fine grain noise** — SVG feTurbulence at 3% opacity, `.window::before`, `mix-blend-mode: multiply`
3. **Coarse fiber** (Screen 1 only) — second noise layer at 4% opacity, `#screen-input::after`
4. **Watercolor gears** — SVG paths, blurred, `mix-blend-mode: multiply`, 3 gear shapes

---

## macOS .app Bundle

### Building

```bash
./build_app.sh
```

Creates `dist/Copysight.app` — a macOS application bundle launchable from Finder and Spotlight.

### How it works

The `.app` is a shell-script launcher, not a standalone binary. It points to the project's Python venv:

```
dist/Copysight.app/
  Contents/
    Info.plist              # Bundle metadata (com.marcinmajsawicki.copysight)
    MacOS/
      Copysight             # Bash script: cd $PROJECT && exec venv/bin/python app.py
    Resources/
      AppIcon.icns          # Generated icon (manila paper + "C" + gear)
```

The launcher script contains the absolute project path (baked in at build time). If the project directory moves, re-run `./build_app.sh`.

### Installing

```bash
cp -r dist/Copysight.app /Applications/
```

Or drag `dist/Copysight.app` to `/Applications` in Finder.

### Icon generation

`build_icon.py` generates a Minimalist Archive-style icon using Pillow:
- Manila paper background with rounded corners
- Serif "C" letter (Georgia Bold or Playfair Display if locally installed)
- Watercolor gear accent (top-right, semi-transparent)
- Red accent line and dot
- Outputs all 10 required macOS icon sizes → `.iconset` → `.icns` via `iconutil`

### Rebuilding after changes

Code changes to `app.py`, `ui/*`, or backend modules take effect immediately on next app launch (no rebuild needed — the launcher just runs `python app.py`). Only rebuild the `.app` bundle if:
- The project directory moved
- You want to update the icon
- You changed `Info.plist` metadata

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pywebview | >=5.0 | Native macOS window (WebKit) |
| yt-dlp | >=2026.2.0 | YouTube audio download |
| mlx-whisper | >=0.4.0 | Local transcription (Apple Silicon GPU) |
| openai | >=1.0.0 | OpenRouter API client |
| Pillow | (build only) | Icon generation (`build_icon.py`) |

### System Requirements

- macOS (Apple Silicon — M1/M2/M3/M4)
- Python 3.12+
- FFmpeg (`brew install ffmpeg`)

---

## Security

- API key stored in `.env` (gitignored), never in `settings.json`
- Library file access restricted to `downloads/analyses/` and `downloads/transcripts/` (path traversal protection via `os.path.realpath()` check in `get_entry()`)
- All processing local except OpenRouter API call
- No telemetry, no analytics, no network calls beyond yt-dlp and OpenRouter

---

## Known Limitations

- Window is fixed 800x600, not resizable
- No drag-and-drop for local audio files (URL-only input)
- No Obsidian export yet (planned)
- Clipboard copy uses `document.execCommand` fallback in pywebview (no secure context)
- Library shows analyses only (transcripts not browsable in UI)
- No batch processing (one video at a time)
- `.app` bundle is a launcher (requires project directory + venv in place)

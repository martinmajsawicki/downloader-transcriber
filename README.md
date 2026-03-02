# Copysight

A local-first macOS app that extracts structured insights from online videos. Paste a URL, click the red button, read the analysis. Under 2 minutes, 9 insights, zero cloud processing of your data.

Works with any video source supported by yt-dlp: YouTube, Vimeo, LinkedIn, Twitter/X, and hundreds more.

Built for Apple Silicon. Transcription runs on-device via mlx-whisper (GPU). Analysis via OpenRouter API.

## How it works

```
Paste URL → Download audio → Transcribe locally → Analyze with AI → Read
```

One click triggers the entire pipeline. Results are auto-saved as plain text files in `downloads/`.

### The 3x3 format

Every video produces exactly 9 insights in 3 categories:

- **Praktyczne tipy** — 3 actionable tips you can use immediately
- **Inspiracje** — 3 ideas, references, or mental models worth remembering
- **Obserwacje** — 3 critical observations about what works, what's overhyped, what's missing

Each insight: bold title + 1-2 sentences. No filler. The analysis prompt is fully customizable in Settings.

## Requirements

- macOS on Apple Silicon (M1/M2/M3/M4) — Intel Macs won't work (mlx-whisper requires Apple Neural Engine)
- Python 3.12+
- FFmpeg
- ~2 GB free disk space (mlx-whisper downloads the Whisper model on first run)

```bash
brew install ffmpeg
```

## Setup

```bash
git clone https://github.com/martinmajsawicki/downloader-transcriber.git
cd downloader-transcriber

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **First run note:** The first transcription will download the Whisper model (~1.5 GB). This is a one-time download. Subsequent runs start instantly.

## Usage

### Run directly

```bash
venv/bin/python app.py
```

### Build macOS app (Spotlight/Finder)

```bash
./build_app.sh
```

Creates `dist/Copysight.app`. Double-click to launch, or install:

```bash
cp -r dist/Copysight.app /Applications/
```

The `.app` is a launcher that points to the project venv. Code changes take effect on next launch (no rebuild needed). Rebuild only if the project directory moves.

### First launch

A native macOS window opens (800x600). On first launch, Settings will open automatically for you to enter your OpenRouter API key.

Without an API key, the app still downloads and transcribes — you just won't get the AI analysis.

### API Key

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Generate a key (starts with `sk-or-`)
3. Paste in Settings (gear icon, bottom-left corner)
4. Click Done — key is stored locally in `.env`

Model: Gemini 2.0 Flash — $0.10/$0.40 per 1M tokens. A typical video analysis costs < $0.01.

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| Enter | Start pipeline (when URL is focused) |
| Escape | Cancel pipeline / return to Input / close Settings |
| ← | Input → Library / Reader → Library |
| → | Library → Reader |

## Architecture

```
app.py              PyWebView entry point + Python API (bridge)
downloader.py       yt-dlp wrapper (any video source → MP3)
transcriber.py      mlx-whisper (local, Apple Silicon GPU, fp16)
analyzer.py         OpenRouter API client (Gemini 2.0 Flash)
vault.py            API key read/write (.env)
ui/
  index.html        Single Page Application (4 screens)
  styles.css        Minimalist Archive visual theme
  app.js            Navigation, pipeline bridge, library
brand/
  guidelines.md     Brand guidelines v0.3
build_app.sh        macOS .app bundle builder
build_icon.py       App icon generator (Pillow → .icns)
```

### Data flow

```
JS (urlInput) → pywebview bridge → Api.start_pipeline(url)
                                      ↓ background thread
                                   downloader → transcriber → analyzer
                                      ↓ polling every 500ms
JS (pollPipelineStatus) ← Api.get_pipeline_status()
                                      ↓ done
JS (populateReader) ← Api.get_result() {transcript, analysis, meta}
```

### Output files

```
downloads/
  *.mp3                                        Audio files
  transcripts/
    Video_Title_20260301_2214.txt               Raw transcription
  analyses/
    <!-- source: https://... -->
    Video_Title_analiza_20260301_2214.txt        AI analysis
```

Analysis files include a source URL comment on the first line.

## The Library

Past results are organized by age — like patina on paper:

| Tab | Age | Color |
|-----|-----|-------|
| **Fresh** | Last 7 days | Black |
| **Recent** | 8-30 days | Blue |
| **Settled** | 1-6 months | Red |
| **Gold** | 6+ months | Gold |

Files move between tabs automatically as they age. Transcript-only entries (no API key) appear with a "T" badge. Each tab shows its entry count.

## Design

Visual direction: **Minimalist Archive** — manila paper texture, watercolor gear stains, typewriter stamps, editorial serif typography. Screens 1-2 (input) are tactile and skeuomorphic. Screens 3-4 (reading/archive) are clean and typographic.

Full design system documented in `brand/guidelines.md`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ffmpeg: command not found` | `brew install ffmpeg` and restart terminal |
| Transcription crashes on Intel Mac | Not supported — mlx-whisper requires Apple Silicon |
| "Error: Could not extract video info" | URL may be unsupported, private, or geo-restricted |
| First transcription is slow | Normal — downloading Whisper model (~1.5 GB). One-time only. |
| Window doesn't appear | Check if another instance is running. Kill it: `pkill -f "python.*app.py"` |
| API key rejected | Must start with `sk-or-`. Get one at [openrouter.ai](https://openrouter.ai) |

## CLI usage (individual modules)

Each backend module works standalone:

```bash
# Download only (any yt-dlp supported URL)
python downloader.py "https://youtube.com/watch?v=..."
python downloader.py "https://vimeo.com/123456789"

# Transcribe only
python transcriber.py path/to/audio.mp3 auto turbo

# Analyze only (requires API key in .env)
python analyzer.py  # (imported as module)
```

## License

Private project. Marcin Majsawicki.

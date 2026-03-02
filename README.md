# Copysight

A local-first macOS app that extracts structured insights from YouTube videos. Paste a URL, click the red button, read the analysis. Under 2 minutes, 9 insights, zero cloud processing of your data.

Built for Apple Silicon. Transcription runs on-device via mlx-whisper (GPU). Analysis via OpenRouter API.

## How it works

```
Paste URL → Download audio → Transcribe locally → Analyze with AI → Read
```

One click triggers the entire pipeline. Results are saved as plain text files in `downloads/`.

### The 3x3 format

Every video produces exactly 9 insights in 3 categories:

- **Praktyczne tipy** — 3 actionable tips you can use immediately
- **Inspiracje** — 3 ideas, references, or mental models worth remembering
- **Obserwacje** — 3 critical observations about what works, what's overhyped, what's missing

Each insight: bold title + 1-2 sentences. No filler. The analysis prompt is fully customizable in Settings.

## Requirements

- macOS on Apple Silicon (M1/M2/M3/M4)
- Python 3.12+
- FFmpeg

```bash
brew install ffmpeg
```

## Setup

```bash
git clone <repo-url>
cd downloader-transcriber

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

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
| ← | Reader → Library |
| → | Library → Reader |
| Escape | Return to Input / close Settings |

## Architecture

```
app.py              PyWebView entry point + Python API
downloader.py       yt-dlp wrapper (YouTube → MP3)
transcriber.py      mlx-whisper (local, Apple Silicon GPU, fp16)
analyzer.py         OpenRouter API client (Gemini 2.0 Flash)
vault.py            API key read/write (.env)
ui/
  index.html        Single Page Application (3 screens)
  styles.css        Minimalist Archive visual theme
  app.js            Navigation, pipeline bridge, library
brand/
  guidelines.md     Brand guidelines v0.3
build_app.sh        macOS .app bundle builder
build_icon.py       App icon generator (Pillow → .icns)
```

### Output files

```
downloads/
  *.mp3                              Audio files
  transcripts/
    Video_Title_20260301_2214.txt     Raw transcription
  analyses/
    Video_Title_analiza_20260301_2214.txt   AI analysis
```

## The Library

Past analyses are organized by age — like patina on paper:

| Tab | Age | Color |
|-----|-----|-------|
| **Fresh** | Last 7 days | Black |
| **Recent** | 8-30 days | Blue |
| **Settled** | 1-6 months | Red |
| **Gold** | 6+ months | Gold |

Files move between tabs automatically as they age.

## Design

Visual direction: **Minimalist Archive** — manila paper texture, watercolor gear stains, typewriter stamps, editorial serif typography. Screens 1-2 (input) are tactile and skeuomorphic. Screens 3-4 (reading/archive) are clean and typographic.

Full design system documented in `brand/guidelines.md`. Technical documentation in `DOCS.md`.

## CLI usage (individual modules)

Each backend module works standalone:

```bash
# Download only
python downloader.py "https://youtube.com/watch?v=..."

# Transcribe only
python transcriber.py path/to/audio.mp3 auto turbo

# Analyze only (requires API key in .env)
python analyzer.py  # (imported as module)
```

## License

Private project. Marcin Majsawicki.

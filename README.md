# Audio Studio (dTr)

A macOS desktop app for downloading YouTube audio, transcribing it locally with OpenAI Whisper, and analyzing the text with AI.

## Features

- **Audio download** from YouTube (yt-dlp) to MP3
- **Local transcription** with OpenAI Whisper (base / small / medium)
- **AI analysis** of transcripts via Gemini 2.0 Flash on OpenRouter
- **Export** raw transcription and AI analysis to `.txt`
- **One-click copy** to clipboard
- **Step tracker** with visual pipeline status
- **API key vault** stored in `.env`

## Requirements

- Python 3.12+
- FFmpeg (required by yt-dlp and Whisper)
- macOS (tested on ARM64 / Apple Silicon)

## Setup

```bash
git clone https://github.com/martinmajsawicki/downloader-transcriber.git
cd downloader-transcriber

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### FFmpeg

```bash
brew install ffmpeg
```

## Usage

```bash
source venv/bin/activate
python app.py
```

The app opens a 1060x700 window with a two-panel layout:
- **Sidebar** (left) — URL input, language/model settings, AI prompt, API key, step tracker
- **Main area** (right) — Transcription / Analysis tabs with copy and export controls

## Building .app (macOS)

```bash
pip install pyinstaller

flet pack app.py \
  -i assets/icon.icns \
  -n "Audio Studio" \
  --product-name "Audio Studio" \
  --bundle-id "com.marcinmajsawicki.audiostudio" \
  --add-data "assets:assets" \
  --add-data "downloader.py:." \
  --add-data "transcriber.py:." \
  --add-data "analyzer.py:." \
  --add-data "vault.py:." \
  -y

# Output: dist/Audio Studio.app
cp -R "dist/Audio Studio.app" /Applications/
```

## Architecture

```
app.py            # UI (Flet 0.81) — layout, logic, step tracker
downloader.py     # yt-dlp wrapper — returns MP3 path
transcriber.py    # Whisper wrapper — auto fp16, log_fn callback
analyzer.py       # OpenRouter client (OpenAI SDK) — Gemini 2.0 Flash
vault.py          # API key read/write to .env
assets/
  icon.png        # App icon (512x512 PNG)
  icon.icns       # macOS icon (iconset)
```

## API Key

The AI analysis feature requires an OpenRouter API key:

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Generate an API key (prefix `sk-or-...`)
3. Paste it in the "OpenRouter Key" field in the sidebar
4. Click the save icon — the key is stored in `.env`

Model: `google/gemini-2.0-flash-001` ($0.10 / $0.40 per 1M tokens)

## License

Private project.

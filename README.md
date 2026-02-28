# Audio Studio (dTr)

Desktopowa aplikacja macOS do pobierania audio z YouTube, transkrypcji lokalnym modelem Whisper i analizy tekstu przez AI.

## Funkcje

- **Pobieranie audio** z YouTube (yt-dlp) do MP3
- **Transkrypcja lokalna** modelem OpenAI Whisper (base / small / medium)
- **Analiza AI** transkrypcji przez Gemini 2.0 Flash via OpenRouter
- **Eksport** surowej transkrypcji i opracowania do `.txt`
- **Kopiowanie** do schowka jednym klikiem
- **Step tracker** z wizualnym statusem pipeline'u
- **Vault** na klucz API OpenRouter (`.env`)

## Wymagania

- Python 3.12+
- FFmpeg (wymagany przez yt-dlp i Whisper)
- macOS (testowane na ARM64 / Apple Silicon)

## Instalacja

```bash
# Klonowanie
git clone <repo-url>
cd downloader-transcriber

# Virtualenv
python -m venv venv
source venv/bin/activate

# Zależności
pip install -r requirements.txt
```

### FFmpeg

```bash
brew install ffmpeg
```

## Uruchamianie

```bash
source venv/bin/activate
python app.py
```

Aplikacja otworzy okno 1060x700 z dwupanelowym layoutem:
- **Sidebar** (lewy) — URL, ustawienia, prompt AI, klucz API, step tracker
- **Main area** (prawy) — zakładki Transkrypcja / Opracowanie

## Budowanie .app (macOS)

```bash
# Wymagane jednorazowo
pip install pyinstaller

# Build
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

# Wynik w dist/Audio Studio.app
cp -R "dist/Audio Studio.app" /Applications/
```

## Architektura

```
app.py            # UI (Flet 0.81) — layout, logika, step tracker
downloader.py     # yt-dlp wrapper — zwraca sciezke MP3
transcriber.py    # Whisper wrapper — auto fp16, log_fn callback
analyzer.py       # OpenRouter client (OpenAI SDK) — Gemini 2.0 Flash
vault.py          # Zapis/odczyt klucza API z .env
assets/
  icon.png        # Ikona aplikacji (512x512 PNG)
  icon.icns       # Ikona macOS (iconset)
```

## Klucz API

Aplikacja wymaga klucza OpenRouter do funkcji "Opracuj z AI":

1. Zarejestruj sie na [openrouter.ai](https://openrouter.ai)
2. Wygeneruj klucz API (prefix `sk-or-...`)
3. Wklej w pole "Klucz OpenRouter" w sidebarze
4. Kliknij ikone zapisu — klucz zostanie zapisany w `.env`

Model: `google/gemini-2.0-flash-001` ($0.10 / $0.40 za 1M tokenow)

## Licencja

Projekt prywatny.

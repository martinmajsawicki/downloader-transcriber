import yt_dlp
import sys
import os


def download_audio_as_mp3(url, output_path="downloads", log_fn=print):
    """
    Pobiera wideo z podanego URL i konwertuje je na format MP3.
    Zwraca ścieżkę do pobranego pliku MP3 lub None w razie błędu.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    log_fn(f"Rozpoczynam pobieranie audio z: {url}")

    downloaded_file = None

    def progress_hook(d):
        nonlocal downloaded_file
        if d['status'] == 'finished':
            # yt-dlp podaje ścieżkę przed post-processing (jeszcze nie .mp3)
            downloaded_file = d.get('info_dict', {}).get('title', '')

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([url])
            if error_code == 0 and downloaded_file:
                mp3_path = os.path.join(output_path, downloaded_file + ".mp3")
                if os.path.exists(mp3_path):
                    log_fn(f"✅ Pobieranie zakończone: {mp3_path}")
                    return mp3_path
                # Fallback: szukaj po tytule (znaki specjalne w nazwie)
                log_fn(f"⚠️ Oczekiwany plik nie znaleziony, szukam w {output_path}...")
                for f in os.listdir(output_path):
                    if f.endswith('.mp3') and downloaded_file[:20] in f:
                        mp3_path = os.path.join(output_path, f)
                        log_fn(f"✅ Znaleziono plik: {mp3_path}")
                        return mp3_path
            log_fn(f"❌ Błąd pobierania (kod: {error_code}).")
            return None
    except Exception as e:
        log_fn(f"❌ Wystąpił błąd: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python downloader.py <URL_YouTube>")
        print("Przykład: python downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    url = sys.argv[1]
    result = download_audio_as_mp3(url)
    if result:
        print(f"Plik: {result}")
    else:
        print("Pobieranie nie powiodło się.")

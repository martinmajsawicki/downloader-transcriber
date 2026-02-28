import yt_dlp
import sys
import os


def download_audio_as_mp3(url, output_path="downloads", log_fn=print):
    """
    Download audio from a given URL and convert it to MP3.
    Returns the path to the downloaded MP3 file, or None on error.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    log_fn(f"Starting audio download from: {url}")

    downloaded_file = None

    def progress_hook(d):
        nonlocal downloaded_file
        if d['status'] == 'finished':
            # yt-dlp reports path before post-processing (not yet .mp3)
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
                    log_fn(f"Download complete: {mp3_path}")
                    return mp3_path
                # Fallback: search by title (special characters in filename)
                log_fn(f"Expected file not found, searching in {output_path}...")
                for f in os.listdir(output_path):
                    if f.endswith('.mp3') and downloaded_file[:20] in f:
                        mp3_path = os.path.join(output_path, f)
                        log_fn(f"Found file: {mp3_path}")
                        return mp3_path
            log_fn(f"Download error (code: {error_code}).")
            return None
    except Exception as e:
        log_fn(f"Error: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <YouTube_URL>")
        print("Example: python downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    url = sys.argv[1]
    result = download_audio_as_mp3(url)
    if result:
        print(f"File: {result}")
    else:
        print("Download failed.")

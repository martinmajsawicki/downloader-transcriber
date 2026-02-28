import yt_dlp
import sys
import os
import glob
import re


def _normalize_youtube_url(url):
    """Extract video ID from any YouTube URL format and return a clean watch URL.
    Strips playlist params, tracking tokens, timestamps, and other noise.
    Returns the original URL unchanged if it's not a recognized YouTube URL."""
    url = url.strip()
    pattern = r'(?:youtube\.com/watch\?.*?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url


def download_audio_as_mp3(url, output_path="downloads", log_fn=print, progress_fn=None):
    """
    Download audio from a given URL and convert it to MP3.
    Returns the path to the downloaded MP3 file, or None on error.

    :param progress_fn: Optional callback(percent, msg) for live progress.
                        percent: 0-100 float, msg: human-readable status string.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Normalize URL — strip playlist params, tracking tokens, etc.
    url = _normalize_youtube_url(url)
    log_fn(f"Starting audio download from: {url}")

    # Snapshot existing mp3 files before download (for reliable new-file detection)
    existing_mp3s = set(glob.glob(os.path.join(output_path, "*.mp3")))

    downloaded_title = None

    def progress_hook(d):
        nonlocal downloaded_title
        try:
            if d['status'] == 'downloading' and progress_fn:
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    pct = (downloaded / total) * 100
                    speed = d.get('speed')
                    speed_str = f" · {speed / 1024 / 1024:.1f} MB/s" if speed else ""
                    progress_fn(pct, f"{pct:.0f}%{speed_str}")
            elif d['status'] == 'finished':
                # Capture title before post-processing (not yet .mp3)
                downloaded_title = d.get('info_dict', {}).get('title', '')
                if progress_fn:
                    progress_fn(100, "Converting to MP3...")
        except Exception as e:
            log_fn(f"Progress hook error: {e}")

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
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        # Enable EJS challenge solver for YouTube anti-bot bypass
        'remote_components': ['ejs:github'],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([url])

            if error_code != 0:
                log_fn(f"yt-dlp returned error code {error_code}")
                return None

            # Strategy 1: Match by title from progress hook
            if downloaded_title:
                mp3_path = os.path.join(output_path, downloaded_title + ".mp3")
                if os.path.exists(mp3_path):
                    log_fn(f"Download complete: {mp3_path}")
                    return mp3_path

                # Title may differ from sanitized filename — search by prefix
                prefix = downloaded_title[:30]
                for f in os.listdir(output_path):
                    if f.endswith('.mp3') and prefix in f:
                        mp3_path = os.path.join(output_path, f)
                        log_fn(f"Found file (by prefix): {mp3_path}")
                        return mp3_path

            # Strategy 2: Find the newest mp3 file that didn't exist before
            current_mp3s = set(glob.glob(os.path.join(output_path, "*.mp3")))
            new_files = current_mp3s - existing_mp3s
            if new_files:
                mp3_path = max(new_files, key=os.path.getmtime)
                log_fn(f"Found new file: {mp3_path}")
                return mp3_path

            # Strategy 3: Find most recently modified mp3 (re-download of existing file)
            all_mp3 = glob.glob(os.path.join(output_path, "*.mp3"))
            if all_mp3:
                mp3_path = max(all_mp3, key=os.path.getmtime)
                # Only accept if modified in the last 60 seconds
                if os.path.getmtime(mp3_path) > (os.path.getmtime(__file__) - 60):
                    import time
                    if time.time() - os.path.getmtime(mp3_path) < 60:
                        log_fn(f"Found recent file: {mp3_path}")
                        return mp3_path

            log_fn("Download finished but mp3 file not found.")
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
    result = download_audio_as_mp3(url, progress_fn=lambda pct, msg: print(f"  [{msg}]"))
    if result:
        print(f"File: {result}")
    else:
        print("Download failed.")

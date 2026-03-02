import yt_dlp
import sys
import os
import re
import time


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


def _format_duration(seconds):
    """Format seconds as M:SS or H:MM:SS."""
    if not seconds or seconds <= 0:
        return ""
    seconds = int(seconds)
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h}:{m:02d}:{s:02d}"
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def _extract_meta(info, url):
    """Extract generic metadata dict from yt-dlp info (works for any source)."""
    return {
        "title": info.get("title", ""),
        "channel": info.get("uploader") or info.get("channel") or "",
        "duration": _format_duration(info.get("duration")),
        "url": info.get("webpage_url") or url,
        "source": info.get("extractor", ""),
    }


def download_audio_as_mp3(url, output_path="downloads", log_fn=print, progress_fn=None):
    """
    Download audio from a given URL and convert it to MP3.
    Returns {"mp3": path, "meta": {...}} on success, or None on error.

    Meta dict contains: title, channel, duration, url, source.
    Works with any yt-dlp supported site (YouTube, Vimeo, LinkedIn, etc.).

    :param progress_fn: Optional callback(percent, msg) for live progress.
                        percent: 0-100 float, msg: human-readable status string.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Normalize URL — strip playlist params, tracking tokens, etc.
    url = _normalize_youtube_url(url)
    log_fn(f"Starting audio download from: {url}")

    def progress_hook(d):
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
                if progress_fn:
                    progress_fn(100, "Converting to MP3...")
        except Exception as e:
            log_fn(f"Progress hook error: {e}")

    # Custom logger to route yt-dlp messages through log_fn
    class YdlLogger:
        def debug(self, msg):
            pass
        def info(self, msg):
            pass
        def warning(self, msg):
            log_fn(f"Warning: {msg}")
        def error(self, msg):
            log_fn(f"Error: {msg}")

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
        'logger': YdlLogger(),
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'retries': 5,
        'fragment_retries': 10,
        'socket_timeout': 30,
        'extractor_args': {'youtube': {'player_client': ['default']}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Step 1: Extract info to get the expected filename
            info = ydl.extract_info(url, download=False)
            if not info:
                log_fn("Error: Could not extract video info")
                return None

            # Compute the expected mp3 path (yt-dlp sanitizes the filename)
            info['ext'] = 'mp3'
            expected_mp3 = ydl.prepare_filename(info)

            meta = _extract_meta(info, url)

            # Step 2: If mp3 already exists → return it (same video, same file)
            if os.path.exists(expected_mp3):
                log_fn(f"Already downloaded: {os.path.basename(expected_mp3)}")
                return {"mp3": expected_mp3, "meta": meta}

            # Step 3: Download and convert
            error_code = ydl.download([url])
            if error_code != 0:
                log_fn(f"Error: yt-dlp returned error code {error_code}")
                return None

            # Step 4: Find the resulting mp3
            mp3_path = None
            if os.path.exists(expected_mp3):
                mp3_path = expected_mp3
            else:
                # Fallback: scan for recently created mp3
                for f in os.listdir(output_path):
                    if f.endswith('.mp3'):
                        fpath = os.path.join(output_path, f)
                        if time.time() - os.path.getmtime(fpath) < 120:
                            mp3_path = fpath
                            break

            if not mp3_path:
                log_fn("Error: Download finished but mp3 file not found")
                return None

            log_fn(f"Download complete: {mp3_path}")
            return {"mp3": mp3_path, "meta": meta}

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
        print(f"File: {result['mp3']}")
        for k, v in result['meta'].items():
            if v:
                print(f"  {k}: {v}")
    else:
        print("Download failed.")

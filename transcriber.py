import sys
import os
import subprocess


# Model name mapping: UI key → HuggingFace repo (MLX-optimized)
_MLX_MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
    "turbo": "mlx-community/whisper-large-v3-turbo",
}


def _get_audio_duration(audio_path):
    """Get audio duration in seconds using ffprobe. Returns None on failure."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def _format_duration(seconds):
    """Format seconds as M:SS or H:MM:SS."""
    seconds = int(seconds)
    if seconds >= 3600:
        h, rest = divmod(seconds, 3600)
        m, s = divmod(rest, 60)
        return f"{h}:{m:02d}:{s:02d}"
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def transcribe_audio(audio_path, language=None, model_size="turbo", initial_prompt=None,
                     log_fn=print, phase_fn=None):
    """
    Transcribe an audio file using mlx-whisper (Apple Silicon GPU via MLX).
    Runs in fp16 on the M-series GPU — ~3-4x faster than openai-whisper on CPU.

    Models are downloaded on first use and cached in ~/.cache/huggingface/hub/.

    :param audio_path: Path to the audio file (e.g. .mp3).
    :param language: Expected language (e.g. 'pl', 'en'). If None, Whisper auto-detects.
    :param model_size: Model key ('tiny', 'base', 'small', 'medium', 'large', 'turbo').
    :param initial_prompt: Context hint to reduce hallucinations.
    :param log_fn: Logging callback (default: print).
    :param phase_fn: Optional callback(phase_str) for live UI updates.
    """
    import mlx_whisper

    def phase(msg):
        if phase_fn:
            phase_fn(msg)
        log_fn(msg)

    if not os.path.exists(audio_path):
        log_fn(f"Audio file not found: {audio_path}")
        return None

    # Resolve model HF repo
    model_repo = _MLX_MODELS.get(model_size, _MLX_MODELS["turbo"])
    model_label = model_size if model_size in _MLX_MODELS else "turbo"

    # Audio duration for progress display
    duration = _get_audio_duration(audio_path)
    duration_str = _format_duration(duration) if duration else None

    if duration_str:
        phase(f"Transcribing {duration_str} ({model_label})")
    else:
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        phase(f"Transcribing {file_size_mb:.0f} MB ({model_label})")

    # Build decode options
    decode_options = {}
    if language and language.lower() not in ['auto', 'none', '']:
        decode_options["language"] = language
        log_fn(f"Language forced: {language}")
    else:
        log_fn("Auto-detecting language")

    if initial_prompt:
        decode_options["initial_prompt"] = initial_prompt

    log_fn(f"Engine: mlx-whisper · {model_repo} · fp16")

    try:
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=model_repo,
            fp16=True,
            **decode_options,
        )
        lang = result.get('language', '?')
        phase(f"Done — {lang}")
        return result["text"]
    except Exception as e:
        log_fn(f"Transcription error: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <audio_file> [language] [model] [prompt]")
        sys.exit(1)

    audio_file = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "auto"
    mod_size = sys.argv[3] if len(sys.argv) > 3 else "turbo"
    prompt = sys.argv[4] if len(sys.argv) > 4 else None

    text = transcribe_audio(audio_file, language=lang, model_size=mod_size, initial_prompt=prompt)

    if text:
        print("\n--- TRANSCRIPTION RESULT ---")
        print(text.strip()[:500] + "...\n(rest saved to txt file)")
        print("----------------------------")

        result_path = os.path.splitext(audio_file)[0] + ".txt"
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {result_path}")

import whisper
import torch
import sys
import os


def transcribe_audio(audio_path, language=None, model_size="base", initial_prompt=None, log_fn=print):
    """
    Transcribe an audio file using a local Whisper model.

    :param audio_path: Path to the audio file (e.g. .mp3).
    :param language: Expected language (e.g. 'pl', 'en'). If None, Whisper auto-detects.
    :param model_size: Model size ('tiny', 'base', 'small', 'medium', 'large').
    :param initial_prompt: Context hint to reduce hallucinations.
    :param log_fn: Logging callback (default: print).
    """
    if not os.path.exists(audio_path):
        log_fn(f"Audio file not found: {audio_path}")
        return None

    log_fn(f"Loading Whisper model ({model_size})...")
    try:
        model = whisper.load_model(model_size)
    except Exception as e:
        log_fn(f"Model loading error: {e}")
        return None

    log_fn(f"Transcribing: {os.path.basename(audio_path)}")

    decode_options = {}
    if language and language.lower() not in ['auto', 'none', '']:
        decode_options["language"] = language
        log_fn(f"Language forced: {language}")
    else:
        log_fn("Auto-detecting language")

    if initial_prompt:
        decode_options["initial_prompt"] = initial_prompt
        log_fn(f"Initial prompt: '{initial_prompt[:60]}...'") if len(initial_prompt) > 60 else log_fn(f"Initial prompt: '{initial_prompt}'")

    use_fp16 = torch.cuda.is_available()
    log_fn(f"FP16: {'yes (GPU)' if use_fp16 else 'no (CPU)'}")

    try:
        result = model.transcribe(audio_path, fp16=use_fp16, **decode_options)
        log_fn(f"Transcription complete. Language: {result.get('language', '?')}")
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
    mod_size = sys.argv[3] if len(sys.argv) > 3 else "base"
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

import whisper
import torch
import sys
import os


def transcribe_audio(audio_path, language=None, model_size="base", initial_prompt=None, log_fn=print):
    """
    Transkrybuje plik audio przy użyciu lokalnego modelu Whisper.

    :param audio_path: Ścieżka do pliku audio (np. .mp3)
    :param language: Oczekiwany język (np. 'pl', 'en'). Jeśli None, Whisper wykrywa automatycznie.
    :param model_size: Rozmiar modelu ('tiny', 'base', 'small', 'medium', 'large').
    :param initial_prompt: Kontekst pomagający uniknąć halucynacji.
    :param log_fn: Funkcja logująca (domyślnie print).
    """
    if not os.path.exists(audio_path):
        log_fn(f"❌ Plik audio nie istnieje: {audio_path}")
        return None

    log_fn(f"Ładowanie modelu Whisper ({model_size})...")
    try:
        model = whisper.load_model(model_size)
    except Exception as e:
        log_fn(f"❌ Błąd ładowania modelu: {e}")
        return None

    log_fn(f"Transkrypcja: {os.path.basename(audio_path)}")

    decode_options = {}
    if language and language.lower() not in ['auto', 'none', '']:
        decode_options["language"] = language
        log_fn(f"Język wymuszony: {language}")
    else:
        log_fn("Automatyczne wykrywanie języka")

    if initial_prompt:
        decode_options["initial_prompt"] = initial_prompt
        log_fn(f"Initial prompt: '{initial_prompt[:60]}...'") if len(initial_prompt) > 60 else log_fn(f"Initial prompt: '{initial_prompt}'")

    use_fp16 = torch.cuda.is_available()
    log_fn(f"FP16: {'tak (GPU)' if use_fp16 else 'nie (CPU)'}")

    try:
        result = model.transcribe(audio_path, fp16=use_fp16, **decode_options)
        log_fn(f"✅ Transkrypcja zakończona. Język: {result.get('language', '?')}")
        return result["text"]
    except Exception as e:
        log_fn(f"❌ Błąd transkrypcji: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python transcriber.py <plik_mp3> [język] [model] [prompt]")
        sys.exit(1)

    audio_file = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "auto"
    mod_size = sys.argv[3] if len(sys.argv) > 3 else "base"
    prompt = sys.argv[4] if len(sys.argv) > 4 else None

    text = transcribe_audio(audio_file, language=lang, model_size=mod_size, initial_prompt=prompt)

    if text:
        print("\n--- WYNIK TRANSKRYPCJI ---")
        print(text.strip()[:500] + "...\n(reszta w pliku txt)")
        print("--------------------------")

        wynik_path = os.path.splitext(audio_file)[0] + ".txt"
        with open(wynik_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Zapisano: {wynik_path}")

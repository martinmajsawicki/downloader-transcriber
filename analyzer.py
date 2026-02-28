"""Analiza tekstu przez OpenRouter API (domyślnie Gemini 2.0 Flash)."""

from openai import OpenAI

DEFAULT_MODEL = "google/gemini-2.0-flash-001"


def analyze_text(text: str, prompt: str, api_key: str,
                 model: str = DEFAULT_MODEL, log_fn=print) -> str | None:
    """
    Wysyła tekst do modelu LLM przez OpenRouter i zwraca opracowanie.

    :param text: Tekst źródłowy (np. transkrypcja).
    :param prompt: Instrukcja użytkownika (np. "Znajdź porady...").
    :param api_key: Klucz API OpenRouter.
    :param model: ID modelu na OpenRouter.
    :param log_fn: Callback do logowania postępu.
    :return: Tekst opracowania lub None w razie błędu.
    """
    if not api_key:
        log_fn("Brak klucza API.")
        return None

    if not text:
        log_fn("Brak tekstu do analizy.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    log_fn(f"Wysyłanie do {model.split('/')[-1]}...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        result = response.choices[0].message.content
        log_fn("Odpowiedź otrzymana.")
        return result
    except Exception as e:
        log_fn(f"Błąd API: {e}")
        return None

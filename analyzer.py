"""Text analysis via OpenRouter API (default: Gemini 2.0 Flash)."""

DEFAULT_MODEL = "google/gemini-2.0-flash-001"


def analyze_text(text: str, prompt: str, api_key: str,
                 model: str = DEFAULT_MODEL, log_fn=print) -> str | None:
    """
    Send text to an LLM via OpenRouter and return the analysis.
    OpenAI SDK import is deferred to first call for faster app startup.

    :param text: Source text (e.g. a transcription).
    :param prompt: User instruction (e.g. "Find practical tips...").
    :param api_key: OpenRouter API key.
    :param model: Model ID on OpenRouter.
    :param log_fn: Progress logging callback.
    :return: Analysis text or None on error.
    """
    from openai import OpenAI

    if not api_key:
        log_fn("Missing API key.")
        return None

    if not text:
        log_fn("No text to analyze.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    log_fn(f"Sending to {model.split('/')[-1]}...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        result = response.choices[0].message.content
        log_fn("Response received.")
        return result
    except Exception as e:
        log_fn(f"API error: {e}")
        return None

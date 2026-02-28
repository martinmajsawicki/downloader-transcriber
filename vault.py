"""Prosty vault — zapis/odczyt klucza API z pliku .env."""

import os

_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def save_key(key: str) -> None:
    """Zapisz klucz API do .env."""
    lines = []
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH, "r") as f:
            lines = [l for l in f.readlines() if not l.startswith("OPENROUTER_API_KEY=")]
    lines.append(f"OPENROUTER_API_KEY={key}\n")
    with open(_ENV_PATH, "w") as f:
        f.writelines(lines)


def load_key() -> str:
    """Wczytaj klucz API z .env. Zwraca pusty string jeśli brak."""
    if not os.path.exists(_ENV_PATH):
        return ""
    with open(_ENV_PATH, "r") as f:
        for line in f:
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""

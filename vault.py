"""Simple vault — read/write API key from .env file."""

import os

_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def save_key(key: str) -> None:
    """Save the API key to .env, preserving other entries."""
    lines = []
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH, "r") as f:
            lines = [l for l in f.readlines() if not l.startswith("OPENROUTER_API_KEY=")]
    lines.append(f"OPENROUTER_API_KEY={key}\n")
    with open(_ENV_PATH, "w") as f:
        f.writelines(lines)


def load_key() -> str:
    """Load the API key from .env. Returns empty string if not found."""
    if not os.path.exists(_ENV_PATH):
        return ""
    with open(_ENV_PATH, "r") as f:
        for line in f:
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""

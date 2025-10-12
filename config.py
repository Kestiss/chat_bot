"""Central configuration helpers for the chat bot project."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Optional


def _load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _get_env(name: str, default: Optional[str] = None, *, required: bool = False) -> Optional[str]:
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise RuntimeError(
            f"Environment variable '{name}' must be set. "
            "Add it to .env or export it before running the app."
        )
    return value

# === LCD / Display configuration ===
LCD_WIDTH = int(_get_env("CHAT_LCD_WIDTH", "55"))

# === API configuration ===
GROQ_ENDPOINT = _get_env(
    "GROQ_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions"
)
GROQ_API_KEYS = {
    "bot1": _get_env("GROQ_BOT1_KEY", required=True) or "",
    "bot2": _get_env("GROQ_BOT2_KEY", required=True) or "",
}

# === Control panel credentials ===
ADMIN_USERNAME = _get_env("CHAT_ADMIN_USERNAME", required=True)
ADMIN_PASSWORD = _get_env("CHAT_ADMIN_PASSWORD", required=True)

# === Log configuration ===
LOG_MAX_LINES = int(_get_env("CHAT_LOG_MAX_LINES", "200"))

# === Default conversation / scheduler settings ===
_DEFAULT_TOPIC = _get_env("CHAT_DEFAULT_TOPIC", "Who are you?")
_DEFAULT_MODEL = _get_env("CHAT_DEFAULT_MODEL", "gemma2-9b-it")
_DEFAULT_FIRST_SPEAKER = _get_env("CHAT_DEFAULT_FIRST", "bot1")
_DEFAULT_MAX_TURNS = int(_get_env("CHAT_DEFAULT_MAX_TURNS", "0"))
_DEFAULT_DELAY = float(_get_env("CHAT_DEFAULT_DELAY", "20"))
_DEFAULT_TYPING_SPEED = float(_get_env("CHAT_DEFAULT_TYPING_SPEED", "0.01"))
_DEFAULT_CONTEXT_LIMIT = int(_get_env("CHAT_DEFAULT_CONTEXT", "6"))
_DEFAULT_START_HOUR = _get_env("CHAT_DEFAULT_START_HOUR")
_DEFAULT_START_MINUTE = _get_env("CHAT_DEFAULT_START_MINUTE")
_DEFAULT_STOP_HOUR = _get_env("CHAT_DEFAULT_STOP_HOUR")
_DEFAULT_STOP_MINUTE = _get_env("CHAT_DEFAULT_STOP_MINUTE")


def _parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_control_defaults() -> Dict[str, Any]:
    """Return a mutable dict with the default control panel settings."""
    return {
        "topic": _DEFAULT_TOPIC,
        "first_speaker": _DEFAULT_FIRST_SPEAKER,
        "model": _DEFAULT_MODEL,
        "max_turns": _DEFAULT_MAX_TURNS,
        "delay": _DEFAULT_DELAY,
        "typing_speed": _DEFAULT_TYPING_SPEED,
        "context_limit": _DEFAULT_CONTEXT_LIMIT,
        "start_hour": _parse_optional_int(_DEFAULT_START_HOUR) or 14,
        "start_minute": _parse_optional_int(_DEFAULT_START_MINUTE) or 54,
        "stop_hour": _parse_optional_int(_DEFAULT_STOP_HOUR) or 14,
        "stop_minute": _parse_optional_int(_DEFAULT_STOP_MINUTE) or 58,
    }


__all__ = [
    "LCD_WIDTH",
    "GROQ_ENDPOINT",
    "GROQ_API_KEYS",
    "ADMIN_USERNAME",
    "ADMIN_PASSWORD",
    "LOG_MAX_LINES",
    "load_control_defaults",
]

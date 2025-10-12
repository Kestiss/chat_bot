"""Simple Groq-powered two-bot conversation loop with terminal output."""

from __future__ import annotations

import argparse
import sys
import textwrap
import time
from typing import Dict, List

import requests

from config import LCD_WIDTH, GROQ_API_KEYS, GROQ_ENDPOINT

GREEN = "\033[92m"
RESET = "\033[0m"
CLEAR = "\033c"


class MultiOutput:
    """Mirror writes to multiple file-like objects."""

    def __init__(self, *targets):
        self.targets = targets

    def write(self, message: str) -> None:
        for target in self.targets:
            try:
                target.write(message)
                target.flush()
            except Exception:
                continue

    def flush(self) -> None:
        for target in self.targets:
            try:
                target.flush()
            except Exception:
                continue


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Groq chat loop between two bots.")
    parser.add_argument("topic", nargs="?", default="Default topic")
    parser.add_argument("first_speaker", nargs="?", default="bot1")
    parser.add_argument("model", nargs="?", default="groq/compound-mini")
    parser.add_argument("max_turns", nargs="?", type=int, default=10)
    parser.add_argument("delay", nargs="?", type=float, default=1.2)
    parser.add_argument("typing_speed", nargs="?", type=float, default=0.015)
    parser.add_argument("context_limit", nargs="?", type=int, default=6)
    parser.add_argument("temperature", nargs="?", type=float, default=0.3)
    return parser.parse_args(argv)


def setup_outputs() -> None:
    try:
        lcd = open("/dev/tty1", "w")
        sys.stdout = MultiOutput(sys.__stdout__, lcd)
        sys.stderr = MultiOutput(sys.__stderr__, lcd)
    except Exception as exc:
        print(f"[Warning] Could not open /dev/tty1: {exc}")


def build_initial_conversation(topic: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an AI model engaging in a friendly and thoughtful conversation "
                f"with another AI about: {topic}. Keep your responses brief (1-5 sentences)."
            ),
        },
        {"role": "user", "content": f"Let's start our conversation about {topic}."},
    ]


def ensure_api_keys() -> None:
    missing = [bot for bot, key in GROQ_API_KEYS.items() if not key]
    if missing:
        raise RuntimeError(
            "Missing GROQ API keys for: " + ", ".join(missing) + ". "
            "Set GROQ_BOT1_KEY / GROQ_BOT2_KEY environment variables."
        )


def wrap_text(text: str, width: int) -> List[str]:
    return textwrap.wrap(text, width=width, break_long_words=True, break_on_hyphens=False)


def type_text(text: str, speaker_name: str, typing_speed: float) -> None:
    prefix = f"{GREEN}[{speaker_name}]:{RESET}"
    margin = "  "
    wrapped = wrap_text(text, LCD_WIDTH)

    sys.stdout.write(prefix + "\n")
    sys.stdout.flush()

    for line in wrapped:
        sys.stdout.write(margin)
        for char in line:
            sys.stdout.write(GREEN + char + RESET)
            sys.stdout.flush()
            time.sleep(typing_speed)
        sys.stdout.write("\n")
    sys.stdout.flush()


def chat_turn(
    conversation: List[Dict[str, str]],
    model: str,
    api_key: str,
    context_limit: int,
    temperature: float,
) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    context = conversation[-context_limit:]

    if context and context[-1]["role"] == "assistant":
        context.append({"role": "user", "content": context[-1]["content"]})

    body = {"model": model, "messages": context, "temperature": temperature}

    response = requests.post(GROQ_ENDPOINT, headers=headers, json=body)
    if not response.ok:
        print(f"[Groq error] {response.status_code}: {response.text}")
    response.raise_for_status()
    reply = response.json()["choices"][0]["message"]
    reply_content = reply.get("content", "").strip() or "(no response)"
    conversation.append({"role": "assistant", "content": reply_content})
    return reply_content


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    ensure_api_keys()
    setup_outputs()

    print(CLEAR)
    print(GREEN + "╔══════════════════════════════╗")
    print("║  AI CONVERSATION TERMINAL    ║")
    print("╚══════════════════════════════╝" + RESET)
    print()

    conversation = build_initial_conversation(args.topic)
    turn = 0

    while True:
        expects_bot1 = (turn % 2 == 0)
        current_bot = "bot1" if expects_bot1 == (args.first_speaker == "bot1") else "bot2"
        bot_label = "Bot 1" if current_bot == "bot1" else "Bot 2"

        try:
            reply = chat_turn(
                conversation,
                args.model,
                GROQ_API_KEYS[current_bot],
                max(args.context_limit, 1),
                args.temperature,
            )
            type_text(reply, bot_label, args.typing_speed)
            print(GREEN + "─" * LCD_WIDTH + RESET)
        except Exception as exc:  # noqa: BLE001 broad catch to keep loop alive
            type_text(f"[ERROR] {exc}", bot_label, args.typing_speed)

        time.sleep(args.delay)
        turn += 1
        if args.max_turns > 0 and turn >= args.max_turns:
            break


if __name__ == "__main__":
    main()

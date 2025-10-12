from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

from chat_runner import ChatRunner
from config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    LOG_MAX_LINES,
    load_control_defaults,
)
from log_buffer import LogBuffer
from scheduler import ChatScheduler

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static")
)

log_buffer = LogBuffer(LOG_MAX_LINES)
control_config: Dict[str, Any] = load_control_defaults()
chat_runner = ChatRunner(log_buffer)
chat_scheduler = ChatScheduler(chat_runner, control_config)
is_authenticated = False


def _update_config_from_form(form_data: Dict[str, str]) -> List[str]:
    warnings: List[str] = []
    for key in control_config:
        if key in form_data:
            raw_value = form_data[key]
            try:
                if key in {"max_turns", "context_limit"}:
                    control_config[key] = int(raw_value)
                elif key in {"delay", "typing_speed", "temperature"}:
                    control_config[key] = float(raw_value)
                elif key in {"start_hour", "start_minute", "stop_hour", "stop_minute"}:
                    control_config[key] = int(raw_value) if raw_value != "" else None
                else:
                    control_config[key] = raw_value
            except ValueError:
                warnings.append(f"Invalid input for {key}.")
    return warnings


@app.route("/", methods=["GET", "POST"])
def control() -> str:
    global is_authenticated

    if not is_authenticated or request.form.get("action") == "logout":
        if request.method == "POST" and request.form.get("action") == "logout":
            chat_runner.stop()
            is_authenticated = False
            return render_template("login.html", error=None)

        if request.method == "POST" and request.form.get("action") == "login":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                is_authenticated = True
            else:
                is_authenticated = False
                return render_template("login.html", error="Invalid username or password.")

        if not is_authenticated:
            return render_template("login.html", error=None)

    message_segments: List[str] = []
    if request.method == "POST":
        message_segments.extend(_update_config_from_form(request.form))
        action = request.form.get("action")

        if action == "save":
            message_segments.append("✅ Settings saved.")

        elif action == "start":
            if chat_runner.start(control_config):
                message_segments.append("✅ Chat started.")
            else:
                message_segments.append("⚠️ Chat is already running.")

        elif action == "stop":
            if chat_runner.stop():
                message_segments.append("⏹ Chat stopped.")
            else:
                message_segments.append("⚠️ No chat is running.")

        elif action == "restart":
            chat_runner.restart(control_config)
            message_segments.append("🔁 Chat restarted.")

    running = chat_runner.is_running()
    schedule_enabled = None not in (
        control_config.get("start_hour"),
        control_config.get("start_minute"),
        control_config.get("stop_hour"),
        control_config.get("stop_minute"),
    )

    log_lines = log_buffer.snapshot()
    status_message = " ".join(message_segments) if message_segments else "Ready for commands."

    return render_template(
        "control.html",
        config=control_config,
        running=running,
        schedule_enabled=schedule_enabled,
        status_message=status_message,
        log_lines=log_lines,
    )


@app.route("/logs")
def logs() -> Any:
    return jsonify({"lines": log_buffer.snapshot()})


def run() -> None:
    chat_scheduler.start()
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    run()

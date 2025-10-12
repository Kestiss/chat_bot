"""Background scheduler that starts/stops the chat based on configured hours."""

from __future__ import annotations

import datetime
import threading
import time
from typing import Dict, Any

from chat_runner import ChatRunner


def _time_in_range(start: datetime.time, stop: datetime.time, current: datetime.time) -> bool:
    if start < stop:
        return start <= current < stop
    return current >= start or current < stop


class ChatScheduler:
    def __init__(self, runner: ChatRunner, config: Dict[str, Any]) -> None:
        self._runner = runner
        self._config = config
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def _loop(self) -> None:
        while True:
            try:
                start_hour = self._config.get("start_hour")
                start_minute = self._config.get("start_minute")
                stop_hour = self._config.get("stop_hour")
                stop_minute = self._config.get("stop_minute")

                if None not in (start_hour, start_minute, stop_hour, stop_minute):
                    start_time = datetime.time(start_hour, start_minute)
                    stop_time = datetime.time(stop_hour, stop_minute)
                    now = datetime.datetime.now().time()

                    should_run = _time_in_range(start_time, stop_time, now)
                    running = self._runner.is_running()

                    if should_run and not running:
                        self._runner.start(self._config)
                    elif not should_run and running:
                        self._runner.stop()
            except Exception:
                # Silent error to keep the scheduler alive. For troubleshooting,
                # inspect the control panel logs or run the app in verbose mode.
                pass
            time.sleep(60)


__all__ = ["ChatScheduler"]

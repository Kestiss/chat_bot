"""Utilities for launching and supervising the chat subprocess."""

from __future__ import annotations

import datetime as _dt
import pathlib
import re
import subprocess
import sys
import threading
from typing import Dict, Any, Optional

from log_buffer import LogBuffer

ANSI_RE = re.compile(r"\x1B(?:\[[0-?]*[ -/]*[@-~]|c)")


class ChatRunner:
    """Launches chat.py and streams its output into a LogBuffer."""

    def __init__(self, log_buffer: LogBuffer, script_name: str = "chat.py") -> None:
        self._log = log_buffer
        self._script_path = pathlib.Path(__file__).resolve().parent / script_name
        self._process: Optional[subprocess.Popen[str]] = None
        self._lock = threading.Lock()

    # --- public API -----------------------------------------------------

    def start(self, chat_config: Dict[str, Any]) -> bool:
        """Spawn chat.py with the provided configuration.

        Returns True if a new subprocess was launched, False if one was already
        running.
        """
        with self._lock:
            if self._process and self.is_running():
                return False

            args = self._build_args(chat_config)
            self._log.clear()
            timestamp = _dt.datetime.now().strftime("%H:%M:%S")
            self._log.append(f"[system {timestamp}] Chat launched.")

            self._process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if self._process.stdout:
                threading.Thread(
                    target=self._stream_output,
                    args=(self._process,),
                    daemon=True,
                ).start()
                threading.Thread(
                    target=self._monitor_exit,
                    args=(self._process,),
                    daemon=True,
                ).start()

            return True

    def stop(self) -> bool:
        with self._lock:
            if not self._process or not self.is_running():
                return False
            self._process.terminate()
            return True

    def restart(self, chat_config: Dict[str, Any]) -> None:
        self.stop()
        self.start(chat_config)

    def is_running(self) -> bool:
        proc = self._process
        return bool(proc and proc.poll() is None)

    def current_pid(self) -> Optional[int]:
        proc = self._process
        if proc and proc.poll() is None:
            return proc.pid
        return None

    # --- helpers --------------------------------------------------------

    def _build_args(self, chat_config: Dict[str, Any]) -> list[str]:
        return [
            sys.executable,
            str(self._script_path),
            chat_config["topic"],
            chat_config["first_speaker"],
            chat_config["model"],
            str(chat_config["max_turns"]),
            str(chat_config["delay"]),
            str(chat_config["typing_speed"]),
            str(chat_config["context_limit"]),
        ]

    def _stream_output(self, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        for raw_line in iter(process.stdout.readline, ""):
            line = ANSI_RE.sub("", raw_line.rstrip())
            if not line:
                continue
            self._log.append(line)
        process.stdout.close()

    def _monitor_exit(self, process: subprocess.Popen[str]) -> None:
        process.wait()
        timestamp = _dt.datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[system {timestamp}] Chat process exited.")
        with self._lock:
            if self._process is process:
                self._process = None


__all__ = ["ChatRunner"]

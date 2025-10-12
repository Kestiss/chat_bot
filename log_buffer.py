"""Thread-safe in-memory log buffer used by the control panel."""

from __future__ import annotations

from collections import deque
from typing import Iterable, List
import threading


class LogBuffer:
    """Fixed-size FIFO of string lines with thread-safe access."""

    def __init__(self, max_lines: int = 200) -> None:
        self._max_lines = max_lines
        self._lines: deque[str] = deque(maxlen=max_lines)
        self._lock = threading.Lock()

    def append(self, line: str) -> None:
        with self._lock:
            self._lines.append(line)

    def clear(self) -> None:
        with self._lock:
            self._lines.clear()

    def snapshot(self) -> List[str]:
        with self._lock:
            return list(self._lines)

    def extend(self, lines: Iterable[str]) -> None:
        with self._lock:
            self._lines.extend(lines)

    @property
    def max_lines(self) -> int:
        return self._max_lines


__all__ = ["LogBuffer"]

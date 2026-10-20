"""In-process event bus: every `StreamEvent` is appended to a JSONL log AND
pushed to in-process subscribers (used by the SSE endpoint).

The log is the source of truth — readers (HUD agent, an external service) can
recover the last N events by reading the tail of the file.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from typing import Deque, List

from .voice import StreamEvent


class EventBus:
    def __init__(self, log_path: Path, history: int = 500):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._history: Deque[StreamEvent] = deque(maxlen=history)
        self._subscribers: Deque[Deque[StreamEvent]] = deque()
        if self.log_path.exists():
            try:
                # replay the last `history` lines for warm starts
                lines = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-history:]
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    self._history.append(_from_dict(d))
            except Exception:
                pass

    def publish(self, event: StreamEvent) -> None:
        self._history.append(event)
        try:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict()) + "\n")
        except Exception:
            pass
        # fan out to subscribers
        dead: List[Deque[StreamEvent]] = []
        for q in self._subscribers:
            try:
                q.append(event)
            except Exception:
                dead.append(q)
        for q in dead:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def history(self, n: int = 100) -> List[StreamEvent]:
        out = list(self._history)[-n:]
        return out

    def subscribe(self) -> Deque[StreamEvent]:
        q: Deque[StreamEvent] = deque(maxlen=2000)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: Deque[StreamEvent]) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass


def _from_dict(d: dict) -> StreamEvent:
    return StreamEvent(
        type=d.get("type", "voice_command"),
        ts=float(d.get("ts", time.time())),
        window_t=float(d.get("window_t", 0.0)),
        text=d.get("text", ""),
        intent=d.get("intent", ""),
        target=d.get("target", ""),
        value=d.get("value", ""),
        confidence=float(d.get("confidence", 0.0)),
        source=d.get("source", "regex"),
        extra=d.get("extra", {}),
    )

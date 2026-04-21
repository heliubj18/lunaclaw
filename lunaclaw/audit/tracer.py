from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lunaclaw.audit.types import TraceEvent


class TraceContext:
    def __init__(self) -> None:
        self.trace_id: str = uuid.uuid4().hex[:16]
        self.events: list[TraceEvent] = []

    def record(self, event: TraceEvent) -> None:
        self.events.append(event)

    def to_json(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "events": [e.model_dump(mode="json") for e in self.events],
        }

    def summary(self) -> str:
        lines = [f"Trace {self.trace_id} ({len(self.events)} events):"]
        for e in self.events:
            prefix = "  └─ " if e.parent_id else "  "
            dur = f" ({e.duration_ms:.0f}ms)" if e.duration_ms else ""
            lines.append(f"{prefix}{e.event_type}{dur}")
        return "\n".join(lines)


class AuditLogger:
    def __init__(self, log_dir: str | Path) -> None:
        self._dir = Path(log_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, trace: TraceContext) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{trace.trace_id}.json"
        path = self._dir / filename
        path.write_text(json.dumps(trace.to_json(), indent=2, default=str))
        return path

    def list_traces(self) -> list[dict[str, Any]]:
        traces = []
        for path in sorted(self._dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(path.read_text())
                traces.append(
                    {
                        "trace_id": data["trace_id"],
                        "event_count": len(data.get("events", [])),
                        "file": path.name,
                    }
                )
            except Exception:
                continue
        return traces

    def load(self, trace_id: str) -> dict[str, Any] | None:
        for path in self._dir.glob(f"*{trace_id}*.json"):
            try:
                return json.loads(path.read_text())
            except Exception:
                continue
        return None

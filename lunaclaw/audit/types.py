from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    data: dict[str, Any] = Field(default_factory=dict)
    parent_id: str | None = None
    duration_ms: float | None = None

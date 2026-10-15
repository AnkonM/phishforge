"""server/sse.py -- minimal Server-Sent-Events formatting, no extra dependency."""

from __future__ import annotations

import json
from typing import Any


def format_sse(data: dict[str, Any]) -> str:
    """Format one event as an SSE `data: ...\\n\\n` frame. The event type is
    carried inside the JSON payload's "event" key (simpler client parsing
    than a separate `event:` line, and keeps one code path for both the
    run-events and benchmark-events streams)."""
    return f"data: {json.dumps(data)}\n\n"

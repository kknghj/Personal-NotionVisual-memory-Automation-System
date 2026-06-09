"""Read recent entries from UI feedback JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.feedback_logging import DEFAULT_LOG_PATH


def read_recent_feedback(
    *,
    limit: int = 20,
    log_path: Path | None = None,
) -> list[dict[str, Any]]:
    path = log_path or DEFAULT_LOG_PATH
    if not path.is_file():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return []
    tail = lines[-limit:]
    return [json.loads(line) for line in reversed(tail)]

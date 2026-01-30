"""MZX-aware Logging — All logs include the MZX-ID for end-to-end traceability.

Provides a structured logger that attaches MZX identifiers to every log entry,
enabling full audit trails across the XCircle ecosystem.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from atlas.core.mzx_protocol import generate_mzx_id


class MZXLogFormatter(logging.Formatter):
    """JSON log formatter that includes MZX-ID in every entry."""

    def format(self, record: logging.LogRecord) -> str:
        mzx_id = getattr(record, "mzx_id", None) or generate_mzx_id()

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mzx_id": mzx_id,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields
        for key in ("agent_name", "tool_name", "user_id", "action", "success", "error"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry, ensure_ascii=False)


def get_mzx_logger(name: str = "atlas") -> logging.Logger:
    """Get a logger configured with MZX traceability.

    Args:
        name: Logger name (default: "atlas").

    Returns:
        A Logger instance with MZX JSON formatting.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(MZXLogFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger


def log_mzx_event(
    logger: logging.Logger,
    message: str,
    *,
    mzx_id: str | None = None,
    agent_name: str | None = None,
    tool_name: str | None = None,
    user_id: str | None = None,
    action: str | None = None,
    success: bool = True,
    error: str | None = None,
    level: int = logging.INFO,
) -> None:
    """Log an event with MZX traceability fields.

    Args:
        logger: The logger to use.
        message: Log message.
        mzx_id: MZX identifier (auto-generated if not provided).
        agent_name: Name of the agent.
        tool_name: Name of the tool called.
        user_id: User identifier.
        action: Action being performed.
        success: Whether the action succeeded.
        error: Error message if failed.
        level: Log level (default: INFO).
    """
    extra = {
        "mzx_id": mzx_id or generate_mzx_id(),
        "agent_name": agent_name,
        "tool_name": tool_name,
        "user_id": user_id,
        "action": action,
        "success": success,
        "error": error,
    }
    logger.log(level, message, extra=extra)

#!/usr/bin/env python3
"""Analyze Atlas database guardrail logs for operational insights."""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_LOGGER = logging.getLogger(__name__)

_GUARDRAIL_EVENT = "db_guardrail_triggered"
_GUARDRAIL_REGEX = re.compile(r"guardrail[=:]\s*([a-zA-Z_]+)")
_TIMEOUT_REGEX = re.compile(r"timeout_seconds[=:]\s*([0-9.]+)")
_MAX_ROWS_REGEX = re.compile(r"max_rows[=:]\s*([0-9]+)")
_LEGACY_MARKER = "Guardrail triggered:"


@dataclass
class GuardrailEvent:
    """Parsed guardrail event extracted from a log line."""

    guardrail: str
    timeout_seconds: float | None = None
    max_rows: int | None = None


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments for log analysis.

    Returns:
        Parsed argparse namespace
    """
    parser = argparse.ArgumentParser(description="Analyze Atlas DB guardrail logs.")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the log file to analyze",
    )
    return parser.parse_args()


def read_lines(path: Path) -> list[str]:
    """
    Read all lines from the provided log file path.

    Args:
        path: Path to the log file

    Returns:
        List of log lines

    Raises:
        FileNotFoundError: If the log file does not exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def parse_line(line: str) -> GuardrailEvent | None:
    """
    Parse a log line and return a GuardrailEvent if present.

    Args:
        line: Raw log line

    Returns:
        GuardrailEvent when the line indicates a guardrail trigger, otherwise None
    """
    data = _try_parse_json(line)
    if isinstance(data, dict):
        event = str(data.get("event", "")).strip()
        if event != _GUARDRAIL_EVENT:
            return None
        guardrail = str(data.get("guardrail", "")).strip()
        if guardrail:
            return GuardrailEvent(
                guardrail=guardrail,
                timeout_seconds=_coerce_float(data.get("timeout_seconds")),
                max_rows=_coerce_int(data.get("max_rows")),
            )

    if _GUARDRAIL_EVENT not in line:
        legacy = _parse_legacy_guardrail(line)
        return legacy

    guardrail_match = _GUARDRAIL_REGEX.search(line)
    guardrail = guardrail_match.group(1).lower() if guardrail_match else "unknown"
    return GuardrailEvent(
        guardrail=guardrail,
        timeout_seconds=_match_float(_TIMEOUT_REGEX, line),
        max_rows=_match_int(_MAX_ROWS_REGEX, line),
    )


def _parse_legacy_guardrail(line: str) -> GuardrailEvent | None:
    """
    Parse legacy guardrail log lines with inline JSON payloads.

    Args:
        line: Raw log line

    Returns:
        GuardrailEvent when a legacy guardrail entry is detected, otherwise None
    """
    if _LEGACY_MARKER not in line:
        return None
    payload = line.split(_LEGACY_MARKER, 1)[-1].strip()
    data = _try_parse_json(payload)
    if not isinstance(data, dict):
        return None
    violation = str(data.get("violation", "")).strip().lower()
    guardrail = "timeout" if violation == "timeout" else "row_limit" if violation == "row_limit" else "unknown"
    timeout_seconds = _coerce_float(data.get("duration"))
    return GuardrailEvent(
        guardrail=guardrail,
        timeout_seconds=timeout_seconds,
        max_rows=None,
    )


def analyze_events(lines: Iterable[str]) -> dict[str, Any]:
    """
    Analyze log lines for guardrail events and build a summary.

    Args:
        lines: Iterable of log lines

    Returns:
        Summary dictionary containing counts and guardrail metadata
    """
    events: list[GuardrailEvent] = []
    total_lines = 0
    for line in lines:
        total_lines += 1
        parsed = parse_line(line)
        if parsed:
            events.append(parsed)

    guardrail_counts = Counter(event.guardrail for event in events)
    timeouts = [event.timeout_seconds for event in events if event.timeout_seconds]
    max_rows = [event.max_rows for event in events if event.max_rows]

    return {
        "total_lines": total_lines,
        "event_count": len(events),
        "guardrail_counts": dict(guardrail_counts),
        "timeout_seconds_samples": timeouts,
        "max_rows_samples": max_rows,
    }


def format_report(summary: dict[str, Any]) -> str:
    """
    Format the summary into a human-readable report.

    Args:
        summary: Summary dictionary from analyze_events

    Returns:
        Formatted report string
    """
    lines = [
        "Atlas DB Guardrail Report",
        "-" * 32,
        f"Events detected: {summary.get('event_count', 0)}",
    ]
    guardrails = summary.get("guardrail_counts", {})
    if guardrails:
        lines.append("Guardrail breakdown:")
        for guardrail, count in sorted(guardrails.items()):
            lines.append(f"  - {guardrail}: {count}")
    else:
        lines.append("Guardrail breakdown: none")

    timeout_samples = summary.get("timeout_seconds_samples", [])
    if timeout_samples:
        lines.append(f"Timeout samples (seconds): {timeout_samples}")

    max_rows_samples = summary.get("max_rows_samples", [])
    if max_rows_samples:
        lines.append(f"Max rows samples: {max_rows_samples}")

    return "\n".join(lines)


def _try_parse_json(line: str) -> dict[str, Any] | None:
    """
    Attempt to parse a line as JSON.

    Args:
        line: Raw log line

    Returns:
        Parsed JSON dict or None if parsing fails
    """
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _match_float(pattern: re.Pattern[str], line: str) -> float | None:
    """
    Extract a float value from a regex match.

    Args:
        pattern: Compiled regex pattern
        line: Raw log line

    Returns:
        Parsed float if present, otherwise None
    """
    match = pattern.search(line)
    return float(match.group(1)) if match else None


def _match_int(pattern: re.Pattern[str], line: str) -> int | None:
    """
    Extract an int value from a regex match.

    Args:
        pattern: Compiled regex pattern
        line: Raw log line

    Returns:
        Parsed int if present, otherwise None
    """
    match = pattern.search(line)
    return int(match.group(1)) if match else None


def _coerce_float(value: Any) -> float | None:
    """
    Coerce a value into a float if possible.

    Args:
        value: Input value

    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    """
    Coerce a value into an int if possible.

    Args:
        value: Input value

    Returns:
        Int value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    """
    Run the log analysis workflow.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()
    try:
        lines = read_lines(Path(args.file))
        summary = analyze_events(lines)
        print(format_report(summary))
        return 0
    except Exception as exc:  # pragma: no cover - defensive guard
        _LOGGER.error(
            "db_log_analysis_failed",
            extra={"event": "db_log_analysis_failed", "error": str(exc)},
        )
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())

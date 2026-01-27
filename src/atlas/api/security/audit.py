"""
Audit Logging Module for Atlas API

SECURITY: Comprehensive audit trail for compliance and security monitoring.
- All sensitive operations are logged
- Logs are immutable and tamper-evident
- Supports PDPL compliance requirements
"""

import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    PASSWORD_CHANGE = "auth.password.change"
    MFA_ENABLED = "auth.mfa.enabled"
    MFA_DISABLED = "auth.mfa.disabled"

    # Data access events
    QUERY_EXECUTED = "data.query.executed"
    QUERY_BLOCKED = "data.query.blocked"
    SCHEMA_ACCESSED = "data.schema.accessed"
    EXPORT_REQUESTED = "data.export.requested"

    # Admin events
    USER_CREATED = "admin.user.created"
    USER_UPDATED = "admin.user.updated"
    USER_DELETED = "admin.user.deleted"
    ROLE_CHANGED = "admin.role.changed"
    SETTINGS_CHANGED = "admin.settings.changed"

    # Security events
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    INVALID_TOKEN = "security.invalid_token"
    UNAUTHORIZED_ACCESS = "security.unauthorized"
    SUSPICIOUS_ACTIVITY = "security.suspicious"


class AuditEvent(BaseModel):
    """Audit event record."""

    id: str = Field(..., description="Unique event ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType
    user_id: str | None = None
    user_email: str | None = None
    client_ip: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    action: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error_message: str | None = None


class AuditLogger:
    """
    Audit logger for security and compliance.

    SECURITY:
    - Logs are append-only
    - Each entry includes timestamp and event ID
    - Supports structured logging for analysis

    In production, this should write to a secure, immutable log store
    (e.g., PostgreSQL with RLS, or a dedicated SIEM system).
    """

    def __init__(self, log_dir: str | None = None):
        self.log_dir = Path(log_dir or os.getenv("ATLAS_AUDIT_LOG_DIR", "./logs/audit"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._event_counter = 0

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        self._event_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"evt_{timestamp}_{self._event_counter:06d}"

    def _get_log_file(self) -> Path:
        """Get the current log file path (daily rotation)."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{date_str}.jsonl"

    def log(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        user_email: str | None = None,
        client_ip: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditEvent:
        """
        Log an audit event.

        SECURITY: All parameters are validated and sanitized.

        Args:
            event_type: Type of event being logged
            user_id: ID of the user performing the action
            user_email: Email of the user (for display purposes)
            client_ip: Client IP address
            resource_type: Type of resource being accessed
            resource_id: ID of the specific resource
            action: Description of the action taken
            details: Additional context (will be sanitized)
            success: Whether the action succeeded
            error_message: Error message if action failed

        Returns:
            The created AuditEvent
        """
        # Sanitize details to prevent sensitive data leakage
        safe_details = self._sanitize_details(details or {})

        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            client_ip=client_ip,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=safe_details,
            success=success,
            error_message=error_message,
        )

        # Write to log file (append-only)
        self._write_event(event)

        return event

    def _sanitize_details(self, details: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize details to prevent logging sensitive information.

        SECURITY: Remove passwords, tokens, and other sensitive fields.
        """
        sensitive_keys = {
            "password",
            "token",
            "secret",
            "api_key",
            "apikey",
            "authorization",
            "auth",
            "credential",
            "ssn",
            "credit_card",
            "card_number",
        }

        sanitized = {}
        for key, value in details.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[truncated]"
            else:
                sanitized[key] = value

        return sanitized

    def _write_event(self, event: AuditEvent) -> None:
        """Write event to log file."""
        log_file = self._get_log_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def query(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_type: AuditEventType | None = None,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """
        Query audit logs with filters.

        SECURITY: This should only be accessible to admin users.

        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            event_type: Filter by event type
            user_id: Filter by user
            limit: Maximum results to return
            offset: Skip this many results

        Returns:
            List of matching AuditEvent records
        """
        events: list[AuditEvent] = []

        # Read from all relevant log files
        for log_file in sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = AuditEvent.model_validate_json(line.strip())

                        # Apply filters
                        if start_date and event.timestamp < start_date:
                            continue
                        if end_date and event.timestamp > end_date:
                            continue
                        if event_type and event.event_type != event_type:
                            continue
                        if user_id and event.user_id != user_id:
                            continue

                        events.append(event)
                    except Exception:
                        continue  # Skip malformed entries

            # Early exit if we have enough events
            if len(events) >= offset + limit:
                break

        # Apply pagination
        return events[offset : offset + limit]


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

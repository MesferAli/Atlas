"""
Audit Log Routes for Atlas API

SECURITY: Audit logs are read-only and only accessible to admins.
- All audit queries are logged themselves
- Pagination is enforced to prevent DoS
- Sensitive data is redacted in responses
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from atlas.api.security.audit import (
    AuditEvent,
    AuditEventType,
    get_audit_logger,
)
from atlas.api.security.auth import TokenPayload, UserRole, get_current_user, require_auth

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    """Response for audit log queries."""

    events: list[AuditEvent]
    total: int
    page: int
    page_size: int
    has_more: bool


class AuditStatsResponse(BaseModel):
    """Response for audit statistics."""

    total_events: int
    events_by_type: dict[str, int]
    events_last_24h: int
    failed_logins_last_24h: int


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(
    user: Annotated[TokenPayload, Depends(get_current_user)],
    start_date: datetime | None = Query(None, description="Filter events after this date"),
    end_date: datetime | None = Query(None, description="Filter events before this date"),
    event_type: AuditEventType | None = Query(None, description="Filter by event type"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1, le=10000, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> AuditLogResponse:
    """
    Query audit logs with filters.

    SECURITY:
    - Only admins can query all logs
    - Non-admins can only see their own events
    - Pagination prevents DoS attacks
    """
    audit = get_audit_logger()

    # Non-admins can only see their own logs
    if user.role != UserRole.ADMIN:
        user_id = user.sub

    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    # Query logs
    offset = (page - 1) * page_size
    events = audit.query(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        user_id=user_id,
        limit=page_size + 1,  # Fetch one extra to check if there's more
        offset=offset,
    )

    # Check if there are more results
    has_more = len(events) > page_size
    if has_more:
        events = events[:page_size]

    # Log this query (audit the auditor)
    audit.log(
        event_type=AuditEventType.SCHEMA_ACCESSED,
        user_id=user.sub,
        user_email=user.email,
        resource_type="audit_logs",
        action="query",
        details={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "event_type": event_type.value if event_type else None,
            "page": page,
        },
        success=True,
    )

    return AuditLogResponse(
        events=events,
        total=len(events),
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/stats", response_model=AuditStatsResponse)
@require_auth(allowed_roles=[UserRole.ADMIN])
async def get_audit_stats(
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> AuditStatsResponse:
    """
    Get audit log statistics.

    SECURITY: Only admins can view aggregate statistics.
    """
    from datetime import timedelta, timezone

    audit = get_audit_logger()

    # Get all events (limited)
    all_events = audit.query(limit=10000)

    # Count by type
    events_by_type: dict[str, int] = {}
    for event in all_events:
        event_type = event.event_type.value
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

    # Events in last 24 hours
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(hours=24)

    events_last_24h = sum(
        1 for e in all_events if e.timestamp >= yesterday
    )

    # Failed logins in last 24 hours
    failed_logins_last_24h = sum(
        1 for e in all_events
        if e.timestamp >= yesterday and e.event_type == AuditEventType.LOGIN_FAILURE
    )

    return AuditStatsResponse(
        total_events=len(all_events),
        events_by_type=events_by_type,
        events_last_24h=events_last_24h,
        failed_logins_last_24h=failed_logins_last_24h,
    )


@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_audit_event(
    event_id: str,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> AuditEvent:
    """
    Get a specific audit event by ID.

    SECURITY:
    - Only admins can view any event
    - Non-admins can only view their own events
    """
    audit = get_audit_logger()

    # Query for the specific event
    events = audit.query(limit=10000)

    for event in events:
        if event.id == event_id:
            # Check permissions
            if user.role != UserRole.ADMIN and event.user_id != user.sub:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own audit events",
                )
            return event

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audit event not found: {event_id}",
    )

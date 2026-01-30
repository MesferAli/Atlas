"""MZX Identity Protocol — Signature Engine, Base Schema, and Validation.

The MZX protocol is the official intellectual identity for the XCircle ecosystem.
Every agent-tool interaction is signed with an MZX seal for traceability.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, TypeVar

from pydantic import BaseModel, Field

# Signature format: MZX-{PRODUCT}-{DATE}-{UUID}
_MZX_PREFIX = "MZX"
_MZX_PRODUCT = "ATLAS"

F = TypeVar("F")


def generate_mzx_id(product: str = _MZX_PRODUCT) -> str:
    """Generate a unique MZX signature ID.

    Format: MZX-ATLAS-20260130-<uuid4_short>

    Args:
        product: Product identifier (default: ATLAS).

    Returns:
        MZX signature string.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:12]
    return f"{_MZX_PREFIX}-{product}-{date_str}-{short_uuid}"


class MZXSignature(BaseModel):
    """An MZX signature attached to every response."""

    mzx_id: str = Field(default_factory=generate_mzx_id)
    product: str = Field(default=_MZX_PRODUCT)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(default="1.0.0")


class MZXBaseModel(BaseModel):
    """Base model that mandates an mzx_auth header in every response.

    All agent responses must inherit from this model to ensure
    MZX traceability across the XCircle ecosystem.
    """

    mzx_auth: MZXSignature = Field(default_factory=MZXSignature)

    model_config = {"json_schema_extra": {"description": "MZX-certified response model"}}


class MZXAgentResponse(MZXBaseModel):
    """Standard agent response with MZX seal."""

    agent_name: str
    action: str
    result: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: str | None = None


def mzx_signed(func: F) -> F:
    """Decorator that signs every agent-tool interaction with the MZX seal.

    Works with both sync and async functions. Injects an `mzx_id` into
    the return value if it's a dict, or wraps it in MZXAgentResponse.

    Usage:
        @mzx_signed
        async def my_tool(data: str) -> dict:
            return {"result": data}
    """
    import asyncio

    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            mzx_id = generate_mzx_id()
            result = await func(*args, **kwargs)
            return _attach_mzx(result, mzx_id, func.__name__)

        return async_wrapper  # type: ignore[return-value]
    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            mzx_id = generate_mzx_id()
            result = func(*args, **kwargs)
            return _attach_mzx(result, mzx_id, func.__name__)

        return sync_wrapper  # type: ignore[return-value]


def _attach_mzx(result: Any, mzx_id: str, action: str) -> Any:
    """Attach MZX signature to result."""
    if isinstance(result, dict):
        result["mzx_id"] = mzx_id
        result["mzx_action"] = action
        return result
    if isinstance(result, MZXBaseModel):
        result.mzx_auth = MZXSignature(mzx_id=mzx_id)
        return result
    return MZXAgentResponse(
        agent_name="Atlas",
        action=action,
        result={"value": result},
        mzx_auth=MZXSignature(mzx_id=mzx_id),
    )

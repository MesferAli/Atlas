"""
Pydantic Validation Models for Atlas API

SECURITY: TRUST NO ONE - Validate ALL inputs on the server side.
All API endpoints MUST use these models for request validation.
"""

import re
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

# Type variable for generic validation decorator
T = TypeVar("T")


class UserRole(str, Enum):
    """User roles for RBAC enforcement."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SERVICE = "service"


class AuthRequest(BaseModel):
    """Login request with strict validation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(..., description="User email address")
    password: SecretStr = Field(
        ..., min_length=8, max_length=128, description="User password"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: SecretStr) -> SecretStr:
        """Ensure password meets minimum security requirements."""
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        return v


class RegisterRequest(BaseModel):
    """Registration request with comprehensive validation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(..., description="User email address")
    password: SecretStr = Field(
        ..., min_length=8, max_length=128, description="User password"
    )
    confirm_password: SecretStr = Field(..., description="Password confirmation")
    full_name: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[\w\s\-\.]+$"
    )
    organization: str | None = Field(
        None, max_length=200, description="Organization name"
    )

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        """Ensure password and confirmation match."""
        if self.password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("Passwords do not match")
        return self

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: SecretStr) -> SecretStr:
        """Ensure password meets minimum security requirements."""
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        return v


class AuthResponse(BaseModel):
    """Authentication response."""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: "UserProfile"


class TokenPayload(BaseModel):
    """JWT token payload with validation."""

    sub: str = Field(..., description="User ID (subject)")
    email: EmailStr
    role: UserRole
    exp: datetime
    iat: datetime
    jti: str = Field(..., description="Unique token ID for revocation")


class UserProfile(BaseModel):
    """User profile data (safe to expose to client)."""

    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    organization: str | None = None
    created_at: datetime
    last_login: datetime | None = None
    is_active: bool = True
    mfa_enabled: bool = False


class ChatRequestValidated(BaseModel):
    """Enhanced chat request with strict input validation.

    SECURITY: Validates and sanitizes natural language queries
    to prevent injection attacks.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language question about the database",
    )

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        """Sanitize the question to prevent potential injection."""
        # Remove null bytes
        v = v.replace("\x00", "")
        # Remove excessive whitespace
        v = " ".join(v.split())
        # Basic length check after sanitization
        if len(v) < 3:
            raise ValueError("Question must be at least 3 characters after cleanup")
        return v


class AuditLogQuery(BaseModel):
    """Query parameters for audit log retrieval."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    user_id: str | None = None
    event_type: str | None = None
    resource_type: str | None = None
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def validate_date_range(self) -> "AuditLogQuery":
        """Ensure date range is valid if both dates provided."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")
        return self


class WebhookPayload(BaseModel):
    """Base webhook payload with signature verification fields."""

    event_type: str
    timestamp: datetime
    data: dict[str, Any]
    signature: str = Field(..., description="HMAC signature for verification")


def validate_input(model: type[BaseModel]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to validate input using a Pydantic model.

    SECURITY: Use this decorator on all API endpoints that accept user input.

    Example:
        @app.post("/api/users")
        @validate_input(CreateUserRequest)
        async def create_user(request: CreateUserRequest):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Find the request body in kwargs
            for key, value in kwargs.items():
                if isinstance(value, dict):
                    # Validate and replace with model instance
                    kwargs[key] = model(**value)
            return await func(*args, **kwargs)

        return wrapper

    return decorator

"""
Authentication Module for Atlas API

SECURITY: SERVICE ROLE ONLY
- All authentication verification happens server-side
- Tokens are validated on every request
- Password hashing uses bcrypt with strong work factor
- JWT tokens include unique IDs for revocation support
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Annotated, Any, Callable, TypeVar

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from atlas.api.security.models import TokenPayload, UserProfile, UserRole

# Configuration from environment
JWT_SECRET_KEY = os.getenv("ATLAS_JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("ATLAS_JWT_EXPIRATION_HOURS", "24"))

# Security scheme
security = HTTPBearer(auto_error=False)

# Type variable for decorators
T = TypeVar("T")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    SECURITY: Uses bcrypt with appropriate work factor.
    The work factor automatically increases computation time
    to resist brute force attacks.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    SECURITY: Uses constant-time comparison to prevent timing attacks.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(
    user_id: str,
    email: str,
    role: UserRole,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """
    Create a JWT access token.

    SECURITY:
    - Includes unique token ID (jti) for revocation support
    - Uses short expiration by default
    - Contains minimal claims to reduce token size

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS))

    payload = {
        "sub": user_id,
        "email": email,
        "role": role.value,
        "exp": expire,
        "iat": now,
        "jti": secrets.token_urlsafe(16),  # Unique token ID
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expire


def verify_token(token: str) -> TokenPayload:
    """
    Verify and decode a JWT token.

    SECURITY:
    - Validates signature
    - Checks expiration
    - Returns structured payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenPayload(
            sub=payload["sub"],
            email=payload["email"],
            role=UserRole(payload["role"]),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            jti=payload["jti"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TokenPayload:
    """
    FastAPI dependency to get the current authenticated user.

    SECURITY:
    - Extracts token from Authorization header
    - Validates token signature and expiration
    - Returns user payload for authorization checks

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenPayload = Depends(get_current_user)):
            ...
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_token(credentials.credentials)


async def get_current_user_optional(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TokenPayload | None:
    """
    FastAPI dependency to optionally get the current authenticated user.

    SECURITY:
    - Returns None if no token is provided (allows anonymous access)
    - Validates token if provided
    - Use this for endpoints that work with or without authentication

    Usage:
        @app.get("/public-but-personalized")
        async def optional_auth_route(
            user: TokenPayload | None = Depends(get_current_user_optional)
        ):
            if user:
                # Personalized response
            else:
                # Anonymous response
    """
    if credentials is None:
        return None

    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        # Invalid token, treat as anonymous
        return None


def require_auth(
    allowed_roles: list[UserRole] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to require authentication and optionally specific roles.

    SECURITY: RBAC enforcement at the endpoint level.

    Usage:
        @app.post("/admin/users")
        @require_auth(allowed_roles=[UserRole.ADMIN])
        async def admin_endpoint(user: TokenPayload = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Find the user in kwargs (injected by FastAPI dependency)
            user: TokenPayload | None = None
            for key, value in kwargs.items():
                if isinstance(value, TokenPayload):
                    user = value
                    break

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if allowed_roles and user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Mock user database for demo purposes
# SECURITY: In production, use PostgreSQL with RLS enabled
_mock_users: dict[str, dict[str, Any]] = {
    "demo@atlas.sa": {
        "id": "user_001",
        "email": "demo@atlas.sa",
        "password_hash": get_password_hash("Demo@123"),
        "full_name": "Demo User",
        "role": UserRole.ANALYST,
        "organization": "Atlas Demo",
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
        "is_active": True,
        "mfa_enabled": False,
    }
}


async def authenticate_user(email: str, password: str) -> UserProfile | None:
    """
    Authenticate a user with email and password.

    SECURITY:
    - Password is verified using constant-time comparison
    - Failed attempts should be rate-limited (see middleware)

    Returns:
        UserProfile if authentication succeeds, None otherwise
    """
    user_data = _mock_users.get(email)
    if not user_data:
        # Still perform hash comparison to prevent timing attacks
        verify_password(password, get_password_hash("dummy"))
        return None

    if not user_data["is_active"]:
        return None

    if not verify_password(password, user_data["password_hash"]):
        return None

    # Update last login
    user_data["last_login"] = datetime.now(timezone.utc)

    return UserProfile(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        role=user_data["role"],
        organization=user_data["organization"],
        created_at=user_data["created_at"],
        last_login=user_data["last_login"],
        is_active=user_data["is_active"],
        mfa_enabled=user_data["mfa_enabled"],
    )

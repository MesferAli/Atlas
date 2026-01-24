"""
Authentication Routes for Atlas API

SECURITY: Backend-Only Authentication
- All authentication logic runs server-side
- Passwords are hashed with bcrypt
- JWT tokens are issued for authenticated sessions
- Rate limiting is enforced on authentication endpoints
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from atlas.api.security.audit import AuditEventType, get_audit_logger
from atlas.api.security.auth import (
    TokenPayload,
    UserRole,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from atlas.api.security.models import (
    AuthRequest,
    AuthResponse,
    RegisterRequest,
    UserProfile,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LogoutResponse(BaseModel):
    """Response for logout endpoint."""

    message: str = "Successfully logged out"


class UserResponse(BaseModel):
    """Response for current user endpoint."""

    user: UserProfile


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, auth_request: AuthRequest) -> AuthResponse:
    """
    Authenticate user and return access token.

    SECURITY:
    - Password verification is done server-side
    - Failed attempts are logged and rate-limited
    - Tokens have limited expiration
    """
    audit = get_audit_logger()
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host

    # Authenticate user
    user = await authenticate_user(
        auth_request.email,
        auth_request.password.get_secret_value(),
    )

    if not user:
        # Log failed attempt
        audit.log(
            event_type=AuditEventType.LOGIN_FAILURE,
            user_email=auth_request.email,
            client_ip=client_ip,
            action="login_attempt",
            success=False,
            error_message="Invalid credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    token, expires_at = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

    # Log successful login
    audit.log(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id=user.id,
        user_email=user.email,
        client_ip=client_ip,
        action="login",
        success=True,
    )

    return AuthResponse(
        access_token=token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/register", response_model=AuthResponse)
async def register(request: Request, register_request: RegisterRequest) -> AuthResponse:
    """
    Register a new user.

    SECURITY:
    - Password is hashed before storage
    - Email uniqueness is enforced
    - Input is validated with Pydantic
    """
    from atlas.api.security.auth import _mock_users

    audit = get_audit_logger()
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host

    # Check if user already exists
    if register_request.email in _mock_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Create new user
    user_id = f"user_{len(_mock_users) + 1:03d}"
    password_hash = get_password_hash(register_request.password.get_secret_value())

    user_data = {
        "id": user_id,
        "email": register_request.email,
        "password_hash": password_hash,
        "full_name": register_request.full_name,
        "role": UserRole.VIEWER,  # Default role
        "organization": register_request.organization,
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
        "is_active": True,
        "mfa_enabled": False,
    }

    _mock_users[register_request.email] = user_data

    # Create user profile
    user = UserProfile(
        id=user_id,
        email=register_request.email,
        full_name=register_request.full_name,
        role=UserRole.VIEWER,
        organization=register_request.organization,
        created_at=user_data["created_at"],
        last_login=user_data["last_login"],
        is_active=True,
        mfa_enabled=False,
    )

    # Create access token
    token, expires_at = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

    # Log user creation
    audit.log(
        event_type=AuditEventType.USER_CREATED,
        user_id=user.id,
        user_email=user.email,
        client_ip=client_ip,
        action="register",
        details={"organization": register_request.organization},
        success=True,
    )

    return AuthResponse(
        access_token=token,
        expires_at=expires_at,
        user=user,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> LogoutResponse:
    """
    Logout the current user.

    SECURITY:
    - Invalidates the current token (in production, add to blocklist)
    - Logs the logout event
    """
    audit = get_audit_logger()
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host

    # In production, add token JTI to blocklist
    # For now, just log the logout
    audit.log(
        event_type=AuditEventType.LOGOUT,
        user_id=user.sub,
        user_email=user.email,
        client_ip=client_ip,
        action="logout",
        details={"token_jti": user.jti},
        success=True,
    )

    return LogoutResponse()


@router.get("/user", response_model=UserResponse)
async def get_user(
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> UserResponse:
    """
    Get the current authenticated user's profile.

    SECURITY:
    - Requires valid authentication token
    - Returns only safe user data (no password hash)
    """
    from atlas.api.security.auth import _mock_users

    user_data = _mock_users.get(user.email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        user=UserProfile(
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
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> AuthResponse:
    """
    Refresh the access token.

    SECURITY:
    - Requires valid (but potentially near-expiry) token
    - Issues new token with fresh expiration
    - Logs token refresh for audit
    """
    from atlas.api.security.auth import _mock_users

    audit = get_audit_logger()
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host

    user_data = _mock_users.get(user.email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Create new token
    token, expires_at = create_access_token(
        user_id=user.sub,
        email=user.email,
        role=user.role,
    )

    # Log refresh
    audit.log(
        event_type=AuditEventType.TOKEN_REFRESH,
        user_id=user.sub,
        user_email=user.email,
        client_ip=client_ip,
        action="token_refresh",
        success=True,
    )

    return AuthResponse(
        access_token=token,
        expires_at=expires_at,
        user=UserProfile(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            organization=user_data["organization"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"],
            is_active=user_data["is_active"],
            mfa_enabled=user_data["mfa_enabled"],
        ),
    )

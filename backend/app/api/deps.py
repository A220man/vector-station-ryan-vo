from typing import Optional, Annotated
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_token, get_token_subject, get_token_roles
from app.models import User, UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError


settings = get_settings()


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    import os
    is_test = os.environ.get("PYTEST_CURRENT_TEST") is not None
    
    if not settings.oidc_enabled and settings.environment == "development" and not is_test:
        # Demo mode: return a default dev user (only for local dev, not tests)
        result = await db.execute(select(User).where(User.username == "dev"))
        user = result.scalar_one_or_none()
        if not user:
            from app.core.security import get_password_hash
            user = User(
                email="dev@localhost",
                username="dev",
                hashed_password=get_password_hash("dev"),
                full_name="Development User",
                role=UserRole.ADMIN,
                is_active=True,
                is_superuser=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    if not authorization:
        raise AuthenticationError("Authorization header missing")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise AuthenticationError("Invalid authentication scheme")
    except ValueError:
        raise AuthenticationError("Invalid authorization header format")

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token: missing subject")
    except ValueError as e:
        raise AuthenticationError(str(e))

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise AuthorizationError("Inactive user")
    return current_user


def require_roles(*allowed_roles: UserRole):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if current_user.role not in allowed_roles:
            raise AuthorizationError(f"Required role: {', '.join(r.value for r in allowed_roles)}")
        return current_user

    return role_checker


require_operator = require_roles(UserRole.OPERATOR, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)


async def get_optional_user(
    authorization: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
    except (ValueError, JWTError, AttributeError):
        pass
    return None
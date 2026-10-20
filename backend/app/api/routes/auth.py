from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import secrets
import httpx

from app.api.deps import get_db, get_current_active_user
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
)
from app.models import User, UserRole
from app.schemas import TokenResponse, UserResponse
from app.core.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Local username/password login (development/demo)."""
    if settings.oidc_enabled and settings.environment == "production":
        raise AuthenticationError("Local login disabled when OIDC is enabled")

    result = await db.execute(
        select(User).where(
            (User.username == credentials.username) | (User.email == credentials.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise AuthenticationError("Invalid credentials")

    if not verify_password(credentials.password, user.hashed_password):
        raise AuthenticationError("Invalid credentials")

    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    access_token = create_access_token(subject=str(user.id), roles=[user.role.value])
    refresh_token = create_refresh_token(subject=str(user.id))

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        user_id = payload.get("sub")
    except ValueError:
        raise AuthenticationError("Invalid refresh token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    access_token = create_access_token(subject=str(user.id), roles=[user.role.value])
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return UserResponse.model_validate(current_user)


# OIDC Routes
@router.get("/oidc/login")
async def oidc_login(request: Request):
    if not settings.oidc_enabled:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC not configured")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    request.session["oidc_state"] = state
    request.session["oidc_nonce"] = nonce

    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": " ".join(settings.oidc_scopes),
        "redirect_uri": settings.oidc_redirect_uri,
        "state": state,
        "nonce": nonce,
    }

    auth_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/auth"
    return RedirectResponse(url=f"{auth_url}?{httpx.QueryParams(params)}")


@router.get("/oidc/callback")
async def oidc_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if not settings.oidc_enabled:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC not configured")

    if error:
        raise AuthenticationError(f"OIDC error: {error}")

    if not code or not state:
        raise AuthenticationError("Missing code or state")

    stored_state = request.session.get("oidc_state")
    if not stored_state or stored_state != state:
        raise AuthenticationError("Invalid state parameter")

    stored_nonce = request.session.get("oidc_nonce")

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            f"{settings.oidc_issuer_url}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.oidc_redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_response.json()

    access_token = token_data.get("access_token")
    id_token = token_data.get("id_token")

    from jose import jwt
    claims = jwt.decode(id_token, options={"verify_signature": False})

    if claims.get("nonce") != stored_nonce:
        raise AuthenticationError("Invalid nonce")

    oidc_sub = claims.get("sub")
    email = claims.get("email")
    username = claims.get("preferred_username") or email

    result = await db.execute(select(User).where(User.oidc_sub == oidc_sub))
    user = result.scalar_one_or_none()

    if not user:
        if not email:
            raise AuthenticationError("Email required from OIDC provider")
        
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.oidc_sub = oidc_sub
            user.oidc_provider = settings.oidc_issuer_url
        else:
            user = User(
                email=email,
                username=username,
                full_name=claims.get("name"),
                role=UserRole.VIEWER,
                is_active=True,
                oidc_sub=oidc_sub,
                oidc_provider=settings.oidc_issuer_url,
            )
            db.add(user)

    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    app_access_token = create_access_token(subject=str(user.id), roles=[user.role.value])
    app_refresh_token = create_refresh_token(subject=str(user.id))

    request.session.pop("oidc_state", None)
    request.session.pop("oidc_nonce", None)

    frontend_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:5173"
    return RedirectResponse(
        url=f"{frontend_url}/auth/callback?access_token={app_access_token}&refresh_token={app_refresh_token}"
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}
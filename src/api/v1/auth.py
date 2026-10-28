"""Authentication endpoints: signup, login, refresh, logout, me."""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from src.models import Company, User
from src.schemas import LoginRequest, RefreshRequest, Token, UserCreate, UserRead

router = APIRouter(tags=["auth"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.post("/auth/signup", response_model=Token)
def signup(
    payload: UserCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> Token:
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    company_name = payload.company_name or payload.name
    company_slug = payload.company_slug or payload.email.split("@")[0]
    existing_company = session.exec(select(Company).where(Company.slug == company_slug)).first()
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company slug already taken",
        )

    company = Company(name=company_name, slug=company_slug)
    session.add(company)
    session.flush()

    user = User(
        company_id=company.id,
        email=payload.email,
        name=payload.name,
        role=payload.role if payload.role in ("owner", "bookkeeper", "readonly") else "owner",
        password_hash=get_password_hash(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    access, refresh = _issue_tokens(user)
    request.state.user = user
    request.state.company_id = user.company_id
    _log_auth_event("signup", user, request)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/auth/login", response_model=Token)
def login(
    payload: LoginRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> Token:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    access, refresh = _issue_tokens(user)
    request.state.user = user
    request.state.company_id = user.company_id
    _log_auth_event("login", user, request)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/auth/refresh", response_model=Token)
def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> Token:
    data = decode_refresh_token(payload.refresh_token)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user = session.get(User, UUID(data["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    access, refresh = _issue_tokens(user)
    _log_auth_event("refresh", user, request)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/auth/logout")
def logout(request: Request) -> dict:
    _log_auth_event("logout", request.state.user, request)
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserRead)
def me(request: Request, session: Session = Depends(get_session)) -> UserRead:
    user_id = request.state.user.id if request.state.user else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = session.get(User, user_id)
    return user


def _issue_tokens(user: User) -> tuple[str, str]:
    from src.config import settings

    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        company_id=user.company_id,
        role=user.role,
        expires_delta=access_expires,
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        company_id=user.company_id,
        role=user.role,
    )
    return access_token, refresh_token


def _log_auth_event(action: str, user: User, request: Request) -> None:
    ip = request.client.host if request.client else None
    from src.core.middleware import log_audit

    log_audit(
        company_id=user.company_id,
        user_id=user.id,
        action=f"auth.{action}",
        entity_type="User",
        entity_id=user.id,
        ip_address=ip,
    )

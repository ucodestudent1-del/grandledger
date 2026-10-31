"""Authentication endpoints: signup, login, refresh, logout, me, google."""
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.config import settings
from src.core.middleware import get_company_id, get_db, log_audit
from src.core.rate_limiter import limiter as shared_limiter
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from src.core.validation import validate_company_slug, validate_email, validate_password_strength
from src.models import Company, User
from src.schemas import (
    GoogleLoginRequest,
    GoogleSignupRequest,
    LoginRequest,
    RefreshRequest,
    Token,
    UserCreate,
    UserRead,
)

router = APIRouter(tags=["auth"])

_signup_limit = "1000/minute" if settings.ENVIRONMENT == "testing" else "5/minute"
_login_limit = "1000/minute" if settings.ENVIRONMENT == "testing" else "10/minute"


@router.post("/auth/signup", response_model=Token)
@shared_limiter.limit(_signup_limit)
def signup(
    payload: UserCreate,
    request: Request,
    session: Session = Depends(get_db),
) -> Token:
    valid, msg = validate_password_strength(payload.password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    email_valid, email_msg = validate_email(payload.email)
    if not email_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=email_msg,
        )

    if payload.company_slug:
        slug_valid, slug_msg = validate_company_slug(payload.company_slug)
        if not slug_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=slug_msg,
            )

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
@shared_limiter.limit(_login_limit)
def login(
    payload: LoginRequest,
    request: Request,
    session: Session = Depends(get_db),
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
@shared_limiter.limit(_login_limit)
def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Session = Depends(get_db),
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
def me(request: Request, session: Session = Depends(get_db)) -> UserRead:
    user_id = request.state.user.id if request.state.user else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = session.get(User, user_id)
    return user


@router.post("/auth/google", response_model=Token)
@shared_limiter.limit(_login_limit)
def google_login(
    payload: GoogleLoginRequest,
    request: Request,
    session: Session = Depends(get_db),
) -> Token:
    from google.auth import exceptions as google_exceptions
    from google.oauth2 import id_token as google_id_token

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google authentication is not configured",
        )

    try:
        info = google_id_token.verify_oauth2_token(
            payload.id_token,
            request=None,
            client_id=settings.GOOGLE_CLIENT_ID,
        )
    except google_exceptions.GoogleAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        ) from exc

    google_id = info.get("sub")
    email = info.get("email")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token missing required fields",
        )

    user = session.exec(select(User).where(User.google_id == google_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found. Please sign up with Google first.",
        )

    access, refresh = _issue_tokens(user)
    request.state.user = user
    request.state.company_id = user.company_id
    _log_auth_event("google_login", user, request)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/auth/google-signup", response_model=Token)
@shared_limiter.limit(_signup_limit)
def google_signup(
    payload: GoogleSignupRequest,
    request: Request,
    session: Session = Depends(get_db),
) -> Token:
    from google.auth import exceptions as google_exceptions
    from google.oauth2 import id_token as google_id_token

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google authentication is not configured",
        )

    try:
        info = google_id_token.verify_oauth2_token(
            payload.id_token,
            request=None,
            client_id=settings.GOOGLE_CLIENT_ID,
        )
    except google_exceptions.GoogleAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        ) from exc

    google_id = info.get("sub")
    email = info.get("email")
    name = info.get("name") or (email.split("@")[0] if email else "Unknown")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token missing required fields",
        )

    existing = session.exec(select(User).where(User.google_id == google_id)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists with this Google ID",
        )

    existing_email = session.exec(select(User).where(User.email == email)).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    email_valid, email_msg = validate_email(email)
    if not email_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=email_msg,
        )

    company_name = payload.company_name or name
    company_slug = payload.company_slug or email.split("@")[0]
    if payload.company_slug:
        slug_valid, slug_msg = validate_company_slug(payload.company_slug)
        if not slug_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=slug_msg,
            )

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
        email=email,
        name=name,
        role=payload.role if payload.role in ("owner", "bookkeeper", "readonly") else "owner",
        password_hash="",
        google_id=google_id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    access, refresh = _issue_tokens(user)
    request.state.user = user
    request.state.company_id = user.company_id
    _log_auth_event("google_signup", user, request)
    return Token(access_token=access, refresh_token=refresh)


@router.get("/users", response_model=list[UserRead])
@shared_limiter.limit("1000/minute")
def list_users(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> list[UserRead]:
    user: User = request.state.user
    if user.role not in ("owner", "accountant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    users = session.exec(select(User).where(User.company_id == company_id)).all()
    return users


@router.post("/users/invite", response_model=UserRead)
@shared_limiter.limit("1000/minute")
def invite_user(
    payload: UserCreate,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> UserRead:
    user: User = request.state.user
    if user.role not in ("owner", "accountant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    existing = session.exec(
        select(User).where(User.email == payload.email, User.company_id == company_id)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists in this company")

    new_user = User(
        company_id=company_id,
        email=payload.email,
        name=payload.name,
        role=payload.role if payload.role in ("owner", "bookkeeper", "readonly") else "bookkeeper",
        password_hash=get_password_hash(payload.password),
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    ip = request.client.host if request.client else None

    log_audit(
        company_id=company_id,
        user_id=user.id,
        action="user.invite",
        entity_type="User",
        entity_id=new_user.id,
        ip_address=ip,
    )

    return new_user


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

    log_audit(
        company_id=user.company_id,
        user_id=user.id,
        action=f"auth.{action}",
        entity_type="User",
        entity_id=user.id,
        ip_address=ip,
    )

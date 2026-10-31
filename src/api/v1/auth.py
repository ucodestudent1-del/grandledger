"""Authentication endpoints: signup, login, refresh, logout, me, google, password reset, email verification."""
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.config import settings
from src.core.email import email_service
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
from src.models import ActiveSession, Company, PasswordResetToken, User
from src.schemas import (
    GoogleLoginRequest,
    GoogleSignupRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    SessionRead,
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
        is_verified=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    access, refresh = _issue_tokens(user)
    request.state.user = user
    request.state.company_id = user.company_id
    _log_auth_event("signup", user, request)

    verify_token = _generate_verification_token(user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verify_token}"
    email_service.send_verification_email(
        to=user.email,
        verify_url=verify_url,
        user_name=user.name,
    )

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
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    if not user.is_verified and settings.ENVIRONMENT != "testing":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox.",
        )
    access, refresh, session_record = _issue_tokens_with_session(user, request)
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
    from datetime import UTC, datetime

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

    refresh_hash = _hash_token(payload.refresh_token)
    active_session = session.exec(
        select(ActiveSession).where(
            ActiveSession.user_id == user.id,
            ActiveSession.refresh_token_hash == refresh_hash,
            ActiveSession.revoked is False,
        )
    ).first()

    if not active_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or revoked. Please log in again.",
        )

    if active_session.expires_at < datetime.now(UTC):
        active_session.revoked = True
        session.add(active_session)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
        )

    active_session.last_used_at = datetime.now(UTC)
    session.add(active_session)
    session.commit()

    access, refresh, _ = _issue_tokens_with_session(user, request, replace_session_id=active_session.id)
    _log_auth_event("refresh", user, request)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/auth/logout")
def logout(
    request: Request,
    session: Session = Depends(get_db),
    payload: RefreshRequest | None = None,
) -> dict:
    _log_auth_event("logout", request.state.user, request)

    if payload and payload.refresh_token:
        refresh_hash = _hash_token(payload.refresh_token)
        active_session = session.exec(
            select(ActiveSession).where(
                ActiveSession.user_id == request.state.user.id,
                ActiveSession.refresh_token_hash == refresh_hash,
                ActiveSession.revoked is False,
            )
        ).first()
        if active_session:
            active_session.revoked = True
            session.add(active_session)
            session.commit()

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

    access, refresh, _ = _issue_tokens_with_session(user, request)
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
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    access, refresh, _ = _issue_tokens_with_session(user, request)
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



def _hash_token(token: str) -> str:
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


def _issue_tokens(user: User) -> tuple[str, str]:
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


def _issue_tokens_with_session(
    user: User,
    request: Request,
    replace_session_id: UUID | None = None,
) -> tuple[str, str, ActiveSession]:
    from datetime import UTC, datetime

    from src.database import engine as db_engine

    with Session(db_engine) as sess:
        access, refresh = _issue_tokens(user)
        refresh_hash = _hash_token(refresh)
        now = datetime.now(UTC)
        refresh_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        if replace_session_id:
            existing = sess.get(ActiveSession, replace_session_id)
            if existing:
                existing.refresh_token_hash = refresh_hash
                existing.expires_at = refresh_expires
                existing.revoked = False
                existing.last_used_at = now
                existing.user_agent = request.headers.get("user-agent")
                existing.ip_address = request.client.host if request.client else None
                sess.add(existing)
                sess.commit()
                sess.refresh(existing)
                return access, refresh, existing

        ip = request.client.host if request.client else None
        session_record = ActiveSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            user_agent=request.headers.get("user-agent"),
            ip_address=ip,
            expires_at=refresh_expires,
        )
        sess.add(session_record)
        sess.commit()
        sess.refresh(session_record)
        return access, refresh, session_record


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


@router.post("/auth/forgot-password")
@shared_limiter.limit("5/minute")
def forgot_password(
    payload: PasswordResetRequest,
    request: Request,
    session: Session = Depends(get_db),
) -> dict:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not user.is_active:
        return {"message": "If the email exists, a reset link has been sent"}

    from datetime import UTC, datetime
    from secrets import token_urlsafe

    reset_token = token_urlsafe(32)
    reset_hash = _hash_token(reset_token)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=reset_hash,
        expires_at=expires_at,
    )
    session.add(reset_record)
    session.commit()

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}&uid={user.id}"
    email_service.send_password_reset(
        to=user.email,
        reset_url=reset_url,
        user_name=user.name,
    )

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/auth/reset-password")
@shared_limiter.limit("5/minute")
def reset_password(
    payload: PasswordResetConfirm,
    request: Request,
    session: Session = Depends(get_db),
) -> dict:
    valid, msg = validate_password_strength(payload.new_password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    token_hash = _hash_token(payload.token)
    reset_record = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used is False,
        )
    ).first()

    if not reset_record or reset_record.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = session.get(User, reset_record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.password_hash = get_password_hash(payload.new_password)
    reset_record.used = True
    session.add(user)
    session.add(reset_record)
    session.commit()

    log_audit(
        company_id=user.company_id,
        user_id=user.id,
        action="auth.password_reset",
        entity_type="User",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    return {"message": "Password reset successfully"}


@router.post("/auth/verify-email")
def verify_email(
    token: str,
    request: Request,
    session: Session = Depends(get_db),
) -> dict:
    from src.core.security import decode_access_token

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user = session.get(User, UUID(payload["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_verified = True
    session.add(user)
    session.commit()

    log_audit(
        company_id=user.company_id,
        user_id=user.id,
        action="auth.email_verified",
        entity_type="User",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    return {"message": "Email verified successfully"}


@router.post("/auth/invite-user", response_model=UserRead)
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
        is_verified=False,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    ip = request.client.host if request.client else None
    company_obj = session.get(Company, company_id)
    login_url = f"{settings.FRONTEND_URL}/login"

    log_audit(
        company_id=company_id,
        user_id=user.id,
        action="user.invite",
        entity_type="User",
        entity_id=new_user.id,
        ip_address=ip,
    )

    email_service.send_invitation(
        to=new_user.email,
        login_url=login_url,
        user_name=new_user.name,
        company_name=company_obj.name if company_obj else "a company",
        temp_password=payload.password,
    )

    return new_user


@router.get("/auth/sessions", response_model=list[SessionRead])
def list_sessions(
    request: Request,
    session: Session = Depends(get_db),
) -> list[SessionRead]:
    user: User = request.state.user
    sessions = session.exec(
        select(ActiveSession).where(
            ActiveSession.user_id == user.id,
            ActiveSession.revoked is False,
        ).order_by(ActiveSession.created_at.desc())
    ).all()
    return sessions


@router.delete("/auth/sessions/{session_id}")
def revoke_session(
    session_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
) -> dict:
    user: User = request.state.user
    active_session = session.get(ActiveSession, session_id)
    if not active_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if active_session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke your own sessions",
        )
    active_session.revoked = True
    session.add(active_session)
    session.commit()

    _log_auth_event("session_revoked", user, request)
    return {"message": "Session revoked"}


@router.delete("/auth/sessions")
def revoke_all_sessions(
    request: Request,
    session: Session = Depends(get_db),
) -> dict:
    user: User = request.state.user
    stmt = (
        ActiveSession.__table__.update()
        .where(
            ActiveSession.user_id == user.id,
            ActiveSession.revoked is False,
        )
        .values(revoked=True)
    )
    session.exec(stmt)
    session.commit()

    _log_auth_event("all_sessions_revoked", user, request)
    return {"message": "All sessions revoked"}


def _generate_verification_token(user: User) -> str:
    return create_access_token(
        subject=str(user.id),
        company_id=user.company_id,
        role=user.role,
        expires_delta=timedelta(minutes=settings.VERIFY_TOKEN_EXPIRE_MINUTES),
    )

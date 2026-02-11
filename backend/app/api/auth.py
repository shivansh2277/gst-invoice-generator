"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import Token, UserCreate, UserRead
from app.services.metrics_service import inc
from app.services.rate_limit import rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Register a new user account."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, full_name=payload.full_name, password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    """Issue JWT token for valid credentials."""
    rate_key = f"login:{form_data.username}:{request.client.host if request.client else 'unknown'}"
    if not rate_limiter.allow(rate_key, limit=10, per_seconds=60):
        raise HTTPException(status_code=429, detail="Login rate limit exceeded")

    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        inc("auth_login_fail_total")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    inc("auth_login_success_total")
    return Token(access_token=create_access_token(user.email))

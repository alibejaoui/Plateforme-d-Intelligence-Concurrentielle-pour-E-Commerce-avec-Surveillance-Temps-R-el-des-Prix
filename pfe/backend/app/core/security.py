"""
Security utilities for authentication and password hashing
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.core.database import get_db
from app.models.user import User

# Password hashing context
# Use pbkdf2_sha256 for new hashes, but still accept existing bcrypt hashes.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

# HTTP Bearer scheme for JWT auth in Swagger/OpenAPI.
# This intentionally avoids OAuth2 password flow in docs.
bearer_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Bcrypt only uses the first 72 bytes of a password. To avoid runtime errors
    from overly long inputs, we explicitly truncate here.
    """
    safe_password = plain_password[:72]
    try:
        return pwd_context.verify(safe_password, hashed_password)
    except Exception:
        # If stored hash is malformed/plain-text, treat as invalid credentials
        # instead of crashing auth flow with a 500.
        return False


def get_password_hash(password: str) -> str:
    """Hash a password.

    Bcrypt only supports passwords up to 72 bytes. We truncate to 72 characters
    so user input longer than that does not cause a ValueError.
    """
    safe_password = password[:72]
    return pwd_context.hash(safe_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token (always return str for JSON compatibility)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt if isinstance(encoded_jwt, str) else encoded_jwt.decode("utf-8")


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt if isinstance(encoded_jwt, str) else encoded_jwt.decode("utf-8")


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def is_admin(user: User) -> bool:
    return user.role == "admin"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Load the authenticated user from the token (DB lookup for role and profile)."""
    token = credentials.credentials if credentials else None
    # Be tolerant to accidental "Bearer <jwt>" pasted into Swagger's bearer field.
    # HTTPBearer already handles the Authorization scheme, so we only need the raw JWT.
    if token:
        token = token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

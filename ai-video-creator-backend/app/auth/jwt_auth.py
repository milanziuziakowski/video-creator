"""JWT-based authentication for FastAPI.

This module provides simple username/password authentication with JWT tokens.
Based on FastAPI's official OAuth2 with JWT tutorial.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from pwdlib import PasswordHash

from app.config import settings

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # Subject - username
    user_id: str  # User ID from database
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data extracted from JWT."""

    username: Optional[str] = None
    user_id: Optional[str] = None


# Password hashing using Argon2 (recommended algorithm)
password_hash = PasswordHash.recommended()

# OAuth2 scheme - will look for token in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return password_hash.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


async def get_current_user_token(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    """Validate JWT token and extract user data.
    
    This is a FastAPI dependency that validates the token from the
    Authorization header and returns the token data.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        TokenData with username and user_id
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # For development, allow bypassing auth with a special token
    if settings.is_development and token == "dev-token":
        return TokenData(
            username="dev@example.com",
            user_id="dev-user-id",
        )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None:
            raise credentials_exception
            
        return TokenData(username=username, user_id=user_id)
        
    except InvalidTokenError as e:
        logger.error(f"Token validation failed: {e}")
        raise credentials_exception

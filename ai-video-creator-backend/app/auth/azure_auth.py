"""Azure Entra ID token validation."""

import logging
from typing import Optional
from functools import lru_cache

import httpx
from jose import jwt, JWTError
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """Validated token payload."""

    sub: str  # Subject - Object ID
    oid: str  # Object ID (same as sub for v2 tokens)
    preferred_username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    tid: str  # Tenant ID


@lru_cache(maxsize=1)
def get_jwks_url() -> str:
    """Get JWKS URL for the tenant."""
    return f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/discovery/v2.0/keys"


@lru_cache(maxsize=1)
def get_issuer() -> str:
    """Get expected token issuer."""
    return f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/v2.0"


_cached_jwks: Optional[dict] = None


async def fetch_jwks() -> dict:
    """Fetch JSON Web Key Set from Azure."""
    global _cached_jwks

    if _cached_jwks is not None:
        return _cached_jwks

    async with httpx.AsyncClient() as client:
        response = await client.get(get_jwks_url())
        response.raise_for_status()
        _cached_jwks = response.json()
        return _cached_jwks


async def validate_token(token: str) -> TokenPayload:
    """Validate Azure Entra ID access token.

    Args:
        token: JWT access token from Authorization header

    Returns:
        TokenPayload with user information

    Raises:
        ValueError: If token is invalid
    """
    # For development, allow bypassing auth with a special token
    if settings.is_development and token == "dev-token":
        return TokenPayload(
            sub="dev-user-id",
            oid="dev-user-id",
            preferred_username="dev@example.com",
            email="dev@example.com",
            name="Development User",
            tid="dev-tenant",
        )

    try:
        # Fetch JWKS
        jwks = await fetch_jwks()

        # Get unverified headers to find the key
        unverified_header = jwt.get_unverified_header(token)

        # Find the matching key
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise ValueError("Unable to find appropriate key")

        # Verify and decode token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.AZURE_CLIENT_ID,
            issuer=get_issuer(),
        )

        return TokenPayload(
            sub=payload["sub"],
            oid=payload.get("oid", payload["sub"]),
            preferred_username=payload.get("preferred_username"),
            email=payload.get("email"),
            name=payload.get("name"),
            tid=payload["tid"],
        )

    except JWTError as e:
        logger.error(f"Token validation failed: {e}")
        raise ValueError(f"Invalid token: {e}")


# FastAPI security scheme
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """FastAPI dependency to validate token and return payload."""
    try:
        return await validate_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

# Azure Entra ID Setup Guide

**Phase:** 6  
**Purpose:** Manual Azure Portal configuration for authentication

---

## Overview

This guide covers the manual steps required to configure Azure Entra ID (formerly Azure AD) for the AI Video Creator application. These steps must be completed in the Azure Portal before the frontend authentication will work.

---

## 1. Prerequisites

- Azure subscription with Owner or Contributor role
- Access to Azure Entra ID (Azure Active Directory)
- Tenant ID from your Azure organization

---

## 2. App Registration for Frontend (SPA)

### 2.1 Create App Registration

1. Navigate to **Azure Portal** → **Microsoft Entra ID** → **App registrations**
2. Click **+ New registration**
3. Fill in the details:
   - **Name:** `AI Video Creator - Frontend`
   - **Supported account types:** Select based on your needs:
     - Single tenant: Only accounts in this organizational directory
     - Multi-tenant: Accounts in any organizational directory
   - **Redirect URI:**
     - Platform: **Single-page application (SPA)**
     - URI: `http://localhost:5173` (for development)
4. Click **Register**
5. **Save the Application (client) ID** - you'll need this for `VITE_AZURE_CLIENT_ID`

### 2.2 Configure Authentication

1. Go to **Authentication** in the left menu
2. Under **Single-page application**, add additional Redirect URIs:
   ```
   http://localhost:5173
   http://localhost:3000
   https://your-production-domain.com
   ```
3. Under **Implicit grant and hybrid flows**:
   - ☐ Access tokens (leave unchecked - we use PKCE)
   - ☐ ID tokens (leave unchecked)
4. Under **Advanced settings**:
   - Allow public client flows: **No**
5. Click **Save**

### 2.3 Configure API Permissions

1. Go to **API permissions** in the left menu
2. Click **+ Add a permission**
3. Select **Microsoft Graph** → **Delegated permissions**
4. Add these permissions:
   - `User.Read` (Sign in and read user profile)
   - `openid` (Sign users in)
   - `profile` (View users' basic profile)
   - `email` (View users' email address)
5. Click **Add permissions**
6. If required by your organization, click **Grant admin consent for [Tenant Name]**

### 2.4 Expose an API (for Backend Access)

1. Go to **Expose an API** in the left menu
2. Click **Set** next to Application ID URI
3. Accept the default `api://{client-id}` or customize it
4. Click **Save**
5. Click **+ Add a scope**:
   - **Scope name:** `access_as_user`
   - **Who can consent:** Admins and users
   - **Admin consent display name:** Access AI Video Creator API
   - **Admin consent description:** Allows the app to access AI Video Creator API on behalf of the signed-in user
   - **User consent display name:** Access AI Video Creator
   - **User consent description:** Allows the app to access AI Video Creator API on your behalf
   - **State:** Enabled
6. Click **Add scope**

---

## 3. App Registration for Backend API (Optional)

If you want to validate tokens on the backend with a separate app registration:

### 3.1 Create App Registration

1. Navigate to **App registrations** → **+ New registration**
2. Fill in:
   - **Name:** `AI Video Creator - Backend API`
   - **Supported account types:** Same as frontend
3. Click **Register**
4. **Save the Application (client) ID**

### 3.2 Configure Token Validation

1. Go to **Expose an API**
2. Set Application ID URI: `api://ai-video-creator-api`
3. Add scope: `access_as_user`
4. Go to **Certificates & secrets** → **+ New client secret**
5. Save the secret value securely

### 3.3 Update Frontend API Permissions

1. Go back to **AI Video Creator - Frontend** app registration
2. **API permissions** → **+ Add a permission**
3. Select **My APIs** → **AI Video Creator - Backend API**
4. Check `access_as_user`
5. Click **Add permissions**

---

## 4. Configuration Values

After completing the setup, collect these values:

### Frontend (.env)

```bash
# From "AI Video Creator - Frontend" app registration
VITE_AZURE_CLIENT_ID=<Application (client) ID>
VITE_AZURE_TENANT_ID=<Directory (tenant) ID>
VITE_AZURE_REDIRECT_URI=http://localhost:5173
```

### Backend (.env)

```bash
# For token validation
AZURE_TENANT_ID=<Directory (tenant) ID>
AZURE_CLIENT_ID=<Frontend Application (client) ID>
# OR if using separate backend app:
# AZURE_CLIENT_ID=<Backend Application (client) ID>
```

### Finding Your Tenant ID

1. Go to **Microsoft Entra ID** → **Overview**
2. Copy **Tenant ID** (also called Directory ID)

---

## 5. Token Validation on Backend

### 5.1 Install Dependencies

```bash
uv add python-jose[cryptography] httpx
```

### 5.2 JWT Validation (app/auth/azure_auth.py)

```python
"""Azure Entra ID token validation."""

import logging
from typing import Optional
from functools import lru_cache

import httpx
from jose import jwt, JWTError
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """Validated token payload."""
    
    sub: str  # Object ID
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


async def fetch_jwks() -> dict:
    """Fetch JSON Web Key Set from Azure."""
    async with httpx.AsyncClient() as client:
        response = await client.get(get_jwks_url())
        response.raise_for_status()
        return response.json()


async def validate_token(token: str) -> TokenPayload:
    """Validate Azure Entra ID access token.
    
    Args:
        token: JWT access token from Authorization header
        
    Returns:
        TokenPayload with user information
        
    Raises:
        ValueError: If token is invalid
    """
    try:
        # Fetch JWKS
        jwks = await fetch_jwks()
        
        # Get unverified headers to find the key
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the matching key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
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


# FastAPI dependency
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
```

### 5.3 User Resolution (app/api/deps.py)

```python
"""FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.azure_auth import get_current_user_token, TokenPayload
from app.db.session import get_db_session
from app.db.models.user import User
from app.services.user_service import UserService


async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    token: TokenPayload = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get or create user from Azure token.
    
    This automatically creates a user record on first login.
    """
    service = UserService(db)
    
    user = await service.get_or_create_user(
        entra_id=token.oid,
        email=token.email or token.preferred_username,
        name=token.name,
    )
    
    return user
```

---

## 6. Common Issues & Troubleshooting

### 6.1 CORS Errors

**Symptom:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
- Ensure backend CORS is configured correctly
- Check that the frontend origin is in `CORS_ORIGINS`
- For development, include `http://localhost:5173`

### 6.2 Invalid Audience

**Symptom:** `aud claim does not match`

**Solution:**
- Ensure `AZURE_CLIENT_ID` in backend matches the frontend app registration
- If using separate backend app, add the backend API to frontend permissions

### 6.3 Token Expired

**Symptom:** `Token is expired`

**Solution:**
- MSAL should handle token refresh automatically
- Check that `acquireTokenSilent` is being called before API requests

### 6.4 Redirect URI Mismatch

**Symptom:** `AADSTS50011: The redirect URI specified in the request does not match`

**Solution:**
- Add all redirect URIs in Azure Portal (including port numbers)
- Ensure exact match including protocol (http vs https)
- Check for trailing slashes

### 6.5 Admin Consent Required

**Symptom:** `AADSTS65001: The user or administrator has not consented`

**Solution:**
- Click "Grant admin consent" in API permissions
- Or have users consent individually during login

---

## 7. Security Best Practices

1. **Use PKCE flow** (default in MSAL) - never use implicit grant
2. **Store tokens in sessionStorage** - not localStorage
3. **Validate tokens on every API request**
4. **Use short token lifetimes** - 1 hour is standard
5. **Implement proper logout** - clear all tokens and MSAL cache
6. **Use scopes appropriately** - only request what you need
7. **Enable conditional access** if available in your tenant

---

## 8. Next Steps

After completing Azure Entra setup:

1. **Test authentication flow:**
   - Start frontend: `npm run dev`
   - Click login and verify redirect
   - Check that tokens are acquired

2. **Verify backend integration:**
   - Make authenticated API request
   - Check token validation logs

3. **Proceed to CI/CD Pipeline:**
   - See [07-CI-CD-PIPELINE.md](./07-CI-CD-PIPELINE.md)

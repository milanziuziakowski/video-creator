# JWT Authentication Setup Guide

**Phase:** 6  
**Purpose:** JWT-based authentication configuration and implementation

---

## Overview

This guide covers JWT (JSON Web Token) authentication for the AI Video Creator application. The system uses a simple username/password authentication with JWT access tokens, secured with Argon2 password hashing.

**Key Features:**
- OAuth2 password flow with JWT tokens
- Argon2 password hashing (secure against modern attacks)
- Configurable token expiration (default: 24 hours)
- HSA256 signing algorithm
- No external identity provider required

---

## 1. Prerequisites

- Python 3.11+
- FastAPI application running
- SQLAlchemy models set up
- Environment variables configured

---

## 2. Environment Configuration

### 2.1 Set JWT Secret Key

**CRITICAL:** Generate a secure secret key in production:

```powershell
# Windows PowerShell
# Use an online tool or Python:
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.2 .env File Configuration

```bash
# JWT Authentication
JWT_SECRET_KEY=your-generated-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# API Configuration
OPENAI_API_KEY=your-openai-key
MINIMAX_API_KEY=your-minimax-key

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/video_creator

# CORS - Frontend URLs
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://yourdomain.com

# Application
APP_ENV=development
DEBUG=true
```

### 2.3 Configuration in Code (app/config.py)

The settings are loaded from environment variables:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT Authentication
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # ... other settings
```

---

## 3. Core Authentication Components

### 3.1 Password Hashing (app/auth/jwt_auth.py)

Uses Argon2 for secure password hashing:

```python
from pwdlib import PasswordHash

# Argon2 is recommended - resistant to GPU/ASIC attacks
password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hash."""
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return password_hash.hash(password)
```

### 3.2 Token Creation

Create JWT tokens with user information:

```python
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.
    
    Args:
        data: Claims to encode (e.g., {"sub": "username", "user_id": "123"})
        expires_delta: Optional custom expiration
        
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
```

### 3.3 Token Validation (app/auth/jwt_auth.py)

Validate tokens and extract user information:

```python
async def get_current_user_token(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    """Validate JWT token and return token data.
    
    FastAPI dependency that:
    1. Extracts token from Authorization header
    2. Verifies signature and expiration
    3. Returns decoded token data
    
    Raises:
        HTTPException 401: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(
            username=username,
            user_id=user_id,
        )
    except InvalidTokenError:
        raise credentials_exception
    
    return token_data
```

---

## 4. Database Models

### 4.1 User Model (app/db/models/user.py)

```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
from uuid import uuid4

Base = declarative_base()

class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 5. API Endpoints

### 5.1 Registration (app/api/v1/auth.py)

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.auth.jwt_auth import get_password_hash, create_access_token, Token
from app.db.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserRegister(BaseModel):
    """User registration data."""
    username: str  # Min 3 chars, alphanumeric
    email: EmailStr
    password: str  # Min 8 chars
    full_name: Optional[str] = None

@router.post("/register", response_model=dict)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user.
    
    Args:
        user_data: Registration form data
        db: Database session
        
    Returns:
        Success message with user ID
        
    Raises:
        400: If username or email already exists
    """
    service = UserService(db)
    
    # Check if user exists
    existing = await service.get_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = await service.create_user(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )
    
    return {"user_id": user.id, "message": "User created successfully"}
```

### 5.2 Login (Token Endpoint)

```python
class LoginRequest(BaseModel):
    """Login credentials."""
    username: str
    password: str

@router.post("/token", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT token.
    
    Args:
        credentials: Username and password
        db: Database session
        
    Returns:
        access_token: JWT token to use in Authorization header
        token_type: "bearer"
        
    Raises:
        401: If credentials are invalid
    """
    service = UserService(db)
    user = await service.authenticate_user(
        credentials.username,
        credentials.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with user claims
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
```

### 5.3 Protected Routes

```python
@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user info."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }
```

---

## 6. FastAPI Dependency Injection

### 6.1 Setup (app/api/deps.py)

```python
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_auth import get_current_user_token, TokenData
from app.db.session import get_db_session
from app.db.models.user import User
from app.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db_session():
        yield session


async def get_current_user(
    token: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from JWT token.
    
    This dependency:
    1. Validates JWT token from Authorization header
    2. Extracts user_id and username
    3. Retrieves user from database
    4. Checks user is active
    
    Usage:
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_user)
        ):
            return {"user_id": current_user.id}
    """
    service = UserService(db)
    user = await service.get_by_username(token.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    return user
```

### 6.2 Using in Route Handlers

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter()

@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create project for current user.
    
    The Depends(get_current_user) will:
    - Require Authorization header with "Bearer <token>"
    - Validate the token
    - Return the authenticated user
    - Return 401 if token is missing or invalid
    """
    service = ProjectService(db)
    return await service.create_project(current_user.id, project_data)
```

---

## 7. Frontend Integration

### 7.1 Storing Tokens

```typescript
// src/auth/tokenService.ts
export const tokenService = {
  setToken: (token: string) => {
    // Store in sessionStorage (not localStorage for security)
    sessionStorage.setItem("access_token", token);
  },
  
  getToken: (): string | null => {
    return sessionStorage.getItem("access_token");
  },
  
  clearToken: () => {
    sessionStorage.removeItem("access_token");
  },
  
  isTokenValid: (): boolean => {
    const token = tokenService.getToken();
    if (!token) return false;
    
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.exp > Date.now() / 1000;
    } catch {
      return false;
    }
  },
};
```

### 7.2 API Client with Token

```typescript
// src/api/client.ts
import axios from "axios";
import { tokenService } from "@/auth/tokenService";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
});

// Add token to every request
apiClient.interceptors.request.use((config) => {
  const token = tokenService.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      tokenService.clearToken();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

### 7.3 Login Hook

```typescript
// src/api/hooks/useAuth.ts
export function useLogin() {
  const mutation = useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const { data } = await apiClient.post<Token>(
        "/auth/token",
        credentials
      );
      return data;
    },
    onSuccess: (data) => {
      tokenService.setToken(data.access_token);
      // Redirect to dashboard
      navigate("/dashboard");
    },
  });
  
  return mutation;
}
```

---

## 8. Security Best Practices

### 8.1 Password Requirements

Enforce strong passwords:
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, special chars
- No common patterns (e.g., "password123")

```python
import re
from pydantic import field_validator

class UserRegister(BaseModel):
    password: str
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain special character")
        return v
```

### 8.2 Token Security

- **Short expiration:** Default 24 hours (adjust based on risk)
- **Secure storage:** sessionStorage (not localStorage)
- **HTTPS only:** Always use HTTPS in production
- **No token in logs:** Never log full tokens
- **Rotation:** Implement optional token refresh

### 8.3 Database Security

```python
# Never store plain passwords
user.hashed_password = get_password_hash(password)
await db.commit()

# Always verify before returning
if not verify_password(plain_password, user.hashed_password):
    return None  # Authentication failed
```

### 8.4 Rate Limiting

Protect login endpoint from brute force:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/token")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest, ...):
    # Max 5 login attempts per minute per IP
    pass
```

### 8.5 CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 9. Common Issues & Troubleshooting

### 9.1 "Could not validate credentials"

**Symptom:** 401 error on protected routes

**Solutions:**
- Check Authorization header format: `Bearer <token>`
- Verify JWT_SECRET_KEY matches between requests
- Check token hasn't expired
- Ensure user exists in database

### 9.2 "User not found"

**Symptom:** 401 even with valid token

**Solutions:**
- User may have been deleted
- Check username in token matches database
- Verify user is_active = True

### 9.3 Token Validation Fails Locally

**Symptom:** Different secret keys between sessions

**Solutions:**
- Add `.env` to git ignore
- Use environment variables
- Don't hardcode secrets

### 9.4 CORS Errors on Login

**Symptom:** Login POST blocked by CORS

**Solutions:**
- Add frontend origin to CORS_ORIGINS
- Include credentials in requests
- Use POST method (not GET)

---

## 10. Token Refresh (Optional Enhancement)

For longer sessions with automatic refresh:

```python
class RefreshToken(BaseModel):
    refresh_token: str

def create_refresh_token(user_id: str) -> str:
    """Create long-lived refresh token."""
    return create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=7),
    )

@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshToken,
    db: AsyncSession = Depends(get_db),
):
    """Get new access token using refresh token."""
    token_data = await get_current_user_token(refresh_data.refresh_token)
    
    if token_data.token_type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = await UserService(db).get_by_id(token_data.user_id)
    
    new_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return {"access_token": new_token, "token_type": "bearer"}
```

---

## 11. Testing Authentication

### 11.1 Backend Tests

```python
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/token",
        json={"username": "testuser", "password": "TestPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_protected_route_unauthorized(client: AsyncClient):
    """Test protected route without token."""
    response = await client.get("/api/v1/projects")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_with_token(client: AsyncClient, test_user: User):
    """Test protected route with valid token."""
    token = create_access_token(
        {"sub": test_user.username, "user_id": test_user.id}
    )
    response = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
```

### 11.2 Frontend E2E Tests

```typescript
test("should login and access protected page", async ({ page }) => {
  // Go to login
  await page.goto("/login");
  
  // Fill credentials
  await page.fill('[data-testid="username"]', "testuser");
  await page.fill('[data-testid="password"]', "TestPass123!");
  
  // Submit
  await page.click('[data-testid="login-button"]');
  
  // Should redirect to dashboard
  await expect(page).toHaveURL("/dashboard");
  
  // Token should be in sessionStorage
  const token = await page.evaluate(() =>
    sessionStorage.getItem("access_token")
  );
  expect(token).toBeTruthy();
});
```

---

## 12. Production Deployment Checklist

- [ ] Generate new JWT_SECRET_KEY with `openssl rand -hex 32`
- [ ] Set JWT_SECRET_KEY in Azure Key Vault or secret manager
- [ ] Configure HTTPS for all endpoints
- [ ] Set ACCESS_TOKEN_EXPIRE_MINUTES appropriately
- [ ] Enable rate limiting on /auth/token
- [ ] Configure CORS for production domain only
- [ ] Enable HTTPS redirect
- [ ] Set DEBUG=false
- [ ] Configure logging with sensitive data redacted
- [ ] Set up monitoring for 401 errors
- [ ] Test token expiration behavior
- [ ] Document password requirements for users

---

## 13. Next Steps

After JWT authentication is set up:

1. **Test authentication flow:**
   - Register a new user
   - Login and get token
   - Use token to access protected routes

2. **Implement in all endpoints:**
   - Add `get_current_user` dependency to protected routes
   - Return 401 for missing/invalid tokens

3. **Frontend integration:**
   - Store tokens securely
   - Add token to all API requests
   - Implement logout and token refresh

4. **Proceed to CI/CD Pipeline:**
   - See [07-CI-CD-PIPELINE.md](./07-CI-CD-PIPELINE.md)

---

## References

- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [JWT.io](https://jwt.io) - JWT debugging and specification
- [Argon2 (Password Hashing)](https://argon2-cffi.readthedocs.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [python-jose Documentation](https://python-jose.readthedocs.io/)

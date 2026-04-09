import os
import uuid
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.sql_db import get_db
from app.models.user import User

# --- RSA Key Management ---

# Ensure we have RSA keys for RS256 signing
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")

if not JWT_PRIVATE_KEY or not JWT_PUBLIC_KEY:
    raise ValueError("JWT_PRIVATE_KEY and JWT_PUBLIC_KEY must be set in the environment variables.")

# Because standard .env sometimes wraps newlines in quoted strings literally:
if JWT_PRIVATE_KEY:
    JWT_PRIVATE_KEY = JWT_PRIVATE_KEY.replace('\\n', '\n')
if JWT_PUBLIC_KEY:
    JWT_PUBLIC_KEY = JWT_PUBLIC_KEY.replace('\\n', '\n')

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

from app.models.user import User, BlacklistedToken

# Simple in-memory blacklist (Replace with Redis in production)
# blacklisted_jtis = set() # Removed

# OAuth scheme for FastAPI to extract bearer tokens from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

# --- Token Operations ---

def create_access_token(user: User, company_name: str = "") -> str:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "permissions": user.permissions,
        "company_id": user.company_id,
        "company_name": company_name,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "jti": jti,
        "type": "access"
    }
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: User) -> str:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user.id),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "jti": jti,
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm=ALGORITHM)


def decode_token(token: str, db: Session) -> dict:
    try:
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti:
            if db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first():
                raise JWTError("Token has been revoked/logged out")
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- Dependencies ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency to retrieve the current auth user from the Bearer token."""
    payload = decode_token(token, db)
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
        
    user = db.query(User).filter(User.id == int(user_id_str)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    return user


class RoleChecker:
    """Dependency injection class to enforce RBAC securely on specific routes."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        # Admin bypass
        if user.role == "admin":
            return user
            
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires one of: {', '.join(self.allowed_roles)}"
            )
        return user

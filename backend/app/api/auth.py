from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.sql_db import get_db
from app.models.user import User, Company
from app.core.security import verify_password, get_password_hash, validate_password_complexity
from app.core.auth import create_access_token, create_refresh_token, decode_token, get_current_user

router = APIRouter()

class SetupAdminRequest(BaseModel):
    email: EmailStr
    password: str
    employee_id: str
    company_name: str  # NEW: required for multi-tenancy

@router.post("/setup-admin", summary="Setup a new company with its first Admin user")
def setup_admin(data: SetupAdminRequest, db: Session = Depends(get_db)):
    """Create a new Company and its first Admin user. One admin per company via this route."""
    email = data.email.lower()
    # Check if company already exists
    existing_company = db.query(Company).filter(Company.name == data.company_name).first()
    if existing_company:
        raise HTTPException(status_code=400, detail=f"Company '{data.company_name}' already exists. Contact the existing admin.")
    
    # Check if email already taken
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")
        
    try:
        validate_password_complexity(data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 1. Create Company
    company = Company(
        name=data.company_name,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(company)
    db.flush()  # Get company.id before committing
    
    # 2. Create Admin user linked to this company
    admin = User(
        email=email,
        hashed_password=get_password_hash(data.password),
        role="admin",
        company_id=company.id,
        permissions=["read:manuals", "write:diagnostics", "admin:all"]
    )
    admin.employee_id = data.employee_id
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {"message": f"Company '{data.company_name}' created with admin {data.email}"}


class SetupSuperAdminRequest(BaseModel):
    email: EmailStr
    password: str
    employee_id: str

@router.post("/setup-superadmin", summary="Setup the initial platform super admin")
def setup_superadmin(data: SetupSuperAdminRequest, db: Session = Depends(get_db)):
    """Creates the first and only super admin. Fails if a super admin already exists."""
    email = data.email.lower()
    # Ensure no superadmin exists yet
    existing_superadmin = db.query(User).filter(User.role == "superadmin").first()
    if existing_superadmin:
        raise HTTPException(status_code=400, detail="A super admin already exists.")

    try:
        validate_password_complexity(data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create the internal Platform company if it doesn't exist
    platform_name = "IndustriFix Platform"
    platform_company = db.query(Company).filter(Company.name == platform_name).first()
    if not platform_company:
        platform_company = Company(
            name=platform_name,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        db.add(platform_company)
        db.flush()

    # Create Super Admin User
    superadmin = User(
        email=email,
        hashed_password=get_password_hash(data.password),
        role="superadmin",
        company_id=platform_company.id,
        permissions=["admin:all", "superadmin:all"]
    )
    superadmin.employee_id = data.employee_id
    
    db.add(superadmin)
    db.commit()
    db.refresh(superadmin)
    return {"message": f"Super admin {data.email} successfully created."}


@router.post("/login", summary="Exchange credentials for JWT tokens")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Validates email/password, returns Access Token, sets HttpOnly cookie for Refresh Token."""
    email = form_data.username.lower()
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user account is disabled
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been disabled. Contact your company admin.",
        )

    # Look up company and check its status
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    if not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your company account has been suspended. Please contact platform support.",
        )
    
    company_name = company.name if company else "Unknown"
        
    access_token = create_access_token(user, company_name)
    refresh_token = create_refresh_token(user)
    
    # Store refresh token securely in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions,
            "company_name": company_name
        }
    }


@router.post("/refresh", summary="Obtain a new Access Token via Refresh Cookie")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Validates the Refresh Token from the cookie and issues a fresh Access Token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
        
    payload = decode_token(refresh_token, db)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        
    user_id_str = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id_str)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    company = db.query(Company).filter(Company.id == user.company_id).first()
    company_name = company.name if company else "Unknown"
        
    new_access_token = create_access_token(user, company_name)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout", summary="Logout and revoke tokens")
def logout(request: Request, response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes the current access token and clears the refresh cookie."""
    from app.models.user import BlacklistedToken
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = decode_token(token, db)
        jti = payload.get("jti")
        if jti:
            db.add(BlacklistedToken(jti=jti))
            db.commit()

    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}

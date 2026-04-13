"""Admin-only endpoints for managing users and documents within the admin's company."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.sql_db import get_db
from app.models.user import User, Document
from app.core.security import get_password_hash, validate_password_complexity
from app.core.auth import RoleChecker, get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])
admin_only = RoleChecker(["admin"])


# ── Schemas ──────────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "viewer"
    employee_id: Optional[str] = None


# ── User Management ─────────────────────────────────────────────

@router.get("/users", summary="List users in admin's company")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    users = db.query(User).filter(User.company_id == current_user.company_id).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
        }
        for u in users
    ]


@router.post("/users", summary="Create user in admin's company")
def create_user(
    data: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    # Only viewer/engineer roles can be created — admin is set via /setup-admin
    if data.role not in ("viewer", "engineer"):
        raise HTTPException(status_code=400, detail="Only 'viewer' or 'engineer' roles can be created.")

    # Prevent duplicate email
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    try:
        validate_password_complexity(data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    role_permissions = {
        "viewer": ["read:manuals"],
        "engineer": ["read:manuals", "write:diagnostics"],
        "admin": ["read:manuals", "write:diagnostics", "admin:all"],
    }

    new_user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        company_id=current_user.company_id,  # Inherit admin's company
        permissions=role_permissions.get(data.role, ["read:manuals"]),
    )
    if data.employee_id:
        new_user.employee_id = data.employee_id

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {data.email} created with role '{data.role}'"}


@router.delete("/users/{user_id}", summary="Delete user from admin's company")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    user = db.query(User).filter(
        User.id == user_id,
        User.company_id == current_user.company_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in your company")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@router.patch("/users/{user_id}/toggle", summary="Enable/disable user in admin's company")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    user = db.query(User).filter(
        User.id == user_id,
        User.company_id == current_user.company_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in your company")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'enabled' if user.is_active else 'disabled'}"}


# ── Document Management ─────────────────────────────────────────

@router.get("/documents", summary="List documents in admin's company")
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    docs = db.query(Document).filter(
        Document.company_id == current_user.company_id
    ).order_by(Document.id.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "source": d.source,
            "page_count": d.page_count,
            "chunk_count": d.chunk_count,
            "is_active": d.is_active,
            "uploaded_by": d.uploaded_by,
            "uploaded_at": d.uploaded_at,
        }
        for d in docs
    ]


@router.patch("/documents/{doc_id}/toggle", summary="Activate/deactivate document in admin's company")
def toggle_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.company_id == current_user.company_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in your company")
    doc.is_active = not doc.is_active
    db.commit()
    return {"message": f"Document {'activated' if doc.is_active else 'deactivated'}"}


@router.delete("/documents/{doc_id}", summary="Delete document from admin's company")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.company_id == current_user.company_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in your company")
    
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}

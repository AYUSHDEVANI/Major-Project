from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.sql_db import get_db
from app.models.user import User, Company, Document
from app.core.auth import RoleChecker

router = APIRouter(prefix="/superadmin", tags=["Super Admin"])
superadmin_only = RoleChecker(["superadmin"])

@router.get("/companies", summary="List all companies and their metrics")
def list_companies(db: Session = Depends(get_db), current_user: User = Depends(superadmin_only)):
    # Get all companies
    companies = db.query(Company).order_by(Company.id).all()
    
    # Calculate metrics per company
    results = []
    for company in companies:
        user_count = db.query(User).filter(User.company_id == company.id).count()
        doc_count = db.query(Document).filter(Document.company_id == company.id).count()
        chunk_count_result = db.query(func.sum(Document.chunk_count)).filter(Document.company_id == company.id).scalar()
        
        results.append({
            "id": company.id,
            "name": company.name,
            "created_at": company.created_at,
            "is_active": company.is_active,
            "user_count": user_count,
            "document_count": doc_count,
            "chunk_count": chunk_count_result or 0
        })
    return results

@router.get("/users", summary="List all users globally")
def list_all_users(db: Session = Depends(get_db), current_user: User = Depends(superadmin_only)):
    users = db.query(User).order_by(User.company_id, User.id).all()
    
    results = []
    for user in users:
        company = db.query(Company).filter(Company.id == user.company_id).first()
        results.append({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "company_name": company.name if company else "Unknown",
            "company_id": user.company_id
        })
    return results

@router.get("/documents", summary="List all documents globally")
def list_all_documents(db: Session = Depends(get_db), current_user: User = Depends(superadmin_only)):
    docs = db.query(Document).order_by(Document.company_id, Document.id).all()
    
    results = []
    for doc in docs:
        company = db.query(Company).filter(Company.id == doc.company_id).first()
        results.append({
            "id": doc.id,
            "filename": doc.filename,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "is_active": doc.is_active,
            "uploaded_at": doc.uploaded_at,
            "company_name": company.name if company else "Unknown",
            "company_id": doc.company_id
        })
    return results

@router.patch("/users/{user_id}/toggle", summary="Enable/disable any user globally")
def toggle_user_global(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot toggle your own superadmin account")
    
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {user.email} {'enabled' if user.is_active else 'disabled'}"}

@router.delete("/users/{user_id}", summary="Delete any user globally")
def delete_user_global(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own superadmin account")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted"}

@router.patch("/documents/{doc_id}/toggle", summary="Activate/deactivate any document globally")
def toggle_document_global(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.is_active = not doc.is_active
    db.commit()
    return {"message": f"Document {doc.filename} {'activated' if doc.is_active else 'deactivated'}"}

@router.delete("/documents/{doc_id}", summary="Delete any document globally")
def delete_document_global(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc)
    db.commit()
    return {"message": f"Document {doc.filename} deleted"}

@router.patch("/companies/{company_id}/toggle", summary="Enable/disable any company globally")
def toggle_company_global(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Toggle company status
    company.is_active = not company.is_active
    
    # If company is disabled, cascade deactivate all users
    if not company.is_active:
        db.query(User).filter(User.company_id == company_id).update({"is_active": False})
    
    db.commit()
    return {"message": f"Company {company.name} {'enabled' if company.is_active else 'suspended and all users deactivated'}"}

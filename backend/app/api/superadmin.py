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

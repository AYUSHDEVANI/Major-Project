"""PDF ingestion endpoint – restricted to admin role, tags with company_id."""
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.rag.ingestion import chunk_and_store
from app.core.auth import RoleChecker
from app.core.sql_db import get_db
from app.models.user import User, Document

router = APIRouter()
admin_only = RoleChecker(["admin"])

@router.post("/ingest", summary="Upload and index a PDF manual (admin only)")
async def ingest_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    result = await chunk_and_store(file, company_id=current_user.company_id)

    # Persist document metadata in SQL
    doc = Document(
        filename=file.filename,
        source=file.filename,
        page_count=result.get("pages", 0),
        chunk_count=result.get("chunks_stored", 0),
        is_active=True,
        uploaded_by=current_user.id,
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        company_id=current_user.company_id,
    )
    db.add(doc)
    db.commit()

    return result

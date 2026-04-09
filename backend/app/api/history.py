from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.sql_db import get_db
from app.models.history import RepairLog
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/history")
def get_repair_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get past repair logs with pagination, filtered by user's company.
    """
    logs = (
        db.query(RepairLog)
        .filter(RepairLog.company_id == current_user.company_id)
        .order_by(RepairLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs

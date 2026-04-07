from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.sql_db import get_db
from app.models.history import RepairLog

router = APIRouter()

@router.get("/history")
def get_repair_history(db: Session = Depends(get_db)):
    """
    Get all past repair logs, ordered by newest first.
    """
    logs = db.query(RepairLog).order_by(RepairLog.timestamp.desc()).all()
    return logs

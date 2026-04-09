from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class RepairLog(Base):
    __tablename__ = "repair_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Inputs
    image_filename = Column(String, index=True)
    query_text = Column(String, nullable=True)
    
    # AI Analysis
    machine_part = Column(String)
    failure_type = Column(String)
    repair_steps = Column(JSON)  # List of strings
    tools_required = Column(JSON) # List of strings
    
    # ROI
    estimated_time_minutes = Column(Integer)
    traditional_time_minutes = Column(Float)
    savings_usd = Column(Float)


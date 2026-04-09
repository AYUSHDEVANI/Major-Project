from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import random

router = APIRouter()

class TicketRequest(BaseModel):
    machine_part: str
    failure_type: str
    priority: str = "High"
    cost_estimate: float
    description: str

class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    erp_system: str
    message: str

from app.core.auth import RoleChecker
from app.models.user import User
from fastapi import Depends

engineer_role_checker = RoleChecker(["engineer"])

@router.post("/erp/ticket", response_model=TicketResponse)
def create_maintenance_ticket(
    request: TicketRequest,
    current_user: User = Depends(engineer_role_checker)
):
    """
    Mock endpoint that simulates creating a ticket in SAP/Oracle.
    """
    # Simulate processing delay
    ticket_id = f"INC-{random.randint(10000, 99999)}"
    
    print(f"--- [ERP MOCK] Creating Ticket in SAP ---")
    print(f"Part: {request.machine_part}")
    print(f"Issue: {request.failure_type}")
    print(f"Cost: ${request.cost_estimate}")
    print(f"-----------------------------------------")
    
    return TicketResponse(
        ticket_id=ticket_id,
        status="Created",
        erp_system="SAP S/4HANA (Mock)",
        message=f"Maintenance team dispatched for {request.machine_part}."
    )

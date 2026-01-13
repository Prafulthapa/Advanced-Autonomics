from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.lead_schema import LeadCreate, LeadUpdate, LeadOut
from app.services.lead_service import LeadService
from app.database import SessionLocal
from app.models.email_log import EmailLog
from app.models.email_reply import EmailReply
from app.models.agent_action_log import AgentActionLog
from app.models.email_queue import EmailQueue  # ✅ ADD THIS
from app.models.lead import Lead

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=LeadOut)
def create_lead(lead_in: LeadCreate, db: Session = Depends(get_db)):
    service = LeadService(db)
    lead = service.create_lead(lead_in)
    return lead


@router.get("/", response_model=List[LeadOut])
def get_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = LeadService(db)
    return service.get_all_leads(skip=skip, limit=limit)


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    service = LeadService(db)
    lead = service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, lead_in: LeadUpdate, db: Session = Depends(get_db)):
    service = LeadService(db)
    lead = service.update_lead(lead_id, lead_in)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}", response_model=dict)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    service = LeadService(db)
    success = service.delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"deleted": True}


@router.delete("/", response_model=dict)
def delete_all_leads(db: Session = Depends(get_db)):
    """
    Delete ALL leads and related data.
    WARNING: This cannot be undone!
    """
    try:
        # Delete in order due to foreign key constraints
        deleted_queue = db.query(EmailQueue).delete()  # ✅ NEW
        deleted_replies = db.query(EmailReply).delete()
        deleted_logs = db.query(EmailLog).delete()
        deleted_actions = db.query(AgentActionLog).delete()
        deleted_leads = db.query(Lead).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": "All leads and related data deleted",
            "deleted": {
                "leads": deleted_leads,
                "email_logs": deleted_logs,
                "email_replies": deleted_replies,
                "agent_actions": deleted_actions,
                "email_queue": deleted_queue  # ✅ NEW
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting leads: {str(e)}")
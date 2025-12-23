from sqlalchemy.orm import Session
from datetime import datetime

from app.models.lead import Lead
from app.schemas.lead_schema import LeadCreate, LeadUpdate


class LeadService:
    def __init__(self, db: Session):
        self.db = db

    def create_lead(self, lead_in: LeadCreate) -> Lead:
        lead = Lead(**lead_in.dict())
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def get_lead(self, lead_id: int) -> Lead | None:
        return self.db.query(Lead).filter(Lead.id == lead_id).first()

    def get_all_leads(self, skip: int = 0, limit: int = 100):
        return self.db.query(Lead).offset(skip).limit(limit).all()

    def update_lead(self, lead_id: int, lead_in: LeadUpdate) -> Lead | None:
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        for field, value in lead_in.dict(exclude_unset=True).items():
            setattr(lead, field, value)
        lead.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def delete_lead(self, lead_id: int) -> bool:
        lead = self.get_lead(lead_id)
        if not lead:
            return False
        self.db.delete(lead)
        self.db.commit()
        return True
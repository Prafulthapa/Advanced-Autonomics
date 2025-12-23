from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LeadBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    sequence_step: Optional[int] = None
    next_followup_at: Optional[datetime] = None
    replied: Optional[str] = None
    reply_received_at: Optional[datetime] = None
    # Agent fields
    agent_enabled: Optional[bool] = None
    agent_paused: Optional[bool] = None
    priority_score: Optional[float] = None

class LeadOut(LeadBase):
    id: int
    status: str
    sequence_step: int
    last_email_sent_at: Optional[datetime] = None
    next_followup_at: Optional[datetime] = None
    replied: str
    reply_received_at: Optional[datetime] = None
    
    # Agent fields
    agent_enabled: bool
    agent_paused: bool
    next_agent_check_at: Optional[datetime] = None
    follow_up_count: int
    max_follow_ups: int
    priority_score: float
    error_count: int
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
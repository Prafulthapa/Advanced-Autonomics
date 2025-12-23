"""
Pydantic schemas for agent-related API responses
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgentStatusResponse(BaseModel):
    """Agent status response."""
    is_running: bool
    is_paused: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    emails_today: int
    daily_limit: int


class AgentMetrics(BaseModel):
    """Agent performance metrics."""
    total_emails_sent: int
    total_replies: int
    total_errors: int
    success_rate: float
    actions_today: int


class AgentConfigResponse(BaseModel):
    """Agent configuration."""
    daily_email_limit: int
    hourly_email_limit: int
    business_hours_start: str
    business_hours_end: str
    timezone: str
    respect_business_hours: bool
    check_interval: int


class AgentActionLogOut(BaseModel):
    """Agent action log output."""
    id: int
    action_type: str
    action_result: str
    lead_id: Optional[int]
    lead_email: Optional[str]
    decision_reason: Optional[str]
    error_message: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True
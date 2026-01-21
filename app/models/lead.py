from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from app.database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company = Column(String, nullable=True)

    # Additional fields
    industry = Column(String, nullable=True)
    location = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)  # ✅ ADDED FOR CARPENTRY LEADS
    source = Column(String, nullable=True)  # ✅ ADDED TO TRACK LEAD SOURCE

    # Campaign tracking
    status = Column(String, default="new", index=True)  # new, contacted, replied, interested, not_interested, unsubscribed, paused
    sequence_step = Column(Integer, default=0)
    last_email_sent_at = Column(DateTime, nullable=True)
    next_followup_at = Column(DateTime, nullable=True)

    # Reply tracking
    replied = Column(String, default="no")
    reply_received_at = Column(DateTime, nullable=True)

    # ============ NEW AGENT FIELDS ============
    
    # Agent automation control
    agent_enabled = Column(Boolean, default=True, index=True)  # Can agent contact this lead?
    agent_paused = Column(Boolean, default=False)  # Manually paused by user
    
    # Timing and scheduling
    next_agent_check_at = Column(DateTime, nullable=True, index=True)  # When should agent review this?
    last_agent_action_at = Column(DateTime, nullable=True)  # Last time agent did something
    
    # Follow-up management
    follow_up_count = Column(Integer, default=0)  # How many times contacted
    max_follow_ups = Column(Integer, default=3)  # Stop after N attempts
    days_between_followups = Column(Integer, default=3)  # Wait N days between emails
    
    # Priority and scoring
    priority_score = Column(Float, default=5.0)  # 1-10, higher = more urgent
    engagement_score = Column(Float, default=0.0)  # Track engagement over time
    
    # Failure tracking
    bounce_count = Column(Integer, default=0)  # How many bounces
    error_count = Column(Integer, default=0)  # How many errors
    last_error_message = Column(String, nullable=True)
    
    # Agent metadata
    agent_notes = Column(String, nullable=True)  # Internal notes from agent decisions
    
    # ==========================================

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.database import Base


class AgentConfig(Base):
    """Global agent configuration and state tracking."""
    __tablename__ = "agent_config"

    id = Column(Integer, primary_key=True, index=True)
    
    # Agent control
    is_running = Column(Boolean, default=False)
    is_paused = Column(Boolean, default=False)
    
    # Rate limits
    daily_email_limit = Column(Integer, default=50)
    hourly_email_limit = Column(Integer, default=10)
    emails_sent_today = Column(Integer, default=0)
    emails_sent_this_hour = Column(Integer, default=0)
    
    # Timing
    last_reset_date = Column(String)
    last_hour_reset = Column(DateTime)
    business_hours_start = Column(String, default="09:00")
    business_hours_end = Column(String, default="17:00")
    timezone = Column(String, default="America/New_York")
    
    # Check intervals (minutes)
    agent_check_interval = Column(Integer, default=5)
    inbox_check_interval = Column(Integer, default=15)
    
    # Safety settings
    respect_business_hours = Column(Boolean, default=False)
    respect_unsubscribes = Column(Boolean, default=True)
    pause_on_high_error_rate = Column(Boolean, default=True)
    error_rate_threshold = Column(Integer, default=10)
    
    # Statistics
    total_emails_sent = Column(Integer, default=0)
    total_replies_received = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    
    # Agent lifecycle
    agent_started_at = Column(DateTime, nullable=True)
    agent_stopped_at = Column(DateTime, nullable=True)
    last_agent_run_at = Column(DateTime, nullable=True)
    next_agent_run_at = Column(DateTime, nullable=True)
    
    # Version tracking
    config_version = Column(String, default="1.0.0")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class Config:
        from_attributes = True
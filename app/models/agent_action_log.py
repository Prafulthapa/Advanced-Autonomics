from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.database import Base


class AgentActionLog(Base):
    """Log of all actions taken by the agent for auditing."""
    __tablename__ = "agent_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # What happened
    action_type = Column(String, index=True)
    action_result = Column(String)
    
    # Context
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    lead_email = Column(String, nullable=True)
    
    # Details
    decision_reason = Column(Text, nullable=True)
    action_metadata = Column(Text, nullable=True)  # FIXED: renamed from 'metadata'
    error_message = Column(Text, nullable=True)
    
    # Execution info
    execution_time_ms = Column(Integer, nullable=True)
    
    # Agent state at time of action
    agent_run_id = Column(String, index=True)
    emails_sent_before = Column(Integer)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    class Config:
        from_attributes = True
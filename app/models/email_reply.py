from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from datetime import datetime

from app.database import Base


class EmailReply(Base):
    """Model for storing inbound email replies."""
    __tablename__ = "email_replies"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)

    # Email metadata
    from_email = Column(String(255), nullable=False, index=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)

    # Matching metadata
    message_id = Column(String(255), nullable=True, index=True)
    in_reply_to = Column(String(255), nullable=True, index=True)
    references = Column(Text, nullable=True)

    # Classification
    classification = Column(String(50), nullable=True)
    classification_confidence = Column(String(50), nullable=True)
    classification_reason = Column(Text, nullable=True)

    # Processing status
    processed = Column(Boolean, default=False, index=True)
    matched = Column(Boolean, default=False, index=True)

    # Timestamps
    received_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Raw email for debugging
    raw_headers = Column(Text, nullable=True)

    class Config:
        from_attributes = True
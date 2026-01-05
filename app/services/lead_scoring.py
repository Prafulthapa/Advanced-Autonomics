"""
AI-Powered Lead Scoring
Automatically prioritize leads based on multiple factors
"""

from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.models.lead import Lead


class LeadScorer:
    """Calculate priority scores for leads."""
    
    @staticmethod
    def calculate_score(lead: Lead) -> float:
        """
        Calculate priority score (1-10) for a lead.
        
        Factors:
        - Company size indicators
        - Industry type
        - Previous engagement
        - Time since last contact
        - Error history
        """
        
        score = 5.0  # Base score
        
        # Factor 1: Industry bonus
        if lead.industry:
            industry_lower = lead.industry.lower()
            if "glass" in industry_lower:
                score += 2.0  # High value industry
            elif "manufacturing" in industry_lower:
                score += 1.5
            elif "3pl" in industry_lower or "logistics" in industry_lower:
                score += 1.0
        
        # Factor 2: Company name indicators
        if lead.company:
            company_lower = lead.company.lower()
            if any(word in company_lower for word in ["international", "global", "corporation"]):
                score += 1.0  # Likely larger company
            if any(word in company_lower for word in ["inc", "llc", "ltd", "corp"]):
                score += 0.5  # Established business
        
        # Factor 3: Engagement history
        if lead.replied == "yes":
            score += 3.0  # Highly engaged
        elif lead.status == "contacted" and lead.last_email_sent_at:
            # Recency bonus
            days_since = (datetime.utcnow() - lead.last_email_sent_at).days
            if days_since < 7:
                score += 1.0
        
        # Factor 4: Penalties
        if lead.error_count > 0:
            score -= (lead.error_count * 0.5)
        
        if lead.bounce_count > 0:
            score -= (lead.bounce_count * 1.0)
        
        # Clamp between 1-10
        return max(1.0, min(10.0, score))
    
    @staticmethod
    def score_all_leads(db: Session):
        """Recalculate scores for all leads."""
        
        leads = db.query(Lead).all()
        
        for lead in leads:
            lead.priority_score = LeadScorer.calculate_score(lead)
        
        db.commit()
        
        return len(leads)
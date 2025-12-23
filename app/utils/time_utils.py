"""
Time and scheduling utilities for agent
"""

from datetime import datetime, timedelta
from typing import Optional
import pytz
from dateutil import parser


class TimeUtils:
    """Helper functions for time-based agent logic."""
    
    @staticmethod
    def is_business_hours(
        timezone_str: str = "America/New_York",
        start_time: str = "09:00",
        end_time: str = "17:00",
        active_days: list = [1, 2, 3, 4, 5]  # Mon-Fri
    ) -> bool:
        """
        Check if current time is within business hours.
        
        Args:
            timezone_str: Timezone name
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            active_days: List of active weekdays (1=Monday, 7=Sunday)
        
        Returns:
            True if within business hours, False otherwise
        """
        try:
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            
            # Check day of week (1=Monday, 7=Sunday)
            weekday = now.isoweekday()
            if weekday not in active_days:
                return False
            
            # Parse time strings
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour, end_min = map(int, end_time.split(':'))
            
            # Create datetime objects for comparison
            start_dt = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            end_dt = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
            
            return start_dt <= now <= end_dt
            
        except Exception as e:
            print(f"Error checking business hours: {e}")
            return False  # Fail safe: if error, don't send
    
    @staticmethod
    def calculate_next_followup(
        last_email_at: datetime,
        days_to_wait: int = 3
    ) -> datetime:
        """
        Calculate when next follow-up should be sent.
        
        Args:
            last_email_at: When last email was sent
            days_to_wait: Days to wait before next contact
        
        Returns:
            Datetime for next follow-up
        """
        return last_email_at + timedelta(days=days_to_wait)
    
    @staticmethod
    def is_ready_for_action(next_check_at: Optional[datetime]) -> bool:
        """
        Check if it's time to act on a lead.
        
        Args:
            next_check_at: Scheduled time for next action
        
        Returns:
            True if time has passed, False otherwise
        """
        if next_check_at is None:
            return True  # No schedule = ready now
        
        return datetime.utcnow() >= next_check_at
    
    @staticmethod
    def get_current_date_str() -> str:
        """Get current date as YYYY-MM-DD string."""
        return datetime.utcnow().strftime("%Y-%m-%d")
    
    @staticmethod
    def get_current_hour() -> int:
        """Get current hour (0-23)."""
        return datetime.utcnow().hour
    
    @staticmethod
    def parse_datetime(date_str: str) -> Optional[datetime]:
        """Safely parse datetime string."""
        try:
            return parser.parse(date_str)
        except:
            return None
    
    @staticmethod
    def time_until(target_dt: datetime) -> timedelta:
        """Calculate time remaining until target datetime."""
        return target_dt - datetime.utcnow()
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format seconds into human-readable duration."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
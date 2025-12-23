"""
Configuration loader for AI Agent
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class AgentConfiguration:
    """Load and manage agent configuration."""
    
    def __init__(self, config_path: str = "agent_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            print(f"⚠️  Config file {self.config_path} not found, using defaults")
            return self._default_config()
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            print(f"✅ Loaded agent config from {self.config_path}")
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration if file not found."""
        return {
            'agent': {
                'enabled': True,
                'check_interval': 5,
                'inbox_check_interval': 15,
            },
            'limits': {
                'max_emails_per_day': 2000,      # ← UPDATED from 50
                'max_emails_per_hour': 60,      # ← UPDATED from 10
                'max_follow_ups_per_lead': 3,
                'days_between_followups': 3,
            },
            'timing': {
                'business_hours_start': '09:00',
                'business_hours_end': '17:00',
                'timezone': 'America/New_York',
                'active_days': [1, 2, 3, 4, 5],  # Monday-Friday
            },
            'safety': {
                'respect_business_hours': True,
                'respect_unsubscribes': True,
                'pause_on_high_error_rate': True,
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot notation path.
        Example: config.get('limits.max_emails_per_day')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()


# Global config instance
agent_config = AgentConfiguration()


# Environment variable overrides (with updated defaults)
AGENT_ENABLED = os.getenv("AGENT_ENABLED", "true").lower() == "true"
AGENT_CHECK_INTERVAL = int(os.getenv("AGENT_CHECK_INTERVAL", "5"))
DAILY_EMAIL_LIMIT = int(os.getenv("DAILY_EMAIL_LIMIT", "2000"))     # ← UPDATED
HOURLY_EMAIL_LIMIT = int(os.getenv("HOURLY_EMAIL_LIMIT", "60"))    # ← UPDATED
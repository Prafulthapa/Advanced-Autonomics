"""
Lead Scraper Configuration
Australian robotics/automation companies - All industries
"""

SCRAPER_CONFIG = {
    # Daily targets
    "daily_target": 500,
    "max_linkedin_profiles_per_day": 300,
    
    # Geographic focus (100% Australia)
    "geographic_split": {
        "australia": 100,
        "usa": 0,
        "europe": 0
    },
    
    # Target locations in Australia
    "target_locations": [
        "Australia",
        "Sydney, Australia",
        "Melbourne, Australia",
        "Brisbane, Australia",
        "Perth, Australia",
        "Adelaide, Australia",
        "Canberra, Australia"
    ],
    
    # Industries (Robotics/Automation focused)
    "industries": [
        "Robotics",
        "Industrial Automation",
        "Manufacturing",
        "Factory Automation",
        "Warehouse Automation",
        "Logistics Automation",
        "Mining Automation",
        "Agricultural Technology",
        "Food Processing",
        "Automotive Manufacturing",
        "Electronics Manufacturing",
        "Pharmaceutical Manufacturing",
        "Chemical Manufacturing",
        "Metal Fabrication",
        "Packaging",
        "Material Handling"
    ],
    
    # Keywords for robotics/automation
    "industry_keywords": [
        "robotics",
        "automation",
        "automated",
        "manufacturing",
        "industrial",
        "production",
        "factory",
        "warehouse",
        "logistics",
        "material handling",
        "assembly line",
        "conveyor",
        "packaging",
        "palletizing"
    ],
    
    # Job titles to search
    "job_titles": [
        "CEO",
        "Chief Executive Officer",
        "Owner",
        "President",
        "Managing Director",
        "General Manager",
        "Operations Manager",
        "Plant Manager",
        "Production Manager",
        "Operations Director",
        "Chief Operating Officer",
        "COO"
    ],
    
    # Company sizes
    "company_sizes": ["11-50", "51-200", "201-500", "501-1000", "1001-5000"],
    
    # Email finding methods
    "email_methods": ["pattern", "scrape", "verify"],
    
    # Run schedule (2 AM daily)
    "run_schedule": "0 2 * * *",
    
    # Rate limiting (anti-detection)
    "delays": {
        "min_delay": 5,
        "max_delay": 15,
        "page_load": 3,
        "between_searches": 30
    },
    
    # Chrome options
    "headless": True,
    "stealth_mode": True
}

# LinkedIn credentials
LINKEDIN_EMAIL = "monkeymind4336@gmail.com"
LINKEDIN_PASSWORD = "Nepal123!"

# Hunter.io API (not used, but ready if you get one)
HUNTER_API_KEY = None

# Email pattern templates (for guessing)
EMAIL_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{first}@{domain}",
    "{last}@{domain}",
    "{first_initial}{last}@{domain}",
    "{first}{last_initial}@{domain}",
]

# Common Australian business email domains
COMMON_DOMAINS = [
    "com.au",
    "net.au",
    "org.au",
]
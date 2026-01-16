"""
Lead Scraper Configuration
Australian carpentry, joinery, woodworking companies
NO LinkedIn - Uses public directories
"""

SCRAPER_CONFIG = {
    # Daily targets
    "daily_target": 500,
    "max_leads_per_source": 200,
    
    # Geographic focus (100% Australia)
    "geographic_split": {
        "australia": 100,
        "usa": 0,
        "europe": 0
    },
    
    # Target locations in Australia (Major cities + regions)
    "target_locations": [
        # NSW
        "Sydney NSW",
        "Newcastle NSW",
        "Wollongong NSW",
        "Central Coast NSW",
        
        # VIC
        "Melbourne VIC",
        "Geelong VIC",
        "Ballarat VIC",
        
        # QLD
        "Brisbane QLD",
        "Gold Coast QLD",
        "Sunshine Coast QLD",
        "Townsville QLD",
        "Cairns QLD",
        
        # WA
        "Perth WA",
        "Mandurah WA",
        
        # SA
        "Adelaide SA",
        
        # TAS
        "Hobart TAS",
        "Launceston TAS",
        
        # ACT
        "Canberra ACT",
        
        # NT
        "Darwin NT"
    ],
    
    # Industries (Carpentry/Woodworking focused)
    "industries": [
        "Carpentry",
        "Joinery",
        "Cabinet Making",
        "Woodworking",
        "Timber Construction",
        "Custom Furniture",
        "Kitchen Renovations",
        "Bathroom Renovations",
        "Commercial Fit-outs",
        "Residential Construction",
        "Deck Building",
        "Pergola Construction",
        "Shopfitting",
        "Office Fit-outs",
        "Home Extensions",
        "Renovation Contractors"
    ],
    
    # Keywords for carpentry/woodworking searches
    "industry_keywords": [
        "carpentry",
        "carpenter",
        "joinery",
        "joiner",
        "cabinet maker",
        "cabinetmaker",
        "woodworking",
        "timber construction",
        "custom carpentry",
        "kitchen renovation",
        "bathroom renovation",
        "commercial carpentry",
        "residential carpentry",
        "fit out carpentry",
        "shopfitting",
        "deck builder",
        "pergola builder",
        "renovation carpentry",
        "bespoke joinery",
        "custom furniture"
    ],
    
    # Job titles to find (decision makers)
    "job_titles": [
        "Owner",
        "Director",
        "Managing Director",
        "CEO",
        "Founder",
        "Principal",
        "Manager",
        "General Manager",
        "Operations Manager",
        "Business Owner",
        "Head Carpenter",
        "Master Carpenter",
        "Lead Carpenter"
    ],
    
    # Company sizes (smaller businesses typical for carpentry)
    "company_sizes": [
        "1-10",      # Solo operators & small teams
        "11-50",     # Medium carpentry businesses
        "51-200",    # Larger contractors
    ],
    
    # Scraping sources
    "scraping_sources": {
        "yellow_pages": True,
        "true_local": True,
        "google_maps": False,  # Requires Selenium, slower
        "hipages": False,      # Would need to implement
        "service_seeking": False  # Would need to implement
    },
    
    # Email finding methods
    "email_methods": {
        "scrape_website": True,   # Scrape company website
        "guess_pattern": True,    # Generate from company name
        "smtp_verify": False      # SMTP verification (slow, often blocked)
    },
    
    # Run schedule (2 AM daily by default)
    "run_schedule": "0 2 * * *",  # Cron format: minute hour day month weekday
    
    # Rate limiting (be respectful to avoid blocks)
    "delays": {
        "min_delay": 3,              # Minimum delay between requests (seconds)
        "max_delay": 7,              # Maximum delay between requests
        "page_load": 3,              # Wait for page load
        "between_searches": 15,      # Delay between different searches
        "between_sources": 30        # Delay between different sources
    },
    
    # Scraping limits per run
    "limits": {
        "max_pages_per_search": 3,   # Max pages to scrape per keyword/location
        "max_results_per_page": 50,  # Max results to process per page
        "daily_request_limit": 1000  # Max HTTP requests per day
    },
    
    # Data quality
    "validation": {
        "require_email": False,       # Don't skip leads without email
        "require_phone": False,       # Don't skip leads without phone
        "require_website": False,     # Don't skip leads without website
        "min_company_name_length": 3  # Minimum characters for company name
    }
}

# NO LinkedIn credentials needed anymore!
# Carpentry scraper uses public directories only

# Email pattern templates (for generating emails)
EMAIL_PATTERNS = [
    "info@{domain}",
    "contact@{domain}",
    "admin@{domain}",
    "office@{domain}",
    "enquiries@{domain}",
    "sales@{domain}",
    "{first}.{last}@{domain}",
    "{first}@{domain}",
    "{last}@{domain}"
]

# Common Australian business email domains
COMMON_DOMAINS = [
    ".com.au",
    ".net.au",
    ".org.au",
    ".au"
]

# Executive title patterns (for extracting names from websites)
EXECUTIVE_TITLES = [
    "Owner",
    "Director",
    "Managing Director",
    "CEO",
    "Founder",
    "Principal",
    "Manager",
    "Head Carpenter",
    "Master Carpenter"
]

# Words to remove from company names when generating emails
COMPANY_NAME_STOPWORDS = [
    "pty", "ltd", "inc", "llc", "limited",
    "carpentry", "joinery", "services",
    "group", "company", "co", "solutions",
    "australia", "australian"
]

# Output configuration
OUTPUT_CONFIG = {
    "save_json": True,           # Save raw JSON file
    "save_csv": False,           # Also save CSV? (not needed)
    "json_indent": 2,            # Pretty print JSON
    "include_timestamp": True    # Add timestamp to filenames
}

# Celery/Queue configuration
CELERY_CONFIG = {
    "auto_push_to_queue": True,      # Automatically push to email queue
    "batch_size": 50,                # Process in batches of 50
    "retry_failed": True,            # Retry failed queue pushes
    "max_retries": 3                 # Max retry attempts
}
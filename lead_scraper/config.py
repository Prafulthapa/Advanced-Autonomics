"""
Lead Scraper Configuration - USA EDITION
Ohio carpentry, joinery, woodworking companies
NO LinkedIn - Uses public directories
"""

SCRAPER_CONFIG = {
    # Daily targets
    "daily_target": 500,
    "max_leads_per_source": 200,

    # Geographic focus (100% USA, starting with Ohio)
    "geographic_split": {
        "usa": 100,
        "australia": 0,
        "europe": 0
    },

    # Target locations in USA (Ohio focus + expansion)
    "target_locations": [
        # OHIO - Primary Focus
        "Columbus OH",
        "Cleveland OH",
        "Cincinnati OH",
        "Toledo OH",
        "Akron OH",
        "Dayton OH",
        "Parma OH",
        "Canton OH",
        "Youngstown OH",
        "Lorain OH",
        "Hamilton OH",
        "Springfield OH",
        "Kettering OH",
        "Elyria OH",
        "Lakewood OH",
        "Cuyahoga Falls OH",
        "Middletown OH",
        "Newark OH",
        "Mansfield OH",
        "Mentor OH",
        "Beavercreek OH",
        "Strongsville OH",
        "Dublin OH",
        "Fairfield OH",
        "Warren OH",
        "Lima OH",
        "Huber Heights OH",
        "Marion OH",
        "Findlay OH",
        "Lancaster OH",
        
        # Other states (for expansion later)
        # "Detroit MI",
        # "Indianapolis IN",
        # "Pittsburgh PA",
        # "Louisville KY",
        # "Chicago IL",
    ],

    # Industries (Carpentry/Woodworking focused)
    "industries": [
        "Carpentry",
        "Finish Carpentry",
        "Framing",
        "Cabinet Making",
        "Woodworking",
        "Millwork",
        "Custom Furniture",
        "Kitchen Remodeling",
        "Bathroom Remodeling",
        "Commercial Carpentry",
        "Residential Construction",
        "Deck Building",
        "Trim Carpentry",
        "Door Installation",
        "Window Installation",
        "Flooring Installation",
        "General Contracting"
    ],

    # Keywords for carpentry/woodworking searches
    "industry_keywords": [
        "carpentry",
        "carpenter",
        "cabinet maker",
        "cabinetmaker",
        "woodworking",
        "finish carpentry",
        "framing contractor",
        "custom carpentry",
        "kitchen remodeling",
        "bathroom remodeling",
        "commercial carpentry",
        "residential carpentry",
        "trim carpenter",
        "millwork",
        "custom woodwork",
        "deck builder",
        "renovation carpentry",
        "custom cabinetry",
        "handyman carpentry",
        "remodeling contractor"
    ],

    # Job titles to find (decision makers)
    "job_titles": [
        "Owner",
        "President",
        "CEO",
        "Founder",
        "Principal",
        "Manager",
        "General Manager",
        "Operations Manager",
        "Business Owner",
        "Lead Carpenter",
        "Master Carpenter",
        "Foreman",
        "Project Manager"
    ],

    # Company sizes (smaller businesses typical for carpentry)
    "company_sizes": [
        "1-10",      # Solo operators & small teams
        "11-50",     # Medium carpentry businesses
        "51-200",    # Larger contractors
    ],

    # Scraping sources
    "scraping_sources": {
        "yellow_pages": True,     # YellowPages.com
        "google_maps": True,      # Google Maps (best for local businesses)
        "yelp": False,            # Could add later
        "angi": False,            # Formerly Angie's List
        "homeadvisor": False      # Could add later
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

# Email pattern templates (for generating emails)
EMAIL_PATTERNS = [
    "info@{domain}",
    "contact@{domain}",
    "admin@{domain}",
    "office@{domain}",
    "inquiries@{domain}",
    "sales@{domain}",
    "{first}.{last}@{domain}",
    "{first}@{domain}",
    "{last}@{domain}"
]

# Common USA business email domains
COMMON_DOMAINS = [
    ".com",
    ".net",
    ".us",
    ".biz",
    ".org"
]

# Executive title patterns (for extracting names from websites)
EXECUTIVE_TITLES = [
    "Owner",
    "President",
    "CEO",
    "Founder",
    "Principal",
    "Manager",
    "Lead Carpenter",
    "Master Carpenter"
]

# Words to remove from company names when generating emails
COMPANY_NAME_STOPWORDS = [
    "inc", "llc", "ltd", "limited", "corp", "corporation",
    "carpentry", "services", "company", "co", "solutions",
    "group", "contractors", "construction"
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
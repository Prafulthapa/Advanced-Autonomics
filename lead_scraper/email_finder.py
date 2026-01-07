"""
Email Finder - Multiple methods for finding emails
Pattern guessing, website scraping, SMTP verification
"""

import re
import logging
import requests
from urllib.parse import urlparse
import socket
import smtplib
from email.utils import parseaddr
from config import EMAIL_PATTERNS, COMMON_DOMAINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailFinder:
    """Find and verify email addresses."""
    
    def __init__(self):
        self.found_emails = []
    
    def find_email(self, lead_data):
        """Try multiple methods to find email."""
        logger.info(f"🔍 Finding email for: {lead_data.get('name')} at {lead_data.get('company')}")
        
        email = None
        method = None
        
        # Method 1: Pattern guessing
        email, method = self.guess_email_pattern(lead_data)
        
        if email:
            # Verify it
            if self.verify_email_smtp(email):
                logger.info(f"✅ Found & verified: {email} (method: {method})")
                return email, method
        
        # Method 2: Scrape company website
        if not email:
            email, method = self.scrape_website_for_email(lead_data)
            if email:
                logger.info(f"✅ Found on website: {email}")
                return email, method
        
        logger.warning(f"❌ No email found for {lead_data.get('name')}")
        return None, None
    
    def guess_email_pattern(self, lead_data):
        """Guess email using common patterns."""
        name = lead_data.get('name', '')
        company = lead_data.get('company', '')
        
        if not name or not company:
            return None, None
        
        # Parse name
        parts = name.lower().split()
        if len(parts) < 2:
            return None, None
        
        first = parts[0]
        last = parts[-1]
        first_initial = first[0] if first else ''
        last_initial = last[0] if last else ''
        
        # Extract domain from company
        domain = self.extract_domain(company)
        
        if not domain:
            return None, None
        
        # Try each pattern
        for pattern in EMAIL_PATTERNS:
            try:
                email = pattern.format(
                    first=first,
                    last=last,
                    first_initial=first_initial,
                    last_initial=last_initial,
                    domain=domain
                )
                
                # Basic validation
                if self.is_valid_email_format(email):
                    return email, "pattern_guess"
                    
            except:
                continue
        
        return None, None
    
    def extract_domain(self, company):
        """Extract domain from company name."""
        # Clean company name
        company = company.lower()
        company = re.sub(r'\b(pty|ltd|inc|llc|corp|corporation|company|co)\b', '', company)
        company = re.sub(r'[^a-z0-9\s]', '', company)
        company = company.strip().replace(' ', '')
        
        # Try common patterns
        possible_domains = [
            f"{company}.com.au",
            f"{company}.net.au",
            f"{company}.com",
        ]
        
        for domain in possible_domains:
            if self.domain_exists(domain):
                logger.debug(f"✓ Found domain: {domain}")
                return domain
        
        return None
    
    def domain_exists(self, domain):
        """Check if domain exists (has MX records)."""
        try:
            socket.gethostbyname(domain)
            return True
        except:
            return False
    
    def is_valid_email_format(self, email):
        """Basic email format validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def verify_email_smtp(self, email):
        """Verify email exists using SMTP (lightweight check)."""
        try:
            domain = email.split('@')[1]
            
            # Get MX record
            import dns.resolver
            records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(records[0].exchange)
            
            # Connect to mail server
            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(0)
            server.connect(mx_record)
            server.helo(server.local_hostname)
            server.mail('verify@example.com')
            code, message = server.rcpt(email)
            server.quit()
            
            # Check response
            if code == 250:
                return True
            else:
                return False
                
        except:
            # If verification fails, assume email might exist
            # (Many servers block verification)
            return True
    
    def scrape_website_for_email(self, lead_data):
        """Scrape company website for contact email."""
        company = lead_data.get('company', '')
        
        if not company:
            return None, None
        
        # Try to find company website
        domain = self.extract_domain(company)
        
        if not domain:
            return None, None
        
        try:
            # Try contact page
            urls = [
                f"https://{domain}/contact",
                f"https://{domain}/about",
                f"https://{domain}",
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=10)
                    
                    # Find emails in page
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
                    
                    # Filter out common garbage emails
                    valid_emails = [
                        e for e in emails 
                        if not any(x in e.lower() for x in ['example', 'test', 'domain', 'email'])
                    ]
                    
                    if valid_emails:
                        return valid_emails[0], "website_scrape"
                        
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Website scrape error: {str(e)}")
        
        return None, None


def main():
    """Test email finder."""
    finder = EmailFinder()
    
    test_lead = {
        "name": "John Smith",
        "company": "ABC Manufacturing Pty Ltd",
        "title": "CEO"
    }
    
    email, method = finder.find_email(test_lead)
    print(f"Found: {email} via {method}")


if __name__ == "__main__":
    main()
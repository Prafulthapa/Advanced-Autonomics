"""
FULLY AUTOMATED LEAD PIPELINE
Scrapes → Enriches → Imports → Emails (ALL AUTOMATIC)

Runs every 6 hours via Celery Beat
No manual intervention needed
"""

import logging
import csv
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import random
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://api:8000"


class AutomatedLeadPipeline:
    """Fully automated lead collection and import."""
    
    def __init__(self):
        self.leads_collected = []
        self.leads_imported = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_yellow_pages(self, keywords, locations, max_results=100):
        """
        Scrape Yellow Pages Australia automatically.
        
        Returns leads with:
        - Company name
        - Phone
        - Website
        - Address
        - Guessed email
        """
        
        logger.info(f"🔍 Auto-scraping Yellow Pages...")
        logger.info(f"   Keywords: {keywords}")
        logger.info(f"   Locations: {locations}")
        
        all_leads = []
        
        for keyword in keywords:
            for location in locations:
                logger.info(f"   Searching: {keyword} in {location}")
                
                # Only scrape 2 pages per search (avoid rate limits)
                for page in range(1, 3):
                    try:
                        url = (
                            f"https://www.yellowpages.com.au/search/listings?"
                            f"clue={keyword.replace(' ', '+')}&"
                            f"locationClue={location.replace(' ', '+')}&"
                            f"pageNumber={page}"
                        )
                        
                        response = self.session.get(url, timeout=15)
                        
                        if response.status_code != 200:
                            logger.warning(f"   Status {response.status_code}, skipping")
                            break
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find listings
                        listings = soup.find_all('article', class_='listing-item')
                        
                        if not listings:
                            # Try alternative selector
                            listings = soup.find_all('div', class_='listing')
                        
                        if not listings:
                            logger.info(f"   No results on page {page}")
                            break
                        
                        for listing in listings:
                            lead = self.extract_business_data(listing, location)
                            if lead and lead not in all_leads:
                                all_leads.append(lead)
                                logger.info(f"   ✅ Found: {lead['Name']}")
                        
                        logger.info(f"   Page {page}: {len(listings)} listings")
                        
                        # Rate limiting - be respectful
                        time.sleep(random.uniform(3, 7))
                        
                        if len(all_leads) >= max_results:
                            break
                    
                    except Exception as e:
                        logger.error(f"   Error on page {page}: {e}")
                        break
                
                if len(all_leads) >= max_results:
                    break
            
            if len(all_leads) >= max_results:
                break
        
        logger.info(f"✅ Scraped {len(all_leads)} businesses from Yellow Pages")
        return all_leads
    
    def extract_business_data(self, listing, location):
        """Extract business info from listing."""
        try:
            # Company name
            name = None
            name_selectors = [
                'h3.listing-name',
                'a.listing-name',
                'h2.listing-name',
                '.contact-business-name'
            ]
            
            for selector in name_selectors:
                elem = listing.select_one(selector)
                if elem:
                    name = elem.get_text(strip=True)
                    break
            
            if not name:
                return None
            
            # Phone
            phone = ""
            phone_elem = listing.select_one('.contact-phone, .phone')
            if phone_elem:
                phone = phone_elem.get_text(strip=True)
            
            # Website
            website = ""
            website_elem = listing.select_one('a.contact-url, a[href*="http"]')
            if website_elem:
                website = website_elem.get('href', '')
            
            # Address
            address = ""
            address_elem = listing.select_one('.contact-address, .address')
            if address_elem:
                address = address_elem.get_text(strip=True)
            
            # Generate email from website
            email = self.guess_email_from_website(website, name)
            
            return {
                "STATE": location,
                "Name": name,
                "Address": address,
                "Phone": phone,
                "Email": email,
                "Website": website,
                "Source": "Yellow Pages AU (Auto)",
                "CEO/Owner": "",
                "CEO_Source": "",
                "Validation_Status": "Auto-Collected"
            }
        
        except Exception as e:
            logger.debug(f"Extraction error: {e}")
            return None
    
    def guess_email_from_website(self, website, company_name):
        """Generate likely email addresses."""
        if not website:
            return ""
        
        try:
            # Extract domain
            domain = website.replace('http://', '').replace('https://', '')
            domain = domain.replace('www.', '').split('/')[0]
            
            # Common patterns for Australian businesses
            patterns = [
                f"info@{domain}",
                f"contact@{domain}",
                f"enquiries@{domain}",
                f"sales@{domain}",
            ]
            
            return patterns[0]  # Return most common
        
        except:
            return ""
    
    def deduplicate_leads(self, leads):
        """Remove duplicates by company name + location."""
        seen = set()
        unique = []
        
        for lead in leads:
            key = f"{lead['Name'].lower()}_{lead['STATE'].lower()}"
            
            if key not in seen:
                seen.add(key)
                unique.append(lead)
        
        logger.info(f"📊 Deduplication: {len(leads)} → {len(unique)} unique")
        return unique
    
    def save_to_csv(self, leads):
        """Save leads to CSV file."""
        if not leads:
            logger.warning("No leads to save")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/leads_auto_{timestamp}.csv"
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            "STATE", "Name", "Address", "Phone", "Email", 
            "Website", "Source", "CEO/Owner", "CEO_Source", "Validation_Status"
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(leads)
        
        logger.info(f"💾 Saved {len(leads)} leads to: {filename}")
        return filename
    
    def import_to_system(self, csv_file):
        """Automatically import CSV to email system via API."""
        
        logger.info(f"📤 Auto-importing to system: {csv_file}")
        
        try:
            with open(csv_file, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{API_BASE}/import/csv",
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                data = response.json()
                imported = data.get('imported', 0)
                logger.info(f"✅ Successfully imported {imported} leads")
                return imported
            else:
                logger.error(f"❌ Import failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return 0
        
        except Exception as e:
            logger.error(f"❌ Import error: {e}")
            return 0
    
    def check_system_status(self):
        """Check if email system is running."""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Email system is healthy")
                return True
            else:
                logger.warning(f"⚠️  System status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot reach email system: {e}")
            return False
    
    def run_automated_pipeline(self):
        """
        Run the complete automated pipeline.
        
        Steps:
        1. Check system health
        2. Scrape Yellow Pages
        3. Deduplicate leads
        4. Save to CSV
        5. Auto-import to email system
        6. Email system starts sending automatically
        """
        
        logger.info("=" * 60)
        logger.info("🤖 AUTOMATED LEAD PIPELINE STARTING")
        logger.info("=" * 60)
        
        # Step 1: Health check
        if not self.check_system_status():
            logger.error("❌ Email system not available, aborting")
            return
        
        # Step 2: Scrape leads
        keywords = [
            "robotics",
            "automation",
            "manufacturing",
            "industrial automation",
        ]
        
        locations = [
            "Sydney",
            "Melbourne",
            "Brisbane",
        ]
        
        logger.info("\n📋 Step 1: Scraping Yellow Pages...")
        leads = self.scrape_yellow_pages(keywords, locations, max_results=100)
        
        if not leads:
            logger.warning("⚠️  No leads collected, pipeline stopping")
            return
        
        # Step 3: Deduplicate
        logger.info("\n📋 Step 2: Deduplicating...")
        unique_leads = self.deduplicate_leads(leads)
        
        # Step 4: Save CSV
        logger.info("\n📋 Step 3: Saving to CSV...")
        csv_file = self.save_to_csv(unique_leads)
        
        if not csv_file:
            logger.error("❌ Failed to save CSV")
            return
        
        # Step 5: Auto-import
        logger.info("\n📋 Step 4: Auto-importing to email system...")
        imported = self.import_to_system(csv_file)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ AUTOMATED PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Results:")
        logger.info(f"   - Scraped: {len(leads)} leads")
        logger.info(f"   - Unique: {len(unique_leads)} leads")
        logger.info(f"   - Imported: {imported} leads")
        logger.info(f"   - CSV: {csv_file}")
        logger.info("=" * 60)
        logger.info("🚀 Email system will now automatically:")
        logger.info("   1. Generate AI emails for new leads")
        logger.info("   2. Send during business hours")
        logger.info("   3. Track replies")
        logger.info("   4. Follow up automatically")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "scraped": len(leads),
            "unique": len(unique_leads),
            "imported": imported,
            "csv_file": csv_file
        }


def main():
    """Main execution."""
    pipeline = AutomatedLeadPipeline()
    result = pipeline.run_automated_pipeline()
    
    if result and result.get("success"):
        logger.info("🎉 Pipeline succeeded!")
    else:
        logger.error("❌ Pipeline failed")


if __name__ == "__main__":
    main()
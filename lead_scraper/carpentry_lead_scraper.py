"""
Carpentry Lead Scraper - SELENIUM VERSION
Uses real Chrome browser to avoid blocking
Much more reliable than requests library
"""

import logging
import time
import random
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CarpentryLeadScraper:
    """Scrape carpentry/woodworking leads using Selenium."""
    
    def __init__(self):
        self.all_leads = []
        self.seen_companies = set()
        self.driver = None
        self.setup_selenium()
    
    def setup_selenium(self):
        """Configure Selenium with Chrome."""
        logger.info("🌐 Initializing Chrome browser...")
        
        chrome_options = Options()
        
        # Headless mode (no GUI)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Look like a real browser
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Disable images for faster loading (optional)
        # chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Override webdriver detection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            logger.info("✅ Chrome browser ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome: {e}")
            raise
    
    def scrape_yellow_pages_au(self, keyword, location, max_pages=3):
        """Scrape Yellow Pages Australia with Selenium."""
        logger.info(f"🔍 Yellow Pages: {keyword} in {location}")
        leads = []
        
        for page in range(1, max_pages + 1):
            try:
                url = (
                    f"https://www.yellowpages.com.au/search/listings?"
                    f"clue={quote_plus(keyword)}&"
                    f"locationClue={quote_plus(location)}&"
                    f"pageNumber={page}"
                )
                
                logger.info(f"  📄 Page {page}/{max_pages}")
                
                # Load page
                self.driver.get(url)
                
                # Wait for listings to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article, div.listing"))
                    )
                except:
                    logger.warning(f"  ⏱️ Timeout waiting for listings")
                
                # Random human-like delay
                time.sleep(random.uniform(2, 4))
                
                # Get page source
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find listings
                listings = soup.find_all('article', class_='listing-item')
                if not listings:
                    listings = soup.find_all('div', class_='listing')
                if not listings:
                    listings = soup.find_all('div', attrs={'data-listing-id': True})
                
                if not listings:
                    logger.info(f"  📭 No listings on page {page}")
                    break
                
                logger.info(f"  📋 Found {len(listings)} listings")
                
                for listing in listings:
                    lead = self.extract_yellow_pages_data(listing, location)
                    if lead and lead['company_name'] not in self.seen_companies:
                        leads.append(lead)
                        self.seen_companies.add(lead['company_name'])
                        logger.info(f"  ✅ {lead['company_name']}")
                
                # Human-like delay between pages
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                logger.error(f"  ❌ Error on page {page}: {e}")
                break
        
        logger.info(f"✅ Yellow Pages {location}: {len(leads)} leads")
        return leads
    
    def extract_yellow_pages_data(self, listing, location):
        """Extract data from Yellow Pages listing."""
        try:
            # Company name
            name_elem = listing.find(['h3', 'h2', 'a'], class_=lambda x: x and 'name' in str(x).lower())
            if not name_elem:
                name_elem = listing.find('a', class_='listing-name')
            if not name_elem:
                name_elem = listing.find(['h3', 'h2'])
            if not name_elem:
                return None
            
            company_name = name_elem.get_text(strip=True)
            
            # Phone
            phone = ""
            phone_elem = listing.find('a', href=lambda x: x and 'tel:' in str(x))
            if phone_elem:
                phone = phone_elem.get_text(strip=True)
            
            # Website
            website = ""
            website_elem = listing.find('a', class_=lambda x: x and 'website' in str(x).lower())
            if not website_elem:
                website_elem = listing.find('a', href=lambda x: x and 'http' in str(x) and 'yellowpages' not in str(x))
            if website_elem:
                website = website_elem.get('href', '')
            
            # Address
            address = ""
            address_elem = listing.find(class_=lambda x: x and 'address' in str(x).lower())
            if address_elem:
                address = address_elem.get_text(strip=True)
            
            # Generate email
            email = self.generate_email(company_name, website)
            
            return {
                'company_name': company_name,
                'executive_name': '',
                'email': email,
                'phone': phone,
                'website': website,
                'address': address,
                'state': location,
                'source': 'Yellow Pages AU',
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.debug(f"Extraction error: {e}")
            return None
    
    def scrape_true_local(self, keyword, location):
        """Scrape True Local Australia with Selenium."""
        logger.info(f"🔍 True Local: {keyword} in {location}")
        leads = []
        
        try:
            url = f"https://www.truelocal.com.au/search/{quote_plus(keyword)}/{quote_plus(location)}"
            
            logger.info(f"  🌐 Loading...")
            
            # Load page
            self.driver.get(url)
            
            # Wait for content
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div, article"))
                )
            except:
                logger.warning(f"  ⏱️ Timeout")
            
            time.sleep(random.uniform(2, 4))
            
            # Get page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find business cards
            listings = soup.find_all('div', class_=lambda x: x and 'business' in str(x).lower())
            if not listings:
                listings = soup.find_all('article')
            if not listings:
                listings = soup.find_all('div', class_=lambda x: x and 'listing' in str(x).lower())
            
            logger.info(f"  📋 Found {len(listings)} listings")
            
            for listing in listings[:50]:
                lead = self.extract_true_local_data(listing, location)
                if lead and lead['company_name'] not in self.seen_companies:
                    leads.append(lead)
                    self.seen_companies.add(lead['company_name'])
                    logger.info(f"  ✅ {lead['company_name']}")
            
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            logger.error(f"True Local error: {e}")
        
        logger.info(f"✅ True Local {location}: {len(leads)} leads")
        return leads
    
    def extract_true_local_data(self, listing, location):
        """Extract from True Local listing."""
        try:
            name_elem = listing.find(['h2', 'h3', 'a'])
            if not name_elem:
                return None
            
            company_name = name_elem.get_text(strip=True)
            
            phone = ""
            phone_elem = listing.find('a', href=lambda x: x and 'tel:' in str(x))
            if phone_elem:
                phone = phone_elem.get_text(strip=True)
            
            website = ""
            website_elem = listing.find('a', href=lambda x: x and 'http' in str(x))
            if website_elem:
                website = website_elem.get('href', '')
            
            email = self.generate_email(company_name, website)
            
            return {
                'company_name': company_name,
                'executive_name': '',
                'email': email,
                'phone': phone,
                'website': website,
                'address': '',
                'state': location,
                'source': 'True Local',
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except:
            return None
    
    def generate_email(self, company_name, website=None):
        """Generate likely email address."""
        # For now, just generate from company name
        # (Visiting websites with Selenium would be too slow)
        
        clean = company_name.lower()
        clean = re.sub(r'\b(pty|ltd|inc|llc|carpentry|joinery)\b', '', clean)
        clean = re.sub(r'[^a-z0-9]', '', clean)
        
        if clean:
            return f"info@{clean}.com.au"
        
        return ""
    
    def run_full_scrape(self):
        """Run complete scraping pipeline."""
        logger.info("=" * 70)
        logger.info("🚀 CARPENTRY LEAD SCRAPER STARTING (SELENIUM)")
        logger.info("=" * 70)
        
        keywords = [
            "carpentry",
            "joinery",
            "cabinet maker"
        ]
        
        locations = [
            "Sydney NSW",
            "Melbourne VIC",
            "Brisbane QLD",
            "Perth WA"
        ]
        
        try:
            # Phase 1: True Local
            logger.info("\n🎯 PHASE 1: True Local")
            logger.info("-" * 70)
            
            for keyword in keywords[:2]:
                for location in locations[:2]:
                    leads = self.scrape_true_local(keyword, location)
                    self.all_leads.extend(leads)
                    time.sleep(random.uniform(5, 10))
            
            # Phase 2: Yellow Pages
            logger.info("\n🎯 PHASE 2: Yellow Pages")
            logger.info("-" * 70)
            
            for keyword in keywords[:2]:
                for location in locations[:2]:
                    leads = self.scrape_yellow_pages_au(keyword, location, max_pages=2)
                    self.all_leads.extend(leads)
                    time.sleep(random.uniform(8, 15))
            
        finally:
            # Always close browser
            self.cleanup()
        
        # Save results
        self.save_results()
        
        logger.info("=" * 70)
        logger.info(f"✅ SCRAPING COMPLETE: {len(self.all_leads)} total leads")
        logger.info("=" * 70)
    
    def cleanup(self):
        """Close browser."""
        if self.driver:
            logger.info("🧹 Closing browser...")
            try:
                self.driver.quit()
            except:
                pass
    
    def save_results(self):
        """Save results to JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/raw_leads_{timestamp}.json"
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_leads, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved to: {filename}")


def main():
    """Test the scraper."""
    scraper = CarpentryLeadScraper()
    scraper.run_full_scrape()
    
    print(f"\n✅ Scraped {len(scraper.all_leads)} leads")
    
    if scraper.all_leads:
        print("\n📋 Sample lead:")
        print(json.dumps(scraper.all_leads[0], indent=2))


if __name__ == "__main__":
    main()
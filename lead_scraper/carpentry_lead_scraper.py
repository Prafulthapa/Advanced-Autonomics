"""
Carpentry Lead Scraper - USA EDITION (OHIO FOCUS)
Scrapes Google Maps for carpentry businesses in USA
WITH AUTO-SAVE EVERY 500 LEADS + SEARCH PROGRESS TRACKING
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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Force English locale to prevent Nepali/Devanagari text
import os
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LANGUAGE'] = 'en_US'
os.environ['LC_ALL'] = 'en_US.UTF-8'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CarpentryLeadScraper:
    """Scrape carpentry leads from Google Maps - USA Edition."""

    def __init__(self):
        self.all_leads = []
        self.seen_businesses = set()
        self.driver = None

        # NEW: Progress tracking file (persistent across restarts)
        self.progress_file = "data/scraper_progress.json"
        self.completed_searches = set()
        self.current_search_index = 0

        # NEW: Save every 500 leads
        self.save_milestone = 500
        self.last_save_count = 0

        # Load previous progress (must do this FIRST)
        self.load_progress()
        
        # NEW: Session file - reuse existing or create new
        self.session_file = self.get_or_create_session_file()
        
        # Load previously scraped businesses to avoid duplicates
        self.load_previous_scrapes()

        self.setup_selenium()

    def get_or_create_session_file(self):
        """Get existing session file or create new one."""
        try:
            # Check if we have a progress file with session info
            if Path(self.progress_file).exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                # Check if there's an active session file mentioned
                existing_session = progress_data.get('active_session_file')
                
                if existing_session and Path(existing_session).exists():
                    logger.info(f"📂 Continuing with existing session: {existing_session}")
                    
                    # Load existing leads into memory
                    with open(existing_session, 'r', encoding='utf-8') as f:
                        self.all_leads = json.load(f)
                    
                    self.last_save_count = len(self.all_leads)
                    logger.info(f"✅ Loaded {len(self.all_leads)} leads from previous session")
                    
                    return existing_session
            
            # No existing session, create new one
            session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_session = f"data/session_{session_timestamp}.json"
            logger.info(f"📂 Creating new session file: {new_session}")
            
            return new_session
            
        except Exception as e:
            logger.warning(f"⚠️  Error checking session file: {e}")
            # Fallback to new session
            session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"data/session_{session_timestamp}.json"

    def load_progress(self):
        """Load search progress from previous runs."""
        try:
            if Path(self.progress_file).exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                self.completed_searches = set(progress_data.get('completed_searches', []))
                self.current_search_index = progress_data.get('current_search_index', 0)
                
                logger.info("📋 Loading previous search progress...")
                logger.info(f"  ✅ {len(self.completed_searches)} searches already completed")
                logger.info(f"  ➡️  Will resume from search #{self.current_search_index + 1}")
            else:
                logger.info("  ℹ️  No previous progress found (first run)")
        except Exception as e:
            logger.warning(f"  ⚠️  Could not load progress: {e}")
            self.completed_searches = set()
            self.current_search_index = 0

    def save_progress_state(self):
        """Save current search progress."""
        try:
            progress_data = {
                'completed_searches': list(self.completed_searches),
                'current_search_index': self.current_search_index,
                'last_updated': datetime.now().isoformat(),
                'total_leads_collected': len(self.all_leads),
                'active_session_file': self.session_file  # Track which session file we're using
            }
            
            Path(self.progress_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
                
            logger.debug(f"💾 Progress state saved (search #{self.current_search_index})")
        except Exception as e:
            logger.error(f"❌ Failed to save progress state: {e}")

    def setup_selenium(self):
        """Configure Selenium with Chrome."""
        logger.info("🌐 Initializing Chrome browser...")

        chrome_options = Options()

        # Headless mode
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # Look like a real browser
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

        # Force English (US) language
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--accept-lang=en-US,en')
        chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'en-US,en;q=0.9',
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.geolocation': 2
        })

        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)

            # Override webdriver detection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'language', {
                        get: () => 'en-US'
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                '''
            })

            logger.info("✅ Chrome browser ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome: {e}")
            raise

    def load_previous_scrapes(self):
        """Load all previously scraped businesses to avoid duplicates."""
        logger.info("📂 Loading previous scrapes to avoid duplicates...")

        try:
            data_dir = Path("data")

            if not data_dir.exists():
                logger.info("  ℹ️  No previous data found (first run)")
                return

            # Find all previous raw_leads JSON files AND session files
            json_files = list(data_dir.glob("raw_leads_*.json")) + list(data_dir.glob("session_*.json"))

            if not json_files:
                logger.info("  ℹ️  No previous scrapes found (first run)")
                return

            logger.info(f"  📄 Found {len(json_files)} previous scrape files")

            # Load all business names from previous files
            total_loaded = 0
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        leads = json.load(f)

                    for lead in leads:
                        company_name = lead.get('company_name', '')
                        if company_name:
                            self.seen_businesses.add(company_name)
                            total_loaded += 1

                except Exception as e:
                    logger.debug(f"  ⚠️  Error loading {json_file.name}: {e}")
                    continue

            logger.info(f"  ✅ Loaded {total_loaded} previously scraped businesses")
            logger.info(f"  🛡️  These will be skipped to avoid duplicates")

        except Exception as e:
            logger.error(f"  ❌ Error loading previous scrapes: {e}")

    def save_progress(self, force=False, after_each_search=False):
        """
        Save current progress to file.
        
        Args:
            force: Force save regardless of milestone
            after_each_search: Quiet save after each search (no milestone message)
        """
        current_count = len(self.all_leads)

        # Check if we've hit a 500-lead milestone
        current_milestone = (current_count // self.save_milestone) * self.save_milestone
        last_milestone = (self.last_save_count // self.save_milestone) * self.save_milestone

        should_save_milestone = current_milestone > last_milestone and current_count >= self.save_milestone
        should_save = force or should_save_milestone or after_each_search

        if not should_save:
            return

        if not self.all_leads:
            return

        try:
            Path(self.session_file).parent.mkdir(parents=True, exist_ok=True)

            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_leads, f, indent=2, ensure_ascii=False)

            # Only show milestone message if it's a milestone save
            if should_save_milestone or force:
                logger.info("")
                logger.info("=" * 70)
                logger.info(f"💾 MILESTONE REACHED: {current_count} leads collected!")
                logger.info(f"💾 Progress saved → {self.session_file}")
                logger.info(f"📊 Next save at: {current_milestone + self.save_milestone} leads")
                logger.info("=" * 70)
                logger.info("")
                self.last_save_count = current_count
            elif after_each_search:
                # Quiet save - just update internal counter
                logger.debug(f"💾 Auto-saved {current_count} leads to session file")

        except Exception as e:
            logger.error(f"❌ Failed to save progress: {e}")

    def search_google_maps(self, query, location, max_results=60):
        """Search Google Maps for businesses."""
        logger.info(f"🔍 Google Maps: {query} in {location}")
        leads = []

        try:
            # Build search URL with English locale
            search_query = f"{query} in {location}"
            url = f"https://www.google.com/maps/search/{quote_plus(search_query)}?hl=en"

            logger.info(f"  🌐 Loading Google Maps...")
            self.driver.get(url)

            # Wait for results to load
            time.sleep(5)

            # Scroll to load more results
            logger.info(f"  📜 Scrolling to load results...")
            self.scroll_results_panel(max_results)

            # Get page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find all business cards
            business_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")

            logger.info(f"  📋 Found {len(business_elements)} business listings")

            # Extract data from each business
            processed = 0
            for element in business_elements[:max_results]:
                if processed >= max_results:
                    break

                try:
                    # Click to open details panel
                    element.click()
                    time.sleep(random.uniform(1, 2))

                    # Extract business details
                    lead = self.extract_business_details()

                    if lead and lead['company_name'] not in self.seen_businesses:
                        leads.append(lead)
                        self.seen_businesses.add(lead['company_name'])
                        processed += 1
                        logger.info(f"  ✅ [{processed}] {lead['company_name']}")

                    # Small delay to avoid detection
                    time.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    logger.debug(f"  ⚠️ Error extracting business: {e}")
                    continue

        except Exception as e:
            logger.error(f"  ❌ Search error: {e}")

        logger.info(f"✅ Google Maps {location}: {len(leads)} leads")
        return leads

    def scroll_results_panel(self, target_count=20):
        """Scroll the results panel to load more businesses."""
        try:
            scrollable = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")

            last_height = 0
            attempts = 0
            max_attempts = 10

            while attempts < max_attempts:
                self.driver.execute_script(
                    'arguments[0].scrollTo(0, arguments[0].scrollHeight);',
                    scrollable
                )

                time.sleep(2)

                results = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
                if len(results) >= target_count:
                    break

                new_height = self.driver.execute_script('return arguments[0].scrollHeight', scrollable)
                if new_height == last_height:
                    attempts += 1
                else:
                    attempts = 0

                last_height = new_height

        except Exception as e:
            logger.debug(f"Scroll error: {e}")

    def extract_business_details(self):
        """Extract details from currently selected business."""
        try:
            time.sleep(1)

            # Get business name
            name = ""
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf")
                name = name_elem.text.strip()
            except:
                try:
                    name_elem = self.driver.find_element(By.CSS_SELECTOR, "h2.bwoZTb")
                    name = name_elem.text.strip()
                except:
                    return None

            if not name:
                return None

            # Get rating (optional)
            rating = ""
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-label*='stars']")
                rating = rating_elem.get_attribute('aria-label')
            except:
                pass

            # Get address
            address = ""
            try:
                address_elem = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='address']")
                address = address_elem.get_attribute('aria-label')
                if address and 'Address:' in address:
                    address = address.replace('Address:', '').strip()
                address = address.replace('ठेगाना:', '').strip()
            except:
                try:
                    address_elem = self.driver.find_element(By.CSS_SELECTOR, "div.rogA2c div.Io6YTe")
                    address = address_elem.text.strip()
                    address = address.replace('ठेगाना:', '').strip()
                except:
                    pass

            # Get phone number
            phone = ""
            try:
                phone_elem = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
                phone_text = phone_elem.get_attribute('aria-label')
                if phone_text and 'Phone:' in phone_text:
                    phone = phone_text.replace('Phone:', '').strip()
            except:
                pass

            # Get website
            website = ""
            try:
                website_elem = self.driver.find_element(By.CSS_SELECTOR, "a[data-item-id*='authority']")
                website = website_elem.get_attribute('href')
            except:
                pass

            # Extract state from address
            state = self.extract_state(address)

            # Generate email
            email = self.generate_email(name, website)

            return {
                'company_name': name,
                'executive_name': '',
                'email': email,
                'phone': phone,
                'website': website,
                'address': address,
                'state': state,
                'rating': rating,
                'source': 'Google Maps',
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.debug(f"Extract details error: {e}")
            return None

    def extract_state(self, address):
        """Extract USA state from address string."""
        states = [
            'OH', 'MI', 'IN', 'PA', 'KY', 'IL', 'NY', 'CA', 'TX', 'FL',
            'WA', 'OR', 'CO', 'AZ', 'NV', 'UT', 'NM', 'MT', 'WY', 'ID',
            'ND', 'SD', 'NE', 'KS', 'OK', 'AR', 'LA', 'MS', 'AL', 'TN',
            'GA', 'SC', 'NC', 'VA', 'WV', 'MD', 'DE', 'NJ', 'CT', 'RI',
            'MA', 'VT', 'NH', 'ME', 'AK', 'HI', 'DC'
        ]

        for state in states:
            if re.search(r'\b' + state + r'\b', address.upper()):
                return state

        return ""

    def generate_email(self, business_name, website=None):
        """Generate likely email address."""
        if website:
            try:
                domain = re.search(r'https?://(?:www\.)?([^/]+)', website)
                if domain:
                    domain = domain.group(1)
                    return f"info@{domain}"
            except:
                pass

        clean = business_name.lower()
        clean = re.sub(r'\b(inc|llc|ltd|corp|carpentry|construction)\b', '', clean)
        clean = re.sub(r'[^a-z0-9]', '', clean)

        if clean:
            return f"info@{clean}.com"

        return ""

    def run_full_scrape(self):
        """Run complete scraping pipeline - OHIO TOTAL MARKET SATURATION."""
        logger.info("=" * 70)
        logger.info("🚀 CARPENTRY LEAD SCRAPER STARTING (GOOGLE MAPS)")
        logger.info("🇺🇸 OHIO TOTAL MARKET SATURATION")
        logger.info("🎯 TARGET: 3,000-4,000 LEADS")
        logger.info("=" * 70)

        # EXPANDED search terms
        search_terms = [
            "carpentry", "carpenter", "carpentry services", "carpentry contractor",
            "cabinet maker", "cabinetmaker", "custom cabinets", "kitchen cabinets",
            "woodworking", "custom woodworking", "wood shop",
            "finish carpentry", "trim carpentry", "framing contractor", "millwork",
            "kitchen remodeling", "bathroom remodeling", "home remodeling",
            "renovation contractor"
        ]

        # COMPREHENSIVE Ohio locations
        locations = [
            "Columbus OH", "Cleveland OH", "Cincinnati OH", "Toledo OH", "Akron OH",
            "Dayton OH", "Parma OH", "Canton OH", "Youngstown OH", "Lorain OH",
            "Hamilton OH", "Springfield OH", "Kettering OH", "Elyria OH", "Lakewood OH",
            "Cuyahoga Falls OH", "Middletown OH", "Newark OH", "Mansfield OH", "Mentor OH",
            "Beavercreek OH", "Strongsville OH", "Dublin OH", "Fairfield OH", "Warren OH",
            "Lima OH", "Huber Heights OH", "Marion OH", "Findlay OH", "Lancaster OH",
            "Euclid OH", "Cleveland Heights OH", "Westerville OH", "Delaware OH", "Grove City OH",
            "Reynoldsburg OH", "Upper Arlington OH", "Gahanna OH", "Hilliard OH", "Mason OH",
            "Stow OH", "Brunswick OH", "North Olmsted OH", "North Royalton OH", "Westlake OH",
            "Boardman OH", "Kent OH", "Garfield Heights OH", "Sandusky OH", "Massillon OH",
            "Bowling Green OH", "Alliance OH", "Austintown OH", "Zanesville OH", "Fairborn OH",
            "Ashland OH", "Chillicothe OH", "Portsmouth OH", "Wooster OH", "Xenia OH",
            "Tiffin OH", "Miamisburg OH", "Medina OH", "Wadsworth OH", "Barberton OH",
            "Coshocton OH", "Fremont OH", "Sidney OH", "Oxford OH", "Troy OH",
            "Piqua OH", "Norwalk OH", "Defiance OH", "Cambridge OH", "Bucyrus OH",
            "Marysville OH", "Bellefontaine OH", "Salem OH", "Circleville OH",
            "Washington Court House OH", "Urbana OH", "New Philadelphia OH", "Galion OH",
            "Greenville OH", "Marietta OH", "Athens OH", "Mount Vernon OH", "Ashtabula OH",
            "Conneaut OH", "Willoughby OH", "Painesville OH"
        ]

        # Create all search combinations
        all_searches = [(term, loc) for term in search_terms for loc in locations]
        total_searches = len(all_searches)

        logger.info(f"📊 MARKET SATURATION STRATEGY:")
        logger.info(f"   - {len(search_terms)} search terms")
        logger.info(f"   - {len(locations)} Ohio locations")
        logger.info(f"   - Total searches: {total_searches}")
        logger.info(f"   - 💾 AUTO-SAVE: Every {self.save_milestone} leads")
        logger.info(f"   - 🔄 RESUME: Can restart from last position")
        logger.info(f"🛡️  Will skip {len(self.seen_businesses)} previously scraped businesses")
        
        if self.current_search_index > 0:
            logger.info(f"")
            logger.info(f"🔄 RESUMING FROM PREVIOUS RUN:")
            logger.info(f"   - Starting at search #{self.current_search_index + 1}/{total_searches}")
            logger.info(f"   - Skipping {self.current_search_index} already completed searches")
        
        logger.info("")

        try:
            # Start from where we left off
            for idx in range(self.current_search_index, total_searches):
                # Update current index
                self.current_search_index = idx
                
                # OPTIONAL: Remove this block if you want unlimited scraping
                # STOP AT 4,000 LEADS (comment out these 3 lines to continue forever)
                # if len(self.all_leads) >= 4000:
                #     logger.info(f"🛑 Reached 4,000 leads limit, stopping scrape")
                #     break

                term, location = all_searches[idx]
                search_key = f"{term}|{location}"
                
                # Skip if already completed
                if search_key in self.completed_searches:
                    logger.info(f"⏭️  Skipping search {idx + 1}/{total_searches}: {term} in {location} (already done)")
                    continue

                # RESTART BROWSER EVERY 50 SEARCHES (prevent memory leaks)
                if idx > 0 and idx % 50 == 0:
                    logger.info(f"🔄 Restarting browser to prevent memory issues (search {idx + 1})")
                    try:
                        self.driver.quit()
                    except:
                        pass
                    time.sleep(3)
                    self.setup_selenium()

                logger.info(f"🔍 Search {idx + 1}/{total_searches}: {term} in {location}")

                try:
                    leads = self.search_google_maps(term, location, max_results=60)
                    self.all_leads.extend(leads)
                    
                    # Mark search as completed
                    self.completed_searches.add(search_key)

                    # Show progress
                    logger.info(f"   Progress: {len(self.all_leads)} total leads | Search {idx + 1}/{total_searches}")

                    # Save progress state after each search
                    self.save_progress_state()
                    
                    # IMPORTANT: Save session file after EACH search (prevents data loss)
                    self.save_progress(after_each_search=True)
                    
                    # Check for milestone saves (with announcements)
                    self.save_progress()

                except Exception as e:
                    logger.error(f"❌ Search failed: {e}")
                    logger.info(f"🔄 Attempting to restart browser...")
                    try:
                        self.driver.quit()
                    except:
                        pass
                    time.sleep(3)
                    self.setup_selenium()
                    # Don't mark as completed so it will retry next run
                    continue

                # Delay between searches
                time.sleep(random.uniform(3, 7))

        finally:
            logger.info("")
            logger.info("🔒 Finalizing and saving all data...")
            self.save_progress(force=True)
            self.cleanup()

        # Save results
        if self.all_leads:
            self.save_results()
        else:
            logger.warning("⚠️  No new leads found (all were duplicates)")

        logger.info("=" * 70)
        logger.info(f"✅ SCRAPING COMPLETE: {len(self.all_leads)} NEW leads")
        logger.info(f"🛡️  Skipped {len(self.seen_businesses) - len(self.all_leads)} duplicates")
        logger.info(f"🔍 Completed {len(self.completed_searches)}/{total_searches} searches")
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
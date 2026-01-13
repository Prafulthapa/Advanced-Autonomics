"""
LinkedIn Scraper - FIXED VERSION
✅ Login working
✅ Updated selectors for 2025 LinkedIn
✅ Multiple fallback selectors
✅ Better error handling
"""

import time
import random
import logging
import json
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

from config import SCRAPER_CONFIG, LINKEDIN_EMAIL, LINKEDIN_PASSWORD

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Scrape LinkedIn with updated 2025 selectors."""

    def __init__(self):
        self.driver = None
        self.leads = []
        self.session_profile_count = 0
        self.debug_dir = Path("data/debug")
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def save_debug_screenshot(self, name):
        """Save screenshot for debugging."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.debug_dir / f"{timestamp}_{name}.png"
            self.driver.save_screenshot(str(filename))
            logger.info(f"📸 Screenshot: {filename}")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")

    def save_debug_html(self, name):
        """Save HTML for debugging."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.debug_dir / f"{timestamp}_{name}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"💾 HTML saved: {filename}")
        except Exception as e:
            logger.error(f"HTML save failed: {e}")

    def setup_driver(self):
        """Setup Chrome with anti-detection."""
        logger.info("🔧 Setting up Chrome driver...")

        options = Options()

        # Headless mode
        if SCRAPER_CONFIG.get("headless", True):
            options.add_argument("--headless=new")

        # Docker + stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Create driver
        self.driver = webdriver.Chrome(options=options)

        # Remove webdriver flag
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logger.info("✅ Chrome driver ready")

    def human_delay(self, min_delay=None, max_delay=None):
        """Human-like delay."""
        min_delay = min_delay or SCRAPER_CONFIG["delays"]["min_delay"]
        max_delay = max_delay or SCRAPER_CONFIG["delays"]["max_delay"]
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def login(self):
        """Login to LinkedIn."""
        logger.info("🔐 Logging into LinkedIn...")

        try:
            self.driver.get("https://www.linkedin.com/login")
            self.human_delay(2, 4)

            # Enter email
            email_field = self.driver.find_element(By.ID, "username")
            for char in LINKEDIN_EMAIL:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self.human_delay(1, 2)

            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            for char in LINKEDIN_PASSWORD:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self.human_delay(1, 2)

            # Click submit
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            self.human_delay(5, 8)

            # Check if logged in
            if any(x in self.driver.current_url for x in ("feed", "mynetwork")):
                logger.info("✅ Login successful")
                return True

            logger.error("❌ Login may have failed")
            return False

        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False

    def search_linkedin(self, job_title, location, industry_keyword=None):
        """Search LinkedIn with improved URL and selectors."""
        query = f"{job_title} {location}"
        if industry_keyword:
            query += f" {industry_keyword}"

        logger.info(f"🔍 Searching: {query}")

        try:
            # NEW: Use Sales Navigator-style URL (more reliable)
            # Or regular search with better params
            url = (
                f"https://www.linkedin.com/search/results/people/"
                f"?keywords={query.replace(' ', '%20')}"
                f"&origin=GLOBAL_SEARCH_HEADER"
            )
            
            logger.info(f"📍 URL: {url}")
            self.driver.get(url)
            
            # Save debug info
            self.save_debug_screenshot(f"search_{job_title.replace(' ', '_')}")
            
            # Wait for page load
            self.human_delay(5, 8)  # Longer wait for search results
            
            # Wait for results to appear
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.reusable-search__entity-result-list"))
                )
                logger.info("✅ Search results container found")
            except TimeoutException:
                logger.warning("⚠️  Search results container not found, continuing anyway")

            # Scroll to load more
            self.scroll_page()
            
            # Save HTML for analysis
            self.save_debug_html(f"search_{job_title.replace(' ', '_')}")
            
            # Extract profiles
            profiles = self.extract_profiles_from_page()

            logger.info(f"✅ Found {len(profiles)} profiles for: {query}")
            return profiles

        except Exception as e:
            logger.error(f"❌ Search error: {e}", exc_info=True)
            self.save_debug_screenshot("ERROR_search_failed")
            self.save_debug_html("ERROR_search_failed")
            return []

    def scroll_page(self):
        """Scroll page to load all results."""
        logger.info("📜 Scrolling to load results...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        for i in range(5):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_delay(3, 5)  # Longer delay for results to load
            
            # Calculate new height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            logger.debug(f"Scroll {i+1}/5: height {last_height} → {new_height}")
            
            if new_height == last_height:
                logger.info("📜 No more content to load")
                break
                
            last_height = new_height

    def extract_profiles_from_page(self):
        """Extract profiles with MULTIPLE fallback selectors."""
        profiles = []

        # ============================================
        # TRY MULTIPLE SELECTOR PATTERNS
        # LinkedIn changes these frequently
        # ============================================
        
        selector_attempts = [
            # Modern LinkedIn (2025)
            "li.reusable-search__result-container",
            
            # Alternative modern format
            "div.entity-result",
            
            # Older format (fallback)
            ".entity-result__item",
            
            # Another variation
            "li[class*='search-result']",
            
            # Generic list items in results
            "ul.reusable-search__entity-result-list > li",
        ]

        cards = []
        
        for selector in selector_attempts:
            try:
                found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if found:
                    logger.info(f"✅ Found {len(found)} elements with selector: {selector}")
                    cards = found
                    break
                else:
                    logger.debug(f"⚠️  No elements with selector: {selector}")
            except Exception as e:
                logger.debug(f"⚠️  Selector failed: {selector} - {e}")
                continue

        if not cards:
            logger.error("❌ NO CARDS FOUND WITH ANY SELECTOR!")
            logger.error("🔍 Saving page source for manual analysis...")
            self.save_debug_screenshot("NO_CARDS_FOUND")
            self.save_debug_html("NO_CARDS_FOUND")
            
            # Try to find ANY links to profiles
            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
            logger.info(f"🔗 Found {len(all_links)} profile links on page")
            
            return []

        logger.info(f"📊 Processing {len(cards)} profile cards...")

        # Extract data from cards
        for idx, card in enumerate(cards[:50], 1):
            profile = self.extract_profile_data(card)
            if profile:
                logger.debug(f"✅ Extracted profile {idx}: {profile['name']}")
                profiles.append(profile)
                self.session_profile_count += 1

                if self.session_profile_count >= SCRAPER_CONFIG["max_linkedin_profiles_per_day"]:
                    logger.warning("⚠️  Daily limit reached")
                    break
            else:
                logger.debug(f"⚠️  Failed to extract profile {idx}")

        return profiles

    def extract_profile_data(self, card):
        """Extract data from profile card with multiple selector fallbacks."""
        try:
            # ============================================
            # NAME - Try multiple selectors
            # ============================================
            name = None
            name_selectors = [
                ".entity-result__title-text a span[aria-hidden='true']",
                "span.entity-result__title-text span[dir='ltr']",
                "a.app-aware-link span[aria-hidden='true']",
                ".entity-result__title-text span",
                "span[dir='ltr']",
            ]
            
            for selector in name_selectors:
                try:
                    name = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                    if name:
                        break
                except:
                    continue

            # ============================================
            # PROFILE LINK - Try multiple selectors
            # ============================================
            link = None
            link_selectors = [
                ".entity-result__title-text a",
                "a[href*='/in/']",
                ".app-aware-link",
            ]
            
            for selector in link_selectors:
                try:
                    link = card.find_element(By.CSS_SELECTOR, selector).get_attribute("href")
                    if link and "/in/" in link:
                        break
                except:
                    continue

            # ============================================
            # TITLE (Job Title)
            # ============================================
            title = self.safe_text(card, ".entity-result__primary-subtitle")
            if not title:
                title = self.safe_text(card, "div.entity-result__summary")

            # ============================================
            # COMPANY
            # ============================================
            company = self.safe_text(card, ".entity-result__secondary-subtitle")

            # ============================================
            # LOCATION
            # ============================================
            location = self.safe_text(card, ".entity-result__location")
            if not location:
                location = self.safe_text(card, "div[class*='location']")

            # Validate we got essential data
            if not name or not link:
                logger.debug(f"⚠️  Skipping card - missing name or link")
                return None

            profile = {
                "name": name,
                "linkedin_url": link,
                "title": title,
                "company": company,
                "location": location,
                "scraped_at": datetime.utcnow().isoformat(),
                "source": "linkedin_search",
            }
            
            return profile

        except Exception as e:
            logger.debug(f"Failed to extract profile: {e}")
            return None

    def safe_text(self, parent, selector):
        """Safely extract text from element."""
        try:
            element = parent.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return ""

    def run_all_searches(self):
        """Run configured searches."""
        logger.info("🚀 Starting LinkedIn scraping session")
        logger.info(f"🎯 Target: {SCRAPER_CONFIG['max_linkedin_profiles_per_day']} profiles max")

        all_leads = []

        # Limit searches to avoid overwhelming the session
        for job_title in SCRAPER_CONFIG["job_titles"][:3]:  # First 3 titles only
            for location in SCRAPER_CONFIG["target_locations"][:2]:  # First 2 locations
                if self.session_profile_count >= SCRAPER_CONFIG["max_linkedin_profiles_per_day"]:
                    logger.info("🎯 Daily limit reached, stopping")
                    break

                profiles = self.search_linkedin(job_title, location)
                all_leads.extend(profiles)
                
                logger.info(f"📊 Session progress: {self.session_profile_count}/{SCRAPER_CONFIG['max_linkedin_profiles_per_day']}")
                
                # Longer delay between searches
                self.human_delay(15, 25)

        self.save_raw_leads(all_leads)
        logger.info(f"✅ Scraping finished: {len(all_leads)} total leads")
        
        return all_leads

    def save_raw_leads(self, leads):
        """Save leads to JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = Path(f"data/raw_leads_{timestamp}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Leads saved to: {path}")

    def cleanup(self):
        """Close browser."""
        if self.driver:
            self.driver.quit()
            logger.info("🧹 Browser closed")


def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("LINKEDIN SCRAPER - FIXED VERSION")
    logger.info("=" * 60)
    
    scraper = LinkedInScraper()
    
    try:
        scraper.setup_driver()
        
        if scraper.login():
            logger.info("✅ Login successful - starting scraping")
            leads = scraper.run_all_searches()
            
            if leads:
                logger.info(f"🎉 SUCCESS! Scraped {len(leads)} leads")
            else:
                logger.warning("⚠️  No leads found - check debug files")
                logger.warning("📁 Debug files: data/debug/")
        else:
            logger.error("❌ Login failed")
    
    except KeyboardInterrupt:
        logger.info("⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        scraper.cleanup()
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
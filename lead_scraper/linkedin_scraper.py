"""
LinkedIn Scraper - Automated lead collection
Uses Selenium with anti-detection measures
Docker-safe | Selenium Manager compatible
"""

import time
import random
import logging
import json
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

from config import SCRAPER_CONFIG, LINKEDIN_EMAIL, LINKEDIN_PASSWORD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Scrape LinkedIn for targeted company leaders."""

    def __init__(self):
        self.driver = None
        self.leads = []
        self.session_profile_count = 0

    # --------------------------------------------------
    # DRIVER SETUP (THIS IS WHERE CHROME ACTUALLY STARTS)
    # --------------------------------------------------
    def setup_driver(self):
        logger.info("🔧 Setting up Chrome driver (Selenium Manager)...")

        options = Options()

        if SCRAPER_CONFIG.get("headless", True):
            options.add_argument("--headless=new")

        # Docker + stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        )

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 🔥 THIS LINE IS THE KEY
        # Selenium Manager automatically finds Chrome + driver
        self.driver = webdriver.Chrome(options=options)

        # Remove webdriver flag
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logger.info("✅ Chrome driver ready")

    # --------------------------------------------------
    # HUMAN BEHAVIOR
    # --------------------------------------------------
    def human_delay(self, min_delay=None, max_delay=None):
        min_delay = min_delay or SCRAPER_CONFIG["delays"]["min_delay"]
        max_delay = max_delay or SCRAPER_CONFIG["delays"]["max_delay"]
        time.sleep(random.uniform(min_delay, max_delay))

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------
    def login(self):
        logger.info("🔐 Logging into LinkedIn...")

        try:
            self.driver.get("https://www.linkedin.com/login")
            self.human_delay(2, 4)

            email_field = self.driver.find_element(By.ID, "username")
            for char in LINKEDIN_EMAIL:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self.human_delay(1, 2)

            password_field = self.driver.find_element(By.ID, "password")
            for char in LINKEDIN_PASSWORD:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self.human_delay(1, 2)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            self.human_delay(5, 8)

            if any(x in self.driver.current_url for x in ("feed", "mynetwork")):
                logger.info("✅ Login successful")
                return True

            logger.error("❌ Login may have failed")
            return False

        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False

    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------
    def search_linkedin(self, job_title, location, industry_keyword=None):
        query = f"{job_title} {location}"
        if industry_keyword:
            query += f" {industry_keyword}"

        logger.info(f"🔍 Searching: {query}")

        try:
            url = (
                "https://www.linkedin.com/search/results/people/?keywords="
                + query.replace(" ", "%20")
            )
            self.driver.get(url)
            self.human_delay(3, 5)

            self.scroll_page()
            profiles = self.extract_profiles_from_page()

            logger.info(f"✅ Found {len(profiles)} profiles")
            return profiles

        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []

    # --------------------------------------------------
    # SCROLLING
    # --------------------------------------------------
    def scroll_page(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        for _ in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_delay(2, 4)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    # --------------------------------------------------
    # EXTRACTION
    # --------------------------------------------------
    def extract_profiles_from_page(self):
        profiles = []

        cards = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".entity-result__item, .reusable-search__result-container",
        )

        logger.info(f"📊 Found {len(cards)} cards")

        for card in cards[:50]:
            profile = self.extract_profile_data(card)
            if profile:
                profiles.append(profile)
                self.session_profile_count += 1

                if self.session_profile_count >= SCRAPER_CONFIG["max_linkedin_profiles_per_day"]:
                    logger.warning("⚠️ Daily limit reached")
                    break

        return profiles

    def extract_profile_data(self, card):
        try:
            name = card.find_element(
                By.CSS_SELECTOR,
                ".entity-result__title-text a span[aria-hidden='true']",
            ).text.strip()

            link = card.find_element(
                By.CSS_SELECTOR, ".entity-result__title-text a"
            ).get_attribute("href")

            title = self.safe_text(card, ".entity-result__primary-subtitle")
            company = self.safe_text(card, ".entity-result__secondary-subtitle")
            location = self.safe_text(card, ".entity-result__location")

            if not name or not link:
                return None

            return {
                "name": name,
                "linkedin_url": link,
                "title": title,
                "company": company,
                "location": location,
                "scraped_at": datetime.utcnow().isoformat(),
                "source": "linkedin_search",
            }

        except Exception:
            return None

    def safe_text(self, parent, selector):
        try:
            return parent.find_element(By.CSS_SELECTOR, selector).text.strip()
        except Exception:
            return ""

    # --------------------------------------------------
    # RUNNER
    # --------------------------------------------------
    def run_all_searches(self):
        logger.info("🚀 Starting LinkedIn scraping session")

        all_leads = []

        for job_title in SCRAPER_CONFIG["job_titles"][:5]:
            for location in SCRAPER_CONFIG["target_locations"][:3]:
                if self.session_profile_count >= SCRAPER_CONFIG["max_linkedin_profiles_per_day"]:
                    break

                all_leads.extend(self.search_linkedin(job_title, location))
                self.human_delay(5, 10)

                for keyword in SCRAPER_CONFIG["industry_keywords"][:3]:
                    if self.session_profile_count >= SCRAPER_CONFIG["max_linkedin_profiles_per_day"]:
                        break
                    all_leads.extend(self.search_linkedin(job_title, location, keyword))
                    self.human_delay(5, 10)

        self.save_raw_leads(all_leads)
        logger.info(f"✅ Scraping finished: {len(all_leads)} leads")
        return all_leads

    # --------------------------------------------------
    # SAVE / CLEANUP
    # --------------------------------------------------
    def save_raw_leads(self, leads):
        path = f"data/raw_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved to {path}")

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            logger.info("🧹 Browser closed")


def main():
    scraper = LinkedInScraper()
    try:
        scraper.setup_driver()
        if scraper.login():
            scraper.run_all_searches()
        else:
            logger.error("❌ Login failed")
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()

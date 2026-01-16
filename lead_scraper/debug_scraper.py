"""
Debug Scraper - Shows what's actually on the pages
Run this to see what HTML structure we're dealing with
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def debug_yellow_pages():
    """Debug Yellow Pages structure."""
    print("=" * 70)
    print("🔍 DEBUGGING YELLOW PAGES")
    print("=" * 70)
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = "https://www.yellowpages.com.au/search/listings?clue=carpentry&locationClue=Sydney+NSW&pageNumber=1"
        print(f"\n📄 Loading: {url}\n")
        
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        print("🔍 Page Title:", driver.title)
        print(f"📏 Page HTML length: {len(html)} characters\n")
        
        # Save full HTML for inspection
        with open('data/debug_yellowpages.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 Saved full HTML to: data/debug_yellowpages.html\n")
        
        # Try to find any potential listing containers
        print("🔍 Looking for potential listing elements...\n")
        
        # Try different selectors
        selectors = [
            ('article', {}),
            ('div', {'class': 'listing'}),
            ('div', {'class': 'result'}),
            ('div', {'class': 'search-result'}),
            ('li', {}),
            ('div', {'data-listing-id': True}),
        ]
        
        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs)
            if elements:
                print(f"✅ Found {len(elements)} <{tag}> elements with {attrs}")
                if len(elements) > 0:
                    print(f"   First element preview:")
                    print(f"   {str(elements[0])[:300]}...\n")
            else:
                print(f"❌ No <{tag}> elements found with {attrs}")
        
        # Look for any h2, h3 tags (usually business names)
        print("\n🔍 Looking for headings (business names)...\n")
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        print(f"Found {len(headings)} heading tags")
        for i, h in enumerate(headings[:5]):
            print(f"  {i+1}. <{h.name}>: {h.get_text(strip=True)[:80]}")
        
        # Look for links
        print("\n🔍 Looking for links...\n")
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} total links")
        business_links = [l for l in links if l.get_text(strip=True) and len(l.get_text(strip=True)) > 10]
        print(f"Found {len(business_links)} potential business name links")
        for i, link in enumerate(business_links[:5]):
            print(f"  {i+1}. {link.get_text(strip=True)[:60]}")
        
        # Check if blocked
        if 'blocked' in html.lower() or 'captcha' in html.lower() or 'access denied' in html.lower():
            print("\n⚠️  WARNING: Page might be showing block/captcha message")
        
        print("\n" + "=" * 70)
        
    finally:
        driver.quit()


def debug_true_local():
    """Debug True Local structure."""
    print("\n" + "=" * 70)
    print("🔍 DEBUGGING TRUE LOCAL")
    print("=" * 70)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = "https://www.truelocal.com.au/search/carpentry/Sydney+NSW"
        print(f"\n📄 Loading: {url}\n")
        
        driver.get(url)
        time.sleep(5)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        print("🔍 Page Title:", driver.title)
        print(f"📏 Page HTML length: {len(html)} characters\n")
        
        # Save full HTML
        with open('data/debug_truelocal.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 Saved full HTML to: data/debug_truelocal.html\n")
        
        # Look for business listings
        print("🔍 Looking for potential listing elements...\n")
        
        selectors = [
            ('div', {'class': 'business'}),
            ('article', {}),
            ('div', {'class': 'listing'}),
            ('div', {'class': 'result'}),
            ('li', {}),
        ]
        
        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs)
            if elements:
                print(f"✅ Found {len(elements)} <{tag}> elements")
                if len(elements) > 0:
                    print(f"   First element preview:")
                    print(f"   {str(elements[0])[:300]}...\n")
            else:
                print(f"❌ No <{tag}> elements found")
        
        # Look for headings
        print("\n🔍 Looking for headings...\n")
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        print(f"Found {len(headings)} heading tags")
        for i, h in enumerate(headings[:5]):
            print(f"  {i+1}. <{h.name}>: {h.get_text(strip=True)[:80]}")
        
        print("\n" + "=" * 70)
        
    finally:
        driver.quit()


if __name__ == "__main__":
    print("\n🔬 LEAD SCRAPER DEBUG TOOL\n")
    print("This will show us what HTML structure the sites actually use")
    print("so we can fix the scraper selectors.\n")
    
    input("Press Enter to start debugging...")
    
    debug_yellow_pages()
    debug_true_local()
    
    print("\n✅ Debug complete!")
    print("\nCheck these files:")
    print("  - data/debug_yellowpages.html")
    print("  - data/debug_truelocal.html")
    print("\nShare the output above so I can fix the selectors!")
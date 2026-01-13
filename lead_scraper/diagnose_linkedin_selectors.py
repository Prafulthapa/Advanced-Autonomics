"""
LinkedIn Selector Diagnostic Tool
Run this to see exactly what LinkedIn is showing
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD

print("=" * 60)
print("🔍 LINKEDIN SELECTOR DIAGNOSTIC")
print("=" * 60)
print()

# Setup Chrome (visible mode for debugging)
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=options)

try:
    # Login
    print("🔐 Logging in...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)
    
    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    time.sleep(1)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(6)
    
    if "feed" in driver.current_url or "mynetwork" in driver.current_url:
        print("✅ Login successful")
    else:
        print("❌ Login may have failed")
        print(f"Current URL: {driver.current_url}")
    
    # Search
    print("\n🔍 Performing test search...")
    search_url = "https://www.linkedin.com/search/results/people/?keywords=CEO%20Australia"
    driver.get(search_url)
    time.sleep(8)
    
    print(f"📍 Current URL: {driver.current_url}")
    
    # Try all possible selectors
    print("\n" + "=" * 60)
    print("🔎 TESTING SELECTORS")
    print("=" * 60)
    
    selectors_to_test = [
        ("Modern list items", "li.reusable-search__result-container"),
        ("Entity results", "div.entity-result"),
        ("Old entity items", ".entity-result__item"),
        ("Search results", "li[class*='search-result']"),
        ("List items in results", "ul.reusable-search__entity-result-list > li"),
        ("Any divs with entity", "div[class*='entity']"),
        ("Any list items", "ul.reusable-search__entity-result-list li"),
    ]
    
    results = {}
    
    for name, selector in selectors_to_test:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            count = len(elements)
            results[name] = count
            
            if count > 0:
                print(f"✅ {name:30} → {count} elements")
            else:
                print(f"❌ {name:30} → 0 elements")
        except Exception as e:
            print(f"❌ {name:30} → ERROR: {e}")
            results[name] = 0
    
    # Check for profile links
    print("\n" + "=" * 60)
    print("🔗 PROFILE LINKS")
    print("=" * 60)
    
    profile_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
    print(f"Found {len(profile_links)} profile links")
    
    if profile_links:
        print("\nFirst 5 profile links:")
        for i, link in enumerate(profile_links[:5], 1):
            href = link.get_attribute("href")
            text = link.text.strip()[:50]
            print(f"  {i}. {text} → {href}")
    
    # Check page structure
    print("\n" + "=" * 60)
    print("📋 PAGE STRUCTURE")
    print("=" * 60)
    
    # Look for main containers
    containers = [
        ("Search results container", "div.search-results-container"),
        ("Entity result list", "ul.reusable-search__entity-result-list"),
        ("Main content", "main"),
        ("Search results", "div[class*='search-results']"),
    ]
    
    for name, selector in containers:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"✅ {name:30} → FOUND")
        except:
            print(f"❌ {name:30} → NOT FOUND")
    
    # Save page source
    print("\n💾 Saving page source to: data/debug/page_source.html")
    with open("data/debug/page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    # Screenshot
    print("📸 Saving screenshot to: data/debug/search_page.png")
    driver.save_screenshot("data/debug/search_page.png")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if max(results.values()) == 0:
        print("❌ NO PROFILE CARDS FOUND!")
        print()
        print("Possible causes:")
        print("  1. LinkedIn is showing a different page layout")
        print("  2. You need to scroll first to load results")
        print("  3. LinkedIn detected automation and changed the page")
        print("  4. Search returned no results")
        print()
        print("Next steps:")
        print("  1. Check the screenshot: data/debug/search_page.png")
        print("  2. Look at HTML: data/debug/page_source.html")
        print("  3. Search for 'entity' or 'result' in the HTML")
        print("  4. Update selectors based on actual HTML structure")
    else:
        best_selector = max(results.items(), key=lambda x: x[1])
        print(f"✅ BEST SELECTOR: {best_selector[0]}")
        print(f"   Found {best_selector[1]} elements")
        print()
        print("Use this selector in your scraper!")
    
    # Keep browser open
    print("\n" + "=" * 60)
    print("⏱️  Browser will stay open for 30 seconds")
    print("   Review the page manually if needed")
    print("=" * 60)
    time.sleep(30)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🧹 Browser closed")
    print("\n📁 Check debug files in: data/debug/")
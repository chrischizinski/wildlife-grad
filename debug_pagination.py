#!/usr/bin/env python3
"""
Debug script to investigate pagination structure on the Texas A&M Wildlife job board.
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def debug_pagination():
    """Debug pagination structure on the website."""
    driver = setup_driver()
    
    try:
        # Navigate to the site
        url = "https://jobs.rwfm.tamu.edu/search/"
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        
        # Set page size to 50
        try:
            page_size_select = wait.until(EC.element_to_be_clickable((By.ID, "pageSize")))
            select = Select(page_size_select)
            select.select_by_value("50")
            time.sleep(2)
            print("✓ Set page size to 50")
        except Exception as e:
            print(f"✗ Failed to set page size: {e}")
        
        # Enter search keywords
        try:
            search_box = wait.until(EC.presence_of_element_located((By.ID, "keywords")))
            search_box.clear()
            search_box.send_keys("(Master) OR (PhD) OR (Graduate)")
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
            print("✓ Entered search keywords")
        except Exception as e:
            print(f"✗ Failed to enter keywords: {e}")
        
        # Wait for results to load
        time.sleep(5)
        
        # Check for job results
        try:
            job_elements = driver.find_elements(By.CLASS_NAME, "job-listing")
            if not job_elements:
                job_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='job']")
            if not job_elements:
                job_elements = driver.find_elements(By.TAG_NAME, "h6")
            
            print(f"✓ Found {len(job_elements)} job elements")
        except Exception as e:
            print(f"✗ Error finding job elements: {e}")
        
        # Debug pagination - try multiple selectors
        print("\n=== PAGINATION DEBUG ===")
        
        # Original selector
        pagination_selectors = [
            "//ul[@class='pagination']//a[@class='page-link']",
            "//ul[@class='pagination']//a",
            "//ul[@class='pagination']",
            "//div[@class='pagination']//a",
            "//div[@class='pagination']",
            "//*[contains(@class, 'pagination')]",
            "//*[contains(@class, 'page')]",
            "//a[contains(@onclick, 'pageNumCtrl')]",
            "//a[contains(@onclick, 'page')]",
            "//a[contains(text(), 'Next')]",
            "//a[contains(text(), '2')]",
            "//button[contains(@onclick, 'page')]",
        ]
        
        for i, selector in enumerate(pagination_selectors, 1):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"{i:2d}. {selector}")
                print(f"    Found {len(elements)} elements")
                
                if elements:
                    for j, elem in enumerate(elements[:3]):  # Show first 3 elements
                        try:
                            text = elem.text.strip()
                            onclick = elem.get_attribute("onclick")
                            href = elem.get_attribute("href")
                            class_name = elem.get_attribute("class")
                            
                            print(f"    Element {j+1}:")
                            print(f"      Text: '{text}'")
                            print(f"      Class: '{class_name}'")
                            print(f"      Onclick: '{onclick}'")
                            print(f"      Href: '{href}'")
                        except Exception as e:
                            print(f"    Element {j+1}: Error getting attributes - {e}")
                    
                    if len(elements) > 3:
                        print(f"    ... and {len(elements) - 3} more elements")
                print()
                
            except Exception as e:
                print(f"{i:2d}. {selector}")
                print(f"    Error: {e}")
                print()
        
        # Save page source for manual inspection
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("✓ Saved page source to debug_page_source.html")
        
        # Look for any form of navigation or "more results" indicators
        print("\n=== NAVIGATION ELEMENTS ===")
        nav_selectors = [
            "//input[@name='pageNumCtrl']",
            "//form[contains(@action, 'search')]",
            "//*[contains(text(), 'Next')]",
            "//*[contains(text(), 'Previous')]",
            "//*[contains(text(), 'Page')]",
            "//*[contains(text(), 'of')]",
            "//*[contains(text(), 'results')]",
        ]
        
        for selector in nav_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"Found {len(elements)} elements for: {selector}")
                    for elem in elements[:2]:
                        print(f"  Text: '{elem.text.strip()}'")
                        print(f"  Tag: {elem.tag_name}")
                        print(f"  Attributes: {elem.get_attribute('outerHTML')[:100]}...")
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
        
    except Exception as e:
        print(f"Error during debugging: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_pagination()
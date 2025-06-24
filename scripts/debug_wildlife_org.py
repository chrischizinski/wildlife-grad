#!/usr/bin/env python3
"""
Debug script to save wildlife.org page source for manual inspection.
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_wildlife_org():
    """Save page source for manual inspection."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("Accessing https://careers.wildlife.org")
        driver.get("https://careers.wildlife.org")
        time.sleep(5)  # Wait for any dynamic content
        
        # Save page source
        with open("wildlife_org_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        logger.info("Page source saved to wildlife_org_page_source.html")
        
        # Also try common job board URLs
        test_urls = [
            "https://careers.wildlife.org/jobs",
            "https://careers.wildlife.org/positions", 
            "https://careers.wildlife.org/opportunities",
            "https://wildlife.org/careers",
            "https://wildlife.org/jobs"
        ]
        
        for url in test_urls:
            try:
                logger.info(f"Testing {url}")
                driver.get(url)
                time.sleep(2)
                
                if "404" not in driver.title.lower() and len(driver.page_source) > 1000:
                    filename = url.replace("https://", "").replace("/", "_") + ".html"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logger.info(f"Found content at {url}, saved to {filename}")
                    
            except Exception as e:
                logger.debug(f"URL {url} failed: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_wildlife_org()
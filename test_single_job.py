#!/usr/bin/env python3
"""
Test extraction from a single job to debug description collection
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def test_single_job():
    """Test extracting one job in detail"""
    
    # Setup minimal driver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Navigate to the job board
        driver.get("https://jobs.rwfm.tamu.edu/search/")
        time.sleep(3)
        
        # Get first job link
        job_elements = driver.find_elements(By.CSS_SELECTOR, "a.list-group-item")
        if not job_elements:
            print("No job elements found!")
            return
            
        first_job = job_elements[0]
        job_url = first_job.get_attribute("href")
        title = first_job.find_element(By.TAG_NAME, "h6").text.strip()
        
        print(f"Testing job: {title}")
        print(f"URL: {job_url}")
        
        if not job_url:
            print("No URL found!")
            return
            
        # Navigate to individual job page
        driver.get(job_url)
        time.sleep(2)
        
        # Try to extract description using multiple selectors
        desc_selectors = [
            "div.job-description",
            "div.position-description", 
            "div[class*='description']",
            "div.content",
            "div.job-details",
            ".card-body",
            "main .container"
        ]
        
        description = ""
        for selector in desc_selectors:
            try:
                desc_element = driver.find_element(By.CSS_SELECTOR, selector)
                description = desc_element.text.strip()
                print(f"\nFound description with selector '{selector}':")
                print(f"Length: {len(description)} characters")
                if description and len(description) > 100:
                    print(f"First 200 chars: {description[:200]}...")
                    break
                else:
                    print(f"Too short: {description}")
            except Exception as e:
                print(f"Selector '{selector}' failed: {e}")
                
        if not description:
            # Fallback: get all text from body
            try:
                body_element = driver.find_element(By.TAG_NAME, "body")
                description = body_element.text.strip()
                print(f"\nFallback body text:")
                print(f"Length: {len(description)} characters")
                print(f"First 500 chars: {description[:500]}...")
            except Exception as e:
                print(f"Body fallback failed: {e}")
        
        # Test classification with this content
        if description:
            full_text = f"{title} {description}".lower()
            
            graduate_indicators = ["masters", "master's", "phd", "assistantship", "fellowship", "graduate", "thesis"]
            grad_count = sum(1 for term in graduate_indicators if term in full_text)
            
            print(f"\nClassification test:")
            print(f"Graduate terms found: {grad_count}")
            for term in graduate_indicators:
                if term in full_text:
                    print(f"  - Found: {term}")
                    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_single_job()
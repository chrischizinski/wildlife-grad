#!/usr/bin/env python3
"""
Test the fixed URL extraction and description collection
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def test_fixed_extraction():
    """Test the fixed URL extraction approach"""
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get("https://jobs.rwfm.tamu.edu/search/")
        time.sleep(3)
        
        # Get first job element
        job_elements = driver.find_elements(By.CSS_SELECTOR, "a.list-group-item")
        if not job_elements:
            print("No job elements found!")
            return
            
        job_element = job_elements[0]
        
        # Extract title
        try:
            title_elem = job_element.find_element(By.TAG_NAME, "h6")
            title = title_elem.text.strip()
        except:
            title = "Unknown"
            
        print(f"Testing job: {title}")
        
        # Extract URL using fixed method
        job_url = ""
        try:
            # Look for onclick attribute with job detail URL
            clickable_elements = job_element.find_elements(By.XPATH, ".//*[@onclick]")
            for element in clickable_elements:
                onclick = element.get_attribute("onclick") or ""
                if "view-job/?id=" in onclick:
                    # Extract job ID from onclick
                    match = re.search(r"view-job/\?id=(\d+)", onclick)
                    if match:
                        job_id = match.group(1)
                        job_url = f"https://jobs.rwfm.tamu.edu/view-job/?id={job_id}"
                        break
        except Exception as e:
            print(f"URL extraction failed: {e}")
            
        print(f"Extracted URL: {job_url}")
        
        if not job_url:
            print("No URL found!")
            return
            
        # Navigate to the individual job page
        print(f"Navigating to job detail page...")
        driver.get(job_url)
        time.sleep(2)
        
        # Try to extract description
        desc_selectors = [
            "div.job-description",
            "div.position-description", 
            "div[class*='description']",
            "div.content",
            "div.job-details",
            ".card-body",
            "main .container",
            ".container",
            "#job-details",
            ".job-posting"
        ]
        
        description = ""
        successful_selector = None
        
        for selector in desc_selectors:
            try:
                desc_element = driver.find_element(By.CSS_SELECTOR, selector)
                description = desc_element.text.strip()
                if description and len(description) > 100:
                    successful_selector = selector
                    break
            except:
                continue
                
        if description:
            print(f"\n✅ SUCCESS! Found description with selector: {successful_selector}")
            print(f"Description length: {len(description)} characters")
            print(f"First 300 characters:")
            print(description[:300] + "..." if len(description) > 300 else description)
            
            # Test classification
            full_text = f"{title} {description}".lower()
            graduate_terms = ["masters", "master's", "phd", "assistantship", "fellowship", "graduate", "thesis", "dissertation"]
            professional_terms = ["biologist", "technician", "specialist", "coordinator", "manager", "officer"]
            
            grad_count = sum(1 for term in graduate_terms if term in full_text)
            prof_count = sum(1 for term in professional_terms if term in full_text)
            
            print(f"\nClassification analysis:")
            print(f"Graduate terms found: {grad_count}")
            print(f"Professional terms found: {prof_count}")
            
            if grad_count > prof_count:
                print("➜ Would classify as: GRADUATE")
            else:
                print("➜ Would classify as: PROFESSIONAL")
                
        else:
            print("\n❌ No description found")
            print("Page source length:", len(driver.page_source))
            print("Page title:", driver.title)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    test_fixed_extraction()
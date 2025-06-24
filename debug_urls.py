#!/usr/bin/env python3
"""
Debug the actual URL structure of the job board
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def debug_job_urls():
    """Check what URLs are actually available"""
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get("https://jobs.rwfm.tamu.edu/search/")
        time.sleep(3)
        
        # Find job elements
        job_elements = driver.find_elements(By.CSS_SELECTOR, "a.list-group-item")
        print(f"Found {len(job_elements)} job elements")
        
        for i, job_element in enumerate(job_elements[:3]):  # Check first 3
            try:
                # Get the href attribute
                href = job_element.get_attribute("href")
                print(f"\nJob {i+1}:")
                print(f"  href: {href}")
                
                # Try to find title
                try:
                    title_elem = job_element.find_element(By.TAG_NAME, "h6")
                    title = title_elem.text.strip()
                    print(f"  title: {title}")
                except:
                    print("  title: Could not extract")
                
                # Check if this job element itself contains detailed info
                job_text = job_element.text
                print(f"  element text length: {len(job_text)}")
                if len(job_text) > 200:
                    print(f"  first 200 chars: {job_text[:200]}...")
                    
                # Look for clickable elements within this job
                clickable_elements = job_element.find_elements(By.XPATH, ".//*[@onclick or @href]")
                print(f"  clickable sub-elements: {len(clickable_elements)}")
                
                for j, clickable in enumerate(clickable_elements[:2]):
                    try:
                        onclick = clickable.get_attribute("onclick")
                        href_sub = clickable.get_attribute("href")
                        text = clickable.text.strip()
                        print(f"    {j+1}: onclick='{onclick}', href='{href_sub}', text='{text[:50]}'")
                    except:
                        pass
                        
            except Exception as e:
                print(f"Error processing job {i+1}: {e}")
                
        # Check if there are individual job detail links we're missing
        print("\n" + "="*50)
        print("Looking for other potential job detail patterns...")
        
        # Look for other types of links
        all_links = driver.find_elements(By.TAG_NAME, "a")
        job_detail_links = [link for link in all_links if "job" in (link.get_attribute("href") or "")]
        
        print(f"Found {len(job_detail_links)} links containing 'job':")
        for link in job_detail_links[:5]:
            href = link.get_attribute("href")
            text = link.text.strip()
            print(f"  {href} - '{text[:50]}'")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_job_urls()
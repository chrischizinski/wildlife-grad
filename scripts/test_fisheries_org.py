#!/usr/bin/env python3
"""
Test scraper for jobs.fisheries.org to investigate structure and find graduate assistantships.
"""

import time
import logging
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_driver() -> webdriver.Chrome:
    """Set up Chrome WebDriver with options for scraping."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def investigate_fisheries_org(url: str = "https://jobs.fisheries.org") -> Dict:
    """
    Investigate the fisheries.org jobs page structure.
    
    Args:
        url: The jobs page URL
        
    Returns:
        Dict containing page analysis results
    """
    driver = setup_driver()
    analysis = {
        "url": url,
        "accessible": False,
        "job_listings": [],
        "page_structure": {},
        "potential_selectors": [],
        "assistantship_indicators": [],
        "pagination_info": {},
        "filter_options": []
    }
    
    try:
        logger.info(f"Accessing {url}")
        driver.get(url)
        time.sleep(5)  # Let page load completely
        
        # Check if page is accessible (no CAPTCHA)
        page_title = driver.title
        page_source = driver.page_source
        
        if "captcha" in page_source.lower() or "blocked" in page_source.lower():
            analysis["captcha_detected"] = True
            logger.warning("CAPTCHA or blocking detected")
        else:
            analysis["captcha_detected"] = False
            analysis["accessible"] = True
            
        logger.info(f"Page title: {page_title}")
        analysis["page_title"] = page_title
        
        # Get page source for analysis
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for job listing containers
        job_selectors = [
            ".job-listing", ".job-item", ".job", ".position", 
            ".posting", ".listing", ".job-post", ".opportunity",
            "[class*='job']", "[class*='listing']", "[class*='post']",
            "article", ".card", ".result", ".item"
        ]
        
        found_jobs = []
        for selector in job_selectors:
            try:
                elements = soup.select(selector)
                if elements and len(elements) > 3:  # Likely job listings if multiple found
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    # Analyze first few elements
                    sample_jobs = []
                    for i, elem in enumerate(elements[:3]):
                        job_text = elem.get_text().strip()
                        if len(job_text) > 50:  # Filter out navigation/small elements
                            sample_jobs.append({
                                "index": i,
                                "text": job_text[:200],
                                "html": str(elem)[:300]
                            })
                    
                    if sample_jobs:
                        analysis["potential_selectors"].append({
                            "selector": selector,
                            "count": len(elements),
                            "sample_jobs": sample_jobs
                        })
                        found_jobs.extend(elements)
                        
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
        
        # Look for graduate assistantship indicators
        assistantship_keywords = [
            "graduate assistant", "research assistant", "teaching assistant",
            "graduate student", "assistantship", "grad student", "graduate position",
            "phd student", "masters student", "doctoral student", "postdoc"
        ]
        
        page_text = soup.get_text().lower()
        found_keywords = []
        for keyword in assistantship_keywords:
            if keyword in page_text:
                count = page_text.count(keyword)
                found_keywords.append({"keyword": keyword, "count": count})
        
        analysis["assistantship_indicators"] = found_keywords
        
        # Look for pagination
        pagination_selectors = [
            ".pagination", ".pager", ".page-nav", 
            "a[href*='page']", "button[class*='page']",
            ".next", ".previous", "[class*='pag']"
        ]
        
        pagination_elements = []
        for selector in pagination_selectors:
            elements = soup.select(selector)
            if elements:
                pagination_elements.append({
                    "selector": selector,
                    "count": len(elements),
                    "text": [elem.get_text().strip() for elem in elements[:3]]
                })
        
        analysis["pagination_info"] = pagination_elements
        
        # Look for filters
        filter_elements = soup.find_all(['select', 'input'], {'type': ['search', 'text']})
        filter_info = []
        for elem in filter_elements:
            if elem.get('name') or elem.get('id') or elem.get('placeholder'):
                filter_info.append({
                    "type": elem.name,
                    "name": elem.get('name', ''),
                    "id": elem.get('id', ''),
                    "placeholder": elem.get('placeholder', ''),
                    "class": elem.get('class', [])
                })
        
        analysis["filter_options"] = filter_info
        
        # Extract sample job data if found
        if found_jobs:
            for i, job_elem in enumerate(found_jobs[:5]):
                job_data = extract_job_details(job_elem)
                if job_data:
                    job_data["index"] = i
                    analysis["job_listings"].append(job_data)
        
        logger.info(f"Analysis complete. Found {len(found_jobs)} potential job elements")
        
    except TimeoutException:
        logger.error("Page load timeout")
        analysis["error"] = "Page load timeout"
    except Exception as e:
        logger.error(f"Error investigating fisheries.org: {e}")
        analysis["error"] = str(e)
    finally:
        driver.quit()
    
    return analysis

def extract_job_details(job_element) -> Optional[Dict]:
    """Extract job details from a job listing element."""
    try:
        job_data = {
            "title": "",
            "organization": "",
            "location": "",
            "date": "",
            "description": "",
            "full_text": job_element.get_text().strip()
        }
        
        # Try to find title (usually in h1, h2, h3, or strong tags)
        title_elem = job_element.find(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
        if title_elem:
            job_data["title"] = title_elem.get_text().strip()
        
        # Look for common patterns
        text = job_element.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if lines:
            job_data["first_line"] = lines[0]
            if len(lines) > 1:
                job_data["second_line"] = lines[1]
        
        return job_data
        
    except Exception as e:
        logger.debug(f"Error extracting job details: {e}")
        return None

def main():
    """Run fisheries.org investigation."""
    logger.info("Starting fisheries.org jobs page investigation")
    
    analysis = investigate_fisheries_org()
    
    # Save detailed results
    with open("fisheries_org_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("FISHERIES.ORG JOBS PAGE ANALYSIS")
    print("="*60)
    
    print(f"URL: {analysis['url']}")
    print(f"Accessible: {analysis['accessible']}")
    print(f"CAPTCHA Detected: {analysis.get('captcha_detected', 'Unknown')}")
    
    if analysis.get('error'):
        print(f"Error: {analysis['error']}")
        return
    
    print(f"Page Title: {analysis.get('page_title', 'N/A')}")
    
    print(f"\nAssistantship Keywords Found: {len(analysis['assistantship_indicators'])}")
    for kw_info in analysis['assistantship_indicators']:
        print(f"  - '{kw_info['keyword']}': {kw_info['count']} occurrences")
    
    print(f"\nPotential Job Selectors: {len(analysis['potential_selectors'])}")
    for selector_info in analysis['potential_selectors']:
        print(f"  - {selector_info['selector']}: {selector_info['count']} elements")
        for job in selector_info['sample_jobs']:
            print(f"    Sample {job['index']+1}: {job['text'][:80]}...")
    
    print(f"\nPagination Elements: {len(analysis['pagination_info'])}")
    for page_info in analysis['pagination_info']:
        print(f"  - {page_info['selector']}: {page_info['count']} elements")
    
    print(f"\nFilter Options: {len(analysis['filter_options'])}")
    for filter_info in analysis['filter_options']:
        print(f"  - {filter_info['type']}: {filter_info.get('placeholder', filter_info.get('name', 'unnamed'))}")
    
    print(f"\nSample Job Listings: {len(analysis['job_listings'])}")
    for job in analysis['job_listings']:
        print(f"  Job {job['index']+1}:")
        print(f"    Title: {job.get('title', 'N/A')}")
        print(f"    Text: {job['full_text'][:100]}...")
    
    print(f"\nDetailed analysis saved to fisheries_org_analysis.json")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test scraper for wildlife.org careers page.
Investigates page structure and identifies graduate assistantship opportunities.
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

def investigate_wildlife_org(url: str = "https://careers.wildlife.org") -> Dict:
    """
    Investigate the wildlife.org careers page structure.
    
    Args:
        url: The careers page URL
        
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
        "assistantship_indicators": []
    }
    
    try:
        logger.info(f"Accessing {url}")
        driver.get(url)
        time.sleep(3)  # Let page load
        
        # Check if page is accessible
        page_title = driver.title
        logger.info(f"Page title: {page_title}")
        analysis["accessible"] = True
        analysis["page_title"] = page_title
        
        # Get page source for analysis
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for common job listing patterns
        job_containers = []
        potential_selectors = [
            ".job-listing", ".job-item", ".position", ".career-item",
            "[class*='job']", "[class*='position']", "[class*='career']",
            ".listing", ".opening", ".opportunity"
        ]
        
        for selector in potential_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    analysis["potential_selectors"].append({
                        "selector": selector,
                        "count": len(elements),
                        "sample_text": elements[0].get_text().strip()[:100] if elements else ""
                    })
                    job_containers.extend(elements)
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
        
        # Look for assistantship-specific keywords
        assistantship_keywords = [
            "graduate assistant", "research assistant", "teaching assistant",
            "graduate student", "assistantship", "grad student", "graduate position"
        ]
        
        page_text = soup.get_text().lower()
        found_keywords = [kw for kw in assistantship_keywords if kw in page_text]
        analysis["assistantship_indicators"] = found_keywords
        
        # Look for pagination
        pagination_selectors = [
            ".pagination", ".pager", "[class*='page']", 
            "a[href*='page']", "button[class*='page']"
        ]
        
        pagination_found = []
        for selector in pagination_selectors:
            elements = soup.select(selector)
            if elements:
                pagination_found.append({
                    "selector": selector,
                    "count": len(elements)
                })
        
        analysis["pagination"] = pagination_found
        
        # Try to find specific job listings
        if job_containers:
            for i, container in enumerate(job_containers[:5]):  # Sample first 5
                job_data = {
                    "index": i,
                    "text": container.get_text().strip()[:200],
                    "html_snippet": str(container)[:300],
                    "links": [a.get('href') for a in container.find_all('a', href=True)]
                }
                analysis["job_listings"].append(job_data)
        
        # Check for filters or search functionality
        search_elements = soup.find_all(['input', 'select'], {'type': ['search', 'text']})
        filter_elements = soup.find_all('select')
        
        analysis["search_functionality"] = {
            "search_inputs": len(search_elements),
            "filter_selects": len(filter_elements)
        }
        
        logger.info(f"Analysis complete. Found {len(job_containers)} potential job containers")
        
    except TimeoutException:
        logger.error("Page load timeout")
        analysis["error"] = "Page load timeout"
    except Exception as e:
        logger.error(f"Error investigating wildlife.org: {e}")
        analysis["error"] = str(e)
    finally:
        driver.quit()
    
    return analysis

def main():
    """Run wildlife.org investigation."""
    logger.info("Starting wildlife.org careers page investigation")
    
    analysis = investigate_wildlife_org()
    
    # Print results
    print("\n" + "="*60)
    print("WILDLIFE.ORG CAREERS PAGE ANALYSIS")
    print("="*60)
    
    print(f"URL: {analysis['url']}")
    print(f"Accessible: {analysis['accessible']}")
    
    if analysis.get('error'):
        print(f"Error: {analysis['error']}")
        return
    
    print(f"Page Title: {analysis.get('page_title', 'N/A')}")
    
    print(f"\nAssistantship Keywords Found: {len(analysis['assistantship_indicators'])}")
    for keyword in analysis['assistantship_indicators']:
        print(f"  - {keyword}")
    
    print(f"\nPotential Job Selectors: {len(analysis['potential_selectors'])}")
    for selector_info in analysis['potential_selectors']:
        print(f"  - {selector_info['selector']}: {selector_info['count']} elements")
        if selector_info['sample_text']:
            print(f"    Sample: {selector_info['sample_text']}...")
    
    print(f"\nPagination Elements: {len(analysis['pagination'])}")
    for page_info in analysis['pagination']:
        print(f"  - {page_info['selector']}: {page_info['count']} elements")
    
    print(f"\nSample Job Listings: {len(analysis['job_listings'])}")
    for job in analysis['job_listings']:
        print(f"  Job {job['index']+1}: {job['text'][:100]}...")
    
    search_info = analysis.get('search_functionality', {})
    print(f"\nSearch/Filter Functionality:")
    print(f"  - Search inputs: {search_info.get('search_inputs', 0)}")
    print(f"  - Filter selects: {search_info.get('filter_selects', 0)}")

if __name__ == "__main__":
    main()
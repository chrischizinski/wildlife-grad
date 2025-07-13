#!/usr/bin/env python3
"""
Targeted Graduate Opportunities Scraper

Uses the job board's built-in "Graduate Opportunities" filter for more accurate results.
This is much better than keyword searching since it uses the site's own classification.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import hashlib

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class JobDetails:
    """Complete job posting data structure"""
    
    # Basic Information
    title: str = ""
    organization: str = ""
    location: str = ""
    url: str = ""
    job_id: str = ""
    
    # Structured Details
    salary_range: str = ""
    starting_date: str = ""
    application_deadline: str = ""
    published_date: str = ""
    hours_per_week: str = ""
    education_required: str = ""
    experience_required: str = ""
    tags: List[str] = None
    
    # Content Fields
    description: str = ""
    contact_info: str = ""
    
    # Metadata
    scraped_at: str = ""
    scraper_version: str = "4.0-targeted"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.scraped_at:
            self.scraped_at = datetime.now(timezone.utc).isoformat()


class TargetedGraduateScraper:
    """Targeted scraper using job board's Graduate Opportunities filter"""
    
    def __init__(self, headless: bool = True, debug: bool = False):
        self.base_url = "https://jobs.rwfm.tamu.edu"
        self.search_url = f"{self.base_url}/search/"
        self.headless = headless
        self.debug = debug
        self.driver = None
        self.wait = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('targeted_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # User agents for rotation
        self.ua = UserAgent()
        
    def setup_driver(self) -> None:
        """Initialize Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless=new")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-agent={self.ua.random}")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            
            self.logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def apply_graduate_filter(self) -> bool:
        """Apply the Graduate Opportunities job type filter"""
        try:
            self.logger.info("Applying Graduate Opportunities filter...")
            
            # Click the Job Type dropdown
            job_type_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Job Type')]"))
            )
            job_type_button.click()
            time.sleep(1)
            
            # Check the Graduate Opportunities checkbox
            graduate_checkbox = self.wait.until(
                EC.element_to_be_clickable((By.ID, "Job-Type-Graduate-checkbox"))
            )
            
            if not graduate_checkbox.is_selected():
                graduate_checkbox.click()
                self.logger.info("✅ Graduate Opportunities filter applied")
                time.sleep(2)  # Wait for auto-submit
                
                # Click back to main page to activate filter (user feedback)
                try:
                    main_search_area = self.driver.find_element(By.CSS_SELECTOR, ".container-fluid, .main-content")
                    main_search_area.click()
                    time.sleep(1)
                    self.logger.info("✅ Clicked back to main page to activate filter")
                except:
                    pass  # Not critical if this fails
                
                return True
            else:
                self.logger.info("✅ Graduate Opportunities filter already active")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to apply Graduate filter: {e}")
            return False
    
    def add_keyword_search(self, keywords: str = "graduate AND (assistantship OR fellowship)") -> bool:
        """Add keyword search on top of graduate filter"""
        try:
            self.logger.info(f"Adding keyword search: {keywords}")
            
            search_box = self.driver.find_element(By.ID, "keywords")
            search_box.clear()
            search_box.send_keys(keywords)
            
            search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            search_button.click()
            time.sleep(3)  # Wait for results to load
            
            self.logger.info(f"✅ Keyword search '{keywords}' applied")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add keyword search: {e}")
            return False
    
    def set_time_filter(self, time_period: str = "Last 7 days") -> bool:
        """Set time-based filter for posted dates"""
        try:
            self.logger.info(f"Setting time filter to: {time_period}")
            
            # Click the Posted dropdown button
            posted_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "Posted-button"))
            )
            posted_button.click()
            time.sleep(1)
            
            # Select the time period option
            time_option = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//a[@class='dropdown-item' and contains(text(), '{time_period}')]"))
            )
            time_option.click()
            time.sleep(3)  # Wait for results to reload
            
            self.logger.info(f"✅ Time filter set to: {time_period}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not set time filter to '{time_period}': {e}")
            return False
    
    def set_page_size(self) -> bool:
        """Set page size to show 50 results"""
        try:
            self.logger.info("Setting page size to 50...")
            
            # Find the page size dropdown by name
            page_size_dropdown = self.driver.find_element(By.CSS_SELECTOR, "select[name='PageSize']")
            
            from selenium.webdriver.support.ui import Select
            select = Select(page_size_dropdown)
            select.select_by_value("50")
            
            time.sleep(3)  # Wait for page to reload with more results
            self.logger.info("✅ Page size set to 50")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not set page size: {e}")
            return False
    
    def extract_jobs_from_search_results(self) -> List[JobDetails]:
        """Extract job data directly from search results pages"""
        all_jobs = []
        page = 1
        
        while True:
            self.logger.info(f"Processing page {page}...")
            
            try:
                # Wait for results to load
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.list-group-item"))
                )
                
                # Check for results count to understand pagination
                try:
                    # Look for results indicator in page text
                    page_source = self.driver.page_source
                    if "Results: (" in page_source:
                        # Extract results info
                        results_match = re.search(r'Results: \(([^)]+)\)', page_source)
                        if results_match:
                            results_text = results_match.group(0)
                            self.logger.info(f"Results indicator: {results_text}")
                except Exception as e:
                    self.logger.debug(f"Could not extract results count: {e}")
                
                # Extract job data from current page
                job_items = self.driver.find_elements(By.CSS_SELECTOR, "a.list-group-item[href*='#job-']")
                self.logger.info(f"Found {len(job_items)} job items on page {page}")
                
                page_jobs = []
                for i, item in enumerate(job_items):
                    try:
                        job = JobDetails()
                        
                        # Extract job ID from href
                        href = item.get_attribute('href')
                        if href and '#job-' in href:
                            job.job_id = href.split('#job-')[-1]
                            job.url = f"{self.base_url}/view/{job.job_id}/"
                        
                        # Get full text content
                        item_text = item.text.strip()
                        if not item_text:
                            self.logger.warning(f"Empty text for job item {i+1}")
                            continue
                            
                        lines = item_text.split('\n')
                        
                        # Parse structured data from the text
                        parsed_data = self._parse_job_item_text(item_text)
                        
                        # Set the parsed data
                        job.title = parsed_data.get('title', lines[0] if lines else '')
                        job.organization = parsed_data.get('organization', lines[1] if len(lines) > 1 else '')
                        job.location = parsed_data.get('location', '')
                        job.salary_range = parsed_data.get('salary', '')
                        job.application_deadline = parsed_data.get('deadline', '')
                        job.published_date = parsed_data.get('published', '')
                        job.starting_date = parsed_data.get('starting_date', '')
                        job.ending_date = parsed_data.get('ending_date', '')
                        job.hours_per_week = parsed_data.get('hours', '')
                        job.education_required = parsed_data.get('education', '')
                        job.experience_required = parsed_data.get('experience', '')
                        job.tags = parsed_data.get('tags', [])
                        
                        # Use full text as description
                        job.description = item_text
                        
                        all_jobs.append(job)
                        page_jobs.append(job)
                        
                        self.logger.debug(f"Extracted job {i+1}: {job.title}")
                        
                    except Exception as e:
                        self.logger.warning(f"Error extracting job {i+1} from page {page}: {e}")
                        continue
                
                self.logger.info(f"Successfully extracted {len(page_jobs)} jobs from page {page}")
                
                if not page_jobs:
                    self.logger.info("No jobs found on this page, stopping pagination")
                    break
                
                # Check if there's a next page before trying to navigate
                try:
                    next_page_num = page + 1
                    # Look for next page link
                    next_selectors = [
                        f"a[onclick*='pageNumCtrl.value={next_page_num}']",
                        f"a[href*='PageNum={next_page_num}']",
                        ".pagination a:contains('Next')",
                        ".pagination a:contains('>')",
                        f".pagination a[data-page='{next_page_num}']"
                    ]
                    
                    next_link = None
                    for selector in next_selectors:
                        try:
                            if 'contains' not in selector:  # Skip jQuery selectors for now
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements:
                                    next_link = elements[0]
                                    self.logger.info(f"Found next page link with selector: {selector}")
                                    break
                        except:
                            continue
                    
                    if next_link:
                        # Scroll into view and click
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_link)
                        time.sleep(1)
                        next_link.click()
                        time.sleep(3)  # Wait for page to load
                        page += 1
                        self.logger.info(f"Navigated to page {page}")
                    else:
                        self.logger.info("No next page link found, reached end of results")
                        break
                    
                except Exception as e:
                    self.logger.info(f"Pagination navigation failed: {e}. Reached end of results.")
                    break
                    
            except TimeoutException:
                self.logger.warning(f"Timeout waiting for results on page {page}")
                break
            except Exception as e:
                self.logger.error(f"Error processing page {page}: {e}")
                break
        
        self.logger.info(f"Total graduate opportunities extracted: {len(all_jobs)}")
        return all_jobs
        
    def _parse_job_item_text(self, text: str) -> dict:
        """Parse structured data from job item text"""
        data = {}
        lines = text.split('\n')
        
        # Extract title (first line, remove location suffix)
        if lines:
            title_line = lines[0].strip()
            # Remove location suffix like " - City, ST"
            title_match = re.match(r'^(.+?)\s*-\s*([^,]+(?:,\s*[A-Z]{2})?)\s*$', title_line)
            if title_match:
                data['title'] = title_match.group(1).strip()
                data['location'] = title_match.group(2).strip()
            else:
                data['title'] = title_line
        
        # Extract organization (second line if not a field header)
        if len(lines) > 1 and not lines[1].strip().endswith(':'):
            data['organization'] = lines[1].strip()
        
        # Parse field-value pairs
        current_field = None
        for line in lines:
            line = line.strip()
            
            # Check if this is a field header
            if line.endswith(':'):
                field_name = line[:-1].lower().replace(' ', '_')
                current_field = field_name
                continue
            
            # Check if this line contains a value for current field
            if current_field and line and not line.endswith(':'):
                field_mapping = {
                    'application_deadline': 'deadline',
                    'published': 'published',
                    'starting_date': 'starting_date',
                    'ending_date': 'ending_date',
                    'hours_per_week': 'hours',
                    'salary': 'salary',
                    'education_required': 'education',
                    'experience_required': 'experience',
                    'location': 'location',
                    'tags': 'tags'
                }
                
                mapped_field = field_mapping.get(current_field, current_field)
                if mapped_field == 'tags':
                    # Handle tags specially - could be comma separated
                    data['tags'] = [tag.strip() for tag in line.split('\n') if tag.strip() and not tag.strip().endswith('ago')]
                else:
                    data[mapped_field] = line
                
                current_field = None
        
        return data
    
    def extract_job_details(self, job_url: str) -> Optional[JobDetails]:
        """Extract detailed information from a job posting"""
        try:
            self.logger.debug(f"Extracting: {job_url}")
            self.driver.get(job_url)
            time.sleep(2)
            
            job = JobDetails()
            job.url = job_url
            job.job_id = job_url.split('/')[-2] if '/' in job_url else ""
            
            # Extract title
            try:
                title_element = self.driver.find_element(By.TAG_NAME, "h1")
                job.title = title_element.text.strip()
            except NoSuchElementException:
                job.title = "Title not found"
            
            # Extract organization
            try:
                org_element = self.driver.find_element(By.XPATH, "//strong[contains(text(), 'Organization:')]/following-sibling::text()[1] | //h6[contains(text(), 'Organization')]/following-sibling::*[1]")
                job.organization = org_element.text.strip()
            except NoSuchElementException:
                # Try alternative methods
                try:
                    # Look for pattern in page text
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    if "Organization:" in page_text:
                        lines = page_text.split('\n')
                        for i, line in enumerate(lines):
                            if 'Organization:' in line and i + 1 < len(lines):
                                job.organization = lines[i + 1].strip()
                                break
                except:
                    job.organization = "Organization not found"
            
            # Extract location
            try:
                location_element = self.driver.find_element(By.XPATH, "//strong[contains(text(), 'Location:')]/following-sibling::text()[1] | //h6[contains(text(), 'Location')]/following-sibling::*[1]")
                job.location = location_element.text.strip()
            except NoSuchElementException:
                job.location = "Location not found"
            
            # Extract structured details
            self._extract_detail_fields(job)
            
            # Extract main description
            try:
                description_element = self.driver.find_element(By.CSS_SELECTOR, ".trix-content, .description, .job-description")
                job.description = description_element.text.strip()
            except NoSuchElementException:
                # Get main content area
                try:
                    main_content = self.driver.find_element(By.CSS_SELECTOR, ".my-3, .content, main")
                    job.description = main_content.text.strip()
                except NoSuchElementException:
                    job.description = "Description not found"
            
            # Extract contact info
            try:
                contact_element = self.driver.find_element(By.XPATH, "//h6[contains(text(), 'Contact')]/following-sibling::*")
                job.contact_info = contact_element.text.strip()
            except NoSuchElementException:
                job.contact_info = "Contact not found"
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to extract job details from {job_url}: {e}")
            return None
    
    def _extract_detail_fields(self, job: JobDetails):
        """Extract structured detail fields from job posting"""
        try:
            # Look for common patterns in the page text
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines = page_text.split('\n')
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                
                if any(keyword in line_lower for keyword in ['salary:', 'pay:', 'stipend:', 'compensation:']):
                    if next_line:
                        job.salary_range = next_line
                
                elif any(keyword in line_lower for keyword in ['start date:', 'starting date:', 'begin date:']):
                    if next_line:
                        job.starting_date = next_line
                
                elif any(keyword in line_lower for keyword in ['deadline:', 'apply by:', 'application deadline:']):
                    if next_line:
                        job.application_deadline = next_line
                
                elif any(keyword in line_lower for keyword in ['published:', 'posted:', 'date posted:']):
                    if next_line:
                        job.published_date = next_line
                
                elif any(keyword in line_lower for keyword in ['education required:', 'education:', 'degree required:']):
                    if next_line:
                        job.education_required = next_line
                
                elif any(keyword in line_lower for keyword in ['experience required:', 'experience:', 'years experience:']):
                    if next_line:
                        job.experience_required = next_line
        
        except Exception as e:
            self.logger.warning(f"Error extracting detail fields: {e}")
    
    def scrape_all_graduate_opportunities(self, keywords: str = None, skip_keywords: bool = False, time_filter: str = None) -> List[JobDetails]:
        """Main method to scrape all graduate opportunities"""
        if keywords is None and not skip_keywords:
            keywords = "graduate AND (assistantship OR fellowship)"
            
        self.logger.info("Starting targeted graduate opportunities scraping...")
        
        try:
            self.setup_driver()
            
            # Navigate to search page
            self.driver.get(self.search_url)
            time.sleep(3)
            
            # Step 1: Apply Graduate Opportunities filter
            if not self.apply_graduate_filter():
                self.logger.error("Failed to apply graduate filter")
                return []
            
            # Step 2: Add time filter for weekly automation (optional)
            if time_filter:
                if not self.set_time_filter(time_filter):
                    self.logger.warning(f"Could not set time filter to '{time_filter}', proceeding without time filtering")
            
            # Step 3: Add keyword search (optional)
            if not skip_keywords and keywords:
                if not self.add_keyword_search(keywords):
                    self.logger.error("Failed to add keyword search")
                    return []
            else:
                self.logger.info("Skipping keyword search - using Graduate Opportunities filter only")
            
            # Step 4: Set page size to 50 to get more results per page
            if not self.set_page_size():
                self.logger.warning("Could not set page size, will proceed with default pagination")
            
            # Step 5: Extract jobs directly from search results (with pagination)
            all_jobs = self.extract_jobs_from_search_results()
            
            self.logger.info(f"Successfully scraped {len(all_jobs)} graduate opportunities")
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_jobs(self, jobs: List[JobDetails], filename: str = None) -> Path:
        """Save scraped jobs to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graduate_opportunities_{timestamp}.json"
        
        output_dir = Path("data")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / filename
        
        # Convert to serializable format
        jobs_data = [asdict(job) for job in jobs]
        
        # Add metadata
        metadata = {
            "scrape_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_jobs": len(jobs),
            "scraper_version": "4.0-targeted",
            "filter_used": "Graduate Opportunities job type",
            "jobs_with_description": sum(1 for job in jobs if job.description),
            "jobs_with_salary": sum(1 for job in jobs if job.salary_range),
        }
        
        output_data = {
            "metadata": metadata,
            "jobs": jobs_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(jobs)} graduate opportunities to {output_file}")
        return output_file


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Targeted Graduate Opportunities Scraper")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--keywords", default="graduate AND (assistantship OR fellowship)", 
                       help="Search keywords (default: 'graduate AND (assistantship OR fellowship)')")
    parser.add_argument("--no-keywords", action="store_true", 
                       help="Skip keyword search and use only Graduate Opportunities filter")
    parser.add_argument("--time-filter", choices=["Last 7 days", "Last 14 days", "Last 30 days", "Last 48 hours"], 
                       help="Filter by posting date for weekly automation")
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = TargetedGraduateScraper(headless=args.headless, debug=args.debug)
    
    # Scrape graduate opportunities
    jobs = scraper.scrape_all_graduate_opportunities(
        keywords=args.keywords if not args.no_keywords else None,
        skip_keywords=args.no_keywords,
        time_filter=args.time_filter
    )
    
    if jobs:
        # Save results
        output_file = scraper.save_jobs(jobs)
        print(f"\n✅ Scraping completed successfully!")
        print(f"📁 Results saved to: {output_file}")
        print(f"📊 Total graduate opportunities: {len(jobs)}")
        print(f"📖 Jobs with descriptions: {sum(1 for job in jobs if job.description)}")
        print(f"💰 Jobs with salary info: {sum(1 for job in jobs if job.salary_range)}")
    else:
        print("❌ No graduate opportunities were scraped")


if __name__ == "__main__":
    main()
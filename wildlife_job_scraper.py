"""
Wildlife Jobs Board Scraper

A comprehensive scraper for graduate assistantship opportunities from
the Texas A&M Wildlife and Fisheries job board.
"""

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import quote

import pandas as pd
from dotenv import load_dotenv
from fake_useragent import UserAgent
from pydantic import BaseModel, Field, validator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# Load environment variables
load_dotenv()


@dataclass
class ScraperConfig:
    """Configuration for the wildlife job scraper."""
    
    base_url: str = "https://jobs.rwfm.tamu.edu/search/"
    keywords: str = "(Master) OR (PhD) OR (Graduate)"
    output_dir: Path = Path("data")
    log_file: str = "scrape_jobs.log"
    page_size: int = 50
    min_delay: float = 2.0
    max_delay: float = 5.0
    timeout: int = 20
    headless: bool = True
    
    def __post_init__(self):
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(exist_ok=True)


class JobListing(BaseModel):
    """Data model for a job listing."""
    
    title: str = Field(..., min_length=1, description="Job title")
    organization: str = Field(default="N/A", description="Hiring organization")
    location: str = Field(default="N/A", description="Job location")
    salary: str = Field(default="N/A", description="Salary information")
    starting_date: str = Field(default="N/A", description="Position start date")
    published_date: str = Field(default="N/A", description="Job posting date")
    tags: str = Field(default="N/A", description="Job tags/categories")
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        """Ensure title is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class WildlifeJobScraper:
    """Main scraper class for wildlife job listings."""
    
    def __init__(self, config: ScraperConfig):
        """
        Initialize the scraper with configuration.
        
        Args:
            config (ScraperConfig): Scraper configuration object
        """
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.ua = UserAgent()
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Configure logging for the scraper."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.config.log_file)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _human_pause(self, min_seconds: Optional[float] = None, 
                    max_seconds: Optional[float] = None) -> None:
        """
        Pause execution to simulate human behavior.
        
        Args:
            min_seconds: Minimum delay time
            max_seconds: Maximum delay time
        """
        min_delay = min_seconds or self.config.min_delay
        max_delay = max_seconds or self.config.max_delay
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def setup_driver(self) -> webdriver.Chrome:
        """
        Setup and configure Chrome WebDriver with anti-detection measures.
        
        Returns:
            webdriver.Chrome: Configured Chrome WebDriver instance
        """
        options = Options()
        
        # Basic configuration
        if self.config.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Anti-detection measures
        options.add_argument(f"user-agent={self.ua.random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Setup driver service
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Additional anti-detection
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        self.logger.info("Chrome WebDriver initialized successfully")
        return driver
        
    def _wait_for_element(self, locator: tuple, timeout: Optional[int] = None) -> Any:
        """
        Wait for an element to be present and return it.
        
        Args:
            locator: Tuple of (By type, selector)
            timeout: Optional timeout override
            
        Returns:
            WebElement: The found element
        """
        wait_time = timeout or self.config.timeout
        return WebDriverWait(self.driver, wait_time).until(
            EC.presence_of_element_located(locator)
        )
        
    def _scroll_to_element(self, element) -> None:
        """
        Scroll to center an element in the viewport.
        
        Args:
            element: WebElement to scroll to
        """
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        
    def set_page_size(self) -> None:
        """Set the results page size to maximum (50 items)."""
        try:
            # Scroll to bottom to find page size dropdown
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._human_pause()
            
            dropdown = self._wait_for_element((By.XPATH, "//select[@name='PageSize']"))
            self._scroll_to_element(dropdown)
            
            select = Select(dropdown)
            select.select_by_visible_text(f"Show {self.config.page_size}")
            
            self._human_pause()
            self.logger.info(f"Set page size to {self.config.page_size}")
            
        except Exception as e:
            self.logger.error(f"Failed to set page size: {e}")
            raise
            
    def enter_search_keywords(self, keywords: Optional[str] = None) -> None:
        """
        Enter search keywords in the search box.
        
        Args:
            keywords: Search keywords (uses config default if None)
        """
        try:
            search_terms = keywords or self.config.keywords
            
            search_box = self._wait_for_element((By.ID, "keywords"))
            self._scroll_to_element(search_box)
            
            search_box.clear()
            search_box.send_keys(search_terms)
            self._human_pause()
            
            search_box.send_keys(Keys.RETURN)
            self._human_pause()
            
            self.logger.info(f"Entered search keywords: {search_terms}")
            
        except Exception as e:
            self.logger.error(f"Failed to enter keywords: {e}")
            raise
            
    def extract_job_data(self, job_element) -> Optional[JobListing]:
        """
        Extract job data from a single job listing element.
        
        Args:
            job_element: WebElement containing job information
            
        Returns:
            Optional[JobListing]: Parsed job data or None if invalid
        """
        try:
            # Extract title (required field)
            title_elem = job_element.find_element(By.TAG_NAME, "h6")
            title = title_elem.text.strip()
            
            if not title:
                return None
                
            # Extract optional fields with fallbacks
            def safe_extract(xpath: str, default: str = "N/A") -> str:
                try:
                    elem = job_element.find_element(By.XPATH, xpath)
                    return elem.text.strip() or default
                except:
                    return default
                    
            organization = safe_extract(".//p")
            location = safe_extract(".//div[contains(text(), 'Location')]/following-sibling::div")
            salary = safe_extract(".//div[contains(text(), 'Salary')]/following-sibling::div")
            starting_date = safe_extract(".//div[contains(text(), 'Starting Date')]/following-sibling::div")
            published_date = safe_extract(".//div[contains(text(), 'Published')]/following-sibling::div")
            
            # Extract tags
            try:
                tag_elements = job_element.find_elements(By.CSS_SELECTOR, ".badge.bg-secondary")
                tags = ", ".join(tag.text.strip() for tag in tag_elements if tag.text.strip())
                tags = tags or "N/A"
            except:
                tags = "N/A"
                
            return JobListing(
                title=title,
                organization=organization,
                location=location,
                salary=salary,
                starting_date=starting_date,
                published_date=published_date,
                tags=tags
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to extract job data: {e}")
            return None
            
    def extract_jobs_from_page(self) -> List[JobListing]:
        """
        Extract all job listings from the current page.
        
        Returns:
            List[JobListing]: List of valid job listings
        """
        jobs = []
        job_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.list-group-item")
        
        for job_element in job_elements:
            job_data = self.extract_job_data(job_element)
            if job_data:
                jobs.append(job_data)
                
        self.logger.info(f"Extracted {len(jobs)} jobs from current page")
        return jobs
        
    def get_pagination_pages(self) -> List[int]:
        """
        Get list of available page numbers from pagination.
        
        Returns:
            List[int]: List of page numbers to scrape
        """
        try:
            pagination_links = self.driver.find_elements(
                By.XPATH, "//ul[@class='pagination']//a[@class='page-link']"
            )
            
            page_numbers = []
            for link in pagination_links:
                onclick_attr = link.get_attribute("onclick")
                if onclick_attr and "pageNumCtrl.value=" in onclick_attr:
                    try:
                        page_num = int(onclick_attr.split("=")[1].split(";")[0].strip())
                        page_numbers.append(page_num)
                    except (ValueError, IndexError):
                        continue
                        
            # Remove duplicates and sort
            page_numbers = sorted(set(page_numbers))
            self.logger.info(f"Found {len(page_numbers)} pages to scrape")
            return page_numbers
            
        except Exception as e:
            self.logger.warning(f"Failed to get pagination info: {e}")
            return []
            
    def navigate_to_page(self, page_number: int) -> None:
        """
        Navigate to a specific page number.
        
        Args:
            page_number: Page number to navigate to
        """
        try:
            self.driver.execute_script(
                f"pageNumCtrl.value={page_number}; submitListingForm(true);"
            )
            
            # Wait for new results to load
            self._wait_for_element((By.CSS_SELECTOR, "a.list-group-item"))
            self._human_pause()
            
            self.logger.info(f"Navigated to page {page_number}")
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to page {page_number}: {e}")
            raise
            
    def scrape_all_jobs(self) -> List[JobListing]:
        """
        Scrape job listings from all available pages.
        
        Returns:
            List[JobListing]: Complete list of job listings
        """
        try:
            self.driver = self.setup_driver()
            self.driver.get(self.config.base_url)
            
            # Setup initial page
            self.set_page_size()
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.enter_search_keywords()
            
            # Extract jobs from first page
            all_jobs = self.extract_jobs_from_page()
            
            # Get pagination and scrape remaining pages
            page_numbers = self.get_pagination_pages()
            
            for page_num in page_numbers:
                if page_num == 1:  # Skip first page (already scraped)
                    continue
                    
                self.navigate_to_page(page_num)
                page_jobs = self.extract_jobs_from_page()
                all_jobs.extend(page_jobs)
                
            self.logger.info(f"Total jobs scraped: {len(all_jobs)}")
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                
    def save_jobs_json(self, jobs: List[JobListing], filename: str = "graduate_assistantships.json") -> Path:
        """
        Save job listings to JSON file.
        
        Args:
            jobs: List of job listings to save
            filename: Output filename
            
        Returns:
            Path: Path to saved file
        """
        output_path = self.config.output_dir / filename
        
        # Convert to dictionaries for JSON serialization
        jobs_data = [job.dict() for job in jobs]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(jobs_data, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Saved {len(jobs)} jobs to {output_path}")
        return output_path
        
    def save_jobs_csv(self, jobs: List[JobListing], filename: str = "graduate_assistantships.csv") -> Path:
        """
        Save job listings to CSV file.
        
        Args:
            jobs: List of job listings to save
            filename: Output filename
            
        Returns:
            Path: Path to saved file
        """
        output_path = self.config.output_dir / filename
        
        # Convert to DataFrame and save
        jobs_data = [job.dict() for job in jobs]
        df = pd.DataFrame(jobs_data)
        df.to_csv(output_path, index=False, encoding="utf-8")
        
        self.logger.info(f"Saved {len(jobs)} jobs to {output_path}")
        return output_path


def main() -> None:
    """Main entry point for the scraper."""
    try:
        config = ScraperConfig()
        scraper = WildlifeJobScraper(config)
        
        jobs = scraper.scrape_all_jobs()
        
        if jobs:
            scraper.save_jobs_json(jobs)
            scraper.save_jobs_csv(jobs)
            print(f"Successfully scraped {len(jobs)} job listings")
        else:
            print("No jobs found")
            
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        raise


if __name__ == "__main__":
    main()
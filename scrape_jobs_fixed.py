import logging
import random
import time
import json
import os
import pandas as pd
from dotenv import load_dotenv
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
URL = os.getenv("JOB_SEARCH_URL")

# UserAgent rotation
ua = UserAgent()


def setup_driver():
    """Setup Selenium WebDriver with anti-bot measures."""
    options = Options()
    options.add_argument(f"user-agent={ua.random}")
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=driver_service, options=options)

    # Prevent detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def random_human_pause(min_seconds=2, max_seconds=5):
    """Pause randomly to simulate human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))


def select_show_50(driver):
    """Set 'Show 50' results per page."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_human_pause()

        dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[@name='PageSize']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        select = Select(dropdown)
        select.select_by_visible_text("Show 50")
        random_human_pause()
    except Exception as e:
        logging.error(f"Failed to select 'Show 50': {e}", exc_info=True)
        raise


def enter_keywords(driver, keywords="(Master) OR (PhD) OR (Graduate)"):
    """Enter keywords and trigger the search."""
    try:
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='keywords']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", search_box)
        search_box.clear()
        search_box.send_keys(keywords)
        random_human_pause()
        search_box.send_keys(Keys.RETURN)  # Press Enter to trigger search
        random_human_pause()
    except Exception as e:
        logging.error(f"Failed to enter keywords: {e}", exc_info=True)
        raise


def extract_jobs(driver):
    """Extract job listings using Selenium."""
    jobs = []
    job_elements = driver.find_elements(By.CLASS_NAME, "list-group-item")

    for job in job_elements:
        try:
            title = job.find_element(By.TAG_NAME, "h6").text.strip()
            if not title:  # Skip if title is empty
                continue
        except:
            continue  # Skip empty listings

        try:
            organization = job.find_element(By.TAG_NAME, "p").text.strip()
        except:
            organization = "N/A"

        try:
            location = job.find_element(By.XPATH, ".//div[contains(text(), 'Location')]/following-sibling::div").text.strip()
        except:
            location = "N/A"

        try:
            salary = job.find_element(By.XPATH, ".//div[contains(text(), 'Salary')]/following-sibling::div").text.strip()
        except:
            salary = "N/A"

        try:
            starting_date = job.find_element(By.XPATH, ".//div[contains(text(), 'Starting Date')]/following-sibling::div").text.strip()
        except:
            starting_date = "N/A"

        try:
            published_date = job.find_element(By.XPATH, ".//div[contains(text(), 'Published')]/following-sibling::div").text.strip()
        except:
            published_date = "N/A"

        try:
            tags = [tag.text.strip() for tag in job.find_elements(By.CLASS_NAME, "badge.bg-secondary")]
            tags_text = ", ".join(tags) if tags else "N/A"
        except:
            tags_text = "N/A"

        jobs.append({
            "Title": title,
            "Organization": organization,
            "Location": location,
            "Salary": salary,
            "Starting Date": starting_date,
            "Published Date": published_date,
            "Tags": tags_text,
        })

    return jobs


def apply_filters(driver):
    """Apply filters and extract jobs from all pages."""
    try:
        driver.get(URL)
        select_show_50(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        enter_keywords(driver)

        job_listings = extract_jobs(driver)

        # Get all page numbers from pagination
        pagination = driver.find_elements(By.XPATH, "//ul[@class='pagination']//a[@class='page-link']")
        page_numbers = []
        for link in pagination:
            onclick_attr = link.get_attribute("onclick")
            if onclick_attr and "pageNumCtrl.value=" in onclick_attr:
                page_number = int(onclick_attr.split("=")[1].split(";")[0].strip())
                page_numbers.append(page_number)

        # Navigate through each page
        for page in page_numbers:
            
    # Click the next page button and wait for new results to load
    driver.execute_script(f"pageNumCtrl.value={page}; submitListingForm(true);")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "list-group-item"))
    )
    
            random_human_pause()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "list-group-item"))
            )

            jobs = extract_jobs(driver)
            job_listings.extend(jobs)

        return job_listings

    except Exception as e:
        logging.error(f"Error applying filters: {e}", exc_info=True)
        raise


def save_to_json(data, filename="graduate_assistantships.json"):
    """Save job data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def save_to_csv(data, filename="graduate_assistantships.csv"):
    """Save job data to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)


def main():
    """Main script execution."""
    driver = setup_driver()
    try:
        all_jobs = apply_filters(driver)
        save_to_json(all_jobs)
        save_to_csv(all_jobs)
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
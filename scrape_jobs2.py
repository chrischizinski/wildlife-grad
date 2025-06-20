import os
import time
import random
import logging
import urllib.parse
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# Get credentials from .env
SMARTPROXY_USER = os.getenv("SMARTPROXY_USERNAME")
SMARTPROXY_PASS = os.getenv("SMARTPROXY_PASSWORD")
URL = os.getenv("JOB_SEARCH_URL")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "job_listings.csv")

# Ensure credentials exist
if not SMARTPROXY_USER or not SMARTPROXY_PASS:
    raise ValueError("Missing required .env variables. Ensure SMARTPROXY_USERNAME and SMARTPROXY_PASSWORD are set.")

# Encode password for URL
ENCODED_PASS = urllib.parse.quote(SMARTPROXY_PASS)

# Smartproxy settings
PROXY_HOST = "us.smartproxy.com"
PROXY_PORT = "10000"
PROXY = f"http://{SMARTPROXY_USER}:{ENCODED_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("scrape.log")]
)

def random_human_pause(min_wait=2, max_wait=5):
    """Random delay to mimic human behavior."""
    time.sleep(random.uniform(min_wait, max_wait))

def setup_driver():
    """Initialize Selenium WebDriver with Smartproxy."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--proxy-server={PROXY}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    logging.info("✅ WebDriver initialized with Smartproxy.")
    return driver

def select_show_50(driver):
    """Set results to 'Show 50' per page."""
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
        logging.info("✅ Set 'Show 50' results per page.")
    except Exception as e:
        logging.error(f"⚠️ Failed to select 'Show 50': {e}", exc_info=True)
        raise

def enter_keywords(driver, keywords="(Master) OR (PhD) OR (Graduate)"):
    """Enter search keywords and trigger search."""
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
        logging.info(f"✅ Entered search keywords: {keywords}")
    except Exception as e:
        logging.error(f"⚠️ Failed to enter keywords: {e}", exc_info=True)
        raise

def extract_jobs(driver):
    """Extract job listings from the page."""
    jobs = []
    job_elements = driver.find_elements(By.CLASS_NAME, "list-group-item")

    for job in job_elements:
        try:
            title = job.find_element(By.TAG_NAME, "h6").text.strip()
            if not title:  # Skip empty listings
                continue
        except:
            continue

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

    logging.info(f"✅ Extracted {len(jobs)} jobs from the current page.")
    return jobs

def apply_filters(driver):
    """Apply filters and scrape job listings across pages."""
    try:
        driver.get(URL)
        select_show_50(driver)
        driver.execute_script("window.scrollTo(0, 0);")
        enter_keywords(driver)

        job_listings = extract_jobs(driver)

        pagination = driver.find_elements(By.XPATH, "//ul[@class='pagination']//a[@class='page-link']")
        page_numbers = [int(link.text.strip()) for link in pagination if link.text.strip().isdigit()]

        for page in page_numbers:
            driver.execute_script(f"pageNumCtrl.value={page}; submitListingForm(true);")
            random_human_pause()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "list-group-item"))
            )

            jobs = extract_jobs(driver)
            job_listings.extend(jobs)

        return job_listings

    except Exception as e:
        logging.error(f"⚠️ Error applying filters: {e}", exc_info=True)
        raise

def save_to_csv(jobs):
    """Save job listings to CSV, appending new jobs."""
    if not jobs:
        logging.info("🚫 No new jobs found. CSV not updated.")
        return

    df = pd.DataFrame(jobs)

    if os.path.exists(OUTPUT_CSV):
        df.to_csv(OUTPUT_CSV, mode="a", header=False, index=False)
    else:
        df.to_csv(OUTPUT_CSV, mode="w", header=True, index=False)

    logging.info(f"✅ Saved {len(jobs)} new job listings to {OUTPUT_CSV}.")

def main():
    """Main script execution."""
    logging.info("🔎 Starting job scraping process.")
    
    driver = setup_driver()
    try:
        jobs = apply_filters(driver)
        save_to_csv(jobs)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
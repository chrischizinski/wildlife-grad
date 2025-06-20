import logging
import random
import time
import json
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
CHROME_DRIVER_PATH = "/opt/homebrew/Caskroom/chromedriver/132.0.6834.110/chromedriver-mac-arm64/chromedriver"  # Update this
URL = "https://jobs.rwfm.tamu.edu/search/"


def setup_driver():
    """Setup Selenium WebDriver with anti-bot measures."""
    options = Options()
    
    # Simulate a real browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Setup driver
    driver_service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=driver_service, options=options)
    
    # Prevent detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def random_human_pause(min_seconds=2, max_seconds=5):
    """Pause randomly to simulate human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

from selenium.webdriver.support.ui import Select

def select_show_50(driver):
    """Scroll to the bottom and select 'Show 50' in the dropdown."""
    try:
        # Scroll to the bottom of the page to ensure the dropdown is visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        logging.info("Scrolled to the bottom of the page.")
        random_human_pause()

        # Locate the dropdown and select 'Show 50'
        dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[@name='PageSize']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        select = Select(dropdown)
        select.select_by_visible_text("Show 50")
        logging.info("Set dropdown to 'Show 50'.")
        random_human_pause()
    except Exception as e:
        logging.error(f"Failed to select 'Show 50' in the dropdown: {e}", exc_info=True)
        # Save debug information
        with open("dropdown_debug.html", "w", encoding="utf-8") as file:
            file.write(driver.page_source)
        raise


def apply_filters(driver):
    """Apply filters and submit the form."""
    try:
        logging.info("Applying filters...")
        driver.get(URL)

        # Step 1: Scroll to the bottom and set "Show 50"
        select_show_50(driver)

        # Step 2: Scroll back to the top
        driver.execute_script("window.scrollTo(0, 0);")
        logging.info("Scrolled back to the top of the page.")

        # Step 3: Enter keywords in the search box
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='keywords']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", search_box)
        search_box.clear()
        search_box.send_keys("(Master) OR (PhD) OR (Graduate)")
        logging.info("Entered keywords into the search box.")
        random_human_pause()

        # Step 4: Open the Job Type dropdown and select Graduate Opportunities
        job_type_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/main/div[1]/form/fieldset/div[2]/div[3]/button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", job_type_button)
        job_type_button.click()
        logging.info("Opened Job Type dropdown.")
        random_human_pause()

        graduate_checkbox = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='Job-Type-Graduate-checkbox']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", graduate_checkbox)
        graduate_checkbox.click()
        logging.info("Selected Graduate Opportunities.")
        random_human_pause()

        # Step 5: Click the Submit button using JavaScript
        submit_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/main/div[1]/form/fieldset/div[1]/div[2]/button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        random_human_pause()
        driver.execute_script("arguments[0].click();", submit_button)
        logging.info("Clicked the Submit button using JavaScript.")

        # Wait for results to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'list-group-item')]"))
        )
        logging.info("Filters applied and results loaded.")
        return driver.page_source

    except Exception as e:
        logging.error(f"Error applying filters: {e}", exc_info=True)
        # Save debug information
        with open("debug_page.html", "w", encoding="utf-8") as file:
            file.write(driver.page_source)
        raise

def extract_jobs(soup):
    """Extract job listings from the HTML."""
    logging.info("Extracting job listings...")
    job_posts = soup.find_all("a", class_="list-group-item")
    logging.info(f"Found {len(job_posts)} job posts.")

    jobs = []
    for index, post in enumerate(job_posts, start=1):
        # Title and Organization
        title = post.find("h6").text.strip() if post.find("h6") else "N/A"
        organization = post.find("p").text.strip() if post.find("p") else "N/A"
        
        # Initialize default values
        salary = "N/A"
        location = "N/A"
        starting_date = "N/A"
        published_date = "N/A"

        # Extract details dynamically
        details = post.find_all("div", class_="row align-items-center") + post.find_all("div", class_="row align-items-start")
        for detail in details:
            fields = detail.find_all("div")
            if len(fields) >= 2:
                label = fields[0].text.strip()
                value = fields[1].text.strip()

                if "Salary" in label:
                    salary = value
                elif "Location" in label:
                    location = value
                elif "Starting Date" in label:
                    starting_date = value
                elif "Published" in label:
                    published_date = value

        # Enhanced Salary Detection
        salary_label = post.find("div", class_="col-6 col-md-3 col-xl-6 col-xxl-3 text-end", string="Salary:")
        if salary_label:
            salary_value = salary_label.find_next_sibling("div")
            if salary_value:
                salary = salary_value.text.strip()

        # Enhanced Location Detection
        location_label = post.find("div", class_="col-6 col-md-3 col-xl-6 col-xxl-3 text-end", string="Location:")
        if location_label:
            location_value = location_label.find_next_sibling("div")
            if location_value:
                location = location_value.text.strip()

        # Enhanced Published Date Detection
        published_label = post.find("div", class_="col-6 col-md-3 col-xl-6 col-xxl-3 text-end", string="Published:")
        if published_label:
            published_value = published_label.find_next_sibling("div")
            if published_value:
                published_date = published_value.text.strip()

        # Tags
        tags = post.find_all("div", class_="badge bg-secondary")
        tags_text = ", ".join(tag.text.strip() for tag in tags)

        # Log each job for debugging
        logging.info(f"Job {index}: Title: {title}, Organization: {organization}, Location: {location}, Salary: {salary}, Starting Date: {starting_date}, Published Date: {published_date}, Tags: {tags_text}")

        # Append to jobs list
        jobs.append({
            "Title": title,
            "Organization": organization,
            "Location": location,
            "Salary": salary,
            "Starting Date": starting_date,
            "Published Date": published_date,
            "Tags": tags_text,
        })

    logging.info(f"Extraction complete. Total jobs extracted: {len(jobs)}")
    return jobs

def save_to_json(data, filename="graduate_assistantships.json"):
    """Save job data to a JSON file."""
    if not data:
        logging.warning("No data found to save. Skipping JSON creation.")
        return

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    logging.info(f"Data saved successfully to {filename}.")


def main():
    """Main script execution."""
    driver = setup_driver()

    try:
        html_content = apply_filters(driver)
        if not html_content:
            logging.error("HTML content is empty. Exiting script.")
            return

        jobs = extract_jobs(html_content)
        save_to_json(jobs)
        logging.info(f"Scraped {len(jobs)} jobs.")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
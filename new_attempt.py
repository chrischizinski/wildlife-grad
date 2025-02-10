import logging
import time
import random  # For randomizing pauses
import tempfile
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # For sending the ESCAPE key
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# === Configuration Parameters ===
POSTED_FILTER = "Last 7 days"  # For now, scrape all postings; later you can change to "Last 7 days"
KEYWORDS = "(Master) OR (PhD) OR (Graduate) OR (MS)"
MAX_PAGES = None           # Set to an integer for testing; use None to scrape all pages.

# === Setup Logging ===

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", mode="a")
    ]
)

# === Setup Selenium WebDriver with Browser Logging Enabled ===
def setup_driver(debug=False):
    options = Options()
    if not debug:
        options.add_argument("--headless")  # Run headless unless debugging
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    # Additional options that help in CI environments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Create a unique temporary user-data directory
    temp_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")
    
    # Enable browser logging
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# === Human-like Pause with Randomization ===
def random_human_pause(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

# === Select Show 50 Option ===
def select_show_50(driver):
    logging.info("🔎 Selecting 'Show 50' results per page...")
    try:
        select_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//select[@name='PageSize']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", select_elem)
        random_human_pause()
        
        select_obj = Select(select_elem)
        select_obj.select_by_value("50")
        random_human_pause()
        
        driver.execute_script("window.scrollTo(0, 0);")
        random_human_pause()
        
        logging.info("✅ Selected 'Show 50' results per page.")
    except Exception as e:
        logging.error(f"⚠️ Failed to select 'Show 50': {e}")

# === Select Posted Option from Drop-Down ===
def select_posted_option(driver, option_text):
    logging.info(f"🔎 Selecting 'Posted: {option_text}' filter...")
    try:
        dropdown_button_xpath = "/html/body/div/main/div[1]/form/fieldset/div[2]/div[1]/button"
        dropdown_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, dropdown_button_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_button)
        random_human_pause()
        driver.execute_script("arguments[0].click();", dropdown_button)
        random_human_pause()
        
        option_xpath = f"//a[@class='dropdown-item' and normalize-space(text())='{option_text}']"
        option_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, option_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", option_element)
        random_human_pause()
        driver.execute_script("arguments[0].click();", option_element)
        random_human_pause()
        
        logging.info(f"✅ Selected 'Posted: {option_text}'.")
    except Exception as e:
        logging.error(f"⚠️ Failed to select 'Posted: {option_text}': {e}")

# === Select Graduate Opportunities Filter ===
def select_graduate_opportunities(driver):
    logging.info("🔎 Selecting 'Graduate Opportunities' filter...")
    try:
        grad_dropdown_xpath = "/html/body/div/main/div[1]/form/fieldset/div[2]/div[3]/button"
        grad_dropdown = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, grad_dropdown_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", grad_dropdown)
        random_human_pause()
        driver.execute_script("arguments[0].click();", grad_dropdown)
        random_human_pause()
    except Exception as e:
        logging.error(f"⚠️ Failed to click the Graduate Opportunities drop-down: {e}")
        return

    try:
        grad_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "Job-Type-Graduate-checkbox"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", grad_checkbox)
        random_human_pause()
        driver.execute_script("arguments[0].click();", grad_checkbox)
        random_human_pause()
        
        if not grad_checkbox.is_selected():
            logging.error("⚠️ Graduate Opportunities checkbox was not selected after clicking.")
        else:
            logging.info("✅ Selected 'Graduate Opportunities'.")
    except Exception as e:
        logging.error(f"⚠️ Failed to select 'Graduate Opportunities': {e}")

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        random_human_pause()
        logging.info("✅ Closed Graduate Opportunities drop-down.")
    except Exception as e:
        logging.error(f"⚠️ Failed to close the Graduate Opportunities drop-down: {e}")

    try:
        browser_logs = driver.get_log("browser")
        for entry in browser_logs:
            if entry["level"] == "SEVERE":
                logging.error(f"JS error in browser console: {entry['message']}")
    except Exception as e:
        logging.error(f"Could not fetch browser logs: {e}")

# === Enter Keywords ===
def enter_keywords(driver, keywords):
    logging.info(f"🔎 Entering keywords: {keywords}")
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "keywords"))
        )
        search_box.clear()
        search_box.send_keys(keywords)
        random_human_pause()
        logging.info("✅ Keywords entered successfully.")
    except Exception as e:
        logging.error(f"⚠️ Failed to enter keywords: {e}")

# === Click Search Button ===
def click_search(driver):
    logging.info("🔎 Clicking 'Search' button...")
    try:
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(), 'Search')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
        random_human_pause()
        driver.execute_script("arguments[0].click();", search_button)
        random_human_pause()
        logging.info("✅ Search button clicked successfully.")
    except Exception as e:
        logging.error(f"⚠️ Failed to click 'Search' button: {e}")

# === Extract Job Links from the Main Search Results Page ===
def extract_job_links(driver):
    logging.info("🔎 Extracting job links from the page...")
    try:
        job_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/view-job/?id=')]"))
        )
        job_links = [job.get_attribute("href") for job in job_elements]
        logging.info(f"✅ Extracted {len(job_links)} job links.")
        return job_links
    except Exception as e:
        logging.error(f"⚠️ Failed to extract job links: {e}")
        return []

# === Collect All Job Links from All Pagination Pages (Link Collection Phase) ===
def collect_all_job_links(driver):
    all_links = []
    current_page = 1
    while True:
        logging.info(f"📄 Collecting links from page {current_page}...")
        page_links = extract_job_links(driver)
        if not page_links:
            logging.info("No job links found on this page, assuming end of results.")
            break
        all_links.extend(page_links)
        # Respect MAX_PAGES if set.
        if MAX_PAGES is not None and current_page >= MAX_PAGES:
            logging.info(f"Reached MAX_PAGES limit ({MAX_PAGES}); stopping pagination.")
            break
        # Try to navigate to the next page using dynamic pagination controls.
        next_page_number = current_page + 1
        try:
            next_page_xpath = f"//a[@class='page-link' and normalize-space(text())='{next_page_number}']"
            next_page_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, next_page_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page_element)
            random_human_pause()
            driver.execute_script("arguments[0].click();", next_page_element)
            active_page_xpath = f"//li[@class='page-item active']/span[@class='page-link' and normalize-space(text())='{next_page_number}']"
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, active_page_xpath))
            )
            random_human_pause()
            current_page = next_page_number
        except Exception as e:
            logging.info("🏁 No more pages to collect links or pagination link not found.")
            break
    return all_links

# === Scrape Job Details from a Given Job Link (Job Detail Extraction Phase) ===
def scrape_job_details(driver, job_link):
    logging.info(f"🔎 Scraping job details from {job_link}...")
    driver.get(job_link)
    random_human_pause()

    def safe_find(xpath, default="Not provided"):
        try:
            return driver.find_element(By.XPATH, xpath).text.strip()
        except Exception:
            return default

    # Extract the job title using the provided XPath.
    job_title = safe_find("/html/body/div/main/div[1]/div/h3", default="Not provided")
    
    # Extract the employer using the provided XPath.
    employer = safe_find("/html/body/div/main/div[1]/div/p/em", default="Not provided")
    
    # Extract the location using the provided XPath.
    location = safe_find("/html/body/div/main/div[1]/div/div[1]/div[5]/div[2]", default="Not provided")
    
    # Extract the tags using the provided XPath.
    tags = safe_find("/html/body/div/main/div[1]/div/div[1]/div[6]/div[2]/div", default="Not provided")
    
    # Extract additional fields (adjust these XPaths as needed).
    application_deadline = safe_find("//div[contains(text(), 'Application Deadline:')]/following-sibling::div", default="Not provided")
    published_date = safe_find("//div[contains(text(), 'Published:')]/following-sibling::div", default="Not provided")
    start_date = safe_find("//div[contains(text(), 'Starting Date:')]/following-sibling::div", default="Not provided")
    hours_per_week = safe_find("//div[contains(text(), 'Hours per Week:')]/following-sibling::div", default="Not provided")
    salary = safe_find("//div[contains(text(), 'Salary:')]/following-sibling::div", default="Not provided")
    education_required = safe_find("//div[contains(text(), 'Education Required:')]/following-sibling::div", default="Not provided")
    experience_required = safe_find("//div[contains(text(), 'Experience Required:')]/following-sibling::div", default="Not provided")
    description = safe_find("//div[contains(@class, 'trix-content')]", default="Not provided")
    contact_name = safe_find("//div[contains(text(), 'Contact Name:')]/following-sibling::div", default="Not provided")
    contact_email = safe_find("//a[contains(@href, 'mailto:')]", default="Not provided")

    job_data = {
        "Title": job_title,
        "Employer": employer,
        "Posting URL": job_link,
        "Application Deadline": application_deadline,
        "Published Date": published_date,
        "Start Date": start_date,
        "Hours per Week": hours_per_week,
        "Salary": salary,
        "Education Required": education_required,
        "Experience Required": experience_required,
        "Location": location,
        "Tags": tags,
        "Description": description,
        "Contact Name": contact_name,
        "Contact Email": contact_email,
    }
    return job_data

# === Main Scraping Function (Two-Phase Approach) ===
def scrape_jobs(driver):
    # Open the main search page and apply filters.
    driver.get("https://jobs.rwfm.tamu.edu/search/")
    random_human_pause()
    select_show_50(driver)
    select_posted_option(driver, POSTED_FILTER)
    select_graduate_opportunities(driver)
    enter_keywords(driver, KEYWORDS)
    click_search(driver)
    
    # PHASE 1: Collect all job links from the main search results pages.
    job_links = collect_all_job_links(driver)
    logging.info(f"Total job links collected: {len(job_links)}")
    
    # PHASE 2: Scrape details from each job link.
    jobs = []
    for link in job_links:
        job_data = scrape_job_details(driver, link)
        jobs.append(job_data)
    
    return pd.DataFrame(jobs)

# === Run the Scraper ===
if __name__ == "__main__":
    driver = setup_driver(debug=True)
    try:
        job_data_df = scrape_jobs(driver)
        job_data_df.to_csv("job_listings.csv", index=False)
        logging.info("✅ Job listings saved to job_listings.csv")
    except Exception as e:
        logging.exception("An unexpected error occurred during scraping:")
    finally:
        driver.quit()
import logging
import os
import re
import tempfile
import time
import random
import pandas as pd
import requests  # For Slack notifications
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # For sending the ESCAPE key
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# === Configuration Parameters ===
POSTED_FILTER = "Last 7 days"  # Use "Last 7 days" for scheduled scraping.
KEYWORDS = "(Master) OR (PhD) OR (Graduate) OR (MS)"
MAX_PAGES = None             # Set to an integer for testing; use None to scrape all pages.

# === Setup Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", mode="a")
    ]
)

# === Slack Notification Function ===
def send_slack_notification(message):
    """
    Sends a Slack notification using the incoming webhook URL specified in the SLACK_WEBHOOK environment variable.
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK")
    if not webhook_url:
        logging.info("No SLACK_WEBHOOK environment variable set. Skipping Slack notification.")
        return
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload, headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            logging.error(f"Failed to send Slack notification: {response.status_code}, {response.text}")
        else:
            logging.info("Slack notification sent successfully.")
    except Exception as e:
        logging.error(f"Error sending Slack notification: {e}")

# === Salary Parsing Function ===
def parse_salary(salary_str):
    """
    Parse a salary string and convert it to an annual salary value (float).
    Handles ranges (returns the average) and different time units (per year, per month, per week, per hour).
    Returns None if no numeric value can be extracted.
    """
    if not isinstance(salary_str, str):
        return None

    s = salary_str.lower().strip()
    if any(term in s for term in ["none", "commensurate", "negotiable"]):
        return None

    s = s.replace("starting at", "").strip()
    numbers = re.findall(r"\d[\d,\.]*", s)
    if not numbers:
        return None

    values = []
    for num in numbers:
        try:
            values.append(float(num.replace(",", "")))
        except ValueError:
            continue
    if not values:
        return None

    if "to" in s and len(values) >= 2:
        base_value = sum(values[:2]) / 2.0
    else:
        base_value = values[0]

    if "per year" in s:
        multiplier = 1
    elif "per month" in s:
        multiplier = 12
    elif "per week" in s:
        multiplier = 52
    elif "per hour" in s:
        multiplier = 2080  # 40 hours * 52 weeks
    else:
        multiplier = 1

    return base_value * multiplier

# === Extract State from Location ===
def extract_state(location_str):
    """
    Extracts the state from a location string.
    Handles:
      - Parentheses (e.g., "Auburn University (Alabama)" returns "Alabama")
      - Comma-separated locations (e.g., "Condon, Montana" returns "Montana")
      - Special case for "remote work allowed" returns "Remote"
    """
    if not isinstance(location_str, str):
        return None
    loc = location_str.strip()
    if "remote work allowed" in loc.lower():
        return "Remote"
    m = re.search(r'\(([^)]+)\)\s*$', loc)
    if m:
        content = m.group(1)
        parts = [p.strip() for p in content.split(",")]
        return parts[-1]
    if "," in loc:
        parts = [p.strip() for p in loc.split(",")]
        return parts[-1]
    return None

# === Employer Parsing Functions ===
def parse_employer(employer_str):
    """
    Parses the employer string to separate the employer name and employer type.
    For example:
      "The Jones Center at Ichauway (Private)" -> ("The Jones Center at Ichauway", "Private")
    Returns a tuple (employer_name, employer_type) where employer_type is None if not found.
    """
    if not isinstance(employer_str, str):
        return None, None
    employer_str = employer_str.strip()
    m = re.search(r'\(([^)]+)\)\s*$', employer_str)
    if m:
        employer_type = m.group(1).strip()
        employer_name = re.sub(r'\s*\([^)]+\)\s*$', '', employer_str).strip()
        return employer_name, employer_type
    else:
        return employer_str, None

def is_big_ten(employer_name):
    """
    Determines whether a university is part of the Big Ten.
    Returns True if the employer (assumed to be a university) matches Big Ten keywords,
    False if it's a university but not in the Big Ten, and None if not a university.
    """
    if not isinstance(employer_name, str):
        return None
    lower_name = employer_name.lower()
    if "university" not in lower_name:
        return None
    big_ten_keywords = [
        "university of illinois",
        "indiana university",
        "university of iowa",
        "university of maryland",
        "university of michigan",
        "michigan state university",
        "university of minnesota",
        "university of nebraska",
        "northwestern university",
        "ohio state university",
        "penn state university",
        "purdue university",
        "rutgers university",
        "university of wisconsin"
    ]
    for keyword in big_ten_keywords:
        if keyword in lower_name:
            return True
    return False

def process_employer_column(input_csv="data/job_listings.csv", output_csv="data/job_listings.csv"):
    """
    Processes the Employer column in the master job listings CSV.
    Splits the employer string into 'Employer_Name' and 'Employer_Type',
    and determines if the employer is a Big Ten university.
    Adds new columns 'Employer_Name', 'Employer_Type', and 'Big_Ten'
    (with "Yes" or "No" for universities), without removing the original Employer data.
    Updates the same CSV.
    """
    df = pd.read_csv(input_csv)
    if "Employer" not in df.columns:
        logging.error("Employer column not found in the CSV. Skipping employer processing.")
        return
    df[['Employer_Name', 'Employer_Type']] = df['Employer'].apply(lambda x: pd.Series(parse_employer(x)))
    def check_big_ten(name):
        is_uni = is_big_ten(name)
        if is_uni is None:
            return None
        return "Yes" if is_uni else "No"
    df['Big_Ten'] = df['Employer_Name'].apply(check_big_ten)
    df.to_csv(output_csv, index=False)
    logging.info(f"Processed employer data saved to {output_csv}")

# === Apply Cost-of-Living Adjustment ===
def apply_cost_of_living_adjustment(jobs_csv="data/job_listings.csv", rpp_csv="data/rpp_data.csv"):
    """
    Merges the master job data with the cost-of-living (RPP) data and computes an adjusted salary.
    Expects the RPP CSV to have columns: location,index.
    Uses the extracted State (from the Location field) to merge with the RPP mapping.
    Adds a new column "Adjusted Salary" without removing the original Salary column.
    Updates the same master CSV.
    """
    df = pd.read_csv(jobs_csv)
    rpp_df = pd.read_csv(rpp_csv)
    df["State"] = df["Location"].apply(lambda x: extract_state(x))
    rpp_df["State"] = rpp_df["location"].str.strip()
    merged_df = pd.merge(df, rpp_df, left_on="State", right_on="State", how="left")
    if "Salary" in merged_df.columns:
        merged_df["Salary_numeric"] = merged_df["Salary"].apply(parse_salary)
        base_index = 100.0  # Define your base index (e.g., for Lincoln, NE)
        merged_df["Adjusted Salary"] = merged_df.apply(
            lambda row: round(row["Salary_numeric"] * (base_index / row["index"]), 2)
            if pd.notnull(row["Salary_numeric"]) and pd.notnull(row["index"]) else None,
            axis=1
        )
    merged_df.to_csv(jobs_csv, index=False)
    logging.info(f"Cost-of-living adjustments applied and saved to {jobs_csv}")

# === Update Master CSV Function ===
def update_master_csv(new_data, master_csv="data/job_listings.csv"):
    """
    Updates the master CSV file by appending new data and removing duplicates.
    The update is performed by writing to a temporary file first and then atomically replacing the original file.
    Returns a tuple (new_jobs_count, total_jobs_count).
    """
    if os.path.exists(master_csv):
        master_df = pd.read_csv(master_csv)
        # Normalize column names (strip spaces)
        master_df.columns = [col.strip() for col in master_df.columns]
        new_data.columns = [col.strip() for col in new_data.columns]
        if "Posting URL" not in master_df.columns:
            logging.error(f"Column 'Posting URL' not found in master CSV. Columns found: {master_df.columns}")
            return None, None
        if "Posting URL" not in new_data.columns:
            logging.error(f"Column 'Posting URL' not found in new data. Columns found: {new_data.columns}")
            return None, None
        master_df["job_id"] = master_df["Posting URL"].apply(lambda url: url.split("id=")[-1])
        new_data["job_id"] = new_data["Posting URL"].apply(lambda url: url.split("id=")[-1])
        new_jobs_df = new_data[~new_data["job_id"].isin(master_df["job_id"])]
        new_jobs_count = len(new_jobs_df)
        combined_df = pd.concat([master_df, new_data], ignore_index=True)
        combined_df.drop_duplicates(subset=["job_id"], inplace=True)
        total_jobs_count = len(combined_df)
        combined_df.drop(columns=["job_id"], inplace=True)
    else:
        new_jobs_count = len(new_data)
        total_jobs_count = len(new_data)
        combined_df = new_data

    tmp_file = master_csv + ".tmp"
    try:
        combined_df.to_csv(tmp_file, index=False)
        os.replace(tmp_file, master_csv)
        logging.info("✅ Master CSV updated with new job postings.")
        return new_jobs_count, total_jobs_count
    except Exception as e:
        logging.error(f"⚠️ Failed to update master CSV: {e}")
        return None, None

# === Selenium WebDriver Setup ===
def setup_driver(debug=False):
    options = Options()
    if not debug:
        options.add_argument("--headless")  # Run headless unless debugging
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Always create a unique temporary user-data directory.
    temp_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")
    logging.info(f"Using temporary user-data-dir: {temp_dir}")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# === Human-like Pause ===
def random_human_pause(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

# === Scraper Functions ===
def select_show_50(driver):
    logging.info("🔎 Selecting 'Show 50' results per page...")
    try:
        select_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//select[@name='PageSize']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", select_elem)
        random_human_pause()
        Select(select_elem).select_by_value("50")
        random_human_pause()
        driver.execute_script("window.scrollTo(0, 0);")
        random_human_pause()
        logging.info("✅ Selected 'Show 50' results per page.")
    except Exception as e:
        logging.error(f"⚠️ Failed to select 'Show 50': {e}")

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
        if MAX_PAGES is not None and current_page >= MAX_PAGES:
            logging.info(f"Reached MAX_PAGES limit ({MAX_PAGES}); stopping pagination.")
            break
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

def scrape_job_details(driver, job_link):
    logging.info(f"🔎 Scraping job details from {job_link}...")
    driver.get(job_link)
    random_human_pause()

    def safe_find(xpath, default="Not provided"):
        try:
            return driver.find_element(By.XPATH, xpath).text.strip()
        except Exception:
            return default

    job_title = safe_find("/html/body/div/main/div[1]/div/h3", default="Not provided")
    employer = safe_find("/html/body/div/main/div[1]/div/p/em", default="Not provided")
    location = safe_find("/html/body/div/main/div[1]/div/div[1]/div[5]/div[2]", default="Not provided")
    tags = safe_find("/html/body/div/main/div[1]/div/div[1]/div[6]/div[2]/div", default="Not provided")
    
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

def update_master_csv(new_data, master_csv="data/job_listings.csv"):
    if os.path.exists(master_csv):
        master_df = pd.read_csv(master_csv)
        # Debug: Print column names
        logging.info(f"Master CSV columns: {master_df.columns.tolist()}")
        
        # Normalize column names by stripping whitespace
        master_df.columns = [col.strip() for col in master_df.columns]
        new_data.columns = [col.strip() for col in new_data.columns]
        
        # Check if 'Posting URL' exists; if not, list available columns
        if "Posting URL" not in master_df.columns:
            logging.error(f"Column 'Posting URL' not found in master CSV. Columns found: {master_df.columns.tolist()}")
            return None, None
        if "Posting URL" not in new_data.columns:
            logging.error(f"Column 'Posting URL' not found in new data. Columns found: {new_data.columns.tolist()}")
            return None, None

        master_df["job_id"] = master_df["Posting URL"].apply(lambda url: url.split("id=")[-1])
        new_data["job_id"] = new_data["Posting URL"].apply(lambda url: url.split("id=")[-1])
        new_jobs_df = new_data[~new_data["job_id"].isin(master_df["job_id"])]
        new_jobs_count = len(new_jobs_df)
        combined_df = pd.concat([master_df, new_data], ignore_index=True)
        combined_df.drop_duplicates(subset=["job_id"], inplace=True)
        total_jobs_count = len(combined_df)
        combined_df.drop(columns=["job_id"], inplace=True)
    else:
        new_jobs_count = len(new_data)
        total_jobs_count = len(new_data)
        combined_df = new_data

    tmp_file = master_csv + ".tmp"
    try:
        combined_df.to_csv(tmp_file, index=False)
        os.replace(tmp_file, master_csv)
        logging.info("✅ Master CSV updated with new job postings.")
        return new_jobs_count, total_jobs_count
    except Exception as e:
        logging.error(f"⚠️ Failed to update master CSV: {e}")
        return None, None

def apply_cost_of_living_adjustment(jobs_csv="data/job_listings.csv", rpp_csv="data/rpp_data.csv"):
    """
    Merges the master job data with the cost-of-living (RPP) data and computes an adjusted salary.
    Expects the RPP CSV to have columns: location,index.
    Uses the extracted State (from the Location field) to merge with the RPP mapping.
    Adds a new column "Adjusted Salary" without removing the original Salary column.
    Updates the same master CSV.
    """
    df = pd.read_csv(jobs_csv)
    rpp_df = pd.read_csv(rpp_csv)
    df["State"] = df["Location"].apply(lambda x: extract_state(x))
    rpp_df["State"] = rpp_df["location"].str.strip()
    merged_df = pd.merge(df, rpp_df, left_on="State", right_on="State", how="left")
    if "Salary" in merged_df.columns:
        merged_df["Salary_numeric"] = merged_df["Salary"].apply(parse_salary)
        base_index = 100.0  # Define your base index (e.g., for Lincoln, NE)
        merged_df["Adjusted Salary"] = merged_df.apply(
            lambda row: round(row["Salary_numeric"] * (base_index / row["index"]), 2)
            if pd.notnull(row["Salary_numeric"]) and pd.notnull(row["index"]) else None,
            axis=1
        )
    merged_df.to_csv(jobs_csv, index=False)
    logging.info(f"Cost-of-living adjustments applied and saved to {jobs_csv}")

def scrape_jobs(driver):
    driver.get("https://jobs.rwfm.tamu.edu/search/")
    random_human_pause()
    select_show_50(driver)
    select_posted_option(driver, POSTED_FILTER)
    select_graduate_opportunities(driver)
    enter_keywords(driver, KEYWORDS)
    click_search(driver)
    job_links = collect_all_job_links(driver)
    logging.info(f"Total job links collected: {len(job_links)}")
    jobs = []
    for link in job_links:
        job_data = scrape_job_details(driver, link)
        jobs.append(job_data)
    return pd.DataFrame(jobs)

# === Setup Selenium WebDriver ===
def setup_driver(debug=False):
    options = Options()
    if not debug:
        options.add_argument("--headless")  # Run headless unless debugging
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Always create a unique temporary user-data directory.
    temp_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")
    logging.info(f"Using temporary user-data-dir: {temp_dir}")
    
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# === Human-like Pause ===
def random_human_pause(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

# === Main Entry Point ===
if __name__ == "__main__":
    debug_mode = True
    if os.environ.get("GITHUB_ACTIONS") is not None:
        debug_mode = False

    driver = setup_driver(debug=debug_mode)
    try:
        send_slack_notification("Wildlife Grad Job Scraper has started.")
        job_data_df = scrape_jobs(driver)
        new_jobs_count, total_jobs_count = update_master_csv(job_data_df, master_csv="data/job_listings.csv")
        logging.info("✅ Job listings saved to data/job_listings.csv")
        if new_jobs_count is not None and total_jobs_count is not None:
            send_slack_notification(f"Wildlife Grad Job Scraper completed successfully: {new_jobs_count} new jobs scraped, {total_jobs_count} total jobs.")
        else:
            send_slack_notification("Wildlife Grad Job Scraper completed, but failed to update master CSV properly.")
        apply_cost_of_living_adjustment(jobs_csv="data/job_listings.csv", rpp_csv="data/rpp_data.csv")
        process_employer_column(input_csv="data/job_listings.csv", output_csv="data/job_listings.csv")
        send_slack_notification("Wildlife Grad Job Scraper post-processing completed successfully.")
    except Exception as e:
        logging.exception("An unexpected error occurred during scraping or processing:")
        send_slack_notification(f"Scraper Error: {e}\nCheck the logs for details.")
    finally:
        driver.quit()
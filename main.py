import time
import random
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ---------------------------
# CONFIGURATION
# ---------------------------
BASE_URL = "https://jobs.rwfm.tamu.edu/search/"  # Update with actual job listing URL
PROXY_LIST_URL = "https://www.free-proxy-list.net/"  # Free proxy provider
OUTPUT_FILE = "job_data.csv"

# ---------------------------
# FUNCTION TO GET FREE PROXIES
# ---------------------------
def get_proxies():
    """Scrapes a list of free proxies from the internet."""
    response = requests.get(PROXY_LIST_URL)
    proxies = []
    if response.status_code == 200:
        lines = response.text.split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) > 1 and parts[0].replace(".", "").isdigit():  # Detect valid IPs
                proxy = f"http://{parts[0]}:{parts[1]}"
                proxies.append(proxy)
    return proxies

# Get a list of proxies
proxy_list = get_proxies()
print(f"Found {len(proxy_list)} proxies.")

# ---------------------------
# FUNCTION TO SET UP SELENIUM WEBDRIVER
# ---------------------------
def get_driver():
    """Returns a Selenium WebDriver with a random proxy and user-agent."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Use a random proxy
    if proxy_list:
        proxy = random.choice(proxy_list)
        chrome_options.add_argument(f"--proxy-server={proxy}")
        print(f"Using proxy: {proxy}")

    # Use a fake user-agent
    fake_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={fake_user_agent}")

    # Initialize WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# ---------------------------
# FUNCTION TO SCRAPE JOB LISTINGS
# ---------------------------
def scrape_jobs():
    """Scrapes job postings from the website."""
    driver = get_driver()
    jobs = []
    page = 1

    while True:
        print(f"Scraping page {page}...")
        time.sleep(random.uniform(5, 10))  # Random delay

        try:
            driver.get(f"{BASE_URL}/jobs?page={page}")

            # Find job listings (update the selector to match the actual website)
            job_elements = driver.find_elements(By.CLASS_NAME, "job-listing")
            
            if not job_elements:
                print("No more job listings found. Exiting.")
                break

            for job in job_elements:
                try:
                    title = job.find_element(By.CLASS_NAME, "title").text.strip()
                    organization = job.find_element(By.CLASS_NAME, "organization").text.strip()
                    location = job.find_element(By.CLASS_NAME, "location").text.strip()
                    salary = job.find_element(By.CLASS_NAME, "salary").text.strip()
                    date_posted = job.find_element(By.CLASS_NAME, "date").text.strip()

                    jobs.append({
                        "Title": title,
                        "Organization": organization,
                        "Location": location,
                        "Salary": salary,
                        "Published Date": date_posted,
                    })
                except Exception as e:
                    print(f"Skipping job due to error: {e}")

            page += 1  # Move to the next page

        except Exception as e:
            print(f"Error loading page {page}: {e}")
            break

    driver.quit()
    return jobs

# ---------------------------
# FUNCTION TO REMOVE DUPLICATES AND SAVE DATA
# ---------------------------
def save_jobs(jobs):
    """Saves job postings to a CSV file, appending new data while removing duplicates."""
    try:
        existing_df = pd.read_csv(OUTPUT_FILE)
    except FileNotFoundError:
        existing_df = pd.DataFrame()

    new_df = pd.DataFrame(jobs)
    combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=["Title", "Organization", "Location"])
    combined_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(combined_df)} unique job postings.")

# ---------------------------
# RUN SCRIPT
# ---------------------------
if __name__ == "__main__":
    new_jobs = scrape_jobs()
    if new_jobs:
        save_jobs(new_jobs)
    else:
        print("No new jobs found.")
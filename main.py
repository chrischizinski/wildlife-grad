import os
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# Constants
DATA_FILE = "job_data.csv"
BASE_URL = "https://example-job-board.com"  # Replace with the actual website URL

# Configure Selenium with headless mode and random user-agent
options = Options()
options.add_argument("--headless")  # Run without opening a browser
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(f"user-agent={UserAgent().random}")

# Start WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def scrape_jobs():
    """Scrapes job listings and returns a DataFrame."""
    jobs = []
    page = 1
    
    while True:
        print(f"Scraping page {page}...")
        driver.get(f"{BASE_URL}/jobs?page={page}")
        time.sleep(3)  # Allow the page to load
        
        job_elements = driver.find_elements(By.CLASS_NAME, "job-listing")  # Update this selector as needed
        
        if not job_elements:
            break  # No more pages left
        
        for job in job_elements:
            try:
                title = job.find_element(By.CLASS_NAME, "job-title").text
                organization = job.find_element(By.CLASS_NAME, "job-organization").text
                location = job.find_element(By.CLASS_NAME, "job-location").text
                salary = job.find_element(By.CLASS_NAME, "job-salary").text or "N/A"
                start_date = job.find_element(By.CLASS_NAME, "job-start-date").text or "N/A"
                published_date = job.find_element(By.CLASS_NAME, "job-published-date").text or "N/A"
                tags = job.find_element(By.CLASS_NAME, "job-tags").text or "N/A"
                
                jobs.append({
                    "Title": title,
                    "Organization": organization,
                    "Location": location,
                    "Salary": salary,
                    "Starting Date": start_date,
                    "Published Date": published_date,
                    "Tags": tags
                })
            except Exception as e:
                print(f"Skipping job due to error: {e}")
        
        page += 1

    driver.quit()
    return pd.DataFrame(jobs)

def load_existing_data():
    """Loads existing job data if the file exists."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Title", "Organization", "Location", "Salary", "Starting Date", "Published Date", "Tags"])

def save_updated_data(new_jobs_df):
    """Combines new and old job data, removes duplicates, and saves to CSV."""
    existing_df = load_existing_data()
    
    # Merge, drop duplicates based on 'Title' and 'Organization'
    updated_df = pd.concat([existing_df, new_jobs_df]).drop_duplicates(subset=["Title", "Organization"], keep="last")
    
    # Save to file
    updated_df.to_csv(DATA_FILE, index=False)
    print(f"Updated job data saved to {DATA_FILE}")

if __name__ == "__main__":
    new_jobs = scrape_jobs()
    if not new_jobs.empty:
        save_updated_data(new_jobs)
    else:
        print("No new jobs found.")
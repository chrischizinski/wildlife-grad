# Wildlife Grad Job Scraper

This project is a Python-based web scraper designed to collect graduate assistantship job postings from the Wildlife (or related) jobs website. The scraper uses Selenium to automate browser interactions and extract details (such as job title, employer, location, tags, etc.) from each job posting. It follows a two-phase approach:

1. **Link Collection Phase:**  
   Paginate through the main search results to collect all job posting URLs.
2. **Job Detail Extraction Phase:**  
   Visit each job posting URL and extract detailed job information.

The project also integrates with GitHub Actions to run the scraper on a weekly schedule and is configured for robust logging and error handling.

## Features

- **Configurable Filters:** Easily adjust the posted filter (e.g., "Anytime" or "Last 7 days") and keywords.
- **Pagination Handling:** Collects job links across multiple pages.
- **Two-Phase Scraping:** Separates link collection from job detail extraction for improved reliability.
- **CI/CD Integration:** Automated weekly runs using GitHub Actions.
- **Logging & Error Handling:** Logs output both to the console and to a log file (`scraper.log`).

## Requirements

- Python 3.12.7 (or a compatible version)
- The dependencies listed in the `requirements.txt` file

### Example `requirements.txt`
```
requests
beautifulsoup4
selenium
webdriver-manager
pandas
fake_useragent
```

> **Note:** Some packages (like `requests` and `beautifulsoup4`) may be included for potential future enhancements or alternative parsing methods, even if Selenium is the primary tool used.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/chrischizinski/wildife-grad.git
   cd wildife-grad
   ```

2. **Install the Required Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

In the `new_attempt.py` file, you can adjust the following configuration parameters at the top:

- **POSTED_FILTER:**  
  Currently set to `"Anytime"`. Change to `"Last 7 days"` for weekly automation of recent postings.
- **KEYWORDS:**  
  The search keywords (e.g., `(Master) OR (PhD) OR (Graduate) OR (MS)`).
- **MAX_PAGES:**  
  Set to an integer during testing to limit the number of pages; set to `None` to scrape all available pages.

## Usage

### Running Locally

Run the scraper locally with:
```bash
python new_attempt.py
```
The scraper will produce a CSV file named `job_listings.csv` containing the scraped job details and a log file (`scraper.log`) with detailed execution logs.

## GitHub Actions (Weekly Automation)

A GitHub Actions workflow is configured to run the scraper on a weekly schedule. The workflow file is located at `.github/workflows/weekly_scrape.yml`. This workflow:

- Sets up Python (using Python 3.12.7).
- Installs the required dependencies.
- Runs the scraper script.

### Example Workflow File (`.github/workflows/weekly_scrape.yml`)

```yaml
name: Weekly Job Scraper

on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight UTC
  workflow_dispatch:   # Allows manual triggering

jobs:
  scrape:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12.7'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Scraper
        run: |
          python new_attempt.py
```

## Logging & Error Notifications

The scraper uses Python’s `logging` module to write logs both to the console and to a file (`scraper.log`). In the main entry point, errors are caught and logged. For future enhancements, you can integrate an alert system (such as sending an email or Slack notification) to notify you if the scraping or processing fails.

## Future Enhancements

- **Deduplication:**  
  Compare new job postings against an existing master list (by job ID) and append only new jobs.
- **Data Enrichment:**  
  Add cost-of-living conversions and use NLP (e.g., via spaCy or NLTK) for categorizing grad assistantship positions.
- **Dashboard/Interactive Website:**  
  Build an interactive dashboard with Streamlit, Dash, or host a static site on GitHub Pages to visualize the data.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or contributions, please contact [your_email@example.com](mailto:your_email@example.com).
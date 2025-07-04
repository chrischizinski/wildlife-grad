# Gemini Project Context: Wildlife Jobs Scraper

This document provides context for the Gemini AI assistant to effectively assist with development tasks in this repository.

## Project Overview

This project is a Python-based web scraper designed to collect graduate assistantship opportunities from the Texas A&M Wildlife and Fisheries job board. The primary goal is to automate the collection of job listings for academic research. The project includes features for data analysis and an interactive dashboard to visualize the scraped data.

## Key Technologies

*   **Python:** The core language for the scraper and all related scripts.
*   **Selenium:** Used for web browser automation to scrape the job board.
*   **Pandas:** For data manipulation and analysis of the scraped job listings.
*   **Pydantic:** For data validation and parsing to ensure data quality.
*   **BeautifulSoup4:** For HTML parsing.
*   **Pytest:** The testing framework used for unit tests.
*   **GitHub Actions:** For CI/CD and automating the scraping process.

## Project Structure

*   `wildlife_job_scraper.py`: The main scraper script.
*   `requirements.txt`: A list of all the Python dependencies for this project.
*   `tests/`: Contains all the unit tests for the project.
*   `dashboard/`: Contains the files for the interactive data dashboard.
*   `data/`: The default directory for the output files (JSON and CSV).
*   `scripts/`: Contains various scripts for analysis and debugging.
*   `.github/workflows/`: Contains the GitHub Actions workflow files.

## Common Commands

*   **Install dependencies:** `pip install -r requirements.txt`
*   **Run the scraper:** `python wildlife_job_scraper.py`
*   **Run tests:** `pytest tests/ -v`
*   **Run tests with coverage:** `pytest tests/ --cov=wildlife_job_scraper --cov-report=html`

## Contribution Guidelines

*   Follow PEP 8 formatting standards (using Black).
*   Use type hints throughout the codebase.
*   Write unit tests for new features.
*   Create a feature branch for new features and submit a pull request.

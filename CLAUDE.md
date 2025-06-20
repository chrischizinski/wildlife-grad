# Wildlife Jobs Board Scraper

## Project Overview
This project scrapes graduate assistantship opportunities from the Texas A&M Wildlife and Fisheries job board (https://jobs.rwfm.tamu.edu/search/). It uses Selenium WebDriver to navigate the site and BeautifulSoup to parse job listings for academic research purposes.

## Key Files
- `scrape_jobs.py` - Main scraping script
- `scrape_jobs2.py` - Alternative version 
- `scrape_jobs_fixed.py` - Fixed version of the scraper
- `graduate_assistantships.csv` - Output data in CSV format
- `graduate_assistantships.json` - Output data in JSON format
- `scrape_jobs.log` - Logging output
- `am.html`, `debug_page.html`, `debug_page_after_filters.html` - Debug/test HTML files

## Technology Stack
- Python (following PEP8, using type hints, formatted with black)
- Selenium WebDriver (Chrome)
- BeautifulSoup4
- Logging
- JSON/CSV for data output

## Setup Requirements
- Chrome browser
- ChromeDriver (currently configured for ARM64 Mac at `/opt/homebrew/Caskroom/chromedriver/132.0.6834.110/chromedriver-mac-arm64/chromedriver`)
- Python packages: selenium, beautifulsoup4

## Purpose
Automated collection of wildlife and fisheries graduate assistantship opportunities for research/educational purposes.

## Project-Specific Guidelines
- Respect robots.txt and website terms of service
- Implement rate limiting to avoid overwhelming the target server
- Maintain data privacy and research ethics standards
- Focus on reproducibility and clear documentation for academic use
- Use proper logging for debugging and monitoring scraping activities

## Development Notes
- Code should be modular and well-documented
- Functions should include Google-style docstrings
- Implement proper error handling for network requests
- Consider implementing data validation with pydantic for structured output
- All code should be tested with pytest unit tests

## Automated Workflow
- **GitHub Actions**: Automated weekly scraping every Sunday at 6 AM UTC
- **Data Storage**: Results stored in `/data` directory with timestamped archives
- **Dashboard Deployment**: Automatic deployment to GitHub Pages after each scrape
- **Historical Tracking**: Maintains time-series data for trend analysis

## Dashboard Features
- **Interactive visualizations** using Chart.js
- **Real-time filtering** by location, degree type, and keywords
- **Responsive design** for mobile and desktop viewing
- **Download capabilities** for JSON and CSV data
- **Historical trends** showing job posting patterns over time

## Quick Start
1. Push code to GitHub repository
2. Enable GitHub Actions and Pages
3. Manually trigger first scrape in Actions tab
4. View dashboard at `https://username.github.io/repository-name/`

---
*This project follows the global guidelines in CLAUDE_GLOBAL.md*
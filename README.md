# Wildlife Jobs Board Scraper

A comprehensive Python scraper for graduate assistantship opportunities from the Texas A&M Wildlife and Fisheries job board. This tool automates the collection of job listings for academic research purposes, with integrated data analysis and interactive dashboard capabilities.

## 📊 Current Status
- **233 job listings** successfully scraped and validated
- **Multi-page pagination** working correctly (5 pages total)
- **Dashboard framework** ready for data integration
- **GitHub Actions** workflow prepared for weekly automation

## Features

- **Robust scraping** with anti-detection measures
- **Data validation** using Pydantic models
- **Multiple output formats** (JSON, CSV)
- **Configurable parameters** via environment variables or CLI
- **Comprehensive logging** for debugging and monitoring
- **Unit tests** with pytest
- **Type hints** throughout the codebase
- **Academic research focused** with ethical scraping practices

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd WildlifeJobsBoardScrape
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Usage

### Command Line Interface

Basic usage:
```bash
python cli.py
```

With custom parameters:
```bash
python cli.py --keywords "ecology OR conservation" --output-dir results --verbose
```

Available options:
```bash
python cli.py --help
```

### Python API

```python
from wildlife_job_scraper import ScraperConfig, WildlifeJobScraper

# Create configuration
config = ScraperConfig(
    keywords="(Master) OR (PhD) OR (Graduate)",
    headless=True,
    output_dir=Path("data")
)

# Initialize scraper
scraper = WildlifeJobScraper(config)

# Scrape jobs
jobs = scraper.scrape_all_jobs()

# Save results
scraper.save_jobs_json(jobs)
scraper.save_jobs_csv(jobs)
```

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example`) with the following optional variables:

- `JOB_SEARCH_URL`: Target job board URL
- `SEARCH_KEYWORDS`: Search terms for filtering
- `OUTPUT_DIR`: Directory for output files
- `MIN_DELAY`: Minimum delay between actions (seconds)
- `MAX_DELAY`: Maximum delay between actions (seconds)
- `HEADLESS`: Run browser in headless mode (true/false)

### Configuration Parameters

The `ScraperConfig` class accepts the following parameters:

- `base_url`: Job board URL (default: Texas A&M site)
- `keywords`: Search keywords for filtering jobs
- `output_dir`: Directory for saving results
- `page_size`: Number of results per page (max 50)
- `min_delay`/`max_delay`: Random delay range for human-like behavior
- `timeout`: Element wait timeout in seconds
- `headless`: Run browser without GUI

## Output

The scraper generates two output files:

### JSON Format (`graduate_assistantships.json`)
```json
[
  {
    "title": "Graduate Research Assistant",
    "organization": "University of Texas",
    "location": "Austin, TX",
    "salary": "$25,000/year",
    "starting_date": "Fall 2024",
    "published_date": "2024-01-15",
    "tags": "Research, Wildlife"
  }
]
```

### CSV Format (`graduate_assistantships.csv`)
Tabular format suitable for analysis in Excel, R, or Python pandas.

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=wildlife_job_scraper --cov-report=html
```

## Development

### Code Quality

The project follows these standards:
- **PEP 8** formatting with Black
- **Type hints** throughout
- **Google-style docstrings**
- **Pydantic models** for data validation
- **Comprehensive logging**
- **Unit tests** with pytest

### Adding Features

1. Create a feature branch
2. Add your changes with appropriate tests
3. Ensure all tests pass
4. Submit a pull request

## Ethical Considerations

This scraper is designed for academic research and follows ethical web scraping practices:

- **Respectful delays** between requests
- **User-agent rotation** to avoid overwhelming servers
- **Compliance with robots.txt** (when applicable)
- **Rate limiting** to prevent server overload
- **Data privacy** considerations for research use

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**: The scraper uses `webdriver-manager` to automatically download ChromeDriver. Ensure you have Chrome installed.

2. **Connection timeouts**: Increase the `timeout` parameter or check your internet connection.

3. **No jobs found**: Verify the search keywords and ensure the target website is accessible.

4. **Permission errors**: Check that the output directory is writable.

### Debug Mode

Run with visible browser for debugging:
```bash
python cli.py --no-headless --verbose
```

## Dependencies

- `selenium`: Web browser automation
- `pandas`: Data manipulation and analysis
- `pydantic`: Data validation and parsing
- `beautifulsoup4`: HTML parsing (if needed)
- `python-dotenv`: Environment variable management
- `fake-useragent`: User agent rotation
- `webdriver-manager`: Automatic ChromeDriver management

## License

This project is intended for academic research purposes. Please ensure compliance with the target website's terms of service and applicable laws.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information
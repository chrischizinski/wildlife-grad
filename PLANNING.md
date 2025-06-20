# Wildlife Jobs Board Scraper - Project Planning

## Project Overview
Automated scraping system for wildlife and fisheries graduate assistantship opportunities from the Texas A&M Wildlife and Fisheries job board (https://jobs.rwfm.tamu.edu/search/).

## Current Status
✅ **COMPLETED**
- Basic scraper implementation with Selenium
- Pagination detection and multi-page scraping (233 jobs collected)
- Data validation with Pydantic models
- CSV and JSON output formats
- Comprehensive logging system
- Project file cleanup and organization

✅ **COMPLETED**
- Dashboard data analysis and visualization  
- Integration of analysis features
- Documentation updates

⏳ **PLANNED**
- GitHub Actions workflow for weekly automation
- Historical data tracking and trend analysis
- Dashboard deployment to GitHub Pages
- Error handling and notification system

## Project Architecture

### Core Components
1. **Scraper** (`wildlife_job_scraper.py`)
   - Selenium WebDriver with Chrome
   - Anti-detection measures
   - Rate limiting and human-like behavior
   - Robust pagination handling

2. **Data Pipeline** (`scripts/generate_dashboard_data.py`)
   - Data analysis and categorization
   - Trend analysis over time
   - Export preparation for dashboard

3. **Dashboard** (`dashboard/`)
   - Interactive visualizations with Chart.js
   - Real-time filtering capabilities
   - Responsive design
   - Download functionality

4. **Automation** (`.github/workflows/`)
   - Weekly scheduled scraping
   - Automatic dashboard updates
   - Data archiving with timestamps

### Data Flow
```
Website → Scraper → JSON/CSV → Analysis → Dashboard → GitHub Pages
                                    ↓
                               Data Archive
```

## Technical Specifications

### Dependencies
- Python 3.11+
- Selenium WebDriver
- BeautifulSoup4
- Pandas for data analysis
- Pydantic for validation
- Chrome browser + ChromeDriver

### Output Formats
- **JSON**: `data/graduate_assistantships.json`
- **CSV**: `data/graduate_assistantships.csv`
- **Dashboard Data**: `dashboard/data.json`
- **Archives**: `data/archive/jobs_YYYY-MM-DD.*`

### Data Fields
- Title, Organization, Location
- Salary, Starting Date, Published Date
- Tags, Education Requirements
- Application Deadlines

## Roadmap

### Phase 1: Core Functionality ✅
- [x] Basic scraping implementation
- [x] Data validation and storage
- [x] Pagination handling
- [x] Error handling and logging

### Phase 2: Analysis & Dashboard ✅
- [x] Complete dashboard data generation
- [x] Interactive visualizations
- [x] Trend analysis over time
- [x] Advanced filtering options

### Phase 3: Automation ⏳
- [ ] GitHub Actions workflow
- [ ] Weekly scheduling
- [ ] Data archiving system
- [ ] Error notifications

### Phase 4: Enhancement ⏳
- [ ] Additional data sources
- [ ] Machine learning categorization
- [ ] Email notifications
- [ ] API endpoints

## Risk Mitigation

### Website Changes
- Modular selector system
- Fallback pagination detection
- Comprehensive error handling

### Rate Limiting
- Human-like delays (2-5 seconds)
- User agent rotation
- Respectful scraping practices

### Data Quality
- Pydantic validation models
- Data cleaning and normalization
- Duplicate detection

## Success Metrics
- **Coverage**: 233 job listings captured (100% of available)
- **Accuracy**: Clean, validated data structure
- **Reliability**: Consistent weekly updates
- **Usability**: Interactive dashboard with trend analysis

## Compliance
- Respects robots.txt
- Implements rate limiting
- Academic/research purpose
- No personal data collection
- Transparent data usage
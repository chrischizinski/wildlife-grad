# Setup Guide for Automated Wildlife Jobs Scraper

This guide will help you set up automated weekly scraping with GitHub Actions and deploy a dashboard to view the results.

## Prerequisites

- GitHub account
- Git installed locally
- Python 3.8+ (for local testing)

## Quick Setup

### 1. Repository Setup

1. **Create a new GitHub repository** or fork this one
2. **Clone the repository** to your local machine:
   ```bash
   git clone https://github.com/yourusername/WildlifeJobsBoardScrape.git
   cd WildlifeJobsBoardScrape
   ```

3. **Push the code** to your GitHub repository:
   ```bash
   git add .
   git commit -m "Initial setup of wildlife jobs scraper"
   git push origin main
   ```

### 2. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click on the **Actions** tab
3. GitHub should automatically detect the workflows
4. Click **"I understand my workflows, go ahead and enable them"**

### 3. Enable GitHub Pages

1. Go to **Settings** → **Pages** in your repository
2. Under **Source**, select **"GitHub Actions"**
3. Save the settings

### 4. Test the Setup

1. **Manual trigger**: Go to Actions → "Weekly Job Scraping" → "Run workflow"
2. **Wait for completion**: The workflow should complete in 5-10 minutes
3. **Check results**: After completion, the dashboard should be deployed automatically

## Configuration Options

### Environment Variables (Optional)

You can customize the scraper behavior by setting these repository secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add repository variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARCH_KEYWORDS` | Keywords for job filtering | `(Master) OR (PhD) OR (Graduate)` |
| `MIN_DELAY` | Minimum delay between requests | `1.0` |
| `MAX_DELAY` | Maximum delay between requests | `3.0` |

### Schedule Customization

To change the scraping schedule, edit `.github/workflows/scrape-jobs.yml`:

```yaml
schedule:
  # Current: Every Sunday at 6:00 AM UTC
  - cron: '0 6 * * 0'
  
  # Examples:
  # Daily at 2 AM UTC: '0 2 * * *'
  # Twice weekly (Mon, Thu): '0 6 * * 1,4'
  # Monthly on 1st: '0 6 1 * *'
```

## Dashboard Features

Your dashboard will be available at: `https://yourusername.github.io/WildlifeJobsBoardScrape/`

### Features Include:
- **Real-time statistics** (total jobs, new jobs, locations)
- **Interactive charts** (degree types, research areas, locations, salary ranges)
- **Job search and filtering** by location, degree type, keywords
- **Historical trends** showing job posting patterns over time
- **Download options** for JSON and CSV data

### Dashboard Sections:
1. **Overview** - Key metrics and summary statistics
2. **Analytics** - Visual charts and trends
3. **Job Listings** - Searchable and filterable job cards
4. **Download** - Access to raw data files

## Troubleshooting

### Common Issues

1. **Workflow fails with "Chrome not found"**
   - This is handled automatically by the workflow
   - Check the workflow logs for specific errors

2. **No jobs found**
   - The target website might be down
   - Check if the search keywords are too restrictive
   - Review the workflow logs for details

3. **Dashboard not updating**
   - Ensure GitHub Pages is enabled
   - Check that the deploy workflow completed successfully
   - Clear your browser cache

4. **Data files not found**
   - Verify the scraping workflow completed successfully
   - Check that data files are committed to the repository

### Debugging

1. **Check workflow logs**:
   - Go to Actions tab → Select failed workflow → View logs

2. **Manual testing locally**:
   ```bash
   pip install -r requirements.txt
   python cli.py --no-headless --verbose
   ```

3. **Test dashboard locally**:
   ```bash
   cd dashboard
   python -m http.server 8000
   # Visit http://localhost:8000
   ```

## Data Storage

### File Structure
```
data/
├── jobs_latest.json          # Most recent scrape
├── jobs_latest.csv           # Most recent scrape (CSV)
├── jobs_2024-01-15.json      # Timestamped archives
├── jobs_2024-01-15.csv       # Timestamped archives
└── ...

dashboard/
├── index.html                # Dashboard homepage
├── dashboard.js              # Dashboard logic
├── styles.css                # Dashboard styling
└── data.json                 # Dashboard statistics
```

### Data Retention
- All scraped data is stored in the repository
- Timestamped files create a historical record
- GitHub has a 1GB repository size limit (should be sufficient for years of data)

## Customization

### Modify Scraping Logic
Edit `wildlife_job_scraper.py` to:
- Change search keywords
- Modify extraction logic
- Add new data fields
- Change output format

### Customize Dashboard
Edit dashboard files to:
- Change color scheme (`dashboard/styles.css`)
- Add new charts (`dashboard/dashboard.js`)
- Modify layout (`dashboard/index.html`)

### Add New Features
Consider adding:
- Email notifications when new jobs are found
- Slack/Discord integration
- Job application deadline tracking
- Automated job similarity analysis

## Security Considerations

- **No credentials required**: The scraper works without authentication
- **Rate limiting**: Built-in delays prevent overwhelming the target server
- **Ethical scraping**: Respects robots.txt and implements reasonable delays
- **Public data only**: Only scrapes publicly available job listings

## Support

### Getting Help
1. Check this guide first
2. Review GitHub Actions logs
3. Create an issue in the repository
4. Include relevant error messages and logs

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Legal and Ethical Notes

- This scraper is designed for academic research purposes
- Always respect the target website's terms of service
- The scraper implements ethical delays and practices
- Ensure compliance with your institution's research policies
- Consider reaching out to the website owners for permission if using extensively

## Advanced Configuration

### Custom Workflows
You can create additional workflows for:
- Data analysis and reporting
- Integration with external services
- Backup to cloud storage
- Advanced data processing

### Multiple Target Sites
To scrape multiple job boards:
1. Create separate scraper classes for each site
2. Modify the workflow to run multiple scrapers
3. Combine results in the dashboard

### Data Analysis
The JSON/CSV outputs can be used with:
- R for statistical analysis
- Python pandas for data manipulation
- Tableau/PowerBI for advanced visualization
- Database storage for complex queries
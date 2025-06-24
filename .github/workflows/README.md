# GitHub Actions Workflows

## Overview
This project uses two main workflows for automated deployment:

### 1. `wildlife-scraper.yml` - Full Scraper & Dashboard
**Purpose**: Complete data collection and dashboard deployment
**Triggers**: 
- Manual (`workflow_dispatch`)
- Weekly schedule (Sundays 6 AM UTC)
- Push to main (dashboard files only)

**Process**:
1. Scrapes Texas A&M Wildlife & Fisheries job board
2. Classifies positions using AI (Big 10 universities, disciplines)
3. Generates analytics and trends
4. Archives data with timestamps
5. Deploys updated dashboard

### 2. `deploy-dashboard.yml` - Dashboard Only
**Purpose**: Quick dashboard deployment (no data collection)
**Triggers**:
- Manual (`workflow_dispatch`) 
- Push to main (dashboard files only)

**Process**:
1. Deploys current dashboard files to GitHub Pages
2. Uses existing data in `/dashboard` folder

## Deployment Method
Both workflows use `peaceiris/actions-gh-pages@v4` for consistent deployment to the `gh-pages` branch.

## GitHub Pages Configuration
- **Source**: Deploy from a branch
- **Branch**: `gh-pages` 
- **Folder**: `/ (root)`

## Manual Triggers
All workflows support manual execution via the Actions tab "Run workflow" button.

## Troubleshooting
- If workflows don't show manual trigger: refresh Actions page after ~1 minute
- If deployment fails: check that GitHub Pages is configured for `gh-pages` branch
- For data issues: run `wildlife-scraper.yml` to regenerate all files
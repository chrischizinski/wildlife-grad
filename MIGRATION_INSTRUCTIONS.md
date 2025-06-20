# Migration Instructions: Moving to wildlife-grad Repository

## 🎯 Overview
This guide will help you move the complete wildlife jobs scraper from the dotfiles subdirectory to your dedicated `wildlife-grad` repository.

## 📋 Prerequisites
1. Make sure `wildlife-grad` repository is public
2. Have git installed and GitHub authentication set up

## 🚀 Step-by-Step Migration

### Step 1: Navigate to Your Dev Directory
```bash
cd /Users/cchizinski2/Dev
```

### Step 2: Clone the Wildlife-Grad Repository
```bash
git clone https://github.com/chrischizinski/wildlife-grad.git
cd wildlife-grad
```

### Step 3: Copy All Files
Copy all files from the current scraper directory:

```bash
# Copy main Python files
cp ../WildlifeJobsBoardScrape/wildlife_job_scraper.py .
cp ../WildlifeJobsBoardScrape/cli.py .
cp ../WildlifeJobsBoardScrape/requirements.txt .

# Copy configuration files
cp ../WildlifeJobsBoardScrape/.env.example .
cp ../WildlifeJobsBoardScrape/CLAUDE.md .
cp ../WildlifeJobsBoardScrape/README.md .
cp ../WildlifeJobsBoardScrape/SETUP_GUIDE.md .

# Copy directories
cp -r ../WildlifeJobsBoardScrape/.github .
cp -r ../WildlifeJobsBoardScrape/dashboard .
cp -r ../WildlifeJobsBoardScrape/scripts .
cp -r ../WildlifeJobsBoardScrape/tests .

# Copy any existing data (optional)
mkdir -p data
cp ../WildlifeJobsBoardScrape/graduate_assistantships.* data/ 2>/dev/null || true
```

### Step 4: Set Up Git and Commit
```bash
# Configure git (if not already done)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Commit everything
git commit -m "🚀 Initial setup: Complete wildlife jobs scraper with dashboard

✨ Features:
- Optimized web scraper with Pydantic validation
- GitHub Actions automation (weekly scraping)
- Interactive dashboard with Chart.js visualizations
- Professional CLI interface with customizable options
- Comprehensive unit testing with pytest
- Type hints and Google-style docstrings throughout

🔧 Components:
- wildlife_job_scraper.py: Main scraper class
- cli.py: Command-line interface
- dashboard/: Interactive web dashboard
- .github/workflows/: Automated scraping workflows
- tests/: Comprehensive unit tests

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

### Step 5: Enable GitHub Features
1. Go to `https://github.com/chrischizinski/wildlife-grad`
2. **Enable Actions**: Go to Actions tab → Enable workflows
3. **Enable Pages**: Settings → Pages → Source: "GitHub Actions"

### Step 6: Trigger Initial Scrape
1. Go to Actions tab
2. Find "Initial Setup - Complete Historical Scrape"
3. Click "Run workflow"
4. Configure options:
   - ✅ Scrape all available pages: `true`
   - ✅ Extended search terms: `true`
5. Click "Run workflow"

## 🎯 Expected Results

After migration and first scrape:
- **Repository**: `https://github.com/chrischizinski/wildlife-grad`
- **Dashboard**: `https://chrischizinski.github.io/wildlife-grad/`
- **Data**: Stored in `data/` directory
- **Automation**: Weekly scraping every Sunday

## 🔧 Verification Steps

After migration, verify:
1. ✅ All files are in the new repository
2. ✅ GitHub Actions workflows are detected
3. ✅ Pages deployment is enabled
4. ✅ Initial scrape workflow is available

## 📞 Support
If you encounter any issues during migration, the files are safely backed up in the original location until you're ready to clean up.
#!/bin/bash

# Migration script for wildlife jobs scraper
# Moves all files from current location to wildlife-grad repository

echo "🚀 Wildlife Jobs Scraper Migration Script"
echo "=========================================="

# Check if we're in the right directory
if [[ ! -f "wildlife_job_scraper.py" ]]; then
    echo "❌ Error: Please run this script from the WildlifeJobsBoardScrape directory"
    exit 1
fi

# Set variables
SOURCE_DIR=$(pwd)
TARGET_DIR="../wildlife-grad"

echo "📂 Source: $SOURCE_DIR"
echo "📂 Target: $TARGET_DIR"

# Check if target directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "❌ Error: wildlife-grad directory not found at $TARGET_DIR"
    echo "Please clone the repository first:"
    echo "  cd /Users/cchizinski2/Dev"
    echo "  git clone https://github.com/chrischizinski/wildlife-grad.git"
    exit 1
fi

echo ""
echo "🔄 Copying files..."

# Copy main files
echo "  📄 Copying main Python files..."
cp wildlife_job_scraper.py "$TARGET_DIR/"
cp cli.py "$TARGET_DIR/"
cp requirements.txt "$TARGET_DIR/"

# Copy configuration files
echo "  ⚙️  Copying configuration files..."
cp .env.example "$TARGET_DIR/"
cp CLAUDE.md "$TARGET_DIR/"
cp README.md "$TARGET_DIR/"
cp SETUP_GUIDE.md "$TARGET_DIR/"

# Copy directories
echo "  📁 Copying directories..."
cp -r .github "$TARGET_DIR/"
cp -r dashboard "$TARGET_DIR/"
cp -r scripts "$TARGET_DIR/"
cp -r tests "$TARGET_DIR/"

# Create data directory and copy existing data
echo "  📊 Setting up data directory..."
mkdir -p "$TARGET_DIR/data"
cp graduate_assistantships.* "$TARGET_DIR/data/" 2>/dev/null || echo "    ⚠️  No existing data files to copy"

echo ""
echo "✅ File copying complete!"
echo ""
echo "📋 Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. git add ."
echo "3. git commit -m \"🚀 Initial setup: Complete wildlife jobs scraper\""
echo "4. git push origin main"
echo "5. Enable GitHub Actions and Pages in repository settings"
echo ""
echo "🎯 Your new repository will be at:"
echo "   https://github.com/chrischizinski/wildlife-grad"
echo ""
echo "📊 Your dashboard will be at:"
echo "   https://chrischizinski.github.io/wildlife-grad/"
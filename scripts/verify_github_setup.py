#!/usr/bin/env python3
"""
GitHub Setup Verification Script
Checks that all components are properly configured for the Wildlife Graduate Assistantship scraper
"""

import os
import json
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report status"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False

def check_directory_exists(dir_path, description):
    """Check if a directory exists and report status"""
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (MISSING)")
        return False

def verify_github_setup():
    """Verify complete GitHub setup for wildlife scraper"""
    
    print("🔍 Wildlife Graduate Assistantship Scraper - GitHub Setup Verification")
    print("=" * 70)
    
    all_good = True
    
    # 1. Check GitHub Actions workflow
    print("\n📋 1. GitHub Actions Workflow")
    workflow_path = ".github/workflows/wildlife-scraper.yml"
    if check_file_exists(workflow_path, "Main workflow file"):
        # Check workflow content
        try:
            with open(workflow_path, 'r') as f:
                content = f.read()
                if 'wildlife_job_scraper.py' in content:
                    print("   ✅ Workflow references main scraper")
                else:
                    print("   ❌ Workflow missing scraper reference")
                    all_good = False
                    
                if 'peaceiris/actions-gh-pages' in content:
                    print("   ✅ GitHub Pages deployment configured")
                else:
                    print("   ❌ GitHub Pages deployment missing")
                    all_good = False
        except Exception as e:
            print(f"   ❌ Error reading workflow: {e}")
            all_good = False
    else:
        all_good = False
    
    # 2. Check main scraper file
    print("\n🐍 2. Python Scraper")
    if check_file_exists("wildlife_job_scraper.py", "Main scraper script"):
        # Check for Big 10 classification
        try:
            with open("wildlife_job_scraper.py", 'r') as f:
                content = f.read()
                if 'classify_university' in content:
                    print("   ✅ Big 10 university classification included")
                else:
                    print("   ⚠️ Big 10 classification may be missing")
                    
                if 'is_big10_university' in content:
                    print("   ✅ Big 10 data fields present")
                else:
                    print("   ❌ Big 10 data fields missing")
                    all_good = False
        except Exception as e:
            print(f"   ❌ Error reading scraper: {e}")
            all_good = False
    else:
        all_good = False
    
    # 3. Check requirements
    print("\n📦 3. Python Dependencies")
    if check_file_exists("requirements.txt", "Requirements file"):
        try:
            with open("requirements.txt", 'r') as f:
                reqs = f.read()
                required_packages = ['selenium', 'beautifulsoup4', 'pydantic', 'pandas']
                for pkg in required_packages:
                    if pkg in reqs:
                        print(f"   ✅ {pkg} specified")
                    else:
                        print(f"   ❌ {pkg} missing")
                        all_good = False
        except Exception as e:
            print(f"   ❌ Error reading requirements: {e}")
            all_good = False
    else:
        all_good = False
    
    # 4. Check dashboard files
    print("\n🎨 4. Dashboard Files")
    dashboard_files = [
        ("dashboard/analytics_dashboard.html", "Main dashboard HTML"),
        ("dashboard/analytics_dashboard.js", "Dashboard JavaScript"),
        ("dashboard/analytics-styles.css", "Dashboard styles")
    ]
    
    for file_path, description in dashboard_files:
        if check_file_exists(file_path, description):
            if 'analytics_dashboard.html' in file_path:
                # Check for Big 10 toggle
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if 'big10-toggle' in content:
                            print("   ✅ Big 10 filter toggle present")
                        else:
                            print("   ❌ Big 10 filter toggle missing")
                            all_good = False
                except Exception as e:
                    print(f"   ❌ Error reading dashboard HTML: {e}")
        else:
            all_good = False
    
    # 5. Check data directories
    print("\n📁 5. Directory Structure")
    directories = [
        ("data", "Data directory"),
        ("data/archive", "Archive directory"),
        ("dashboard", "Dashboard directory"),
        ("scripts", "Scripts directory")
    ]
    
    for dir_path, description in directories:
        if not check_directory_exists(dir_path, description):
            all_good = False
    
    # 6. Check support scripts
    print("\n🔧 6. Support Scripts")
    script_files = [
        ("scripts/enhanced_analysis.py", "Enhanced analysis script"),
        ("scripts/enhanced_dashboard_data.py", "Dashboard data generator")
    ]
    
    for file_path, description in script_files:
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"⚠️ {description}: {file_path} (OPTIONAL)")
    
    # 7. Repository checks
    print("\n🏠 7. Repository Configuration")
    if os.path.exists(".git"):
        print("✅ Git repository initialized")
        
        # Check remote origin
        try:
            import subprocess
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                origin = result.stdout.strip()
                print(f"✅ Remote origin: {origin}")
                if 'github.com' in origin:
                    print("✅ GitHub repository detected")
                else:
                    print("⚠️ Non-GitHub remote detected")
            else:
                print("❌ No remote origin configured")
                all_good = False
        except Exception as e:
            print(f"⚠️ Could not check git remote: {e}")
    else:
        print("❌ Not a git repository")
        all_good = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_good:
        print("🎉 ALL CHECKS PASSED! Your GitHub setup is ready.")
        print("\n📋 Next Steps:")
        print("1. Push changes to GitHub: git push origin main")
        print("2. Enable GitHub Pages in repository settings")
        print("3. Test manual workflow trigger in Actions tab")
        print("4. Wait for Sunday 6AM UTC for first automatic run")
    else:
        print("⚠️ SOME ISSUES FOUND - Please fix the items marked with ❌")
        print("\n🔧 Common fixes:")
        print("- Create missing directories: mkdir -p data/archive dashboard scripts")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Commit and push all files to GitHub")
    
    print(f"\n🔗 Expected dashboard URL: https://[USERNAME].github.io/[REPOSITORY]/")
    print("   (Replace [USERNAME] and [REPOSITORY] with your GitHub details)")
    
    return all_good

if __name__ == "__main__":
    success = verify_github_setup()
    sys.exit(0 if success else 1)
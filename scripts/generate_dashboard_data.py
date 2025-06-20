"""
Generate dashboard data from scraped job listings.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from collections import Counter
import re


def load_latest_jobs():
    """Load the latest job data."""
    # Try the current file first
    data_path = Path("data/graduate_assistantships.json")
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback to jobs_latest.json
    data_path = Path("data/jobs_latest.json")
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return []


def extract_degree_types(jobs):
    """Extract degree types from job titles and descriptions."""
    degree_counts = Counter()
    
    for job in jobs:
        title_lower = job['title'].lower()
        tags_lower = job['tags'].lower()
        
        # Check for degree types
        if any(term in title_lower for term in ['phd', 'ph.d', 'doctoral', 'doctorate']):
            degree_counts['PhD'] += 1
        elif any(term in title_lower for term in ['master', 'ms', 'm.s', 'ma', 'm.a']):
            degree_counts['Masters'] += 1
        elif any(term in title_lower for term in ['graduate', 'grad']):
            degree_counts['Graduate'] += 1
        else:
            degree_counts['Unspecified'] += 1
            
    return dict(degree_counts)


def extract_locations(jobs):
    """Extract and count job locations."""
    locations = []
    
    for job in jobs:
        location = job.get('location', 'N/A')
        if location and location != 'N/A':
            # Extract state from location
            state_match = re.search(r'\b([A-Z]{2})\b', location)
            if state_match:
                locations.append(state_match.group(1))
            else:
                locations.append(location)
    
    return dict(Counter(locations))


def extract_salary_ranges(jobs):
    """Extract salary information and categorize."""
    salary_categories = Counter()
    
    for job in jobs:
        salary = job.get('salary', 'N/A')
        if salary and salary != 'N/A':
            salary_lower = salary.lower()
            
            # Extract numeric values
            amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*)', salary)
            if amounts:
                try:
                    amount = int(amounts[0].replace(',', ''))
                    if amount < 20000:
                        salary_categories['Under $20K'] += 1
                    elif amount < 30000:
                        salary_categories['$20K-$30K'] += 1
                    elif amount < 40000:
                        salary_categories['$30K-$40K'] += 1
                    else:
                        salary_categories['$40K+'] += 1
                except ValueError:
                    salary_categories['Unspecified'] += 1
            else:
                salary_categories['Unspecified'] += 1
        else:
            salary_categories['Not Listed'] += 1
    
    return dict(salary_categories)


def extract_research_areas(jobs):
    """Extract research areas from job titles and tags."""
    research_terms = {
        'Wildlife': ['wildlife', 'animal', 'mammal', 'bird', 'species'],
        'Fisheries': ['fish', 'fisheries', 'aquatic', 'marine'],
        'Ecology': ['ecology', 'ecological', 'ecosystem', 'habitat'],
        'Conservation': ['conservation', 'preserve', 'protect', 'restoration'],
        'Genetics': ['genetic', 'genomic', 'dna', 'molecular'],
        'Modeling': ['model', 'modeling', 'statistical', 'analysis'],
        'Field Work': ['field', 'survey', 'monitoring', 'sampling'],
        'GIS/Remote Sensing': ['gis', 'remote sensing', 'spatial', 'mapping']
    }
    
    area_counts = Counter()
    
    for job in jobs:
        title_lower = job['title'].lower()
        tags_lower = job['tags'].lower()
        combined_text = f"{title_lower} {tags_lower}"
        
        for area, terms in research_terms.items():
            if any(term in combined_text for term in terms):
                area_counts[area] += 1
    
    return dict(area_counts)


def generate_dashboard_data():
    """Generate comprehensive dashboard data."""
    jobs = load_latest_jobs()
    
    if not jobs:
        print("No job data found")
        return
    
    # Check if enhanced analysis exists
    enhanced_file = Path("data/enhanced_analysis.json")
    if enhanced_file.exists():
        with open(enhanced_file, 'r', encoding='utf-8') as f:
            enhanced_data = json.load(f)
        
        # Use enhanced analysis data
        stats = {
            'total_jobs': enhanced_data['total_positions'],
            'last_updated': enhanced_data['last_updated'],
            'degree_types': extract_degree_types(jobs),  # Keep original for comparison
            'locations': extract_locations(jobs),
            'salary_ranges': extract_salary_ranges(jobs),
            'research_areas': extract_research_areas(jobs),
            # Add enhanced analytics
            'enhanced_disciplines': enhanced_data['disciplines'],
            'geographic_regions': enhanced_data['geographic_regions'],
            'salary_analysis_lincoln_adjusted': enhanced_data['salary_analysis_lincoln_adjusted'],
            'temporal_trends': enhanced_data['temporal_trends'],
            'merge_stats': enhanced_data['merge_stats']
        }
    else:
        # Fallback to basic analysis
        stats = {
            'total_jobs': len(jobs),
            'last_updated': datetime.now().isoformat(),
            'degree_types': extract_degree_types(jobs),
            'locations': extract_locations(jobs),
            'salary_ranges': extract_salary_ranges(jobs),
            'research_areas': extract_research_areas(jobs),
        }
    
    # Generate time series data (if historical data exists)
    historical_data = []
    data_dir = Path("data")
    
    for file_path in data_dir.glob("jobs_*.json"):
        if file_path.name.startswith("jobs_") and file_path.name.endswith(".json"):
            # Extract date from filename
            date_match = re.search(r'jobs_(\d{4}-\d{2}-\d{2})', file_path.name)
            if date_match:
                date_str = date_match.group(1)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        historical_jobs = json.load(f)
                        historical_data.append({
                            'date': date_str,
                            'job_count': len(historical_jobs)
                        })
                except:
                    continue
    
    # Sort historical data by date
    historical_data.sort(key=lambda x: x['date'])
    stats['historical_data'] = historical_data
    
    # Recent jobs for display
    stats['recent_jobs'] = jobs[:10]  # Show first 10 jobs
    
    # Create dashboard directory
    dashboard_dir = Path("dashboard")
    dashboard_dir.mkdir(exist_ok=True)
    
    # Save dashboard data
    with open(dashboard_dir / "data.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"Dashboard data generated: {len(jobs)} jobs processed")
    print(f"Degree types: {stats['degree_types']}")
    print(f"Top locations: {dict(list(Counter(stats['locations']).most_common(5)))}")


if __name__ == "__main__":
    generate_dashboard_data()
"""
Enhanced dashboard data generation with detailed analytics for disciplines, 
trends, and salary analysis by discipline.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
import re
from typing import Dict, List, Optional


def load_historical_data() -> List[Dict]:
    """Load historical positions data."""
    historical_file = Path("data/historical_positions.json")
    if historical_file.exists():
        with open(historical_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats."""
    if not date_str:
        return None
    
    try:
        # Handle MM/DD/YYYY format
        if '/' in date_str:
            return datetime.strptime(date_str, '%m/%d/%Y')
        # Handle YYYY-MM-DD format
        elif '-' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        pass
    
    return None


def extract_salary_value(salary_str: str) -> Optional[float]:
    """Extract numeric salary value."""
    if not salary_str:
        return None
        
    salary_lower = salary_str.lower()
    
    # Skip non-numeric salaries
    if any(phrase in salary_lower for phrase in [
        'commensurate', 'negotiable', 'competitive', 'none', 'n/a'
    ]):
        return None
    
    # Find monetary amounts
    money_patterns = [
        r'\$?(\d{1,3}(?:,\d{3})+(?:\.\d+)?)',  # $25,000
        r'\$?(\d{4,6}(?:\.\d+)?)',             # $25000
        r'(\d{1,3}(?:\.\d+)?)[kK]',            # 25k
    ]
    
    amounts = []
    for pattern in money_patterns:
        matches = re.findall(pattern, salary_str, re.IGNORECASE)
        for match in matches:
            try:
                clean_num = match.replace(',', '')
                if 'k' in salary_lower:
                    value = float(clean_num) * 1000
                else:
                    value = float(clean_num)
                
                # Convert monthly to annual if detected
                if 'month' in salary_lower and value > 100:
                    value *= 12
                
                if 1000 <= value <= 200000:
                    amounts.append(value)
            except:
                continue
    
    return max(amounts) if amounts else None


def consolidate_discipline(discipline: str) -> str:
    """Map old discipline categories to the 5 consolidated categories."""
    discipline_mapping = {
        # Fisheries Management and Conservation
        'Fisheries Science': 'Fisheries Management and Conservation',
        'Fisheries Management and Conservation': 'Fisheries Management and Conservation',
        
        # Wildlife Management and Conservation  
        'Wildlife Ecology': 'Wildlife Management and Conservation',
        'Wildlife Management and Conservation': 'Wildlife Management and Conservation',
        'Conservation Biology': 'Wildlife Management and Conservation',
        
        # Human Dimensions
        'Human Dimensions': 'Human Dimensions',
        
        # Environmental Science
        'Environmental Science': 'Environmental Science',
        'Quantitative Ecology': 'Environmental Science',
        'Ecosystem Ecology': 'Environmental Science',
        'Ecotoxicology': 'Environmental Science', 
        'Fire Ecology': 'Environmental Science',
        'Climate Science': 'Environmental Science',
        
        # Other
        'Other': 'Other',
        'Genetics/Genomics': 'Other',
        'Non-Graduate': 'Other'  # This should be filtered out by graduate detection
    }
    
    return discipline_mapping.get(discipline, 'Other')


def generate_discipline_analytics(positions: List[Dict]) -> Dict:
    """Generate detailed analytics by discipline using consolidated categories."""
    discipline_data = defaultdict(lambda: {
        'count': 0,
        'salaries': [],
        'monthly_trends': defaultdict(int),
        'positions': []
    })
    
    for pos in positions:
        original_discipline = pos.get('discipline_primary', 'Other')
        # Consolidate to one of the 5 categories
        discipline = consolidate_discipline(original_discipline)
        
        discipline_data[discipline]['count'] += 1
        discipline_data[discipline]['positions'].append(pos)
        
        # Add salary data (Lincoln-adjusted)
        salary_adjusted = pos.get('salary_lincoln_adjusted', 0)
        if salary_adjusted and salary_adjusted > 0:
            discipline_data[discipline]['salaries'].append(salary_adjusted)
        
        # Add to monthly trends
        pub_date = parse_date(pos.get('published_date', ''))
        if pub_date:
            month_key = pub_date.strftime('%Y-%m')
            discipline_data[discipline]['monthly_trends'][month_key] += 1
    
    # Calculate salary statistics for each discipline
    result = {}
    for discipline, data in discipline_data.items():
        salaries = data['salaries']
        salary_stats = {}
        if salaries:
            salary_stats = {
                'count': len(salaries),
                'mean': sum(salaries) / len(salaries),
                'median': sorted(salaries)[len(salaries)//2],
                'min': min(salaries),
                'max': max(salaries),
                'range': max(salaries) - min(salaries)
            }
        
        result[discipline] = {
            'total_positions': data['count'],
            'salary_stats': salary_stats,
            'monthly_trends': dict(data['monthly_trends']),
            'grad_positions': len([p for p in data['positions'] 
                                 if any(tag in p.get('tags', '').lower() 
                                       for tag in ['graduate', 'grad', 'phd', 'master'])])
        }
    
    return result


def generate_time_series_data(positions: List[Dict], timeframes: List[str]) -> Dict:
    """Generate time series data for different timeframes."""
    now = datetime.now()
    timeframe_data = {}
    
    for timeframe in timeframes:
        # Calculate cutoff date
        if timeframe == '1_month':
            cutoff = now - timedelta(days=30)
        elif timeframe == '6_months':
            cutoff = now - timedelta(days=180)
        elif timeframe == '1_year':
            cutoff = now - timedelta(days=365)
        else:
            cutoff = datetime(2020, 1, 1)  # All time
        
        # Filter positions by timeframe
        filtered_positions = []
        for pos in positions:
            pub_date = parse_date(pos.get('published_date', ''))
            if pub_date and pub_date >= cutoff:
                filtered_positions.append(pos)
        
        # Generate monthly counts overall and by discipline
        monthly_counts = defaultdict(int)
        discipline_monthly = defaultdict(lambda: defaultdict(int))
        
        for pos in filtered_positions:
            pub_date = parse_date(pos.get('published_date', ''))
            if pub_date:
                month_key = pub_date.strftime('%Y-%m')
                monthly_counts[month_key] += 1
                
                original_discipline = pos.get('discipline_primary', 'Other')
                # Consolidate to one of the 5 categories
                discipline = consolidate_discipline(original_discipline)
                discipline_monthly[discipline][month_key] += 1
        
        timeframe_data[timeframe] = {
            'total_monthly': dict(monthly_counts),
            'discipline_monthly': {k: dict(v) for k, v in discipline_monthly.items()},
            'position_count': len(filtered_positions)
        }
    
    return timeframe_data


def generate_export_data(positions: List[Dict]) -> List[Dict]:
    """Generate clean data for CSV export."""
    export_data = []
    
    for pos in positions:
        # Clean and standardize data for export
        original_discipline_primary = pos.get('discipline_primary', '')
        original_discipline_secondary = pos.get('discipline_secondary', '')
        
        clean_pos = {
            'title': pos.get('title', ''),
            'organization': pos.get('organization', ''),
            'location': pos.get('location', ''),
            'discipline_primary': consolidate_discipline(original_discipline_primary),
            'discipline_secondary': consolidate_discipline(original_discipline_secondary) if original_discipline_secondary else '',
            'salary_original': pos.get('salary', ''),
            'salary_lincoln_adjusted': pos.get('salary_lincoln_adjusted', ''),
            'cost_of_living_index': pos.get('cost_of_living_index', ''),
            'geographic_region': pos.get('geographic_region', ''),
            'starting_date': pos.get('starting_date', ''),
            'published_date': pos.get('published_date', ''),
            'tags': pos.get('tags', ''),
            'first_seen': pos.get('first_seen', ''),
            'last_updated': pos.get('last_updated', '')
        }
        export_data.append(clean_pos)
    
    return export_data


def main():
    """Generate enhanced dashboard data."""
    # Load historical data
    positions = load_historical_data()
    
    if not positions:
        print("No historical data found. Run enhanced analysis first.")
        return
    
    print(f"Processing {len(positions)} positions for enhanced dashboard...")
    
    # Generate discipline analytics
    discipline_analytics = generate_discipline_analytics(positions)
    
    # Generate time series data for different timeframes
    timeframes = ['1_month', '6_months', '1_year', 'all_time']
    time_series = generate_time_series_data(positions, timeframes)
    
    # Generate export data
    export_data = generate_export_data(positions)
    
    # Get top disciplines for dashboard
    top_disciplines = sorted(discipline_analytics.items(), 
                           key=lambda x: x[1]['total_positions'], 
                           reverse=True)[:10]
    
    # Create comprehensive dashboard data
    dashboard_data = {
        'last_updated': datetime.now().isoformat(),
        'total_positions': len(positions),
        'overview': {
            'total_disciplines': len(discipline_analytics),
            'positions_with_salaries': len([p for p in positions if p.get('salary_lincoln_adjusted', 0) > 0]),
            'graduate_positions': len([p for p in positions if any(tag in p.get('tags', '').lower() 
                                     for tag in ['graduate', 'grad', 'phd', 'master'])]),
            'recent_positions_30_days': time_series['1_month']['position_count']
        },
        'discipline_analytics': discipline_analytics,
        'time_series': time_series,
        'top_disciplines': {name: data for name, data in top_disciplines},
        'geographic_summary': {
            region: len([p for p in positions if p.get('geographic_region') == region])
            for region in set(p.get('geographic_region', 'Other') for p in positions)
        },
        'salary_overview': {
            'positions_with_salary': len([p for p in positions if p.get('salary_lincoln_adjusted', 0) > 0]),
            'average_lincoln_adjusted': sum(p.get('salary_lincoln_adjusted', 0) for p in positions if p.get('salary_lincoln_adjusted', 0) > 0) / 
                                       len([p for p in positions if p.get('salary_lincoln_adjusted', 0) > 0]) if 
                                       len([p for p in positions if p.get('salary_lincoln_adjusted', 0) > 0]) > 0 else 0
        }
    }
    
    # Save dashboard data
    dashboard_dir = Path("dashboard")
    dashboard_dir.mkdir(exist_ok=True)
    
    with open(dashboard_dir / "enhanced_data.json", 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    
    # Save export data as JSON (will be converted to CSV by dashboard)
    with open(dashboard_dir / "export_data.json", 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print("Enhanced dashboard data generated successfully!")
    print(f"- Total positions: {len(positions)}")
    print(f"- Disciplines analyzed: {len(discipline_analytics)}")
    print(f"- Top discipline: {top_disciplines[0][0]} ({top_disciplines[0][1]['total_positions']} positions)")
    print(f"- Positions with salaries: {dashboard_data['overview']['positions_with_salaries']}")
    print(f"- Average salary (Lincoln-adjusted): ${dashboard_data['salary_overview']['average_lincoln_adjusted']:.0f}")


if __name__ == "__main__":
    main()
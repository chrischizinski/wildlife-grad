#!/usr/bin/env python3
"""
Comprehensive Dashboard Data Generator

Generates analytics data from the merged comprehensive dataset for the wildlife
graduate assistantships dashboard.
"""

import json
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict, Counter
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveDashboardGenerator:
    """Generate dashboard analytics from comprehensive dataset"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.output_file = self.data_dir / "enhanced_data.json"
        
    def load_positions(self) -> List[Dict]:
        """Load positions from the comprehensive dataset"""
        historical_file = self.data_dir / "historical_positions.json"
        
        if not historical_file.exists():
            raise FileNotFoundError(f"Historical positions file not found: {historical_file}")
            
        with open(historical_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        positions = data.get('positions', [])
        logger.info(f"Loaded {len(positions)} positions from comprehensive dataset")
        return positions
    
    def extract_salary_info(self, position: Dict) -> Dict:
        """Extract and normalize salary information"""
        salary_range = position.get('salary_range', '').strip()
        if not salary_range or salary_range.lower() in ['', 'commensurate', 'negotiable', 'commensurate / negotiable']:
            return {"min_salary": None, "max_salary": None, "salary_text": salary_range}
        
        # Extract numeric values
        numbers = re.findall(r'[\d,]+(?:\.\d+)?', salary_range.replace(',', ''))
        
        try:
            if len(numbers) >= 2:
                min_sal = float(numbers[0].replace(',', ''))
                max_sal = float(numbers[1].replace(',', ''))
                
                # Handle monthly to annual conversion
                if 'month' in salary_range.lower():
                    min_sal *= 12
                    max_sal *= 12
                    
                # Handle k notation
                if 'k' in salary_range.lower():
                    min_sal *= 1000
                    max_sal *= 1000
                    
                return {
                    "min_salary": min_sal,
                    "max_salary": max_sal,
                    "avg_salary": (min_sal + max_sal) / 2,
                    "salary_text": salary_range
                }
            elif len(numbers) == 1:
                salary = float(numbers[0].replace(',', ''))
                
                if 'month' in salary_range.lower():
                    salary *= 12
                if 'k' in salary_range.lower():
                    salary *= 1000
                    
                return {
                    "min_salary": salary,
                    "max_salary": salary,
                    "avg_salary": salary,
                    "salary_text": salary_range
                }
        except (ValueError, IndexError):
            pass
            
        return {"min_salary": None, "max_salary": None, "salary_text": salary_range}
    
    def classify_position_type(self, position: Dict) -> str:
        """Classify position as graduate or professional"""
        title = position.get('title', '').lower()
        description = position.get('description', '').lower()
        
        # Graduate indicators
        graduate_keywords = [
            'graduate', 'master', 'ms', 'm.s.', 'phd', 'ph.d.', 'doctoral',
            'assistantship', 'fellowship', 'student', 'thesis', 'dissertation'
        ]
        
        text_to_check = f"{title} {description}"
        
        for keyword in graduate_keywords:
            if keyword in text_to_check:
                return "Graduate"
                
        return "Professional"
    
    def extract_location_info(self, position: Dict) -> Dict:
        """Extract and clean location information"""
        location = position.get('location', '').strip()
        
        # Extract state/country
        state_match = re.search(r',\s*([A-Z]{2})\s*$', location)
        state = state_match.group(1) if state_match else None
        
        # Clean location for city extraction
        cleaned_location = re.sub(r'\([^)]*\)', '', location)  # Remove parentheses
        cleaned_location = re.sub(r',\s*[A-Z]{2}\s*$', '', cleaned_location)  # Remove state
        
        city_parts = cleaned_location.split(',')
        city = city_parts[0].strip() if city_parts else location
        
        return {
            "full_location": location,
            "city": city,
            "state": state,
            "cleaned_location": cleaned_location.strip()
        }
    
    def classify_discipline(self, position: Dict) -> str:
        """Classify position by discipline"""
        title = position.get('title', '').lower()
        description = position.get('description', '').lower()
        
        text_to_check = f"{title} {description}"
        
        # Discipline classification keywords
        disciplines = {
            "Wildlife Management": ["wildlife", "deer", "elk", "bear", "ungulate", "mammal", "carnivore"],
            "Fisheries": ["fish", "aquatic", "stream", "river", "salmon", "trout", "fisheries"],
            "Ecology": ["ecology", "ecosystem", "community", "population", "biodiversity"],
            "Conservation": ["conservation", "restoration", "habitat", "preserve", "protected"],
            "Environmental Science": ["environment", "pollution", "contamination", "climate"],
            "Forestry": ["forest", "tree", "timber", "silviculture", "woodland"],
            "Marine Science": ["marine", "ocean", "coastal", "reef", "sea"],
            "Ornithology": ["bird", "avian", "waterfowl", "raptor", "migration"],
            "Botany": ["plant", "vegetation", "flora", "botanical"],
            "Human Dimensions": ["human", "social", "stakeholder", "community", "outreach"]
        }
        
        for discipline, keywords in disciplines.items():
            if any(keyword in text_to_check for keyword in keywords):
                return discipline
                
        return "Other"
    
    def generate_analytics(self, positions: List[Dict]) -> Dict:
        """Generate comprehensive analytics"""
        logger.info("Generating comprehensive analytics...")
        
        # Basic statistics
        total_positions = len(positions)
        
        # Process each position
        processed_positions = []
        salary_data = []
        location_stats = defaultdict(int)
        discipline_stats = defaultdict(int)
        organization_stats = defaultdict(int)
        position_type_stats = defaultdict(int)
        monthly_stats = defaultdict(int)
        
        for position in positions:
            # Extract salary information
            salary_info = self.extract_salary_info(position)
            if salary_info.get('avg_salary'):
                salary_data.append(salary_info['avg_salary'])
            
            # Extract location information
            location_info = self.extract_location_info(position)
            if location_info['state']:
                location_stats[location_info['state']] += 1
            
            # Classify discipline
            discipline = self.classify_discipline(position)
            discipline_stats[discipline] += 1
            
            # Classify position type
            pos_type = self.classify_position_type(position)
            position_type_stats[pos_type] += 1
            
            # Organization stats
            org = position.get('organization', 'Unknown')
            organization_stats[org] += 1
            
            # Monthly posting trends
            published_date = position.get('published_date', '')
            if published_date:
                try:
                    # Try to parse date and extract month
                    month_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', published_date)
                    if month_match:
                        month, day, year = month_match.groups()
                        month_key = f"{year}-{month.zfill(2)}"
                        monthly_stats[month_key] += 1
                except:
                    pass
            
            # Add processed information to position
            enhanced_position = position.copy()
            enhanced_position.update({
                'salary_info': salary_info,
                'location_info': location_info,
                'discipline': discipline,
                'position_type': pos_type
            })
            processed_positions.append(enhanced_position)
        
        # Calculate salary statistics
        salary_stats = {}
        if salary_data:
            salary_stats = {
                "count": len(salary_data),
                "min": min(salary_data),
                "max": max(salary_data),
                "mean": statistics.mean(salary_data),
                "median": statistics.median(salary_data),
                "std_dev": statistics.stdev(salary_data) if len(salary_data) > 1 else 0
            }
        
        # Create analytics summary
        analytics = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_positions": total_positions,
                "positions_with_salary": len(salary_data),
                "data_completeness": len(salary_data) / total_positions if total_positions > 0 else 0
            },
            "summary_stats": {
                "total_positions": total_positions,
                "graduate_positions": position_type_stats.get("Graduate", 0),
                "professional_positions": position_type_stats.get("Professional", 0),
                "positions_with_salary": len(salary_data),
                "salary_statistics": salary_stats
            },
            "breakdowns": {
                "by_discipline": dict(discipline_stats),
                "by_state": dict(location_stats),
                "by_organization_type": self._categorize_organizations(organization_stats),
                "by_position_type": dict(position_type_stats),
                "monthly_trends": dict(monthly_stats)
            },
            "top_lists": {
                "top_states": dict(Counter(location_stats).most_common(10)),
                "top_organizations": dict(Counter(organization_stats).most_common(15)),
                "top_disciplines": dict(Counter(discipline_stats).most_common(10))
            },
            "positions": processed_positions
        }
        
        return analytics
    
    def _categorize_organizations(self, org_stats: Dict) -> Dict:
        """Categorize organizations by type"""
        categories = {
            "State Universities": 0,
            "Federal Agencies": 0,
            "Private Organizations": 0,
            "Non-Profit Organizations": 0,
            "Other": 0
        }
        
        for org, count in org_stats.items():
            org_lower = org.lower()
            
            if "(state)" in org_lower or "university" in org_lower or "college" in org_lower:
                categories["State Universities"] += count
            elif "(federal)" in org_lower or "usgs" in org_lower or "forest service" in org_lower:
                categories["Federal Agencies"] += count
            elif "(private)" in org_lower or "company" in org_lower or "corporation" in org_lower:
                categories["Private Organizations"] += count
            elif "foundation" in org_lower or "society" in org_lower or "trust" in org_lower:
                categories["Non-Profit Organizations"] += count
            else:
                categories["Other"] += count
        
        return categories
    
    def save_analytics(self, analytics: Dict) -> None:
        """Save analytics to dashboard data file"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analytics saved to {self.output_file}")
        
        # Print summary
        metadata = analytics['metadata']
        summary = analytics['summary_stats']
        
        print(f"""
📊 Dashboard Analytics Generated Successfully!

📈 Dataset Overview:
├─ Total positions analyzed: {metadata['total_positions']:,}
├─ Positions with salary data: {metadata['positions_with_salary']:,}
├─ Data completeness: {metadata['data_completeness']:.1%}
└─ Generated at: {metadata['generated_at']}

🎓 Position Breakdown:
├─ Graduate positions: {summary['graduate_positions']:,}
├─ Professional positions: {summary['professional_positions']:,}
└─ Graduate ratio: {summary['graduate_positions'] / metadata['total_positions']:.1%}

💰 Salary Analysis:
├─ Positions with salary: {summary['positions_with_salary']:,}
├─ Average salary: ${summary['salary_statistics'].get('mean', 0):,.0f}
├─ Median salary: ${summary['salary_statistics'].get('median', 0):,.0f}
└─ Salary range: ${summary['salary_statistics'].get('min', 0):,.0f} - ${summary['salary_statistics'].get('max', 0):,.0f}

📁 Output file: {self.output_file}
        """)

def main():
    """Main execution function"""
    generator = ComprehensiveDashboardGenerator()
    
    try:
        # Load comprehensive dataset
        positions = generator.load_positions()
        
        # Generate analytics
        analytics = generator.generate_analytics(positions)
        
        # Save to dashboard data file
        generator.save_analytics(analytics)
        
        logger.info("✅ Dashboard data generation completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Dashboard generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
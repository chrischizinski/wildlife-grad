#!/usr/bin/env python3
"""
Intelligent Data Merger for Wildlife Graduate Opportunities

This script merges new comprehensive data with existing historical data:
1. Preserves all historical positions (no data loss)
2. Updates existing positions with enhanced data fields
3. Adds new positions discovered in the latest scrape
4. Creates timestamped backups before making changes
5. Provides detailed reporting on merge results
"""

import json
import hashlib
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_merger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MergeStats:
    """Statistics for the merge operation"""
    historical_positions: int = 0
    new_positions_added: int = 0
    positions_updated: int = 0
    positions_enhanced: int = 0
    positions_preserved: int = 0
    total_final_positions: int = 0
    
    def summary(self) -> str:
        return f"""
📊 Data Merge Summary:
├─ Historical positions preserved: {self.historical_positions}
├─ New positions added: {self.new_positions_added}  
├─ Existing positions updated: {self.positions_updated}
├─ Positions enhanced with better data: {self.positions_enhanced}
├─ Positions preserved as-is: {self.positions_preserved}
└─ Total final dataset: {self.total_final_positions}
"""

class IntelligentDataMerger:
    """Intelligent merger that preserves historical data while enhancing with new information"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.archive_dir = self.data_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
    def generate_position_hash(self, position: Dict) -> str:
        """Generate consistent hash for position identification"""
        # Use title, organization, and location for matching
        title = position.get('title', '').strip().lower()
        org = position.get('organization', '').strip().lower()
        location = position.get('location', '').strip().lower()
        
        # Clean up common variations
        title = title.replace('–', '-').replace('—', '-')
        org = org.replace('(state)', '').replace('(federal)', '').replace('(private)', '').strip()
        
        hash_string = f"{title}|{org}|{location}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def calculate_data_completeness(self, position: Dict) -> float:
        """Calculate data completeness score for a position"""
        fields_to_check = [
            'title', 'organization', 'location', 'salary_range',
            'application_deadline', 'published_date', 'starting_date',
            'hours_per_week', 'education_required', 'experience_required',
            'description', 'job_id', 'url'
        ]
        
        filled_fields = 0
        for field in fields_to_check:
            value = position.get(field, '')
            if isinstance(value, str) and value.strip():
                filled_fields += 1
            elif isinstance(value, list) and value:
                filled_fields += 1
        
        return filled_fields / len(fields_to_check)
    
    def is_better_data(self, new_position: Dict, existing_position: Dict) -> bool:
        """Determine if new position has better data than existing"""
        new_score = self.calculate_data_completeness(new_position)
        existing_score = self.calculate_data_completeness(existing_position)
        
        # Consider new data better if:
        # 1. Significantly more complete (>10% improvement)
        # 2. Has newer scraping timestamp
        # 3. Has structured fields vs unstructured description
        
        if new_score > existing_score + 0.1:  # 10% improvement threshold
            return True
            
        # Check for structured vs unstructured data
        structured_fields = ['salary_range', 'application_deadline', 'published_date', 
                           'starting_date', 'hours_per_week', 'education_required']
        
        new_structured = sum(1 for field in structured_fields 
                           if new_position.get(field, '').strip())
        existing_structured = sum(1 for field in structured_fields 
                                if existing_position.get(field, '').strip())
        
        if new_structured > existing_structured:
            return True
            
        return False
    
    def merge_positions(self, new_position: Dict, existing_position: Dict) -> Dict:
        """Intelligently merge two position records"""
        merged = existing_position.copy()
        
        # Always preserve original discovery timestamps
        if 'first_seen' in existing_position:
            merged['first_seen'] = existing_position['first_seen']
        
        # Update with new data if better
        if self.is_better_data(new_position, existing_position):
            # Update all fields from new position
            for key, value in new_position.items():
                if key not in ['first_seen']:  # Don't overwrite first_seen
                    merged[key] = value
            
            # Mark as enhanced
            merged['data_enhanced'] = True
            merged['enhanced_at'] = datetime.now(timezone.utc).isoformat()
        else:
            # Keep existing data but update last_seen
            merged['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        return merged
    
    def load_historical_data(self) -> Dict[str, Dict]:
        """Load existing historical positions"""
        historical_file = self.data_dir / "historical_positions.json"
        verified_file = self.data_dir / "verified_graduate_assistantships.json"
        
        historical_positions = {}
        
        # Load from historical file
        if historical_file.exists():
            logger.info(f"Loading historical data from {historical_file}")
            with open(historical_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                positions = data.get('positions', []) if isinstance(data, dict) else data
                
                for position in positions:
                    pos_hash = self.generate_position_hash(position)
                    historical_positions[pos_hash] = position
                    
        # Also load verified assistantships 
        if verified_file.exists():
            logger.info(f"Loading verified assistantships from {verified_file}")
            with open(verified_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                positions = data.get('positions', []) if isinstance(data, dict) else data
                
                for position in positions:
                    pos_hash = self.generate_position_hash(position)
                    if pos_hash not in historical_positions:
                        historical_positions[pos_hash] = position
                        
        logger.info(f"Loaded {len(historical_positions)} historical positions")
        return historical_positions
    
    def load_new_data(self, new_data_file: str) -> Dict[str, Dict]:
        """Load new comprehensive data"""
        new_file = Path(new_data_file)
        if not new_file.exists():
            raise FileNotFoundError(f"New data file not found: {new_data_file}")
            
        logger.info(f"Loading new data from {new_file}")
        with open(new_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        new_positions = {}
        jobs = data.get('jobs', [])
        
        for position in jobs:
            pos_hash = self.generate_position_hash(position)
            new_positions[pos_hash] = position
            
        logger.info(f"Loaded {len(new_positions)} new positions")
        return new_positions
    
    def create_backup(self) -> None:
        """Create timestamped backup of current data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.archive_dir / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        files_to_backup = [
            "historical_positions.json",
            "verified_graduate_assistantships.json"
        ]
        
        for filename in files_to_backup:
            source_file = self.data_dir / filename
            if source_file.exists():
                backup_file = backup_dir / filename
                shutil.copy2(source_file, backup_file)
                logger.info(f"Backed up {filename} to {backup_file}")
    
    def merge_data(self, new_data_file: str) -> MergeStats:
        """Main merge operation"""
        stats = MergeStats()
        
        # Create backup first
        self.create_backup()
        
        # Load existing and new data
        historical_positions = self.load_historical_data()
        new_positions = self.load_new_data(new_data_file)
        
        stats.historical_positions = len(historical_positions)
        
        # Merge data
        merged_positions = {}
        updated_hashes = set()
        
        # Start with all historical positions
        for pos_hash, position in historical_positions.items():
            merged_positions[pos_hash] = position
            stats.positions_preserved += 1
        
        # Process new positions
        for pos_hash, new_position in new_positions.items():
            if pos_hash in historical_positions:
                # Position exists - merge intelligently
                existing_position = historical_positions[pos_hash]
                merged_position = self.merge_positions(new_position, existing_position)
                merged_positions[pos_hash] = merged_position
                updated_hashes.add(pos_hash)
                
                if merged_position.get('data_enhanced'):
                    stats.positions_enhanced += 1
                stats.positions_updated += 1
                stats.positions_preserved -= 1  # No longer just preserved
            else:
                # New position - add it
                new_position['first_seen'] = datetime.now(timezone.utc).isoformat()
                merged_positions[pos_hash] = new_position
                stats.new_positions_added += 1
        
        stats.total_final_positions = len(merged_positions)
        
        # Save merged data
        self._save_merged_data(merged_positions, stats)
        
        return stats
    
    def _save_merged_data(self, merged_positions: Dict[str, Dict], stats: MergeStats) -> None:
        """Save the merged dataset"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Convert to list format
        positions_list = list(merged_positions.values())
        
        # Create metadata
        metadata = {
            "merge_timestamp": timestamp,
            "total_positions": len(positions_list),
            "merge_stats": {
                "historical_preserved": stats.historical_positions,
                "new_added": stats.new_positions_added,
                "updated": stats.positions_updated,
                "enhanced": stats.positions_enhanced,
                "preserved": stats.positions_preserved
            },
            "data_sources": [
                "historical_positions.json",
                "verified_graduate_assistantships.json", 
                "latest_comprehensive_scrape"
            ]
        }
        
        # Save as comprehensive historical dataset
        output_data = {
            "metadata": metadata,
            "positions": positions_list
        }
        
        # Save to historical positions file
        historical_file = self.data_dir / "historical_positions.json"
        with open(historical_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(positions_list)} positions to {historical_file}")
        
        # Also create timestamped archive
        archive_file = self.archive_dir / f"merged_positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Archived merged data to {archive_file}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent Data Merger for Wildlife Graduate Opportunities")
    parser.add_argument("new_data_file", help="Path to new comprehensive data file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    merger = IntelligentDataMerger()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        # TODO: Implement dry run logic
        return
    
    try:
        stats = merger.merge_data(args.new_data_file)
        print(stats.summary())
        
        logger.info("✅ Data merge completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Merge failed: {e}")
        raise

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test the full scraper with just a few jobs to verify it works
"""

import json
import logging
from pathlib import Path
from wildlife_job_scraper import ScraperConfig, WildlifeJobScraper

def test_sample_scraper():
    """Test scraper with limited jobs"""
    
    # Configure for testing
    config = ScraperConfig()
    config.headless = True  # Run in background
    config.min_delay = 0.5  # Faster for testing
    config.max_delay = 1.0
    
    scraper = WildlifeJobScraper(config)
    
    try:
        print("Starting test scrape (first page only)...")
        
        # Setup driver and navigate
        scraper.driver = scraper.setup_driver()
        scraper.driver.get(config.base_url)
        
        # Setup page
        scraper.set_page_size()
        scraper.driver.execute_script("window.scrollTo(0, 0);")
        scraper.enter_search_keywords()
        
        # Extract just first 5 jobs for testing
        all_jobs = scraper.extract_jobs_from_page()[:5]  # Limit to 5 jobs
        print(f"Extracted {len(all_jobs)} jobs for testing")
        
        # Process each job with detailed extraction
        enhanced_jobs = []
        for i, job in enumerate(all_jobs):
            print(f"\nProcessing job {i+1}/{len(all_jobs)}: {job.title}")
            
            try:
                # Extract detailed information
                enhanced_job = scraper.extract_detailed_job_info(job)
                print(f"  Description length: {len(enhanced_job.description)} chars")
                
                # Classify position type
                classified_job = scraper.classify_graduate_position(enhanced_job)
                print(f"  Classification: {classified_job.position_type} (confidence: {classified_job.grad_confidence:.3f})")
                print(f"  Is graduate: {classified_job.is_graduate_position}")
                
                # Classify discipline
                disciplined_job = scraper.classify_discipline(classified_job)
                print(f"  Discipline: {disciplined_job.discipline} (confidence: {disciplined_job.discipline_confidence:.3f})")
                if disciplined_job.discipline_keywords:
                    print(f"  Keywords: {', '.join(disciplined_job.discipline_keywords[:3])}")
                
                # Classify university
                final_job = scraper.classify_university(disciplined_job)
                print(f"  Big 10 University: {final_job.is_big10_university}")
                if final_job.university_name:
                    print(f"  University: {final_job.university_name}")
                
                enhanced_jobs.append(final_job)
                
            except Exception as e:
                print(f"  ❌ Error processing: {e}")
                enhanced_jobs.append(job)
        
        # Summary
        total_jobs = len(enhanced_jobs)
        graduate_jobs = sum(1 for job in enhanced_jobs if job.is_graduate_position)
        high_confidence = sum(1 for job in enhanced_jobs if job.grad_confidence >= 0.8)
        
        print(f"\n{'='*50}")
        print(f"TEST RESULTS:")
        print(f"Total positions processed: {total_jobs}")
        print(f"Graduate assistantships identified: {graduate_jobs}")
        print(f"High confidence classifications: {high_confidence}")
        
        # Show breakdowns
        position_types = {}
        disciplines = {}
        big10_count = 0
        big10_universities = {}
        
        for job in enhanced_jobs:
            pos_type = job.position_type
            position_types[pos_type] = position_types.get(pos_type, 0) + 1
            
            if hasattr(job, 'discipline'):
                discipline = job.discipline
                disciplines[discipline] = disciplines.get(discipline, 0) + 1
                
            if hasattr(job, 'is_big10_university') and job.is_big10_university:
                big10_count += 1
                if job.university_name:
                    big10_universities[job.university_name] = big10_universities.get(job.university_name, 0) + 1
        
        print(f"\nPosition Type Breakdown:")
        for pos_type, count in sorted(position_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pos_type}: {count}")
            
        print(f"\nDiscipline Breakdown:")
        for discipline, count in sorted(disciplines.items(), key=lambda x: x[1], reverse=True):
            print(f"  {discipline}: {count}")
            
        print(f"\nUniversity Classification:")
        print(f"  Big 10 Universities: {big10_count}")
        print(f"  Non-Big 10: {total_jobs - big10_count}")
        
        if big10_universities:
            print(f"\nBig 10 Universities Found:")
            for university, count in sorted(big10_universities.items(), key=lambda x: x[1], reverse=True):
                print(f"  {university}: {count}")
            
        # Save test results
        test_output = Path("test_sample_results.json")
        jobs_data = [job.model_dump() if hasattr(job, 'model_dump') else job.dict() for job in enhanced_jobs]
        
        with open(test_output, "w", encoding="utf-8") as f:
            json.dump(jobs_data, f, indent=2, ensure_ascii=False)
            
        print(f"\nTest results saved to: {test_output}")
        
        return enhanced_jobs
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    # Reduce logging for cleaner output
    logging.getLogger().setLevel(logging.WARNING)
    
    test_sample_scraper()
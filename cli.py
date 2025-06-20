"""
Command-line interface for the Wildlife Job Scraper.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from wildlife_job_scraper import ScraperConfig, WildlifeJobScraper


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Scrape wildlife job listings from Texas A&M job board",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--url",
        default="https://jobs.rwfm.tamu.edu/search/",
        help="Base URL for job search"
    )
    
    parser.add_argument(
        "--keywords",
        default="(Master) OR (PhD) OR (Graduate)",
        help="Search keywords for job filtering"
    )
    
    parser.add_argument(
        "--extended-search",
        action="store_true",
        help="Use extended search terms for comprehensive results"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory for scraped data"
    )
    
    parser.add_argument(
        "--json-file",
        default="graduate_assistantships.json",
        help="JSON output filename"
    )
    
    parser.add_argument(
        "--csv-file",
        default="graduate_assistantships.csv",
        help="CSV output filename"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode"
    )
    
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Run browser with GUI (useful for debugging)"
    )
    
    parser.add_argument(
        "--min-delay",
        type=float,
        default=2.0,
        help="Minimum delay between actions (seconds)"
    )
    
    parser.add_argument(
        "--max-delay",
        type=float,
        default=5.0,
        help="Maximum delay between actions (seconds)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Timeout for web elements (seconds)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Use extended search terms if requested
        keywords = args.keywords
        if args.extended_search:
            keywords = "graduate OR master OR masters OR phd OR doctoral OR assistantship OR fellowship OR research"
            print(f"Using extended search terms: {keywords}")
        
        # Create configuration from arguments
        config = ScraperConfig(
            base_url=args.url,
            keywords=keywords,
            output_dir=args.output_dir,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            timeout=args.timeout,
            headless=args.headless
        )
        
        # Initialize and run scraper
        scraper = WildlifeJobScraper(config)
        
        print(f"Starting scraper with keywords: {config.keywords}")
        print(f"Output directory: {config.output_dir}")
        print(f"Headless mode: {config.headless}")
        
        jobs = scraper.scrape_all_jobs()
        
        if jobs:
            # Save results
            json_path = scraper.save_jobs_json(jobs, args.json_file)
            csv_path = scraper.save_jobs_csv(jobs, args.csv_file)
            
            print(f"\\nScraping completed successfully!")
            print(f"Found {len(jobs)} job listings")
            print(f"JSON saved to: {json_path}")
            print(f"CSV saved to: {csv_path}")
            
            # Show sample of results
            if args.verbose and jobs:
                print(f"\\nSample job listings:")
                for i, job in enumerate(jobs[:3], 1):
                    print(f"{i}. {job.title} at {job.organization}")
                    
        else:
            print("No job listings found")
            
        return 0
        
    except KeyboardInterrupt:
        print("\\nScraping interrupted by user")
        return 1
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
MedEx Scraper Runner
Run the MedEx medicine scraper to collect data from medex.com.bd
"""

import asyncio
import sys
import argparse
from loguru import logger
from scrapers.medex_scraper import MedExScraper

def setup_logging():
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/medex_scraper.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

def main():
    """Main function to run the MedEx scraper"""
    parser = argparse.ArgumentParser(description="MedEx Medicine Scraper")
    parser.add_argument(
        "--no-resume", 
        action="store_true", 
        help="Start fresh without resuming from previous session"
    )
    parser.add_argument(
        "--headless", 
        action="store_true", 
        help="Run in headless mode (no browser window)"
    )
    parser.add_argument(
        "--test-pages", 
        type=int, 
        default=None,
        help="Limit scraping to specified number of pages for testing"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    logger.info("Starting MedEx scraper...")
    logger.info(f"Arguments: resume={not args.no_resume}, headless={args.headless}")
    
    try:
        # Create scraper instance
        scraper = MedExScraper()
        
        # Modify total pages if testing
        if args.test_pages:
            scraper.total_pages = args.test_pages
            logger.info(f"Testing mode: limiting to {args.test_pages} pages")
        
        # Set headless mode based on argument
        if args.headless:
            from config import Config
            Config.SELENIUM_HEADLESS = True
            logger.info("Running in headless mode")
        
        # Run the scraper
        scraper.scrape_all_medicines(resume=not args.no_resume)
        
        logger.success("Scraping completed successfully!")
        
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
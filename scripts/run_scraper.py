#!/usr/bin/env python3
"""
Standalone script to run the MedEasy scraper
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scrapers.medeasy_scraper import MedEasyScraper
from database.connection import init_db, check_db_connection
from loguru import logger
from config import Config

async def main():
    """Main function to run the scraper"""
    try:
        logger.info("Initializing MedEasy scraper...")
        
        # Initialize database
        init_db()
        
        # Check database connection
        if not check_db_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        # Create scraper instance
        scraper = MedEasyScraper()
        
        # Start scraping
        logger.info("Starting scraping process...")
        await scraper.scrape_all_medicines(resume=True)
        
        logger.info("Scraping completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'scraper' in locals():
            await scraper.close()

if __name__ == "__main__":
    asyncio.run(main()) 
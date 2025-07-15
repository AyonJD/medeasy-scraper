#!/usr/bin/env python3
"""
Standalone script to run the MedEasy scraper locally (without Docker/PostgreSQL)
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scrapers.medeasy_scraper_local import MedEasyScraperLocal
from database.connection_local import init_db, check_db_connection
from loguru import logger
from config_local import Config

async def main():
    """Main function to run the local scraper"""
    try:
        logger.info("Initializing MedEasy scraper (Local)...")
        
        # Initialize database
        init_db()
        
        # Check database connection
        if not check_db_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        # Create scraper instance
        scraper = MedEasyScraperLocal()
        
        # Start scraping
        logger.info("Starting local scraping process...")
        await scraper.scrape_all_medicines(resume=True)
        
        logger.info("Local scraping completed successfully!")
        
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
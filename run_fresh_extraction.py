#!/usr/bin/env python3
"""
Script to run fresh extraction and test hardcoded category IDs
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.medeasy_scraper import MedEasyScraper
from database.connection_local import SessionLocal
from database.models import Medicine
import requests
from loguru import logger

async def run_fresh_extraction():
    """Run fresh extraction and verify category IDs"""
    
    logger.info("Starting fresh extraction with hardcoded category IDs...")
    
    # Create scraper instance
    scraper = MedEasyScraper()
    
    try:
        # Run the scraper
        await scraper.scrape_all_medicines(resume=False)
        
        logger.info("Extraction completed!")
        
        # Check results in database
        db = SessionLocal()
        try:
            total_medicines = db.query(Medicine).count()
            logger.info(f"Total medicines extracted: {total_medicines}")
            
            # Check medicines with categories
            medicines_with_categories = db.query(Medicine).filter(Medicine.category_id.isnot(None)).count()
            logger.info(f"Medicines with categories: {medicines_with_categories}")
            
            # Show sample medicines with their categories
            sample_medicines = db.query(Medicine).filter(Medicine.category_id.isnot(None)).limit(5).all()
            logger.info("Sample medicines with categories:")
            for medicine in sample_medicines:
                logger.info(f"  - {medicine.name} (ID: {medicine.id}, Category: {medicine.category_id})")
                
        finally:
            db.close()
        
        # Test API response
        logger.info("Testing API response...")
        response = requests.get('http://localhost:8000/medicines?skip=0&limit=10')
        data = response.json()
        
        logger.info(f"API Response - Total: {data['total']}")
        logger.info("Sample medicines from API:")
        for medicine in data['medicines'][:5]:
            logger.info(f"  - {medicine['name']} (Category: {medicine['category']})")
        
        # Test category filtering
        logger.info("Testing category filtering...")
        for category_id in [1, 2, 3, 11]:  # Test a few categories
            response = requests.get(f'http://localhost:8000/medicines?category={category_id}')
            data = response.json()
            logger.info(f"Category {category_id}: {data['total']} medicines")
            
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(run_fresh_extraction()) 
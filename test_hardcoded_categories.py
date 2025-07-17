#!/usr/bin/env python3
"""
Test script to verify hardcoded category IDs are working correctly
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.medeasy_scraper import MedEasyScraper
from database.connection_local import SessionLocal
from database.models import Medicine

async def test_hardcoded_categories():
    """Test that medicines are saved with correct hardcoded category IDs"""
    
    print("Testing hardcoded category IDs...")
    
    # Create scraper instance
    scraper = MedEasyScraper()
    
    # Test with a specific category - dental-care (ID: 11)
    test_category_slug = 'dental-care'
    test_category_id = scraper.category_mappings.get(test_category_slug)
    
    print(f"Testing category: {test_category_slug} (ID: {test_category_id})")
    
    # Get the first page of the category
    category_url = f"{scraper.base_url}/{test_category_slug}"
    print(f"Fetching: {category_url}")
    
    try:
        # Fetch the category page
        content = await scraper.fetch_page_async(category_url)
        if not content:
            print("Failed to fetch category page")
            return
        
        soup = scraper.parse_html(content)
        
        # Extract medicine links from this page
        medicine_links = scraper.extract_medicine_links_from_page(soup)
        
        if not medicine_links:
            print("No medicine links found")
            return
        
        print(f"Found {len(medicine_links)} medicine links")
        
        # Test with the first medicine
        test_url = medicine_links[0]
        print(f"Testing with medicine URL: {test_url}")
        
        # Scrape the medicine page with hardcoded category ID
        success = await scraper.scrape_medicine_page(test_url, test_category_id, test_category_slug)
        
        if success:
            print("✅ Successfully scraped medicine with hardcoded category ID")
            
            # Verify in database
            db = SessionLocal()
            try:
                # Get the most recently added medicine
                medicine = db.query(Medicine).order_by(Medicine.id.desc()).first()
                if medicine:
                    print(f"Medicine ID: {medicine.id}")
                    print(f"Medicine Name: {medicine.name}")
                    print(f"Category ID: {medicine.category_id}")
                    print(f"Expected Category ID: {test_category_id}")
                    
                    if medicine.category_id == test_category_id:
                        print("✅ Category ID matches expected value!")
                    else:
                        print("❌ Category ID does not match expected value!")
                else:
                    print("❌ No medicine found in database")
            finally:
                db.close()
        else:
            print("❌ Failed to scrape medicine")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_hardcoded_categories()) 
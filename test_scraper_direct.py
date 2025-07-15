#!/usr/bin/env python3
"""
Direct test of the scraper to debug URL discovery and extraction
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.medeasy_scraper_local import MedEasyScraperLocal
from loguru import logger

async def test_scraper():
    """Test the scraper directly"""
    scraper = MedEasyScraperLocal()
    
    print("🔍 Testing MedEasy Scraper")
    print("=" * 50)
    
    # Test 1: URL Discovery
    print("1. Testing URL discovery...")
    try:
        urls = await scraper.discover_medicine_urls()
        print(f"   Found {len(urls)} medicine listing URLs:")
        for url in urls:
            print(f"     - {url}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Test a single medicine page
    print("\n2. Testing single medicine page extraction...")
    try:
        # Use one of the URLs we know works
        test_url = "https://medeasy.health/medicines/freedom-heavy-flow-wings-16-pads-women-s-choice"
        print(f"   Testing: {test_url}")
        
        success = await scraper.scrape_medicine_page(test_url)
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check database
    print("\n3. Checking database...")
    try:
        from database.connection_local import SessionLocal
        from database.models import Medicine
        
        db = SessionLocal()
        medicines = db.query(Medicine).all()
        print(f"   Found {len(medicines)} medicines in database")
        
        for medicine in medicines[:3]:  # Show first 3
            print(f"     - {medicine.name} (${medicine.price})")
        
        db.close()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Direct scraper test completed!")

if __name__ == "__main__":
    asyncio.run(test_scraper()) 
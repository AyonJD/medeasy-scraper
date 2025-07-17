#!/usr/bin/env python3
"""
Test script to debug API scraping endpoint
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.medeasy_scraper_local import MedEasyScraperLocal

async def test_scraping():
    """Test the scraping functionality directly"""
    try:
        print("Starting scraper test...")
        
        # Create scraper instance
        scraper = MedEasyScraperLocal()
        print("✅ Scraper created")
        
        # Test discovering URLs (just a few)
        print("Testing URL discovery...")
        urls = await scraper.discover_medicine_urls()
        print(f"✅ Discovered {len(urls)} category pages")
        
        if urls:
            # Test with just the first URL
            test_url = urls[0]
            print(f"Testing with URL: {test_url}")
            
            # Fetch the page
            content = await scraper.fetch_page_async(test_url)
            if content:
                print("✅ Page fetched successfully")
                
                # Parse HTML
                soup = scraper.parse_html(content)
                print("✅ HTML parsed successfully")
                
                # Extract medicine links
                medicine_links = scraper.extract_medicine_links_from_page(soup)
                print(f"✅ Found {len(medicine_links)} medicine links")
                
                if medicine_links:
                    # Test with first medicine
                    test_medicine_url = medicine_links[0]
                    print(f"Testing medicine: {test_medicine_url}")
                    
                    # Extract medicine data
                    medicine_data = scraper.extract_medicine_data(soup, test_medicine_url)
                    print(f"✅ Medicine data extracted: {medicine_data.get('name', 'Unknown')}")
                    print(f"Category ID: {medicine_data.get('category_id')}")
                    
            else:
                print("❌ Failed to fetch page")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scraping()) 
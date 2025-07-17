#!/usr/bin/env python3
"""
Test script to debug MedEasyScraperLocal issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    from scrapers.medeasy_scraper_local import MedEasyScraperLocal
    print("✅ MedEasyScraperLocal imported successfully")
    
    print("Testing scraper initialization...")
    scraper = MedEasyScraperLocal()
    print("✅ Scraper initialized successfully")
    
    print("Testing scraper attributes...")
    print(f"Base URL: {scraper.base_url}")
    print(f"Task name: {scraper.task_name}")
    print("✅ Scraper attributes accessible")
    
    print("Testing category extraction...")
    test_url = "https://medeasy.health/dental-care/some-medicine"
    category_id = scraper.extract_category_id_from_url(test_url)
    print(f"Category ID for {test_url}: {category_id}")
    print("✅ Category extraction working")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 
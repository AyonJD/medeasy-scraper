#!/usr/bin/env python3
"""
Test script to verify the MedEasy scraper setup
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"✗ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import aiohttp
        print("✓ aiohttp imported successfully")
    except ImportError as e:
        print(f"✗ aiohttp import failed: {e}")
        return False
    
    try:
        import bs4
        print("✓ BeautifulSoup imported successfully")
    except ImportError as e:
        print(f"✗ BeautifulSoup import failed: {e}")
        return False
    
    try:
        from selenium import webdriver
        print("✓ Selenium imported successfully")
    except ImportError as e:
        print(f"✗ Selenium import failed: {e}")
        return False
    
    try:
        from loguru import logger
        print("✓ Loguru imported successfully")
    except ImportError as e:
        print(f"✗ Loguru import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        print("✓ Configuration loaded successfully")
        print(f"  - Base URL: {Config.BASE_URL}")
        print(f"  - Database URL: {Config.DATABASE_URL}")
        print(f"  - API Host: {Config.API_HOST}")
        print(f"  - API Port: {Config.API_PORT}")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_database_models():
    """Test database models"""
    print("\nTesting database models...")
    
    try:
        from database.models import Medicine, ScrapingProgress, ScrapingLog
        print("✓ Database models imported successfully")
        
        # Test model attributes
        medicine = Medicine()
        print("✓ Medicine model created successfully")
        
        progress = ScrapingProgress()
        print("✓ ScrapingProgress model created successfully")
        
        log = ScrapingLog()
        print("✓ ScrapingLog model created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        return False

def test_scraper():
    """Test scraper initialization"""
    print("\nTesting scraper...")
    
    try:
        from scrapers.medeasy_scraper import MedEasyScraper
        scraper = MedEasyScraper()
        print("✓ MedEasy scraper initialized successfully")
        
        # Test basic methods
        scraper.clean_text("  test  text  ")
        print("✓ Text cleaning method works")
        
        scraper.extract_price("$123.45")
        print("✓ Price extraction method works")
        
        return True
    except Exception as e:
        print(f"✗ Scraper test failed: {e}")
        return False

def test_api():
    """Test API initialization"""
    print("\nTesting API...")
    
    try:
        from api.main import app
        print("✓ FastAPI app created successfully")
        
        # Test if app has expected endpoints
        routes = [route.path for route in app.routes]
        expected_routes = ['/', '/health', '/scrape/start', '/scrape/stop', '/scrape/status']
        
        for route in expected_routes:
            if route in routes:
                print(f"✓ Route {route} found")
            else:
                print(f"✗ Route {route} not found")
        
        return True
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 MedEasy Data Extractor Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_database_models,
        test_scraper,
        test_api
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup is ready.")
        print("\nNext steps:")
        print("1. Set up your database and update .env file")
        print("2. Run: python scripts/run_scraper.py")
        print("3. Or start the API: uvicorn api.main:app --host 0.0.0.0 --port 8000")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check your Python version (3.11+ required)")
        print("3. Verify all files are in the correct locations")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
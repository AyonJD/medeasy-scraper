#!/usr/bin/env python3
"""
Test script to verify the MedEasy scraper local setup
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

def test_local_config():
    """Test local configuration loading"""
    print("\nTesting local configuration...")
    
    try:
        from config_local import Config
        print("✓ Local configuration loaded successfully")
        print(f"  - Base URL: {Config.BASE_URL}")
        print(f"  - Database URL: {Config.DATABASE_URL}")
        print(f"  - API Host: {Config.API_HOST}")
        print(f"  - API Port: {Config.API_PORT}")
        return True
    except Exception as e:
        print(f"✗ Local configuration loading failed: {e}")
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

def test_local_scraper():
    """Test local scraper initialization"""
    print("\nTesting local scraper...")
    
    try:
        from scrapers.medeasy_scraper_local import MedEasyScraperLocal
        scraper = MedEasyScraperLocal()
        print("✓ Local MedEasy scraper initialized successfully")
        
        # Test basic methods
        scraper.clean_text("  test  text  ")
        print("✓ Text cleaning method works")
        
        scraper.extract_price("$123.45")
        print("✓ Price extraction method works")
        
        return True
    except Exception as e:
        print(f"✗ Local scraper test failed: {e}")
        return False

def test_local_api():
    """Test local API initialization"""
    print("\nTesting local API...")
    
    try:
        from api.main_local import app
        print("✓ Local FastAPI app created successfully")
        
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
        print(f"✗ Local API test failed: {e}")
        return False

def test_sqlite_database():
    """Test SQLite database connection"""
    print("\nTesting SQLite database...")
    
    try:
        from database.connection_local import init_db, check_db_connection
        
        # Initialize database
        init_db()
        print("✓ SQLite database initialized successfully")
        
        # Check connection
        if check_db_connection():
            print("✓ SQLite database connection successful")
            return True
        else:
            print("✗ SQLite database connection failed")
            return False
            
    except Exception as e:
        print(f"✗ SQLite database test failed: {e}")
        return False

def main():
    """Run all local tests"""
    print("🧪 MedEasy Data Extractor Local Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_local_config,
        test_database_models,
        test_local_scraper,
        test_local_api,
        test_sqlite_database
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
        print("🎉 All local tests passed! Setup is ready.")
        print("\nNext steps:")
        print("1. Run the local scraper: python scripts/run_scraper_local.py")
        print("2. Or start the local API: uvicorn api.main_local:app --host 127.0.0.1 --port 8000")
        print("3. Access the API at: http://127.0.0.1:8000")
        print("4. View API docs at: http://127.0.0.1:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install local dependencies: pip install -r requirements_local.txt")
        print("2. Check your Python version (3.11+ required)")
        print("3. Verify all files are in the correct locations")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
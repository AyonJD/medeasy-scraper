import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration - Using PostgreSQL for VPS
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/medeasy_db")
    
    # Redis Configuration for caching and rate limiting
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Base URL
    BASE_URL = "https://medeasy.health"
    
    # All category URLs with their page counts
    CATEGORIES = {
        "womens-choice": {
            "url": "/womens-choice",
            "pages": 4,  # Based on search results showing "Showing 1 to 10 of 37 (4 Pages)"
            "description": "Women's health and hygiene products"
        },
        "sexual-wellness": {
            "url": "/sexual-wellness", 
            "pages": 7,  # Based on search results showing "Showing 1 to 10 of 69 (7 Pages)"
            "description": "Sexual wellness and contraceptive products"
        },
        "skin-care": {
            "url": "/skin-care",
            "pages": 7,  # Based on search results showing "Showing 1 to 10 of 61 (7 Pages)"
            "description": "Skincare and beauty products"
        },
        "diabetic-care": {
            "url": "/diabetic-care",
            "pages": 4,  # Based on search results showing "Showing 1 to 10 of 33 (4 Pages)"
            "description": "Diabetes management products"
        },
        "devices": {
            "url": "/devices",
            "pages": 2,  # Based on search results showing "Showing 1 to 10 of 14 (2 Pages)"
            "description": "Medical devices and equipment"
        },
        "supplement": {
            "url": "/supplement",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Nutritional supplements"
        },
        "diapers": {
            "url": "/diapers",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Baby diapers and related products"
        },
        "baby-care": {
            "url": "/baby-care",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Baby care products"
        },
        "personal-care": {
            "url": "/personal-care",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Personal care and hygiene products"
        },
        "hygiene-and-freshness": {
            "url": "/Hygiene-And-Freshness",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Hygiene and freshness products"
        },
        "dental-care": {
            "url": "/dental-care",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Dental care products"
        },
        "herbal-medicine": {
            "url": "/Herbal-Medicine",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Herbal and natural medicines"
        },
        "prescription-medicine": {
            "url": "/prescription-medicine",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Prescription medicines"
        },
        "otc-medicine": {
            "url": "/otc-medicine",
            "pages": 1,  # No pagination info, starting with 1
            "description": "Over-the-counter medicines"
        }
    }
    
    # Scraping settings
    REQUEST_DELAY = 0.5  # Faster for VPS
    MAX_RETRIES = 3
    TIMEOUT = 30
    
    # Selenium Configuration
    SELENIUM_HEADLESS = True
    SELENIUM_TIMEOUT = 30
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "/var/log/medeasy_scraper.log"
    
    # Batch Processing
    BATCH_SIZE = 100  # Larger batch size for VPS
    MAX_CONCURRENT_REQUESTS = 10  # More concurrent requests for VPS
    
    # Rate limiting
    REQUESTS_PER_MINUTE = 60
    
    # Resume settings
    SAVE_RESUME_DATA = True
    RESUME_INTERVAL = 20  # Save resume data every N items
    
    # User Agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    
    # Nginx configuration
    NGINX_CONFIG_PATH = "/etc/nginx/sites-available/medeasy_scraper"
    
    # SSL configuration
    SSL_CERT_PATH = "/etc/letsencrypt/live/your-domain.com/fullchain.pem"
    SSL_KEY_PATH = "/etc/letsencrypt/live/your-domain.com/privkey.pem" 
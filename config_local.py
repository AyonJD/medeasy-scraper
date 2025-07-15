import os
from typing import Dict, List

class Config:
    # Database
    DATABASE_URL = "sqlite:///./medeasy_local.db"
    
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
    REQUEST_DELAY = 1.0  # Delay between requests in seconds
    MAX_RETRIES = 3
    TIMEOUT = 30
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/scraper_local.log"
    
    # API settings
    API_HOST = "127.0.0.1"
    API_PORT = 8000
    
    # Redis (for local, we'll use in-memory storage)
    REDIS_URL = None
    
    # Rate limiting
    REQUESTS_PER_MINUTE = 30
    
    # Resume settings
    SAVE_RESUME_DATA = True
    RESUME_INTERVAL = 10  # Save resume data every N items 
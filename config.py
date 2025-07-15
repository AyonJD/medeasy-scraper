import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/medeasy_db")
    
    # Redis Configuration (for job queue)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Scraping Configuration
    BASE_URL = "https://medeasy.health"
    DELAY_BETWEEN_REQUESTS = 1  # seconds
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
    LOG_FILE = "medeasy_scraper.log"
    
    # Batch Processing
    BATCH_SIZE = 100
    MAX_CONCURRENT_REQUESTS = 5
    
    # User Agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ] 
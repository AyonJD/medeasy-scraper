import asyncio
import re
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from loguru import logger
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from database.models import Medicine, MedicineImage, ScrapingProgress, ScrapingLog
from database.connection_local import SessionLocal
from utils.image_storage import ImageStorage
from utils.html_storage import HtmlStorage
import requests

class ProxyMedExScraper:
    """Enhanced MedEx scraper with proxy rotation support"""
    
    def __init__(self, use_proxies: bool = False):
        self.base_url = "https://medex.com.bd"
        self.total_pages = 822
        self.use_proxies = use_proxies
        
        # Proxy list (add your own proxy servers)
        self.proxy_list = [
            # Example proxies (replace with real ones)
            # "http://proxy1:port",
            # "http://proxy2:port", 
            # "socks5://proxy3:port"
        ]
        self.current_proxy_index = 0
        
        # Enhanced anti-blocking measures
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.160 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36 Edg/120.0.2210.144",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36"
        ]
        
        self.image_storage = ImageStorage()
        self.html_storage = HtmlStorage()
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.use_proxies or not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy
    
    def create_driver(self) -> webdriver.Chrome:
        """Create Chrome driver with enhanced stealth options"""
        options = Options()
        
        # Basic stealth options
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Enhanced anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random window size
        window_sizes = [(1920, 1080), (1366, 768), (1440, 900), (1600, 900)]
        width, height = random.choice(window_sizes)
        options.add_argument(f"--window-size={width},{height}")
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"--user-agent={user_agent}")
        
        # Proxy configuration
        if self.use_proxies:
            proxy = self.get_next_proxy()
            if proxy:
                options.add_argument(f"--proxy-server={proxy}")
                logger.info(f"Using proxy: {proxy}")
        
        # Additional stealth options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Faster loading
        options.add_argument("--disable-javascript")  # If site works without JS
        
        # Create driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def random_delay(self, min_seconds: float = 3.0, max_seconds: float = 8.0):
        """Random delay with jitter"""
        delay = random.uniform(min_seconds, max_seconds)
        # Add occasional longer pauses (10% chance)
        if random.random() < 0.1:
            delay += random.uniform(5, 15)
            logger.info(f"Taking longer break: {delay:.1f}s")
        
        logger.debug(f"Waiting {delay:.1f}s...")
        time.sleep(delay)
    
    def check_for_blocking(self, driver: webdriver.Chrome) -> bool:
        """Check if we're being blocked or seeing captcha"""
        page_source = driver.page_source.lower()
        
        blocking_indicators = [
            "captcha",
            "blocked",
            "rate limit",
            "too many requests",
            "access denied",
            "forbidden",
            "cloudflare",
            "please verify"
        ]
        
        for indicator in blocking_indicators:
            if indicator in page_source:
                logger.warning(f"Possible blocking detected: {indicator}")
                return True
        
        # Check status code if possible
        try:
            current_url = driver.current_url
            if "error" in current_url or "block" in current_url:
                logger.warning(f"Blocking URL detected: {current_url}")
                return True
        except:
            pass
        
        return False
    
    def handle_blocking(self, driver: webdriver.Chrome):
        """Handle blocking detection"""
        logger.warning("🚫 Blocking detected! Taking countermeasures...")
        
        # Close current driver
        try:
            driver.quit()
        except:
            pass
        
        # Wait longer
        wait_time = random.uniform(60, 180)  # 1-3 minutes
        logger.info(f"Waiting {wait_time/60:.1f} minutes before retry...")
        time.sleep(wait_time)
        
        # Switch proxy if using proxies
        if self.use_proxies:
            logger.info("Switching to next proxy...")
            self.get_next_proxy()
        
        # Create new driver
        return self.create_driver()

# Usage example in config
ENHANCED_SCRAPER_CONFIG = {
    "use_proxies": False,  # Set to True if you have proxy list
    "extra_delays": True,
    "max_retries": 5,
    "longer_breaks_frequency": 50,  # Take 5-10 min break every 50 medicines
} 
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from retrying import retry
import time
import random
from typing import Optional, Dict, Any, List
from loguru import logger
from config import Config

class BaseScraper:
    def __init__(self):
        self.session = None
        self.driver = None
        self.ua = UserAgent()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logger.add(
            Config.LOG_FILE,
            rotation="10 MB",
            retention="7 days",
            level=Config.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    async def get_aiohttp_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=Config.TIMEOUT)
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'User-Agent': self.ua.random}
            )
        return self.session
    
    def get_selenium_driver(self):
        """Get or create Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            if Config.SELENIUM_HEADLESS:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={self.ua.random}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(Config.SELENIUM_TIMEOUT)
        return self.driver
    
    @retry(stop_max_attempt_number=Config.MAX_RETRIES, wait_fixed=2000)
    async def fetch_page_async(self, url: str) -> Optional[str]:
        """Fetch page content using aiohttp with retry logic"""
        session = await self.get_aiohttp_session()
        try:
            headers = {'User-Agent': random.choice(Config.USER_AGENTS)}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    await asyncio.sleep(Config.DELAY_BETWEEN_REQUESTS)
                    return content
                else:
                    logger.warning(f"HTTP {response.status} for URL: {url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    @retry(stop_max_attempt_number=Config.MAX_RETRIES, wait_fixed=2000)
    def fetch_page_sync(self, url: str) -> Optional[str]:
        """Fetch page content using requests with retry logic"""
        try:
            headers = {'User-Agent': random.choice(Config.USER_AGENTS)}
            response = requests.get(url, headers=headers, timeout=Config.TIMEOUT)
            if response.status_code == 200:
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
                return response.text
            else:
                logger.warning(f"HTTP {response.status_code} for URL: {url}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    def fetch_page_selenium(self, url: str) -> Optional[str]:
        """Fetch page content using Selenium for JavaScript-heavy pages"""
        driver = self.get_selenium_driver()
        try:
            driver.get(url)
            # Wait for page to load
            WebDriverWait(driver, Config.SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            return driver.page_source
        except Exception as e:
            logger.error(f"Error fetching {url} with Selenium: {e}")
            return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, 'lxml')
    
    def extract_text_safe(self, element) -> str:
        """Safely extract text from BeautifulSoup element"""
        if element:
            return element.get_text(strip=True)
        return ""
    
    def extract_attribute_safe(self, element, attribute: str) -> str:
        """Safely extract attribute from BeautifulSoup element"""
        if element and element.has_attr(attribute):
            return element[attribute]
        return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = " ".join(text.split())
        return text.strip()
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        try:
            # Remove currency symbols and non-numeric characters except decimal point
            import re
            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if price_match:
                return float(price_match.group())
        except (ValueError, AttributeError):
            pass
        return None
    
    async def close(self):
        """Close all sessions and drivers"""
        if self.session and not self.session.closed:
            await self.session.close()
        if self.driver:
            self.driver.quit()
    
    def __del__(self):
        """Cleanup on object destruction"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 
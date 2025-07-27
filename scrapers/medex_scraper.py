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
from scrapers.base_scraper import BaseScraper
from utils.image_processor import ImageProcessor
from utils.html_storage import HtmlStorage
from config import Config
from sqlalchemy import func

class MedExScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://medex.com.bd"
        self.task_name = "medex_scraper"
        self.image_processor = ImageProcessor()
        self.html_storage = HtmlStorage()
        self.ua = UserAgent()
        
        # User agents for rotation to avoid blocking
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
        ]
        
        # Total pages on MedEx (as mentioned by user)
        self.total_pages = 822
        
    def get_random_user_agent(self) -> str:
        """Get a random user agent to avoid blocking"""
        return random.choice(self.user_agents)
    
    def setup_selenium_driver(self):
        """Setup Selenium WebDriver with anti-blocking measures"""
        chrome_options = Options()
        
        # Anti-detection measures
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Random user agent
        user_agent = self.get_random_user_agent()
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Optional headless mode
        if Config.SELENIUM_HEADLESS:
            chrome_options.add_argument("--headless")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.set_page_load_timeout(Config.SELENIUM_TIMEOUT)
        return driver
    
    def fetch_page_with_selenium(self, url: str) -> Optional[str]:
        """Fetch page content using Selenium with anti-blocking measures"""
        driver = None
        try:
            driver = self.setup_selenium_driver()
            logger.info(f"Fetching page with Selenium: {url}")
            
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Random delay to appear more human-like
            time.sleep(random.uniform(2, 5))
            
            html_content = driver.page_source
            logger.info(f"Successfully fetched page: {url}")
            return html_content
            
        except Exception as e:
            logger.error(f"Error fetching page {url} with Selenium: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def log_scraping_event(self, level: str, message: str, url: str = None):
        """Log scraping events to database"""
        db = SessionLocal()
        try:
            log_entry = ScrapingLog(
                task_name=self.task_name,
                level=level,
                message=message,
                url=url
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
        finally:
            db.close()
    
    def update_progress(self, current_page: int, total_pages: int, processed_items: int, total_items: int, status: str = "running"):
        """Update scraping progress in database"""
        db = SessionLocal()
        try:
            progress = db.query(ScrapingProgress).filter_by(task_name=self.task_name).first()
            if not progress:
                progress = ScrapingProgress(task_name=self.task_name)
                db.add(progress)
            
            progress.current_page = current_page
            progress.total_pages = total_pages
            progress.processed_items = processed_items
            progress.total_items = total_items
            progress.status = status
            
            db.commit()
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
        finally:
            db.close()
    
    def get_resume_data(self) -> Optional[Dict]:
        """Get resume data from database"""
        db = SessionLocal()
        try:
            progress = db.query(ScrapingProgress).filter_by(task_name=self.task_name).first()
            if progress and progress.resume_data:
                return progress.resume_data
        except Exception as e:
            logger.error(f"Failed to get resume data: {e}")
        finally:
            db.close()
        return None
    
    def save_resume_data(self, resume_data: Dict):
        """Save resume data to database"""
        db = SessionLocal()
        try:
            progress = db.query(ScrapingProgress).filter_by(task_name=self.task_name).first()
            if not progress:
                progress = ScrapingProgress(task_name=self.task_name)
                db.add(progress)
            
            progress.resume_data = resume_data
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save resume data: {e}")
        finally:
            db.close()
    
    def discover_medicine_urls(self) -> List[str]:
        """Discover all medicine URLs from MedEx brands pages"""
        medicine_urls = []
        
        logger.info(f"Starting discovery from {self.total_pages} pages")
        
        try:
            for page_num in range(1, self.total_pages + 1):
                if page_num == 1:
                    page_url = f"{self.base_url}/brands"
                else:
                    page_url = f"{self.base_url}/brands?page={page_num}"
                
                logger.info(f"Processing page {page_num}/{self.total_pages}: {page_url}")
                
                # Fetch page with Selenium
                content = self.fetch_page_with_selenium(page_url)
                if not content:
                    logger.warning(f"Failed to fetch page: {page_url}")
                    continue
                
                soup = self.parse_html(content)
                
                # Extract medicine links from this page
                page_medicine_urls = self.extract_medicine_links_from_page(soup)
                medicine_urls.extend(page_medicine_urls)
                
                logger.info(f"Found {len(page_medicine_urls)} medicines on page {page_num}")
                
                # Random delay between pages to avoid blocking
                time.sleep(random.uniform(3, 7))
            
            logger.info(f"Discovered {len(medicine_urls)} total medicine URLs")
            return medicine_urls
            
        except Exception as e:
            logger.error(f"Error discovering medicine URLs: {e}")
            self.log_scraping_event("ERROR", f"Error discovering medicine URLs: {e}")
            return []
    
    def extract_medicine_links_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract individual medicine links from a brands listing page"""
        medicine_links = []
        
        try:
            # Based on the MedEx website structure, look for brand links
            # The pattern appears to be: /brands/{id}/{medicine-name}
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and '/brands/' in href and href.count('/') >= 3:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    elif not href.startswith('http'):
                        href = urljoin(self.base_url, href)
                    
                    # Only include links from the same domain and with brand pattern
                    if self.base_url in href and href not in medicine_links:
                        # Validate it looks like a medicine page
                        if re.match(r'.*/brands/\d+/[^/]+$', href):
                            medicine_links.append(href)
            
        except Exception as e:
            logger.error(f"Error extracting medicine links: {e}")
        
        return medicine_links
    
    def extract_medicine_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract medicine data from MedEx product page"""
        medicine_data = {
            'product_url': url,
            'raw_data': {}
        }
        
        try:
            # Extract medicine name - look for h1 or main title
            name_selectors = [
                'h1',
                '.medicine-name',
                '.product-name',
                '.brand-name',
                '[class*="title"]'
            ]
            
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    medicine_data['name'] = self.clean_text(element.get_text(strip=True))
                    break
            
            # Extract generic name - typically shown in the composition section
            generic_selectors = [
                '.generic-name',
                '[class*="generic"]',
                '[class*="composition"]'
            ]
            
            for selector in generic_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    text = element.get_text(strip=True)
                    # Extract the first part which is usually the generic name
                    if text:
                        medicine_data['generic_name'] = self.clean_text(text.split(' ')[0])
                    break
            
            # Extract manufacturer - look for company information
            manufacturer_selectors = [
                '.manufacturer',
                '.company',
                '[class*="manufacturer"]',
                '[class*="company"]'
            ]
            
            for selector in manufacturer_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    medicine_data['manufacturer'] = self.clean_text(element.get_text(strip=True))
                    break
            
            # Extract price information
            price_selectors = [
                '.price',
                '[class*="price"]',
                '.cost',
                '.amount'
            ]
            
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    price_text = element.get_text(strip=True)
                    price = self.extract_price(price_text)
                    if price:
                        medicine_data['price'] = price
                        medicine_data['currency'] = 'BDT'
                    break
            
            # Extract strength/dosage from the name or composition
            if medicine_data.get('name'):
                strength_match = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|%|IU))', medicine_data['name'])
                if strength_match:
                    medicine_data['strength'] = strength_match.group(1)
            
            # Extract dosage form from name
            dosage_forms = ['tablet', 'capsule', 'syrup', 'injection', 'cream', 'ointment', 'drops', 'suspension', 'powder']
            name_lower = medicine_data.get('name', '').lower()
            for form in dosage_forms:
                if form in name_lower:
                    medicine_data['dosage_form'] = form.title()
                    break
            
            # Extract description from various sections
            desc_selectors = [
                '.description',
                '.indications',
                '.details',
                '[class*="indication"]',
                '[class*="description"]'
            ]
            
            descriptions = []
            for selector in desc_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 20:  # Only meaningful descriptions
                        descriptions.append(text)
            
            if descriptions:
                medicine_data['description'] = ' | '.join(descriptions[:3])  # Limit to first 3 descriptions
            
            # Generate product code from URL
            url_parts = url.split('/')
            if len(url_parts) >= 2:
                medicine_data['product_code'] = f"MX_{url_parts[-2]}"  # Use the ID from URL
            else:
                medicine_data['product_code'] = f"MX_{hash(url) % 1000000:06d}"
            
            # Store raw HTML data
            medicine_data['raw_data'] = {
                'html_content': str(soup),
                'url': url,
                'extracted_fields': {k: v for k, v in medicine_data.items() if k not in ['raw_data', 'product_url']}
            }
            
        except Exception as e:
            logger.error(f"Error extracting medicine data from {url}: {e}")
            self.log_scraping_event("ERROR", f"Error extracting medicine data: {e}", url)
        
        return medicine_data
    
    def extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract image URL from MedEx medicine page"""
        try:
            # Look for product/medicine images
            image_selectors = [
                'img[src*="pack"]',
                'img[alt*="pack"]',
                'img[alt*="medicine"]',
                'img[alt*="tablet"]',
                'img[alt*="capsule"]',
                '.product-image img',
                '.medicine-image img',
                'img[src*="product"]',
                'img[src*="medicine"]'
            ]
            
            for selector in image_selectors:
                img = soup.select_one(selector)
                if img:
                    src = img.get('src')
                    if src:
                        # Convert relative URLs to absolute
                        if src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        elif not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        
                        # Ensure it's from the same domain
                        if self.base_url in src:
                            return src
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting image URL: {e}")
            return None
    
    def process_medicine_image(self, image_url: str) -> Optional[Dict]:
        """Download and process medicine image to WebP format"""
        if not image_url:
            return None
        
        try:
            logger.debug(f"Processing image: {image_url}")
            image_data = self.image_processor.download_and_convert_to_webp(image_url)
            
            if image_data:
                logger.info(f"Successfully processed image: {image_data['width']}x{image_data['height']}, {image_data['file_size']} bytes")
                return image_data
            else:
                logger.warning(f"Failed to process image: {image_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing image {image_url}: {e}")
            return None
    
    def save_medicine_to_db(self, medicine_data: Dict[str, Any], image_data: Optional[Dict] = None, html_url: Optional[str] = None) -> bool:
        """Save medicine data to database with optional image and HTML URL"""
        db = SessionLocal()
        try:
            # Check if medicine already exists by product code
            existing = None
            if medicine_data.get('product_code'):
                existing = db.query(Medicine).filter_by(product_code=medicine_data['product_code']).first()
            
            if existing:
                # Update existing record
                for key, value in medicine_data.items():
                    if key not in ['raw_data', 'product_url'] and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.last_scraped = func.now()
                
                # Update HTML URL if provided
                if html_url and hasattr(existing, 'html_url'):
                    existing.html_url = html_url
                
                logger.info(f"Updated existing medicine: {medicine_data.get('name', 'Unknown')}")
                medicine = existing
            else:
                # Create new record - filter out non-model fields
                model_fields = {k: v for k, v in medicine_data.items() 
                              if k not in ['raw_data', 'product_url'] and hasattr(Medicine, k)}
                
                # Add HTML URL if the model supports it
                if html_url and hasattr(Medicine, 'html_url'):
                    model_fields['html_url'] = html_url
                
                medicine = Medicine(**model_fields)
                db.add(medicine)
                db.flush()  # Get the ID
                logger.info(f"Added new medicine: {medicine_data.get('name', 'Unknown')} (ID: {medicine.id})")
            
            # Process and save image if provided
            if image_data:
                try:
                    # Check if image already exists for this medicine
                    existing_image = db.query(MedicineImage).filter_by(medicine_id=medicine.id).first()
                    
                    if existing_image:
                        # Update existing image
                        existing_image.image_data = image_data['image_data']
                        existing_image.original_url = image_data['original_url']
                        existing_image.file_size = image_data['file_size']
                        existing_image.width = image_data['width']
                        existing_image.height = image_data['height']
                        existing_image.updated_at = func.now()
                        logger.info(f"Updated image for medicine ID {medicine.id}")
                    else:
                        # Create new image record
                        medicine_image = MedicineImage(
                            medicine_id=medicine.id,
                            image_data=image_data['image_data'],
                            original_url=image_data['original_url'],
                            file_size=image_data['file_size'],
                            width=image_data['width'],
                            height=image_data['height']
                        )
                        db.add(medicine_image)
                        logger.info(f"Added image for medicine ID {medicine.id}: {image_data['width']}x{image_data['height']}, {image_data['file_size']} bytes")
                        
                except Exception as e:
                    logger.error(f"Error saving image for medicine {medicine.id}: {e}")
                    # Continue with medicine save even if image fails
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving medicine to database: {e}")
            db.rollback()
            self.log_scraping_event("ERROR", f"Error saving medicine to database: {e}")
            return False
        finally:
            db.close()
    
    def scrape_medicine_page(self, url: str) -> bool:
        """Scrape a single medicine page from MedEx"""
        try:
            logger.info(f"Scraping medicine page: {url}")
            
            # Fetch page content with Selenium
            content = self.fetch_page_with_selenium(url)
            if not content:
                logger.warning(f"Failed to fetch content from: {url}")
                return False
            
            # Parse HTML
            soup = self.parse_html(content)
            
            # Extract medicine data
            medicine_data = self.extract_medicine_data(soup, url)
            
            if not medicine_data.get('name'):
                logger.warning(f"No medicine name found on page: {url}")
                return False
            
            # Save HTML content to filesystem
            html_url = None
            try:
                # Generate a temporary medicine ID for HTML storage (we'll update after DB save)
                temp_id = hash(url) % 1000000
                html_url = self.html_storage.save_html(content, temp_id, url)
                if html_url:
                    logger.info(f"Saved HTML content: {html_url}")
            except Exception as e:
                logger.error(f"Failed to save HTML content: {e}")
            
            # Extract and process image
            image_data = None
            image_url = self.extract_image_url(soup)
            if image_url:
                logger.debug(f"Found image URL: {image_url}")
                image_data = self.process_medicine_image(image_url)
                if image_data:
                    logger.info(f"Successfully processed image: {image_data['width']}x{image_data['height']}, {image_data['file_size']} bytes")
                else:
                    logger.warning(f"Failed to process image from: {image_url}")
            else:
                logger.debug(f"No image found on page: {url}")
            
            # Save to database
            success = self.save_medicine_to_db(medicine_data, image_data, html_url)
            if success:
                self.log_scraping_event("INFO", f"Successfully scraped medicine: {medicine_data.get('name')}", url)
                return True
            else:
                self.log_scraping_event("ERROR", "Failed to save medicine to database", url)
                return False
                
        except Exception as e:
            logger.error(f"Error scraping medicine page {url}: {e}")
            self.log_scraping_event("ERROR", f"Error scraping medicine page: {e}", url)
            return False
    
    def scrape_all_medicines(self, resume: bool = True):
        """Main method to scrape all medicines from MedEx"""
        try:
            logger.info("Starting MedEx medicine scraping")
            self.log_scraping_event("INFO", "Starting MedEx medicine scraping")
            
            # Check for resume data
            resume_data = None
            if resume:
                resume_data = self.get_resume_data()
                if resume_data:
                    logger.info("Resuming from previous session")
                    self.log_scraping_event("INFO", "Resuming from previous session")
            
            # Discover medicine URLs
            if resume_data and 'medicine_urls' in resume_data:
                medicine_urls = resume_data['medicine_urls']
                current_index = resume_data.get('current_index', 0)
                processed_items = resume_data.get('processed_items', 0)
            else:
                medicine_urls = self.discover_medicine_urls()
                current_index = 0
                processed_items = 0
            
            if not medicine_urls:
                logger.error("No medicine URLs found")
                self.log_scraping_event("ERROR", "No medicine URLs found")
                return
            
            total_items = len(medicine_urls)
            
            # Update progress
            self.update_progress(1, self.total_pages, processed_items, total_items)
            
            # Process each medicine URL
            for idx, url in enumerate(medicine_urls[current_index:], current_index):
                try:
                    logger.info(f"Processing medicine {idx + 1}/{total_items}: {url}")
                    
                    # Scrape the medicine page
                    success = self.scrape_medicine_page(url)
                    if success:
                        processed_items += 1
                    
                    # Update progress
                    self.update_progress(1, self.total_pages, processed_items, total_items)
                    
                    # Save resume data
                    resume_data = {
                        'medicine_urls': medicine_urls,
                        'current_index': idx + 1,
                        'processed_items': processed_items
                    }
                    self.save_resume_data(resume_data)
                    
                    # Random delay between requests to avoid blocking
                    time.sleep(random.uniform(3, 7))
                    
                except Exception as e:
                    logger.error(f"Error processing medicine {url}: {e}")
                    self.log_scraping_event("ERROR", f"Error processing medicine: {e}", url)
            
            # Mark as completed
            self.update_progress(self.total_pages, self.total_pages, processed_items, total_items, "completed")
            logger.info(f"Scraping completed. Processed {processed_items} medicines")
            self.log_scraping_event("INFO", f"Scraping completed. Processed {processed_items} medicines")
            
        except Exception as e:
            logger.error(f"Error in scrape_all_medicines: {e}")
            self.log_scraping_event("ERROR", f"Error in scrape_all_medicines: {e}")
            self.update_progress(0, 0, 0, 0, "failed") 
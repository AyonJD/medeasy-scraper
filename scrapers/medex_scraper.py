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
from utils.image_storage import ImageStorage
from utils.html_storage import HtmlStorage
from config import Config
from sqlalchemy import func

class MedExScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://medex.com.bd"
        self.task_name = "medex_scraper"
        self.image_processor = ImageProcessor()
        self.image_storage = ImageStorage()  # Add ImageStorage for server URLs
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
        """Extract medicine data from MedEx product page with complete data extraction"""
        medicine_data = {
            'product_url': url,
            'raw_data': {}
        }
        
        try:
            # Extract medicine name from h1.brand
            name_element = soup.select_one('h1.page-heading-1-l.brand')
            if name_element:
                # Get the main text without the dosage form subtitle
                name_text = name_element.get_text(strip=True)
                # Remove dosage form from name if it's at the end
                dosage_subtitle = name_element.select_one('small.h1-subtitle')
                if dosage_subtitle:
                    dosage_form_text = dosage_subtitle.get_text(strip=True)
                    name_text = name_text.replace(dosage_form_text, '').strip()
                medicine_data['name'] = self.clean_text(name_text)
            
            # Extract dosage form from h1 subtitle
            dosage_element = soup.select_one('h1.page-heading-1-l.brand small.h1-subtitle')
            if dosage_element:
                medicine_data['dosage_form'] = self.clean_text(dosage_element.get_text(strip=True))
            
            # Extract generic name from the generic name link
            generic_element = soup.select_one('div[title="Generic Name"] a')
            if generic_element:
                medicine_data['generic_name'] = self.clean_text(generic_element.get_text(strip=True))
            
            # Extract strength from div with title "Strength"
            strength_element = soup.select_one('div[title="Strength"]')
            if strength_element:
                medicine_data['strength'] = self.clean_text(strength_element.get_text(strip=True))
            
            # Extract manufacturer from div with title "Manufactured by"
            manufacturer_element = soup.select_one('div[title="Manufactured by"] a')
            if manufacturer_element:
                medicine_data['manufacturer'] = self.clean_text(manufacturer_element.get_text(strip=True))
            
            # Extract comprehensive pricing information
            price_info = {}
            unit_price = None
            strip_price = None
            pack_info = None
            
            # Unit price - Fixed to find the correct sibling span
            try:
                # Look for the package container which has the pricing structure
                package_container = soup.select_one('.package-container')
                if package_container:
                    # Find all spans in the package container
                    spans = package_container.find_all('span')
                    for i, span in enumerate(spans):
                        if span.get_text(strip=True) == "Unit Price:":
                            # The price should be in the next span
                            if i + 1 < len(spans):
                                price_span = spans[i + 1]
                                price_text = price_span.get_text(strip=True)
                                price_match = re.search(r'৳\s*([\d,]+\.?\d*)', price_text)
                                if price_match:
                                    price_value = price_match.group(1).replace(',', '')
                                    try:
                                        medicine_data['price'] = float(price_value)
                                        medicine_data['currency'] = 'BDT'
                                        unit_price = f"৳ {price_value}"
                                        price_info['unit_price'] = unit_price
                                        logger.debug(f"Extracted unit price: {price_value}")
                                        break
                                    except ValueError:
                                        pass
                        elif span.get_text(strip=True) == "Strip Price:":
                            # The strip price should be in the next span
                            if i + 1 < len(spans):
                                price_span = spans[i + 1]
                                price_text = price_span.get_text(strip=True)
                                price_match = re.search(r'৳\s*([\d,]+\.?\d*)', price_text)
                                if price_match:
                                    strip_price = f"৳ {price_match.group(1)}"
                                    price_info['strip_price'] = strip_price
                                    logger.debug(f"Extracted strip price: {price_match.group(1)}")
            except Exception as e:
                logger.debug(f"Error extracting prices from package container: {e}")
            
            # Pack price (like "6 x 10: ৳ 720.00")
            pack_price_element = soup.select_one('.pack-size-info')
            if pack_price_element:
                pack_text = pack_price_element.get_text(strip=True)
                pack_info = pack_text
                price_info['pack_info'] = pack_text
                logger.debug(f"Extracted pack info: {pack_text}")
            
            # Store individual pricing fields
            medicine_data['unit_price'] = unit_price
            medicine_data['strip_price'] = strip_price
            medicine_data['pack_info'] = pack_info
            
            # Extract comprehensive description from all available sections
            descriptions = []
            
            # List of all sections to extract
            sections = [
                ('indications', 'Indications'),
                ('composition', 'Composition'),
                ('mode_of_action', 'Pharmacology'), 
                ('dosage', 'Dosage & Administration'),
                ('interaction', 'Interaction'),
                ('contraindications', 'Contraindications'),
                ('side_effects', 'Side Effects'),
                ('pregnancy_cat', 'Pregnancy & Lactation'),
                ('precautions', 'Precautions & Warnings'),
                ('pediatric_uses', 'Use in Special Populations'),
                ('overdose_effects', 'Overdose Effects'),
                ('drug_classes', 'Therapeutic Class'),
                ('storage_conditions', 'Storage Conditions')
            ]
            
            section_data = {}
            for section_id, section_name in sections:
                section_element = soup.select_one(f'#{section_id}')
                if section_element:
                    # Find the corresponding body content - try multiple approaches
                    body_element = None
                    
                    # Method 1: Direct sibling
                    body_element = section_element.find_next_sibling('div', class_='ac-body')
                    
                    # Method 2: Parent's next sibling (if wrapped in a div)
                    if not body_element and section_element.parent:
                        body_element = section_element.parent.find('div', class_='ac-body')
                    
                    # Method 3: Look in parent container
                    if not body_element:
                        parent_div = section_element.find_parent('div')
                        if parent_div:
                            body_element = parent_div.find('div', class_='ac-body')
                    
                    if body_element:
                        content = body_element.get_text(strip=True)
                        if content and len(content) > 5:  # Lower threshold for meaningful content
                            # Clean up the content
                            content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
                            content = content.replace('* রেজিস্টার্ড চিকিৎসকের পরামর্শ মোতাবেক ঔষধ সেবন করুন', '').strip()
                            
                            if content:  # Only if there's still content after cleaning
                                section_key = section_name.lower().replace(' & ', '_').replace(' ', '_').replace('&', 'and')
                                section_data[section_key] = content
                                descriptions.append(f"{section_name}: {content}")
                                logger.debug(f"✅ Extracted {section_name}: {len(content)} chars")
                        else:
                            logger.debug(f"⚠️ {section_name}: No meaningful content found (length: {len(content) if content else 0})")
                    else:
                        logger.debug(f"❌ {section_name}: No body element found for #{section_id}")
            
            # Extract Common Questions section
            common_questions = []
            questions_section = soup.select_one('#commonly_asked_questions')
            if questions_section:
                # Find the corresponding body content
                questions_body = questions_section.find_next_sibling('div', class_='ac-body')
                if questions_body:
                    # Extract individual Q&A pairs
                    qa_pairs = questions_body.select('.caq')
                    for qa in qa_pairs:
                        question_elem = qa.select_one('.caq-q')
                        answer_elem = qa.select_one('.caq-a')
                        if question_elem and answer_elem:
                            question = question_elem.get_text(strip=True)
                            answer = answer_elem.get_text(strip=True)
                            common_questions.append({'question': question, 'answer': answer})
                    
                    if common_questions:
                        medicine_data['common_questions'] = common_questions
                        # Add to descriptions as well
                        qa_text = ' | '.join([f"Q: {qa['question']} A: {qa['answer']}" for qa in common_questions])
                        descriptions.append(f"Common Questions: {qa_text}")
                        logger.debug(f"Extracted {len(common_questions)} common questions")
            
            # Create comprehensive description with ALL sections
            if descriptions:
                # Store detailed sections separately
                medicine_data['detailed_info'] = section_data
                # Create main description with ALL extracted sections - NO LIMIT!
                medicine_data['description'] = ' | '.join(descriptions)
                logger.debug(f"Created comprehensive description with {len(descriptions)} sections")
            
            # Store pricing info in raw_data
            if price_info:
                medicine_data['price_info'] = price_info
            
            # Generate product code from URL
            url_parts = url.split('/')
            if len(url_parts) >= 2:
                try:
                    medicine_id = url_parts[-2] if url_parts[-2].isdigit() else url_parts[-1].split('-')[0]
                    medicine_data['product_code'] = f"MX_{medicine_id}"
                except:
                    medicine_data['product_code'] = f"MX_{hash(url) % 1000000:06d}"
            
            # Extract additional metadata from page title and meta tags
            title_element = soup.select_one('title')
            if title_element:
                title_text = title_element.get_text(strip=True)
                medicine_data['page_title'] = title_text
            
            # Extract meta description
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc:
                medicine_data['meta_description'] = meta_desc.get('content', '').strip()
            
            # Store comprehensive raw data
            medicine_data['raw_data'] = {
                'html_content': str(soup),
                'url': url,
                'extracted_fields': {k: v for k, v in medicine_data.items() if k not in ['raw_data', 'product_url']},
                'section_data': section_data if 'section_data' in locals() else {},
                'price_details': price_info,
                'common_questions': common_questions if common_questions else []
            }
            
        except Exception as e:
            logger.error(f"Error extracting medicine data from {url}: {e}")
            self.log_scraping_event("ERROR", f"Error extracting medicine data: {e}", url)
        
        return medicine_data
    
    def extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract image URL from MedEx medicine page - specifically pack images"""
        try:
            # Method 1: Extract from Pack Images button (most reliable)
            pack_images_btn = soup.select_one('a.innovator-brand-badge[data-mp-objects]')
            if pack_images_btn:
                href = pack_images_btn.get('href')
                if href and 'storage/images/packaging' in href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    return href
            
            # Method 2: Extract from pack images section at bottom
            pack_images = soup.select('div[style*="margin: 10px"] a[href*="storage/images/packaging"]')
            if pack_images:
                for img_link in pack_images:
                    href = img_link.get('href')
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        return href
            
            # Method 3: Direct image elements with pack image URLs
            pack_img_elements = soup.select('img[src*="storage/images/packaging"]')
            if pack_img_elements:
                for img in pack_img_elements:
                    src = img.get('src')
                    if src:
                        # Convert relative URLs to absolute
                        if src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        return src
            
            # Method 4: Look for any images with "pack" in alt text or filename
            pack_alt_images = soup.select('img[alt*="Pack"], img[src*="pack"], img[alt*="packaging"]')
            if pack_alt_images:
                for img in pack_alt_images:
                    src = img.get('src') or img.get('data-src')
                    if src and ('storage/images' in src or 'pack' in src.lower()):
                        # Convert relative URLs to absolute
                        if src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        elif not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        
                        # Ensure it's from the same domain and not a generic icon
                        if self.base_url in src and 'dosage-forms' not in src:
                            return src
            
            # Method 5: Check for any medicine/product images as fallback
            general_selectors = [
                'img[src*="medicine"]',
                'img[src*="tablet"]',
                'img[src*="capsule"]',
                'img[alt*="medicine"]',
                '.product-image img',
                '.medicine-image img'
            ]
            
            for selector in general_selectors:
                img = soup.select_one(selector)
                if img:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        # Convert relative URLs to absolute
                        if src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        elif not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        
                        # Ensure it's from the same domain and not a generic icon
                        if self.base_url in src and 'dosage-forms' not in src and 'logo' not in src.lower():
                            return src
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting image URL: {e}")
            return None
    
    def process_medicine_image(self, image_url: str, medicine_id: int = None) -> Optional[Dict]:
        """Download and process medicine image to WebP format and save to server"""
        if not image_url:
            return None
        
        try:
            logger.debug(f"Processing image: {image_url}")
            # Download and convert to WebP
            image_data = self.image_processor.download_and_convert_to_webp(image_url)
            
            if image_data:
                # Use a temporary ID if medicine_id not provided yet
                temp_id = medicine_id or hash(image_url) % 1000000
                
                # Save to filesystem and get server URL
                server_image_url = self.image_storage.save_image(
                    image_data['image_data'], 
                    temp_id, 
                    image_url
                )
                
                if server_image_url:
                    # Add server URL to the image data
                    image_data['server_url'] = server_image_url
                    logger.info(f"Successfully processed and saved image: {image_data['width']}x{image_data['height']}, {image_data['file_size']} bytes -> {server_image_url}")
                    return image_data
                else:
                    logger.warning(f"Failed to save image to server: {image_url}")
                    return None
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
                # Update existing record - filter out non-model fields but keep raw_data
                for key, value in medicine_data.items():
                    if key not in ['product_url'] and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.last_scraped = func.now()
                
                # Update HTML URL if provided
                if html_url and hasattr(existing, 'html_url'):
                    existing.html_url = html_url
                
                # Set image_url from processed image data
                if image_data and 'server_url' in image_data:
                    existing.image_url = image_data['server_url']
                    logger.debug(f"Updated image_url: {image_data['server_url']}")
                
                # IMPORTANT: Save comprehensive raw_data to database
                if 'raw_data' in medicine_data:
                    existing.raw_data = medicine_data['raw_data']
                    logger.debug(f"Updated raw_data with comprehensive information")
                
                logger.info(f"Updated existing medicine: {medicine_data.get('name', 'Unknown')}")
                medicine = existing
            else:
                # Create new record - filter out non-model fields but keep raw_data
                model_fields = {k: v for k, v in medicine_data.items() 
                              if k not in ['product_url'] and hasattr(Medicine, k)}
                
                # Add HTML URL if the model supports it
                if html_url and hasattr(Medicine, 'html_url'):
                    model_fields['html_url'] = html_url
                
                # Set image_url from processed image data
                if image_data and 'server_url' in image_data:
                    model_fields['image_url'] = image_data['server_url']
                    logger.debug(f"Setting image_url: {image_data['server_url']}")
                
                # IMPORTANT: Ensure comprehensive raw_data is saved to database
                if 'raw_data' in medicine_data:
                    model_fields['raw_data'] = medicine_data['raw_data']
                    logger.debug(f"Setting raw_data with comprehensive information")
                
                medicine = Medicine(**model_fields)
                db.add(medicine)
                db.flush()  # Get the ID
                logger.info(f"Added new medicine: {medicine_data.get('name', 'Unknown')} (ID: {medicine.id})")
            
            # Process and save image to database if provided
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
                # Generate a temporary medicine ID for HTML storage
                temp_id = hash(url) % 1000000
                html_url = self.html_storage.save_html(content, temp_id, url)
                if html_url:
                    logger.info(f"Saved HTML content: {html_url}")
            except Exception as e:
                logger.error(f"Failed to save HTML content: {e}")
            
            # Extract and process image with server storage
            image_data = None
            image_url = self.extract_image_url(soup)
            if image_url:
                logger.debug(f"Found image URL: {image_url}")
                # Process image without medicine_id first (will use temp_id)
                image_data = self.process_medicine_image(image_url)
                if image_data:
                    logger.info(f"Successfully processed image: {image_data['width']}x{image_data['height']}, {image_data['file_size']} bytes")
                    logger.info(f"Image saved to server: {image_data['server_url']}")
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
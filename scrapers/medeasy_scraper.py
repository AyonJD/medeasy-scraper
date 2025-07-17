import asyncio
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from loguru import logger
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from database.models import Medicine, MedicineImage, ScrapingProgress, ScrapingLog
from database.connection_local import SessionLocal
from scrapers.base_scraper import BaseScraper
from utils.image_processor import ImageProcessor
from config import Config
from sqlalchemy import func

class MedEasyScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = Config.BASE_URL
        self.task_name = "medeasy_scraper"
        self.image_processor = ImageProcessor()
        self.category_cache = {}  # Cache for category name to ID mapping
        
        # Define category mappings with their IDs
        self.category_mappings = {
            'womens-choice': 1,
            'sexual-wellness': 2,
            'skin-care': 3,
            'diabetic-care': 4,
            'devices': 5,
            'supplement': 6,
            'diapers': 7,
            'baby-care': 8,
            'personal-care': 9,
            'hygiene-and-freshness': 10,
            'dental-care': 11,
            'herbal-medicine': 12,
            'prescription-medicine': 13,
            'otc-medicine': 14
        }
        
        # Category URLs to scrape
        self.category_urls = [
            'womens-choice',
            'sexual-wellness', 
            'skin-care',       
            'diabetic-care',
            'devices',
            'supplement',
            'diapers',
            'baby-care',
            'personal-care',
            'hygiene-and-freshness',
            'dental-care',
            'herbal-medicine',
            'prescription-medicine',
            'otc-medicine'
        ]
    
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
    
    def get_category_id_by_name(self, category_name: str) -> Optional[int]:
        """Get category ID by name, with fuzzy matching and caching"""
        if not category_name:
            return None
        
        # Check cache first
        if category_name in self.category_cache:
            return self.category_cache[category_name]
        
        db = SessionLocal()
        try:
            from database.models import Category
            
            # Clean the category name
            clean_name = self.clean_text(category_name).strip()
            if not clean_name:
                return None
            
            # Try exact match first
            category = db.query(Category).filter(Category.name.ilike(clean_name)).first()
            if category:
                self.category_cache[category_name] = category.id
                return category.id
            
            # Try fuzzy matching with common variations
            variations = [
                clean_name,
                clean_name.lower(),
                clean_name.title(),
                clean_name.upper(),
                clean_name.replace(' ', ''),
                clean_name.replace('-', ' '),
                clean_name.replace('_', ' '),
                clean_name.replace('&', 'and'),
                clean_name.replace('and', '&')
            ]
            
            for variation in variations:
                category = db.query(Category).filter(Category.name.ilike(variation)).first()
                if category:
                    self.category_cache[category_name] = category.id
                    logger.info(f"Found category '{clean_name}' via variation '{variation}' -> ID {category.id}")
                    return category.id
            
            # Try partial matching for common category patterns
            if 'women' in clean_name.lower() or 'feminine' in clean_name.lower() or 'sanitary' in clean_name.lower():
                category = db.query(Category).filter(Category.name.ilike('%women%')).first()
                if category:
                    self.category_cache[category_name] = category.id
                    return category.id
            
            if 'vitamin' in clean_name.lower() or 'supplement' in clean_name.lower():
                category = db.query(Category).filter(Category.name.ilike('%vitamin%')).first()
                if category:
                    self.category_cache[category_name] = category.id
                    return category.id
            
            if 'pain' in clean_name.lower() or 'fever' in clean_name.lower() or 'headache' in clean_name.lower():
                category = db.query(Category).filter(Category.name.ilike('%pain%')).first()
                if category:
                    self.category_cache[category_name] = category.id
                    return category.id
            
            logger.warning(f"No category found for name: {clean_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting category ID for '{category_name}': {e}")
            return None
        finally:
            db.close()

    def extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract image URL from medicine page - improved to get high-resolution images from MedEasy's Next.js image system"""
        
        # First, try to find MedEasy's Next.js image URLs (highest priority)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if '/_next/image?url=' in src:
                try:
                    # Parse the Next.js image URL to extract the original image URL
                    original_url = self._extract_nextjs_image_url(src)
                    if original_url:
                        logger.info(f"Found Next.js image URL: {original_url}")
                        return original_url
                except Exception as e:
                    logger.debug(f"Failed to parse Next.js image URL {src}: {e}")
                    continue
        
        # Fallback to other image selectors if Next.js images not found
        image_selectors = [
            # Product-specific selectors (highest priority)
            'img.product-image',
            'img.medicine-image',
            '.product-gallery img',
            '.medicine-gallery img',
            '.product-photo img',
            '.main-image img',
            '.hero-image img',
            '.product-detail img',
            '.medicine-detail img',
            
            # Generic selectors with size hints (but avoid social media icons)
            'img[src*="product"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[src*="medicine"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[alt*="product"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[alt*="medicine"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            
            # High-resolution image selectors (but avoid social media)
            'img[src*="large"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[src*="original"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[src*="full"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[src*="high"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[src*="big"]:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"])',
            'img[data-src*="large"]:not([data-src*="facebook"]):not([data-src*="twitter"]):not([data-src*="instagram"])',
            'img[data-src*="original"]:not([data-src*="facebook"]):not([data-src*="twitter"]):not([data-src*="instagram"])',
            'img[data-src*="full"]:not([data-src*="facebook"]):not([data-src*="twitter"]):not([data-src*="instagram"])',
            'img[data-src*="high"]:not([data-src*="facebook"]):not([data-src*="twitter"]):not([data-src*="instagram"])',
            'img[data-src*="big"]:not([data-src*="facebook"]):not([data-src*="twitter"]):not([data-src*="instagram"])',
            
            # Fallback selectors (but exclude social media and small icons)
            'img:not([src*="facebook"]):not([src*="twitter"]):not([src*="instagram"]):not([src*="icon"]):not([src*="logo"]):not([width="16"]):not([height="16"]):not([width="32"]):not([height="32"])'
        ]
        
        best_image_url = None
        best_size = 0
        
        for selector in image_selectors:
            try:
                img_elements = soup.select(selector)
                for img_element in img_elements:
                    # Try different attributes for image URL
                    src = (img_element.get('src') or 
                           img_element.get('data-src') or 
                           img_element.get('data-original') or
                           img_element.get('data-lazy-src'))
                    
                    if src:
                        # Skip social media icons and small images
                        if any(skip in src.lower() for skip in ['facebook', 'twitter', 'instagram', 'icon', 'logo']):
                            continue
                        
                        # Skip very small images (likely icons)
                        width = img_element.get('width')
                        height = img_element.get('height')
                        if width and height:
                            try:
                                w, h = int(width), int(height)
                                if w < 50 or h < 50:  # Skip very small images
                                    continue
                            except (ValueError, TypeError):
                                pass
                        
                        # Convert relative URLs to absolute
                        if src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        elif not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        
                        # Only include images from the same domain or trusted CDNs
                        if any(domain in src for domain in [self.base_url, 'medeasy.health', 'cdn', 'images']):
                            # Try to get higher resolution version by modifying URL
                            high_res_url = self._get_high_resolution_url(src)
                            
                            # Estimate image size from URL or attributes
                            estimated_size = self._estimate_image_size(img_element, high_res_url)
                            
                            # Keep the largest image found
                            if estimated_size > best_size:
                                best_image_url = high_res_url
                                best_size = estimated_size
                                logger.debug(f"Found better image: {high_res_url} (estimated size: {estimated_size})")
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        if best_image_url:
            logger.info(f"Selected fallback image URL: {best_image_url} (estimated size: {best_size})")
            return best_image_url
        
        return None
    
    def _extract_nextjs_image_url(self, nextjs_url: str) -> Optional[str]:
        """Extract the original image URL from MedEasy's Next.js image URL"""
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            
            # Parse the Next.js image URL
            parsed = urlparse(nextjs_url)
            query_params = parse_qs(parsed.query)
            
            # Extract the 'url' parameter which contains the original image URL
            if 'url' in query_params:
                original_url = unquote(query_params['url'][0])
                
                # The original URL should be from MedEasy's API
                if 'api.medeasy.health' in original_url:
                    logger.debug(f"Extracted original image URL: {original_url}")
                    return original_url
                else:
                    logger.warning(f"Extracted URL is not from MedEasy API: {original_url}")
                    return None
            else:
                logger.warning(f"No 'url' parameter found in Next.js image URL: {nextjs_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting Next.js image URL: {e}")
            return None
    
    def _get_high_resolution_url(self, image_url: str) -> str:
        """Try to get a higher resolution version of the image URL"""
        # Common patterns for high-resolution images
        high_res_patterns = [
            # Replace size indicators
            ('_small', '_large'),
            ('_medium', '_large'),
            ('_thumb', '_original'),
            ('thumbnail', 'original'),
            ('small', 'large'),
            ('medium', 'large'),
            
            # Add size parameters
            ('?', '?size=large&'),
            ('?', '?width=1024&height=1024&'),
            ('?', '?quality=high&'),
            
            # Remove size restrictions
            ('&size=small', ''),
            ('&size=medium', ''),
            ('&width=300', '&width=1024'),
            ('&height=300', '&height=1024'),
        ]
        
        # Try to modify URL for higher resolution
        for old_pattern, new_pattern in high_res_patterns:
            if old_pattern in image_url:
                high_res_url = image_url.replace(old_pattern, new_pattern)
                logger.debug(f"Trying high-res URL: {high_res_url}")
                return high_res_url
        
        # If no patterns match, try adding common high-res suffixes
        if '.' in image_url:
            base_url, extension = image_url.rsplit('.', 1)
            high_res_url = f"{base_url}_large.{extension}"
            logger.debug(f"Trying high-res URL with suffix: {high_res_url}")
            return high_res_url
        
        return image_url
    
    def _estimate_image_size(self, img_element, image_url: str) -> int:
        """Estimate image size based on URL patterns and element attributes"""
        size = 0
        
        # Check for size hints in URL
        if any(size_hint in image_url.lower() for size_hint in ['large', 'original', 'full', 'high', 'big']):
            size += 1000
        
        # Check for size hints in class names
        class_attr = img_element.get('class', [])
        if isinstance(class_attr, str):
            class_attr = [class_attr]
        
        for class_name in class_attr:
            if any(size_hint in class_name.lower() for size_hint in ['large', 'original', 'full', 'high', 'big']):
                size += 500
        
        # Check for width/height attributes
        width = img_element.get('width')
        height = img_element.get('height')
        if width and height:
            try:
                w, h = int(width), int(height)
                size += w * h
            except (ValueError, TypeError):
                pass
        
        # Check for data attributes
        data_width = img_element.get('data-width')
        data_height = img_element.get('data-height')
        if data_width and data_height:
            try:
                w, h = int(data_width), int(data_height)
                size += w * h
            except (ValueError, TypeError):
                pass
        
        return size

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
    
    async def discover_medicine_urls(self) -> List[Dict]:
        """Cover all medicine URLs from the categorized pages"""
        medicine_urls = []
        
        logger.info(f"Starting discovery from {len(self.category_urls)} category pages")
        
        try:
            # Process each category
            for category_slug in self.category_urls:
                category_id = self.category_mappings.get(category_slug)
                if not category_id:
                    logger.warning(f"No category ID found for slug: {category_slug}")
                    continue
                
                logger.info(f"Processing category: {category_slug} (ID: {category_id})")
                
                # Start with page1
                page = 1
                
                while True:
                    # Construct category page URL
                    if page == 1:
                        category_url = f"{self.base_url}/{category_slug}"
                    else:
                        category_url = f"{self.base_url}/{category_slug}?page={page}"
                    
                    logger.info(f"Fetching category page: {category_url}")
                    
                    # Fetch the category page
                    content = await self.fetch_page_async(category_url)
                    if not content:
                        logger.warning(f"Failed to fetch category page: {category_url}")
                        break
                    
                    soup = self.parse_html(content)
                    
                    # Extract medicine links from this page
                    medicine_links = self.extract_medicine_links_from_page(soup)
                    
                    if not medicine_links:
                        logger.info(f"No medicine links found on page {page} for category {category_slug}")
                        break
                    
                    # Add category information to each URL
                    for link in medicine_links:
                        # Store category info with the URL
                        medicine_urls.append({
                            'url': link,
                            'category_id': category_id,
                            'category_slug': category_slug
                        })
                    
                    logger.info(f"Found {len(medicine_links)} medicines on page {page} for category {category_slug}")
                    
                    # Check if there's a next page
                    next_page = soup.find(string=lambda text: text and 'next' in text.lower())
                    if not next_page:
                        # Also check for pagination links
                        pagination = soup.find('ul', class_='pagination')
                        if pagination:
                            page_links = pagination.find_all('a')
                            has_next = any('next' in link.get('href', '').lower() or 
                                         'next' in link.get_text().lower() for link in page_links)
                            if not has_next:
                                break
                        else:
                            break
                    
                    page += 1
                    
                    # Safety limit to prevent infinite loops
                    if page > 50:
                        logger.warning(f"Reached safety limit of 50 pages for category {category_slug}")
                        break
                
                logger.info(f"Completed category {category_slug}: {len([u for u in medicine_urls if u['category_slug'] == category_slug])} medicines found")
            
            logger.info(f"Discovered {len(medicine_urls)} total medicines across all categories")
            return medicine_urls
            
        except Exception as e:
            logger.error(f"Error discovering medicine URLs: {e}")
            self.log_scraping_event("ERROR", f"Error discovering medicine URLs: {e}")
            return []
    
    def extract_medicine_links_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract individual medicine product links from a listing page"""
        medicine_links = []
        
        # Common selectors for medicine product links
        selectors = [
            'a[href*="/medicine/"]',
            'a[href*="/product/"]',
            '.product-link',
            '.medicine-link',
            '.item-link',
            'a[href*="medeasy.health"]'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    elif not href.startswith('http'):
                        href = urljoin(self.base_url, href)
                    
                    # Only include links from the same domain
                    if self.base_url in href and href not in medicine_links:
                        medicine_links.append(href)
        
        logger.info(f"Extracted {len(medicine_links)} medicine links from page")
        return medicine_links
    
    def extract_medicine_data(self, soup: BeautifulSoup, url: str, category_id: int = None, category_slug: str = None) -> Dict[str, Any]:
        """Extract medicine data from product page"""
        medicine_data = {
            'raw_data': {}
        }
        
        # Add category information if provided - use hardcoded category ID
        if category_id is not None:
            medicine_data['category_id'] = category_id  # Save to category_id field
            logger.info(f"Setting hardcoded category_id: {category_id} for medicine from {category_slug}")
        
        try:
            # Extract basic information
            # Product name
            name_selectors = [
                'h1.product-title',
                'h1.medicine-title',
                '.product-name',
                '.medicine-name',
                'h1',
                '.title'
            ]
            
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['name'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Generic name
            generic_selectors = [
                '.generic-name',
                '.generic',
                '[data-field="generic"]',
                '.product-generic'
            ]
            
            for selector in generic_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['generic_name'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Brand name
            brand_selectors = [
                '.brand-name',
                '.brand',
                '[data-field="brand"]',
                '.product-brand'
            ]
            
            for selector in brand_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['brand_name'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Manufacturer
            manufacturer_selectors = [
                '.manufacturer',
                '.company',
                '[data-field="manufacturer"]',
                '.product-manufacturer'
            ]
            
            for selector in manufacturer_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['manufacturer'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Price
            price_selectors = [
                '.price',
                '.product-price',
                '.medicine-price',
                '[data-field="price"]',
                '.cost'
            ]
            
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = self.extract_text_safe(element)
                    price = self.extract_price(price_text)
                    if price:
                        medicine_data['price'] = price
                        medicine_data['currency'] = 'BDT'  # Default for Bangladesh
                    break
            
            # Strength
            strength_selectors = [
                '.strength',
                '.dosage-strength',
                '[data-field="strength"]'
            ]
            
            for selector in strength_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['strength'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Dosage form
            form_selectors = [
                '.dosage-form',
                '.form',
                '[data-field="form"]'
            ]
            
            for selector in form_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['dosage_form'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Pack size
            pack_selectors = [
                '.pack-size',
                '.size',
                '[data-field="pack"]'
            ]
            
            for selector in pack_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['pack_size'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Description
            desc_selectors = [
                '.description',
                '.product-description',
                '.medicine-description',
                '.details',
                '.info'
            ]
            
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['description'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # Product code/SKU
            code_selectors = [
                '.product-code',
                '.sku',
                '.code',
                '[data-field="code"]'
            ]
            
            for selector in code_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['product_code'] = self.clean_text(self.extract_text_safe(element))
                    break
            # Store all raw data for flexibility
            medicine_data['raw_data'] = {
                'html_content': str(soup),
                'extracted_fields': {k: v for k, v in medicine_data.items() if k not in ['raw_data', 'product_url']}
            }
            
            # Generate product code if not found
            if not medicine_data.get('product_code'):
                medicine_data['product_code'] = f"ME_{hash(url) % 1000000:06d}"
            
        except Exception as e:
            logger.error(f"Error extracting medicine data from {url}: {e}")
            self.log_scraping_event("ERROR", f"Error extracting medicine data: {e}", url)
        
        return medicine_data
    
    def save_medicine_to_db(self, medicine_data: Dict[str, Any], image_data: Optional[Dict] = None) -> bool:
        """Save medicine data to database with optional image"""
        db = SessionLocal()
        try:
            # Check if medicine already exists by product code
            existing = None
            if medicine_data.get('product_code'):
                existing = db.query(Medicine).filter_by(product_code=medicine_data['product_code']).first()
            
            if existing:
                # Update existing record
                for key, value in medicine_data.items():
                    if key != 'raw_data' and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.last_scraped = func.now()
                logger.info(f"Updated existing medicine: {medicine_data.get('name', 'Unknown')}")
                medicine = existing
            else:
                # Create new record - filter out non-model fields
                model_fields = {k: v for k, v in medicine_data.items() 
                              if k != 'raw_data' and hasattr(Medicine, k)}
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
    
    async def scrape_medicine_page(self, url: str, category_id: int = None, category_slug: str = None) -> bool:
        """Scrape a single medicine page"""
        try:
            logger.info(f"Scraping medicine page: {url}")
            
            # Fetch page content
            content = await self.fetch_page_async(url)
            if not content:
                logger.warning(f"Failed to fetch content from: {url}")
                return False
            
            # Parse HTML
            soup = self.parse_html(content)
            
            # Extract medicine data with category information
            medicine_data = self.extract_medicine_data(soup, url, category_id, category_slug)
            
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
            if medicine_data.get('name'):  # Only save if we have at least a name
                success = self.save_medicine_to_db(medicine_data, image_data)
                if success:
                    self.log_scraping_event("INFO", f"Successfully scraped medicine: {medicine_data.get('name')}", url)
                    return True
                else:
                    self.log_scraping_event("ERROR", "Failed to save medicine to database", url)
                    return False
            else:
                logger.warning(f"No medicine name found on page: {url}")
                self.log_scraping_event("WARNING", "No medicine name found on page", url)
                return False
                
        except Exception as e:
            logger.error(f"Error scraping medicine page {url}: {e}")
            self.log_scraping_event("ERROR", f"Error scraping medicine page: {e}", url)
            return False
    
    async def scrape_all_medicines(self, resume: bool = True):
        """Main method to scrape all medicines"""
        try:
            logger.info("Starting MedEasy medicine scraping")
            self.log_scraping_event("INFO", "Starting MedEasy medicine scraping")
            
            # Check for resume data
            resume_data = None
            if resume:
                resume_data = self.get_resume_data()
                if resume_data:
                    logger.info("Resuming from previous session")
                    self.log_scraping_event("INFO", "Resuming from previous session")
            
            # Discover medicine URLs with category information
            if resume_data and 'medicine_urls' in resume_data:
                medicine_urls = resume_data['medicine_urls']
                current_index = resume_data.get('current_index', 0)
                processed_items = resume_data.get('processed_items', 0)
            else:
                medicine_urls = await self.discover_medicine_urls()
                current_index = 0
                processed_items = 0
            
            if not medicine_urls:
                logger.error("No medicine URLs found")
                self.log_scraping_event("ERROR", "No medicine URLs found")
                return
            
            total_items = len(medicine_urls)
            
            # Update progress
            self.update_progress(1, 1, processed_items, total_items)
            
            # Process each medicine URL
            for idx, medicine_info in enumerate(medicine_urls[current_index:], current_index):
                try:
                    url = medicine_info['url']
                    category_id = medicine_info.get('category_id')
                    category_slug = medicine_info.get('category_slug')
                    
                    logger.info(f"Processing medicine {idx +1}/{total_items}: {url} (Category: {category_slug}, ID: {category_id})")
                    
                    # Scrape the medicine page with category information
                    success = await self.scrape_medicine_page(url, category_id, category_slug)
                    if success:
                        processed_items += 1
                    
                    # Update progress
                    self.update_progress(1, 1, processed_items, total_items)
                    
                    # Save resume data
                    resume_data = {
                        'medicine_urls': medicine_urls,
                        'current_index': idx + 1,
                        'processed_items': processed_items
                    }
                    self.save_resume_data(resume_data)
                    
                except Exception as e:
                    logger.error(f"Error processing medicine {url}: {e}")
                    self.log_scraping_event("ERROR", f"Error processing medicine: {e}", url)
            
            # Mark as completed
            self.update_progress(1, 1, processed_items, total_items, "completed")
            logger.info(f"Scraping completed. Processed {processed_items} medicines")
            self.log_scraping_event("INFO", f"Scraping completed. Processed {processed_items} medicines")
            
        except Exception as e:
            logger.error(f"Error in scrape_all_medicines: {e}")
            self.log_scraping_event("ERROR", f"Error in scrape_all_medicines: {e}")
            self.update_progress(0, 0, 0, 0, "failed")
        finally:
            await self.close() 
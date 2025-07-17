import asyncio
import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from loguru import logger
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from database.models import Medicine, MedicineImage, ScrapingProgress, ScrapingLog
from database.connection_local import SessionLocal
from scrapers.base_scraper import BaseScraper
from utils.image_processor import ImageProcessor
from utils.image_storage import ImageStorage
from utils.category_manager import CategoryManager
from config_local import Config
from sqlalchemy import func

class MedEasyScraperLocal(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = Config.BASE_URL
        self.task_name = "medeasy_scraper_local"
        self.image_processor = ImageProcessor()
        self.image_storage = ImageStorage()
        self.category_manager = CategoryManager()
    
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
        """Discover all medicine URLs from all categories, attaching category_id to each"""
        medicine_urls = []
        logger.info("Starting discovery from all categories")
        try:
            # Hardcoded mapping of category slugs to IDs
            category_mappings = {
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
            for category_slug, category_info in Config.CATEGORIES.items():
                category_id = category_mappings.get(category_slug)
                if not category_id:
                    logger.warning(f"No category ID found for slug: {category_slug}")
                    continue
                category_url = category_info['url']
                total_pages = category_info['pages']
                logger.info(f"Processing category: {category_slug} (ID: {category_id}, {total_pages} pages)")
                for page in range(1, total_pages + 1):
                    if page == 1:
                        page_url = f"{self.base_url}{category_url}"
                    else:
                        page_url = f"{self.base_url}{category_url}?page={page}"
                    logger.debug(f"Fetching category page: {page_url}")
                    content = await self.fetch_page_async(page_url)
                    if not content:
                        logger.warning(f"Failed to fetch category page: {page_url}")
                        continue
                    soup = self.parse_html(content)
                    medicine_links = self.extract_medicine_links_from_page(soup)
                    for med_url in medicine_links:
                        medicine_urls.append({
                            'url': med_url,
                            'category_id': category_id
                        })
                    logger.info(f"Found {len(medicine_links)} medicines on page {page} for category {category_slug}")
            logger.info(f"Discovered {len(medicine_urls)} total medicines across all categories")
            return medicine_urls
        except Exception as e:
            logger.error(f"Error discovering medicine URLs: {e}")
            self.log_scraping_event("ERROR", f"Error discovering medicine URLs: {e}")
            return []
    
    def extract_medicine_links_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract individual medicine product links from a category listing page"""
        medicine_links = []
        
        # Based on the search results, products have "Add to cart" buttons
        # Look for product containers that contain "Add to cart" buttons
        product_containers = soup.find_all('div', class_='item')
        
        for container in product_containers:
            # Find the product link within the container
            # Look for links that contain product URLs
            links = container.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and '/medicines/' in href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    elif not href.startswith('http'):
                        href = urljoin(self.base_url, href)
                    
                    # Only include links from the same domain and not already added
                    if self.base_url in href and href not in medicine_links:
                        medicine_links.append(href)
                        break  # Found the product link for this container
        
        # Fallback: if no products found with the above method, try alternative selectors
        if not medicine_links:
            fallback_selectors = [
                'a[href*="/medicines/"]',
                '.product a[href*="/medicines/"]',
                '.item a[href*="/medicines/"]',
                'a[href*="medeasy.health/medicines/"]'
            ]
            
            for selector in fallback_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        elif not href.startswith('http'):
                            href = urljoin(self.base_url, href)
                        
                        # Only include links from the same domain and not already added
                        if self.base_url in href and href not in medicine_links:
                            medicine_links.append(href)
        
        logger.info(f"Extracted {len(medicine_links)} medicine links from page")
        return medicine_links
    
    def extract_medicine_data(self, soup: BeautifulSoup, url: str, category_id: int = None) -> Dict[str, Any]:
        """Extract medicine data from product page using structured data and HTML, using passed category_id"""
        medicine_data = {
            'raw_data': {}
        }
        if category_id is not None:
            medicine_data['category_id'] = category_id
        
        try:
            # 1. Extract from structured data (JSON-LD) - Most reliable
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Product':
                        logger.info(f"Found structured product data for {url}")
                        medicine_data['name'] = data.get('name', '')
                        medicine_data['description'] = data.get('description', '')
                        
                        # Extract price from offers
                        if data.get('offers'):
                            offers = data['offers']
                            if isinstance(offers, list) and offers:
                                offers = offers[0]
                            medicine_data['price'] = float(offers.get('price', 0)) if offers.get('price') else None
                            medicine_data['currency'] = offers.get('priceCurrency', 'BDT')
                        break
                except Exception as e:
                    logger.debug(f"Failed to parse JSON-LD: {e}")
                    continue
            
            # 2. Extract from meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name', '') or meta.get('property', '')
                content = meta.get('content', '')
                
                if 'description' in name.lower() and not medicine_data.get('description'):
                    medicine_data['description'] = content
                elif 'title' in name.lower() and not medicine_data.get('name'):
                    medicine_data['name'] = content.replace(' | MedEasy', '').replace(' | MedEasy | MedEasy', '')
            
            # 3. Extract from HTML elements (fallback)
            if not medicine_data.get('name'):
                name_selectors = ['h1', '.product-title', '.title', '[class*="title"]']
                for selector in name_selectors:
                    element = soup.select_one(selector)
                    if element:
                        medicine_data['name'] = self.clean_text(self.extract_text_safe(element))
                        break
            
            # 4. Extract price from HTML if not found in structured data
            if not medicine_data.get('price'):
                price_selectors = [
                    '.price',
                    '.product-price',
                    '.medicine-price',
                    '[class*="price"]',
                    '.cost',
                    '.amount'
                ]
                
                for selector in price_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        price_text = self.extract_text_safe(element)
                        price = self.extract_price(price_text)
                        if price:
                            medicine_data['price'] = price
                            medicine_data['currency'] = 'BDT'
                            break
                    if medicine_data.get('price'):
                        break
            
            # 5. Extract manufacturer/brand
            manufacturer_selectors = [
                '.manufacturer',
                '.brand',
                '.company',
                '[class*="manufacturer"]',
                '[class*="brand"]',
                '.vendor'
            ]
            
            for selector in manufacturer_selectors:
                element = soup.select_one(selector)
                if element:
                    text = self.clean_text(self.extract_text_safe(element))
                    if text and len(text) < 100:  # Avoid very long text
                        medicine_data['manufacturer'] = text
                        break
            
            # 6. Extract category from URL path and map to category ID
            # category_id = self.extract_category_id_from_url(url) # This line is removed as category_id is now passed
            if category_id:
                medicine_data['category_id'] = category_id
            
            # 7. Extract additional details
            detail_selectors = ['.product-details', '.medicine-details', '.details']
            for selector in detail_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['details'] = self.clean_text(self.extract_text_safe(element))
                    break
            
            # 8. Generate product code
            if not medicine_data.get('product_code'):
                medicine_data['product_code'] = f"ME_{hash(url) % 1000000:06d}"
            
            # 9. Store raw data for flexibility
            medicine_data['raw_data'] = {
                'html_content': str(soup),
                'extracted_fields': {k: v for k, v in medicine_data.items() if k not in ['raw_data']}
            }
            
        except Exception as e:
            logger.error(f"Error extracting medicine data from {url}: {e}")
            self.log_scraping_event("ERROR", f"Error extracting medicine data: {e}", url)
        
        return medicine_data
    
    def extract_category_id_from_url(self, url: str) -> Optional[int]:
        """Extract category ID from URL using hardcoded mapping"""
        from urllib.parse import urlparse
        
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # Hardcoded mapping of URL paths to category IDs
            url_to_category_id_map = {
                '/womens-choice': 1,
                '/sexual-wellness': 2,
                '/skin-care': 3,
                '/diabetic-care': 4,
                '/devices': 5,
                '/supplement': 6,
                '/diapers': 7,
                '/baby-care': 8,
                '/personal-care': 9,
                '/Hygiene-And-Freshness': 10,
                '/hygiene-and-freshness': 10,
                '/dental-care': 11,
                '/Herbal-Medicine': 12,
                '/herbal-medicine': 12,
                '/prescription-medicine': 13,
                '/otc-medicine': 14
            }
            
            # First, try to find category in the URL path
            for url_path, category_id in url_to_category_id_map.items():
                if url_path in path:
                    logger.info(f"Found category from URL path '{url_path}' -> ID: {category_id}")
                    return category_id
            
            # If not found in path, try to extract from medicine URL pattern
            # Medicine URLs are like: /medicines/product-name-category-slug
            if '/medicines/' in path:
                # Extract the last part of the URL which contains the category
                url_parts = path.split('/')
                if len(url_parts) > 2:
                    medicine_slug = url_parts[-1]  # Get the last part
                    
                    # Look for category patterns in the medicine slug
                    category_patterns = {
                        'women-s-choice': 1,
                        'womens-choice': 1,
                        'sexual-wellness': 2,
                        'skin-care': 3,
                        'skincare': 3,
                        'diabetic-care': 4,
                        'diabetes': 4,
                        'devices': 5,
                        'supplement': 6,
                        'supplements': 6,
                        'diapers': 7,
                        'baby-care': 8,
                        'babycare': 8,
                        'personal-care': 9,
                        'personalcare': 9,
                        'hygiene-and-freshness': 10,
                        'hygiene': 10,
                        'dental-care': 11,
                        'dental': 11,
                        'herbal-medicine': 12,
                        'herbal': 12,
                        'prescription-medicine': 13,
                        'prescription': 13,
                        'otc-medicine': 14,
                        'otc': 14
                    }
                    
                    for pattern, category_id in category_patterns.items():
                        if pattern in medicine_slug:
                            logger.info(f"Found category from medicine slug pattern '{pattern}' -> ID: {category_id}")
                            return category_id
            
            logger.warning(f"No category mapping found for URL path: {path}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting category ID from URL {url}: {e}")
            return None
    
    def save_medicine_to_db(self, medicine_data: Dict[str, Any], image_data: Optional[Dict] = None) -> bool:
        """Save medicine data to database with optional image"""
        db = SessionLocal()
        try:
            # Check if medicine already exists by product code
            existing = None
            if medicine_data.get('product_code'):
                existing = db.query(Medicine).filter_by(product_code=medicine_data['product_code']).first()
            
            if existing:
                # Update existing medicine with new data
                for key, value in medicine_data.items():
                    if key != 'raw_data' and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.last_scraped = func.now()
                logger.info(f"Updated existing medicine: {medicine_data.get('name', 'Unknown')}")
                medicine = existing
                
                # Process and save image if provided
                if image_data:
                    try:
                        image_url = self.image_storage.save_image(
                            image_data['image_data'], 
                            existing.id, 
                            image_data['original_url']
                        )
                        
                        if image_url:
                            existing.image_url = image_url
                            logger.info(f"Image saved to server: {image_url}")
                        else:
                            logger.warning("Failed to save image to server")
                            
                    except Exception as e:
                        logger.error(f"Error saving image to server: {e}")
                
                # Update other fields
                for key, value in medicine_data.items():
                    if key not in ['raw_data', 'category', 'subcategory'] and hasattr(existing, key):
                        setattr(existing, key, value)
                
                existing.last_scraped = func.now()
                logger.info(f"Updated existing medicine: {medicine_data.get('name', 'Unknown')}")
                medicine = existing
            else:
                # Map details to dosage_instructions if available
                dosage_instructions = medicine_data.get('details', '') or medicine_data.get('dosage_instructions', '')
                
                # Get category_id from medicine_data (already extracted from URL)
                category_id = medicine_data.get('category_id')
                subcategory_id = None
                
                # Process and save image if provided
                image_url = None
                if image_data:
                    try:
                        # Generate temporary ID for new medicine
                        medicine_id = int(hash(medicine_data.get('name', '')) % 1000000)
                        
                        image_url = self.image_storage.save_image(
                            image_data['image_data'], 
                            medicine_id, 
                            image_data['original_url']
                        )
                        
                        if image_url:
                            logger.info(f"Image saved to server: {image_url}")
                        else:
                            logger.warning("Failed to save image to server")
                            
                    except Exception as e:
                        logger.error(f"Error saving image to server: {e}")
                
                # Create new record with only valid fields
                valid_fields = {
                    'name': medicine_data.get('name', ''),
                    'generic_name': medicine_data.get('generic_name', ''),
                    'brand_name': medicine_data.get('brand_name', ''),
                    'manufacturer': medicine_data.get('manufacturer', ''),
                    'strength': medicine_data.get('strength', ''),
                    'dosage_form': medicine_data.get('dosage_form', ''),
                    'pack_size': medicine_data.get('pack_size', ''),
                    'price': medicine_data.get('price'),
                    'currency': medicine_data.get('currency', 'BDT'),
                    'description': medicine_data.get('description', ''),
                    'indications': medicine_data.get('indications', ''),
                    'contraindications': medicine_data.get('contraindications', ''),
                    'side_effects': medicine_data.get('side_effects', ''),
                    'dosage_instructions': dosage_instructions,
                    'storage_conditions': medicine_data.get('storage_conditions', ''),
                    'product_code': medicine_data.get('product_code', ''),
                    'category_id': category_id,
                    'subcategory_id': subcategory_id,
                    'image_url': image_url,
                    'raw_data': medicine_data.get('raw_data', {}),
                    'is_active': True
                }
                
                medicine = Medicine(**valid_fields)
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
    
    async def scrape_medicine_page(self, url: str, category_id: int = None) -> bool:
        """Scrape a single medicine page, using passed category_id"""
        try:
            logger.info(f"Scraping medicine page: {url}")
            content = await self.fetch_page_async(url)
            if not content:
                logger.warning(f"Failed to fetch content from: {url}")
                return False
            soup = self.parse_html(content)
            medicine_data = self.extract_medicine_data(soup, url, category_id)
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
            if medicine_data.get('name'):
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
        """Main method to scrape all medicines, using category_id from discovery"""
        try:
            logger.info("Starting MedEasy medicine scraping (local)")
            self.log_scraping_event("INFO", "Starting MedEasy medicine scraping (local)")
            resume_data = None
            if resume:
                resume_data = self.get_resume_data()
                if resume_data:
                    logger.info("Resuming from previous session")
                    self.log_scraping_event("INFO", "Resuming from previous session")
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
            self.update_progress(1, 1, processed_items, total_items)
            for idx, med_info in enumerate(medicine_urls[current_index:], current_index):
                try:
                    url = med_info['url']
                    category_id = med_info.get('category_id')
                    logger.info(f"Processing medicine {idx + 1}/{total_items}: {url} (Category ID: {category_id})")
                    success = await self.scrape_medicine_page(url, category_id)
                    if success:
                        processed_items += 1
                    self.update_progress(1, 1, processed_items, total_items)
                    resume_data = {
                        'medicine_urls': medicine_urls,
                        'current_index': idx + 1,
                        'processed_items': processed_items
                    }
                    self.save_resume_data(resume_data)
                except Exception as e:
                    logger.error(f"Error processing medicine {url}: {e}")
                    self.log_scraping_event("ERROR", f"Error processing medicine: {e}", url)
            self.update_progress(1, 1, processed_items, total_items, "completed")
            logger.info(f"Scraping completed. Processed {processed_items} medicines")
            self.log_scraping_event("INFO", f"Scraping completed. Processed {processed_items} medicines")
        except Exception as e:
            logger.error(f"Error in scrape_all_medicines: {e}")
            self.log_scraping_event("ERROR", f"Error in scrape_all_medicines: {e}")
            self.update_progress(0, 0, 0, 0, "failed")
        finally:
            await self.close() 
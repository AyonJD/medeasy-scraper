import requests
import io
from PIL import Image
from loguru import logger
import hashlib
from typing import Optional, Tuple
import time

class ImageProcessor:
    """Utility class for downloading and processing images to WebP format"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def download_and_convert_to_webp(self, image_url: str, quality: int = 95, max_size: Tuple[int, int] = (2048, 2048)) -> Optional[dict]:
        """
        Download image from URL and convert to WebP format
        
        Args:
            image_url: URL of the image to download
            quality: WebP quality (1-100) - increased to 95 for better quality
            max_size: Maximum dimensions (width, height) - increased to 2048x2048 for higher resolution
            
        Returns:
            Dictionary with image data and metadata, or None if failed
        """
        if not image_url:
            logger.warning("No image URL provided")
            return None
            
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Downloading image from {image_url} (attempt {attempt + 1})")
                
                # Download image
                response = self.session.get(image_url, timeout=self.timeout)
                response.raise_for_status()
                
                # Open image with PIL
                image = Image.open(io.BytesIO(response.content))
                
                # Convert to RGB if necessary (WebP doesn't support RGBA)
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Resize if too large (only if significantly larger than max_size)
                original_size = image.size
                if image.size[0] > max_size[0] * 1.2 or image.size[1] > max_size[1] * 1.2:
                    # Use LANCZOS resampling for better quality
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.debug(f"Resized image from {original_size} to {image.size}")
                else:
                    logger.debug(f"Keeping original image size: {original_size}")
                
                # Convert to WebP with high quality settings
                webp_buffer = io.BytesIO()
                image.save(webp_buffer, format='WEBP', quality=quality, optimize=True, method=6)
                webp_data = webp_buffer.getvalue()
                
                # Calculate file size
                file_size = len(webp_data)
                
                # Generate hash for deduplication
                image_hash = hashlib.md5(webp_data).hexdigest()
                
                result = {
                    'image_data': webp_data,
                    'original_url': image_url,
                    'file_size': file_size,
                    'width': image.size[0],
                    'height': image.size[1],
                    'format': 'WEBP',
                    'quality': quality,
                    'hash': image_hash,
                    'original_size': original_size
                }
                
                logger.debug(f"Successfully processed image: {image.size[0]}x{image.size[1]}, {file_size} bytes")
                return result
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to download image from {image_url} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # Wait before retry
                continue
                
            except Exception as e:
                logger.error(f"Error processing image from {image_url}: {e}")
                return None
        
        logger.error(f"Failed to download image from {image_url} after {self.max_retries} attempts")
        return None
    
    def process_image_data(self, image_data: bytes, original_url: str = "", quality: int = 95, max_size: Tuple[int, int] = (2048, 2048)) -> Optional[dict]:
        """
        Process existing image data and convert to WebP
        
        Args:
            image_data: Raw image data
            original_url: Original URL for reference
            quality: WebP quality (1-100) - increased to 95 for better quality
            max_size: Maximum dimensions (width, height) - increased to 2048x2048 for higher resolution
            
        Returns:
            Dictionary with processed image data and metadata, or None if failed
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (only if significantly larger than max_size)
            original_size = image.size
            if image.size[0] > max_size[0] * 1.2 or image.size[1] > max_size[1] * 1.2:
                # Use LANCZOS resampling for better quality
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized image from {original_size} to {image.size}")
            else:
                logger.debug(f"Keeping original image size: {original_size}")
            
            # Convert to WebP with high quality settings
            webp_buffer = io.BytesIO()
            image.save(webp_buffer, format='WEBP', quality=quality, optimize=True, method=6)
            webp_data = webp_buffer.getvalue()
            
            # Calculate file size
            file_size = len(webp_data)
            
            # Generate hash
            image_hash = hashlib.md5(webp_data).hexdigest()
            
            result = {
                'image_data': webp_data,
                'original_url': original_url,
                'file_size': file_size,
                'width': image.size[0],
                'height': image.size[1],
                'format': 'WEBP',
                'quality': quality,
                'hash': image_hash,
                'original_size': original_size
            }
            
            logger.debug(f"Successfully processed image data: {image.size[0]}x{image.size[1]}, {file_size} bytes")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image data: {e}")
            return None
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
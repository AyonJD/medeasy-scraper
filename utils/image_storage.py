import os
import hashlib
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
from datetime import datetime

class ImageStorage:
    """Utility class for storing images on the server filesystem"""
    
    def __init__(self, base_path: str = "static/images", base_url: str = "/images"):
        """
        Initialize image storage
        
        Args:
            base_path: Directory to store images (relative to project root)
            base_url: Base URL for serving images
        """
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip('/')
        
        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create year/month subdirectories for organization
        current_date = datetime.now()
        self.year_month_path = self.base_path / str(current_date.year) / f"{current_date.month:02d}"
        self.year_month_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Image storage initialized: {self.base_path}")
    
    def save_image(self, image_data: bytes, medicine_id: int, original_url: str = "") -> Optional[str]:
        """
        Save image data to filesystem and return the URL
        
        Args:
            image_data: WebP image data
            medicine_id: Medicine ID for filename
            original_url: Original URL for reference
            
        Returns:
            URL to access the image, or None if failed
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_hash = hashlib.md5(image_data).hexdigest()[:8]
            filename = f"medicine_{medicine_id}_{timestamp}_{image_hash}.webp"
            
            # Full path for saving
            file_path = self.year_month_path / filename
            
            # Save image to filesystem
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            # Generate URL
            relative_path = file_path.relative_to(self.base_path)
            image_url = f"{self.base_url}/{relative_path}"
            
            logger.info(f"Image saved: {file_path} -> {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Error saving image for medicine {medicine_id}: {e}")
            return None
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from filesystem
        
        Args:
            image_url: URL of the image to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Extract path from URL
            if image_url.startswith(self.base_url):
                relative_path = image_url[len(self.base_url):].lstrip('/')
                file_path = self.base_path / relative_path
                
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Image deleted: {file_path}")
                    return True
                else:
                    logger.warning(f"Image file not found: {file_path}")
                    return False
            else:
                logger.error(f"Invalid image URL format: {image_url}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image {image_url}: {e}")
            return False
    
    def get_image_path(self, image_url: str) -> Optional[Path]:
        """
        Get filesystem path from image URL
        
        Args:
            image_url: URL of the image
            
        Returns:
            Path object or None if invalid
        """
        try:
            if image_url.startswith(self.base_url):
                relative_path = image_url[len(self.base_url):].lstrip('/')
                return self.base_path / relative_path
            return None
        except Exception as e:
            logger.error(f"Error getting image path for {image_url}: {e}")
            return None
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            total_files = 0
            total_size = 0
            
            for file_path in self.base_path.rglob("*.webp"):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "base_path": str(self.base_path),
                "base_url": self.base_url
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}
    
    def cleanup_old_images(self, days_old: int = 30) -> int:
        """
        Clean up old images (optional maintenance)
        
        Args:
            days_old: Delete images older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0
            
            for file_path in self.base_path.rglob("*.webp"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old images")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old images: {e}")
            return 0 
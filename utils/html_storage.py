import os
import hashlib
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
from datetime import datetime

class HtmlStorage:
    """Utility class for storing medicine HTML files on the server filesystem"""
    
    def __init__(self, base_path: str = "static/html", base_url: str = "/html"):
        """
        Initialize HTML storage
        
        Args:
            base_path: Directory to store HTML files (relative to project root)
            base_url: Base URL for serving HTML files
        """
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip('/')
        
        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create year/month subdirectories for organization
        current_date = datetime.now()
        self.year_month_path = self.base_path / str(current_date.year) / f"{current_date.month:02d}"
        self.year_month_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"HTML storage initialized: {self.base_path}")
    
    def save_html(self, html_content: str, medicine_id: int, original_url: str = "") -> Optional[str]:
        """
        Save HTML content to filesystem and return the URL
        
        Args:
            html_content: Raw HTML content
            medicine_id: Medicine ID for filename
            original_url: Original URL for reference
            
        Returns:
            URL to access the HTML file, or None if failed
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_hash = hashlib.md5(html_content.encode('utf-8')).hexdigest()[:8]
            filename = f"medicine_{medicine_id}_{timestamp}_{html_hash}.html"
            
            # Full path for saving
            file_path = self.year_month_path / filename
            
            # Save HTML to filesystem
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate URL
            relative_path = file_path.relative_to(self.base_path)
            html_url = f"{self.base_url}/{relative_path}"
            
            logger.info(f"HTML saved: {file_path} -> {html_url}")
            return html_url
            
        except Exception as e:
            logger.error(f"Error saving HTML for medicine {medicine_id}: {e}")
            return None
    
    def delete_html(self, html_url: str) -> bool:
        """
        Delete HTML file from filesystem
        
        Args:
            html_url: URL of the HTML file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Extract path from URL
            if html_url.startswith(self.base_url):
                relative_path = html_url[len(self.base_url):].lstrip('/')
                file_path = self.base_path / relative_path
                
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"HTML file deleted: {file_path}")
                    return True
                else:
                    logger.warning(f"HTML file not found: {file_path}")
                    return False
            else:
                logger.error(f"Invalid HTML URL format: {html_url}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting HTML file {html_url}: {e}")
            return False
    
    def get_html_path(self, html_url: str) -> Optional[Path]:
        """
        Get filesystem path from HTML URL
        
        Args:
            html_url: URL of the HTML file
            
        Returns:
            Path object or None if invalid
        """
        try:
            if html_url.startswith(self.base_url):
                relative_path = html_url[len(self.base_url):].lstrip('/')
                return self.base_path / relative_path
            return None
        except Exception as e:
            logger.error(f"Error getting HTML path for {html_url}: {e}")
            return None
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            total_files = 0
            total_size = 0
            
            for file_path in self.base_path.rglob("*.html"):
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
    
    def cleanup_old_html(self, days_old: int = 30) -> int:
        """
        Clean up old HTML files (optional maintenance)
        
        Args:
            days_old: Delete HTML files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0
            
            for file_path in self.base_path.rglob("*.html"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old HTML files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old HTML files: {e}")
            return 0 
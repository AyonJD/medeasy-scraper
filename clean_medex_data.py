#!/usr/bin/env python3
"""
Clean MedEx Scraped Data
Remove all scraped HTML files, images, and database records for a fresh start
"""

import os
import shutil
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import Session
from database.connection_local import SessionLocal, engine
from database.models import Medicine, MedicineImage, ScrapingProgress, ScrapingLog
from utils.html_storage import HtmlStorage
from utils.image_storage import ImageStorage

def setup_logging():
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

def clean_html_files():
    """Remove all HTML files"""
    html_storage = HtmlStorage()
    base_path = Path("static/html")
    
    if base_path.exists():
        # Count files before deletion
        html_files = list(base_path.rglob("*.html"))
        count = len(html_files)
        
        if count > 0:
            logger.info(f"🗑️  Found {count} HTML files to delete...")
            
            # Remove all HTML files
            for html_file in html_files:
                try:
                    html_file.unlink()
                    logger.debug(f"   Deleted: {html_file}")
                except Exception as e:
                    logger.warning(f"   Failed to delete {html_file}: {e}")
            
            # Remove empty directories
            for root, dirs, files in os.walk(base_path, topdown=False):
                for directory in dirs:
                    dir_path = Path(root) / directory
                    try:
                        if not any(dir_path.iterdir()):  # If directory is empty
                            dir_path.rmdir()
                            logger.debug(f"   Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty, skip
            
            logger.success(f"✅ Deleted {count} HTML files")
        else:
            logger.info("📂 No HTML files found to delete")
    else:
        logger.info("📂 HTML directory doesn't exist")

def clean_image_files():
    """Remove all medicine image files"""
    image_storage = ImageStorage()
    base_path = Path("static/images")
    
    if base_path.exists():
        # Count image files before deletion
        image_files = list(base_path.rglob("*.webp"))
        count = len(image_files)
        
        if count > 0:
            logger.info(f"🖼️  Found {count} image files to delete...")
            
            # Remove all image files
            for image_file in image_files:
                try:
                    image_file.unlink()
                    logger.debug(f"   Deleted: {image_file}")
                except Exception as e:
                    logger.warning(f"   Failed to delete {image_file}: {e}")
            
            # Remove empty directories
            for root, dirs, files in os.walk(base_path, topdown=False):
                for directory in dirs:
                    dir_path = Path(root) / directory
                    try:
                        if not any(dir_path.iterdir()):  # If directory is empty
                            dir_path.rmdir()
                            logger.debug(f"   Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty, skip
            
            logger.success(f"✅ Deleted {count} image files")
        else:
            logger.info("🖼️  No image files found to delete")
    else:
        logger.info("📂 Images directory doesn't exist")

def clean_database_records():
    """Remove all medicine records from database"""
    try:
        db = SessionLocal()
        
        # Count records before deletion
        medicine_count = db.query(Medicine).count()
        image_count = db.query(MedicineImage).count()
        progress_count = db.query(ScrapingProgress).count()
        log_count = db.query(ScrapingLog).count()
        
        logger.info(f"💾 Database records found:")
        logger.info(f"   • Medicines: {medicine_count}")
        logger.info(f"   • Images: {image_count}")
        logger.info(f"   • Progress: {progress_count}")
        logger.info(f"   • Logs: {log_count}")
        
        if medicine_count > 0 or image_count > 0 or progress_count > 0 or log_count > 0:
            logger.info("🗑️  Deleting database records...")
            
            # Delete in correct order (foreign key constraints)
            db.query(MedicineImage).delete()  # Delete images first
            db.query(Medicine).delete()       # Then medicines
            db.query(ScrapingProgress).delete()  # Delete progress
            db.query(ScrapingLog).delete()    # Delete logs
            
            db.commit()
            logger.success("✅ All database records deleted")
        else:
            logger.info("💾 No database records to delete")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Error cleaning database: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

def clean_log_files():
    """Clean old log files"""
    log_files = [
        "logs/medex_scraper.log",
        "medex_scraper.log"  # In case it's in root
    ]
    
    cleaned_count = 0
    for log_file in log_files:
        log_path = Path(log_file)
        if log_path.exists():
            try:
                log_path.unlink()
                logger.info(f"🗑️  Deleted log file: {log_file}")
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"   Failed to delete {log_file}: {e}")
    
    if cleaned_count > 0:
        logger.success(f"✅ Deleted {cleaned_count} log files")
    else:
        logger.info("📝 No log files found to delete")

def display_summary():
    """Display cleanup summary"""
    logger.info("\n" + "="*60)
    logger.info("🎯 CLEANUP SUMMARY")
    logger.info("="*60)
    
    # Check remaining files
    html_path = Path("static/html")
    image_path = Path("static/images")
    
    remaining_html = len(list(html_path.rglob("*.html"))) if html_path.exists() else 0
    remaining_images = len(list(image_path.rglob("*.webp"))) if image_path.exists() else 0
    
    try:
        db = SessionLocal()
        remaining_medicines = db.query(Medicine).count()
        remaining_images_db = db.query(MedicineImage).count()
        db.close()
    except:
        remaining_medicines = "Error checking"
        remaining_images_db = "Error checking"
    
    logger.info(f"📂 Remaining HTML files: {remaining_html}")
    logger.info(f"🖼️  Remaining image files: {remaining_images}")
    logger.info(f"💾 Remaining medicines in DB: {remaining_medicines}")
    logger.info(f"💾 Remaining images in DB: {remaining_images_db}")
    
    if remaining_html == 0 and remaining_images == 0 and remaining_medicines == 0:
        logger.success("\n🎉 SUCCESS: All MedEx data has been cleaned!")
        logger.success("   You can now start fresh with the scraper.")
    else:
        logger.warning("\n⚠️  Some files may still remain. Check manually if needed.")

def main():
    setup_logging()
    
    logger.info("🧹 MedEx Data Cleanup Tool")
    logger.info("="*50)
    logger.info("This will delete ALL scraped MedEx data:")
    logger.info("• HTML files in static/html/")
    logger.info("• Image files in static/images/")
    logger.info("• All medicine records in database")
    logger.info("• Scraping progress and logs")
    logger.info("")
    
    # Ask for confirmation
    try:
        confirm = input("❓ Are you sure you want to proceed? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            logger.info("❌ Cleanup cancelled by user")
            return
    except KeyboardInterrupt:
        logger.info("\n❌ Cleanup cancelled by user")
        return
    
    logger.info("\n🚀 Starting cleanup process...")
    logger.info("-" * 40)
    
    # Perform cleanup
    clean_html_files()
    clean_image_files()
    clean_database_records()
    clean_log_files()
    
    # Display summary
    display_summary()

if __name__ == "__main__":
    main() 
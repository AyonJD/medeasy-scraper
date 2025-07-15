#!/usr/bin/env python3
"""
Script to clear all medicines, images, and related data from the database
"""

import os
from loguru import logger
from database.connection_local import SessionLocal
from database.models import Medicine, MedicineImage, Category, ScrapingProgress, ScrapingLog
from utils.image_storage import ImageStorage

def clear_all_data():
    """Clear all data from the database and delete image files"""
    
    logger.info("Starting data cleanup...")
    
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Get counts before deletion
        medicine_count = db.query(Medicine).count()
        image_count = db.query(MedicineImage).count()
        category_count = db.query(Category).count()
        progress_count = db.query(ScrapingProgress).count()
        log_count = db.query(ScrapingLog).count()
        
        logger.info(f"Current data counts:")
        logger.info(f"  - Medicines: {medicine_count}")
        logger.info(f"  - Images: {image_count}")
        logger.info(f"  - Categories: {category_count}")
        logger.info(f"  - Scraping Progress: {progress_count}")
        logger.info(f"  - Scraping Logs: {log_count}")
        
        # Delete all data
        logger.info("Deleting all data...")
        
        # Delete images first (due to foreign key constraints)
        deleted_images = db.query(MedicineImage).delete()
        logger.info(f"Deleted {deleted_images} images")
        
        # Delete medicines
        deleted_medicines = db.query(Medicine).delete()
        logger.info(f"Deleted {deleted_medicines} medicines")
        
        # Delete categories
        deleted_categories = db.query(Category).delete()
        logger.info(f"Deleted {deleted_categories} categories")
        
        # Delete scraping progress
        deleted_progress = db.query(ScrapingProgress).delete()
        logger.info(f"Deleted {deleted_progress} scraping progress records")
        
        # Delete scraping logs
        deleted_logs = db.query(ScrapingLog).delete()
        logger.info(f"Deleted {deleted_logs} scraping log records")
        
        # Commit the changes
        db.commit()
        logger.success("✅ All database data cleared successfully!")
        
        # Clear image files from filesystem
        logger.info("Clearing image files from filesystem...")
        image_storage = ImageStorage()
        
        # Get storage stats before cleanup
        stats_before = image_storage.get_storage_stats()
        logger.info(f"Image storage before cleanup: {stats_before.get('total_files', 0)} files, {stats_before.get('total_size_mb', 0):.2f} MB")
        
        # Delete all image files
        deleted_files = 0
        total_size = 0
        
        for file_path in image_storage.base_path.rglob("*.webp"):
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_files += 1
                    total_size += file_size
                    logger.debug(f"Deleted: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
        
        logger.success(f"✅ Deleted {deleted_files} image files ({total_size / (1024*1024):.2f} MB)")
        
        # Verify cleanup
        stats_after = image_storage.get_storage_stats()
        logger.info(f"Image storage after cleanup: {stats_after.get('total_files', 0)} files, {stats_after.get('total_size_mb', 0):.2f} MB")
        
        # Final verification
        final_medicine_count = db.query(Medicine).count()
        final_image_count = db.query(MedicineImage).count()
        final_category_count = db.query(Category).count()
        
        logger.info(f"Final verification:")
        logger.info(f"  - Medicines: {final_medicine_count}")
        logger.info(f"  - Images: {final_image_count}")
        logger.info(f"  - Categories: {final_category_count}")
        
        if final_medicine_count == 0 and final_image_count == 0 and final_category_count == 0:
            logger.success("✅ Database is completely empty!")
        else:
            logger.warning("⚠️ Some data may still exist in the database")
            
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def reset_database():
    """Reset the entire database by deleting the file and recreating it"""
    
    logger.info("Resetting entire database...")
    
    # Close any existing connections
    db = SessionLocal()
    db.close()
    
    # Delete the database file
    db_file = "medeasy_local.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            logger.success(f"✅ Deleted database file: {db_file}")
        except Exception as e:
            logger.error(f"Failed to delete database file: {e}")
            return False
    
    # Recreate the database
    try:
        from database.connection_local import init_db
        init_db()
        logger.success("✅ Database recreated successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to recreate database: {e}")
        return False

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    print("🗑️ Clearing All Data")
    print("=" * 50)
    
    # Ask user what they want to do
    print("\nChoose an option:")
    print("1. Clear all data but keep database structure")
    print("2. Reset entire database (delete and recreate)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        clear_all_data()
    elif choice == "2":
        reset_database()
    else:
        print("Invalid choice. Exiting.") 
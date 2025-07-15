#!/usr/bin/env python3
"""
Script to clear all medicine and image data from database and filesystem
"""

import sys
import os
import shutil
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_local import SessionLocal, init_db
from database.models import Medicine, MedicineImage, Category, ScrapingProgress, ScrapingLog
from utils.image_storage import ImageStorage
from loguru import logger

def clear_all_data():
    """Clear all data from database and filesystem"""
    
    # Clear database
    db = SessionLocal()
    try:
        logger.info("Clearing database...")
        
        # Clear medicines and related data
        deleted_medicines = db.query(Medicine).delete()
        logger.info(f"Deleted {deleted_medicines} medicines")
        
        # Clear images
        deleted_images = db.query(MedicineImage).delete()
        logger.info(f"Deleted {deleted_images} medicine images")
        
        # Clear categories
        deleted_categories = db.query(Category).delete()
        logger.info(f"Deleted {deleted_categories} categories")
        
        # Clear scraping progress
        deleted_progress = db.query(ScrapingProgress).delete()
        logger.info(f"Deleted {deleted_progress} scraping progress records")
        
        # Clear scraping logs
        deleted_logs = db.query(ScrapingLog).delete()
        logger.info(f"Deleted {deleted_logs} scraping log records")
        
        db.commit()
        logger.success("Database cleared successfully!")
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    # Clear filesystem images
    try:
        logger.info("Clearing filesystem images...")
        
        # Get project root
        project_root = Path(__file__).parent.parent
        static_images_path = project_root / "static" / "images"
        
        if static_images_path.exists():
            # Delete all image files
            image_count = 0
            for image_file in static_images_path.rglob("*.webp"):
                image_file.unlink()
                image_count += 1
            
            logger.info(f"Deleted {image_count} image files")
            
            # Remove empty directories
            for dir_path in reversed(list(static_images_path.rglob("*"))):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    logger.debug(f"Removed empty directory: {dir_path}")
            
            logger.success("Filesystem images cleared successfully!")
        else:
            logger.info("No static/images directory found")
            
    except Exception as e:
        logger.error(f"Error clearing filesystem images: {e}")
        raise

def reset_database():
    """Drop all tables and recreate them"""
    try:
        logger.info("Resetting database...")
        
        from database.connection_local import engine
        from database.models import Base
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables recreated")
        
        logger.success("Database reset successfully!")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

def create_static_directories():
    """Create necessary static directories"""
    try:
        logger.info("Creating static directories...")
        
        project_root = Path(__file__).parent.parent
        static_path = project_root / "static"
        images_path = static_path / "images"
        
        # Create directories
        static_path.mkdir(exist_ok=True)
        images_path.mkdir(exist_ok=True)
        
        logger.success(f"Static directories created: {images_path}")
        
    except Exception as e:
        logger.error(f"Error creating static directories: {e}")
        raise

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear all MedEasy data")
    parser.add_argument("--reset-db", action="store_true", 
                       help="Reset database (drop and recreate tables)")
    parser.add_argument("--confirm", action="store_true", 
                       help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    if not args.confirm:
        if args.reset_db:
            confirm = input("\n⚠️  This will DELETE ALL DATA and RESET THE DATABASE. Continue? (y/N): ")
        else:
            confirm = input("\n⚠️  This will delete all medicine and image data. Continue? (y/N): ")
        
        if confirm.lower() != 'y':
            logger.info("Operation cancelled")
            sys.exit(0)
    
    try:
        # Create static directories first
        create_static_directories()
        
        if args.reset_db:
            reset_database()
        else:
            clear_all_data()
        
        logger.success("All data cleared successfully!")
        
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
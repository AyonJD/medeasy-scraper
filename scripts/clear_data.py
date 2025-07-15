#!/usr/bin/env python3
"""
Script to clear extracted data from the MedEasy database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal, engine
from database.models import Medicine, ScrapingProgress, ScrapingLog
from sqlalchemy import text
from loguru import logger

def clear_all_data():
    """Clear all data from all tables"""
    db = SessionLocal()
    try:
        # Clear medicines table
        deleted_medicines = db.query(Medicine).delete()
        logger.info(f"Deleted {deleted_medicines} medicines")
        
        # Clear scraping progress
        deleted_progress = db.query(ScrapingProgress).delete()
        logger.info(f"Deleted {deleted_progress} scraping progress records")
        
        # Clear scraping logs
        deleted_logs = db.query(ScrapingLog).delete()
        logger.info(f"Deleted {deleted_logs} scraping log records")
        
        db.commit()
        logger.success("All data cleared successfully!")
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def clear_medicines_only():
    """Clear only medicines data, keep progress and logs"""
    db = SessionLocal()
    try:
        deleted_medicines = db.query(Medicine).delete()
        logger.info(f"Deleted {deleted_medicines} medicines")
        
        db.commit()
        logger.success("Medicines data cleared successfully!")
        
    except Exception as e:
        logger.error(f"Error clearing medicines: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def clear_progress_and_logs():
    """Clear only progress and logs, keep medicines"""
    db = SessionLocal()
    try:
        # Clear scraping progress
        deleted_progress = db.query(ScrapingProgress).delete()
        logger.info(f"Deleted {deleted_progress} scraping progress records")
        
        # Clear scraping logs
        deleted_logs = db.query(ScrapingLog).delete()
        logger.info(f"Deleted {deleted_logs} scraping log records")
        
        db.commit()
        logger.success("Progress and logs cleared successfully!")
        
    except Exception as e:
        logger.error(f"Error clearing progress and logs: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_data_counts():
    """Get current data counts"""
    db = SessionLocal()
    try:
        medicine_count = db.query(Medicine).count()
        progress_count = db.query(ScrapingProgress).count()
        log_count = db.query(ScrapingLog).count()
        
        logger.info(f"Current data counts:")
        logger.info(f"  Medicines: {medicine_count}")
        logger.info(f"  Scraping Progress: {progress_count}")
        logger.info(f"  Scraping Logs: {log_count}")
        
        return medicine_count, progress_count, log_count
        
    except Exception as e:
        logger.error(f"Error getting counts: {e}")
        raise
    finally:
        db.close()

def reset_database():
    """Drop all tables and recreate them (nuclear option)"""
    from database.models import Base
    
    try:
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

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear MedEasy database data")
    parser.add_argument("--action", choices=["all", "medicines", "progress", "counts", "reset"], 
                       default="all", help="What to clear")
    parser.add_argument("--confirm", action="store_true", 
                       help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    # Show current counts first
    logger.info("Current database state:")
    get_data_counts()
    
    if args.action == "counts":
        sys.exit(0)
    
    # Confirmation prompt
    if not args.confirm:
        if args.action == "all":
            confirm = input("\n⚠️  This will delete ALL data (medicines, progress, logs). Continue? (y/N): ")
        elif args.action == "medicines":
            confirm = input("\n⚠️  This will delete all medicines data. Continue? (y/N): ")
        elif args.action == "progress":
            confirm = input("\n⚠️  This will delete all progress and logs. Continue? (y/N): ")
        elif args.action == "reset":
            confirm = input("\n⚠️  This will DROP ALL TABLES and recreate them. Continue? (y/N): ")
        
        if confirm.lower() != 'y':
            logger.info("Operation cancelled")
            sys.exit(0)
    
    # Execute the requested action
    try:
        if args.action == "all":
            clear_all_data()
        elif args.action == "medicines":
            clear_medicines_only()
        elif args.action == "progress":
            clear_progress_and_logs()
        elif args.action == "reset":
            reset_database()
        
        # Show final counts
        logger.info("\nFinal database state:")
        get_data_counts()
        
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        sys.exit(1) 
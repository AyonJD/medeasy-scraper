#!/usr/bin/env python3
"""
Script to clear medicines data from the local MedEasy database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_local import SessionLocal
from database.models import Medicine
from loguru import logger

def clear_medicines():
    """Clear all medicines data"""
    db = SessionLocal()
    try:
        # Get count before deletion
        medicine_count = db.query(Medicine).count()
        logger.info(f"Found {medicine_count} medicines to delete")
        
        # Clear medicines table
        deleted_medicines = db.query(Medicine).delete()
        logger.info(f"Deleted {deleted_medicines} medicines")
        
        db.commit()
        logger.success("Medicines data cleared successfully!")
        
        # Verify deletion
        final_count = db.query(Medicine).count()
        logger.info(f"Final medicine count: {final_count}")
        
    except Exception as e:
        logger.error(f"Error clearing medicines: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Clearing all medicines data...")
    clear_medicines()
    logger.info("Done!") 
#!/usr/bin/env python3
"""
Simple script to delete the database file directly
"""

import os
import sys
from pathlib import Path
from loguru import logger

def delete_database_file():
    """Delete the SQLite database file"""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    db_file = project_root / "medeasy_local.db"
    
    if db_file.exists():
        try:
            # Get file size for logging
            file_size = db_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Found database file: {db_file}")
            logger.info(f"File size: {file_size_mb:.2f} MB")
            
            # Delete the file
            db_file.unlink()
            logger.success(f"Database file deleted: {db_file}")
            
        except Exception as e:
            logger.error(f"Error deleting database file: {e}")
            return False
    else:
        logger.warning(f"Database file not found: {db_file}")
        return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Delete MedEasy database file")
    parser.add_argument("--confirm", action="store_true", 
                       help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    if not args.confirm:
        confirm = input("\n⚠️  This will delete the entire database file. Continue? (y/N): ")
        if confirm.lower() != 'y':
            logger.info("Operation cancelled")
            sys.exit(0)
    
    success = delete_database_file()
    if success:
        logger.info("Database file deleted successfully!")
    else:
        logger.error("Failed to delete database file")
        sys.exit(1) 
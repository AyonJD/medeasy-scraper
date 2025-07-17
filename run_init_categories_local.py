#!/usr/bin/env python3
"""
Simple script to run category initialization for LOCAL environment only
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.init_categories import init_categories_local
from loguru import logger

if __name__ == "__main__":
    logger.info("Initializing categories for LOCAL environment only...")
    try:
        init_categories_local()
        logger.success("Local category initialization completed successfully!")
    except Exception as e:
        logger.error(f"Local category initialization failed: {e}")
        sys.exit(1) 
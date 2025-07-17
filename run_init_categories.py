#!/usr/bin/env python3
"""
Simple script to run category initialization
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.init_categories import main

if __name__ == "__main__":
    main() 
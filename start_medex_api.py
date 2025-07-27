#!/usr/bin/env python3
"""
Quick Start Script for MedEx Scraper API
Automatically detects Python executable and starts the server
"""

import sys
import os
import subprocess
from pathlib import Path

def find_python_executable():
    """Find the correct Python executable"""
    # Try different Python commands
    python_commands = [
        "python",
        "python3", 
        "py",
        sys.executable
    ]
    
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and "Python 3" in result.stdout:
                return cmd
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    return None

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import selenium
        import loguru
        import sqlalchemy
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def main():
    print("🚀 Starting MedEx Scraper API Server...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("api/main_medex.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   Make sure 'api/main_medex.py' exists in the current directory")
        sys.exit(1)
    
    # Find Python executable
    python_cmd = find_python_executable()
    if not python_cmd:
        print("❌ Error: Could not find Python 3 executable")
        print("   Please ensure Python 3.7+ is installed and accessible")
        sys.exit(1)
    
    print(f"✅ Found Python: {python_cmd}")
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Missing dependencies. Install them with:")
        print(f"   {python_cmd} -m pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ All dependencies found")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("static/html", exist_ok=True)
    os.makedirs("static/images", exist_ok=True)
    print("✅ Created necessary directories")
    
    # Start the server
    print("\n🌟 Starting API server...")
    print("📋 API will be available at:")
    print("   • Documentation: http://localhost:8000/docs")
    print("   • API Base URL: http://localhost:8000")
    print("   • Alternative Docs: http://localhost:8000/redoc")
    print("\n⚡ Starting server (Press Ctrl+C to stop)...")
    
    try:
        # Start uvicorn server
        cmd = [
            python_cmd, "-m", "uvicorn", 
            "api.main_medex:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTry running manually:")
        print(f"   {python_cmd} -m uvicorn api.main_medex:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    main() 
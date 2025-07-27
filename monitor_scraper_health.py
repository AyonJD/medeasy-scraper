#!/usr/bin/env python3
"""
MedEx Scraper Health Monitor
Monitor scraper performance and detect potential blocking issues
"""

import time
import requests
from datetime import datetime, timedelta
from loguru import logger
from database.connection_local import SessionLocal
from database.models import Medicine, ScrapingLog
from sqlalchemy import func, desc
import re

def setup_logging():
    """Setup logging"""
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

def check_scraper_performance():
    """Check recent scraper performance"""
    try:
        db = SessionLocal()
        
        # Check medicines added in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_medicines = db.query(Medicine).filter(
            Medicine.created_at >= one_hour_ago
        ).count()
        
        # Check total medicines
        total_medicines = db.query(Medicine).count()
        
        # Get latest medicine
        latest_medicine = db.query(Medicine).order_by(desc(Medicine.created_at)).first()
        
        logger.info(f"📊 SCRAPER PERFORMANCE")
        logger.info(f"   • Total medicines: {total_medicines}")
        logger.info(f"   • Added last hour: {recent_medicines}")
        
        if latest_medicine:
            time_diff = datetime.now() - latest_medicine.created_at
            logger.info(f"   • Last medicine: {time_diff.seconds // 60}m ago")
            
            # Calculate rate
            if recent_medicines > 0:
                rate = recent_medicines  # per hour
                logger.info(f"   • Current rate: ~{rate} medicines/hour")
                
                if rate < 5:
                    logger.warning("⚠️  Low scraping rate - possible issues!")
                elif rate > 20:
                    logger.success("🚀 Excellent scraping rate!")
                else:
                    logger.info("✅ Normal scraping rate")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error checking performance: {e}")

def check_for_blocking_signs():
    """Check log files for blocking indicators"""
    try:
        log_file = "logs/medex_scraper.log"
        
        # Read recent log entries
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check last 100 lines
        recent_lines = lines[-100:] if len(lines) > 100 else lines
        
        blocking_patterns = [
            r'error.*403',
            r'error.*429',
            r'blocked',
            r'captcha',
            r'rate.?limit',
            r'too.?many.?requests',
            r'access.?denied',
            r'cloudflare'
        ]
        
        warnings = []
        errors = []
        
        for line in recent_lines:
            line_lower = line.lower()
            
            # Check for blocking patterns
            for pattern in blocking_patterns:
                if re.search(pattern, line_lower):
                    warnings.append(line.strip())
            
            # Check for errors
            if 'error' in line_lower and 'medex' in line_lower:
                errors.append(line.strip())
        
        logger.info(f"🔍 BLOCKING DETECTION")
        
        if warnings:
            logger.warning(f"   ⚠️  Found {len(warnings)} potential blocking signs:")
            for warning in warnings[-3:]:  # Show last 3
                logger.warning(f"      {warning}")
        else:
            logger.success("   ✅ No blocking indicators found")
        
        if errors:
            logger.warning(f"   🚨 Found {len(errors)} recent errors")
        else:
            logger.info("   ✅ No critical errors")
            
    except FileNotFoundError:
        logger.warning("Log file not found - scraper may not be running")
    except Exception as e:
        logger.error(f"Error checking logs: {e}")

def test_medex_accessibility():
    """Test if MedEx website is accessible"""
    try:
        logger.info("🌐 WEBSITE ACCESSIBILITY TEST")
        
        # Test main page
        response = requests.get("https://medex.com.bd/brands?page=1", timeout=10)
        
        if response.status_code == 200:
            logger.success("   ✅ Main page accessible")
            
            # Check content
            if "brand" in response.text.lower() or "medicine" in response.text.lower():
                logger.success("   ✅ Content looks normal")
            else:
                logger.warning("   ⚠️  Unusual content - possible blocking")
                
        elif response.status_code == 403:
            logger.error("   🚫 403 Forbidden - IP may be blocked!")
        elif response.status_code == 429:
            logger.error("   🚫 429 Rate Limited - slow down scraping!")
        else:
            logger.warning(f"   ⚠️  Unusual status code: {response.status_code}")
            
    except requests.exceptions.Timeout:
        logger.error("   ❌ Timeout - website may be slow or blocking")
    except requests.exceptions.ConnectionError:
        logger.error("   ❌ Connection error - check internet or blocking")
    except Exception as e:
        logger.error(f"   ❌ Error testing website: {e}")

def recommend_actions():
    """Recommend actions based on findings"""
    logger.info("\n💡 RECOMMENDATIONS")
    logger.info("   If you see blocking signs:")
    logger.info("   1. 🛑 Stop scraper temporarily")
    logger.info("   2. ⏱️  Wait 30-60 minutes")
    logger.info("   3. 🔄 Restart with longer delays")
    logger.info("   4. 🔄 Consider using proxy rotation")
    logger.info("")
    logger.info("   For optimal performance:")
    logger.info("   • Keep delays between 3-8 seconds")
    logger.info("   • Monitor rate: aim for 10-15 medicines/hour")
    logger.info("   • Run during off-peak hours (night/early morning)")

def main():
    setup_logging()
    
    logger.info("🔍 MedEx Scraper Health Monitor")
    logger.info("=" * 50)
    
    check_scraper_performance()
    print()
    check_for_blocking_signs()
    print()
    test_medex_accessibility()
    print()
    recommend_actions()

if __name__ == "__main__":
    main() 
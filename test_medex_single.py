#!/usr/bin/env python3
"""
Test script for MedEx scraper - single page
Test scraping a single medicine page from MedEx
"""

import sys
from loguru import logger
from scrapers.medex_scraper import MedExScraper

def setup_logging():
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> - <level>{message}</level>",
        level="DEBUG"
    )

def test_single_medicine():
    """Test scraping a single medicine page"""
    
    # Test URL - 3 Bion Tablet from MedEx
    test_url = "https://medex.com.bd/brands/13717/3-bion-100-mg-tablet"
    
    logger.info(f"Testing single medicine scraping: {test_url}")
    
    try:
        # Create scraper instance
        scraper = MedExScraper()
        
        # Set to non-headless for testing (so you can see what's happening)
        from config import Config
        Config.SELENIUM_HEADLESS = False
        
        # Test fetching the page
        logger.info("Fetching page content...")
        content = scraper.fetch_page_with_selenium(test_url)
        
        if not content:
            logger.error("Failed to fetch page content")
            return False
        
        logger.success(f"Successfully fetched page content ({len(content)} characters)")
        
        # Parse the HTML
        soup = scraper.parse_html(content)
        logger.info("Parsed HTML content")
        
        # Extract medicine data
        logger.info("Extracting medicine data...")
        medicine_data = scraper.extract_medicine_data(soup, test_url)
        
        logger.info("Extracted medicine data:")
        for key, value in medicine_data.items():
            if key != 'raw_data':  # Skip raw_data as it's too long
                logger.info(f"  {key}: {value}")
        
        # Test image extraction
        logger.info("Extracting image URL...")
        image_url = scraper.extract_image_url(soup)
        if image_url:
            logger.success(f"Found image URL: {image_url}")
            
            # Test image processing
            logger.info("Processing image...")
            image_data = scraper.process_medicine_image(image_url)
            if image_data:
                logger.success(f"Successfully processed image: {image_data['width']}x{image_data['height']}, {image_data['file_size']} bytes")
            else:
                logger.warning("Failed to process image")
        else:
            logger.warning("No image URL found")
        
        # Test HTML storage
        logger.info("Testing HTML storage...")
        temp_id = 12345  # Test ID
        html_url = scraper.html_storage.save_html(content, temp_id, test_url)
        if html_url:
            logger.success(f"Successfully saved HTML: {html_url}")
        else:
            logger.error("Failed to save HTML")
        
        # Test full scraping (without database save for testing)
        logger.info("Testing full scraping process...")
        success = scraper.scrape_medicine_page(test_url)
        
        if success:
            logger.success("Single medicine scraping test completed successfully!")
            return True
        else:
            logger.error("Single medicine scraping test failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False

def main():
    """Main function"""
    setup_logging()
    
    logger.info("Starting MedEx single medicine test...")
    
    success = test_single_medicine()
    
    if success:
        logger.success("Test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test script to verify improved image processing with higher resolution images
"""

import asyncio
import json
from bs4 import BeautifulSoup
from loguru import logger
from scrapers.medeasy_scraper_local import MedEasyScraperLocal
from utils.image_processor import ImageProcessor

async def test_improved_image_processing():
    """Test the improved image processing with a sample medicine"""
    
    # Initialize scraper
    scraper = MedEasyScraperLocal()
    
    # Test URL - you can change this to any medicine page
    test_url = "https://medeasy.health/womens-choice/contraceptive-pills"
    
    try:
        logger.info(f"Testing improved image processing with: {test_url}")
        
        # Fetch page content
        content = await scraper.fetch_page_async(test_url)
        if not content:
            logger.error("Failed to fetch page content")
            return
        
        # Parse HTML
        soup = scraper.parse_html(content)
        
        # Extract image URL with improved method
        image_url = scraper.extract_image_url(soup)
        
        if image_url:
            logger.info(f"Found image URL: {image_url}")
            
            # Process image with improved settings
            image_processor = ImageProcessor()
            image_data = image_processor.download_and_convert_to_webp(image_url)
            
            if image_data:
                logger.info("=== IMAGE PROCESSING RESULTS ===")
                logger.info(f"Original URL: {image_data['original_url']}")
                logger.info(f"Original size: {image_data['original_size']}")
                logger.info(f"Final size: {image_data['width']}x{image_data['height']}")
                logger.info(f"File size: {image_data['file_size']} bytes ({image_data['file_size'] / 1024:.1f} KB)")
                logger.info(f"Quality: {image_data['quality']}")
                logger.info(f"Format: {image_data['format']}")
                
                # Calculate improvement
                original_pixels = image_data['original_size'][0] * image_data['original_size'][1]
                final_pixels = image_data['width'] * image_data['height']
                improvement = (final_pixels / original_pixels) * 100 if original_pixels > 0 else 0
                
                logger.info(f"Resolution improvement: {improvement:.1f}% of original")
                
                if improvement > 80:
                    logger.success("✅ High resolution image successfully processed!")
                elif improvement > 50:
                    logger.warning("⚠️  Medium resolution image processed")
                else:
                    logger.error("❌ Low resolution image - may need further optimization")
                
            else:
                logger.error("Failed to process image")
        else:
            logger.error("No image URL found")
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
    finally:
        await scraper.close()

async def test_multiple_images():
    """Test image processing with multiple medicine pages"""
    
    scraper = MedEasyScraperLocal()
    
    # Sample medicine URLs to test
    test_urls = [
        "https://medeasy.health/womens-choice/contraceptive-pills",
        "https://medeasy.health/skin-care/face-wash",
        "https://medeasy.health/diabetic-care/glucose-monitor"
    ]
    
    results = []
    
    for url in test_urls:
        try:
            logger.info(f"\nTesting: {url}")
            
            content = await scraper.fetch_page_async(url)
            if not content:
                continue
                
            soup = scraper.parse_html(content)
            image_url = scraper.extract_image_url(soup)
            
            if image_url:
                image_processor = ImageProcessor()
                image_data = image_processor.download_and_convert_to_webp(image_url)
                
                if image_data:
                    original_pixels = image_data['original_size'][0] * image_data['original_size'][1]
                    final_pixels = image_data['width'] * image_data['height']
                    
                    result = {
                        'url': url,
                        'image_url': image_url,
                        'original_size': image_data['original_size'],
                        'final_size': (image_data['width'], image_data['height']),
                        'file_size_kb': image_data['file_size'] / 1024,
                        'resolution_ratio': final_pixels / original_pixels if original_pixels > 0 else 0
                    }
                    results.append(result)
                    
                    logger.info(f"  ✅ {result['final_size'][0]}x{result['final_size'][1]} ({result['file_size_kb']:.1f} KB)")
                else:
                    logger.warning(f"  ❌ Failed to process image")
            else:
                logger.warning(f"  ❌ No image found")
                
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
    
    # Summary
    if results:
        logger.info("\n=== SUMMARY ===")
        avg_resolution = sum(r['resolution_ratio'] for r in results) / len(results)
        avg_file_size = sum(r['file_size_kb'] for r in results) / len(results)
        
        logger.info(f"Average resolution ratio: {avg_resolution:.1%}")
        logger.info(f"Average file size: {avg_file_size:.1f} KB")
        logger.info(f"Total images tested: {len(results)}")
        
        if avg_resolution > 0.8:
            logger.success("✅ Overall: High resolution images achieved!")
        elif avg_resolution > 0.5:
            logger.warning("⚠️  Overall: Medium resolution images")
        else:
            logger.error("❌ Overall: Low resolution images")
    
    await scraper.close()

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    print("🧪 Testing Improved Image Processing")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_improved_image_processing())
    
    print("\n" + "=" * 50)
    print("🧪 Testing Multiple Images")
    print("=" * 50)
    
    asyncio.run(test_multiple_images()) 
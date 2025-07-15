#!/usr/bin/env python3
"""
Test script to verify Next.js image URL extraction from MedEasy product pages
"""

import asyncio
from loguru import logger
from scrapers.medeasy_scraper_local import MedEasyScraperLocal
from utils.image_processor import ImageProcessor

async def test_nextjs_image_extraction():
    """Test Next.js image URL extraction with real MedEasy product pages"""
    
    # Initialize scraper
    scraper = MedEasyScraperLocal()
    
    # Test URLs - real MedEasy product pages
    test_urls = [
        "https://medeasy.health/medicines/freedom-heavy-flow-wings-16-pads-women-s-choice",
        "https://medeasy.health/medicines/atova-10-mg-tablet",
        "https://medeasy.health/medicines/femicon-28"
    ]
    
    results = []
    
    for url in test_urls:
        try:
            logger.info(f"\n🔍 Testing: {url}")
            
            # Fetch page content
            content = await scraper.fetch_page_async(url)
            if not content:
                logger.error("Failed to fetch page content")
                continue
            
            # Parse HTML
            soup = scraper.parse_html(content)
            
            # Extract image URL with new Next.js logic
            image_url = scraper.extract_image_url(soup)
            
            if image_url:
                logger.info(f"✅ Found image URL: {image_url}")
                
                # Test downloading the image
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
                        'resolution_ratio': final_pixels / original_pixels if original_pixels > 0 else 0,
                        'is_nextjs': '/_next/image?url=' in image_url or 'api.medeasy.health' in image_url
                    }
                    results.append(result)
                    
                    logger.info(f"  📏 Original: {result['original_size'][0]}x{result['original_size'][1]}")
                    logger.info(f"  📏 Final: {result['final_size'][0]}x{result['final_size'][1]}")
                    logger.info(f"  💾 Size: {result['file_size_kb']:.1f} KB")
                    logger.info(f"  📊 Resolution: {result['resolution_ratio']:.1%} of original")
                    
                    if result['is_nextjs']:
                        logger.success("  ✅ Next.js image extraction successful!")
                    else:
                        logger.warning("  ⚠️ Using fallback image extraction")
                        
                else:
                    logger.error("  ❌ Failed to download/process image")
            else:
                logger.error("  ❌ No image URL found")
                
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
    
    # Summary
    if results:
        logger.info("\n" + "=" * 60)
        logger.info("📊 SUMMARY")
        logger.info("=" * 60)
        
        nextjs_count = sum(1 for r in results if r['is_nextjs'])
        avg_resolution = sum(r['resolution_ratio'] for r in results) / len(results)
        avg_file_size = sum(r['file_size_kb'] for r in results) / len(results)
        
        logger.info(f"Total products tested: {len(results)}")
        logger.info(f"Next.js images found: {nextjs_count}/{len(results)}")
        logger.info(f"Average resolution ratio: {avg_resolution:.1%}")
        logger.info(f"Average file size: {avg_file_size:.1f} KB")
        
        if nextjs_count == len(results):
            logger.success("🎉 All images extracted using Next.js method!")
        elif nextjs_count > 0:
            logger.warning(f"⚠️ {nextjs_count}/{len(results)} images used Next.js method")
        else:
            logger.error("❌ No Next.js images found - check the extraction logic")
        
        if avg_resolution > 0.8:
            logger.success("✅ High resolution images achieved!")
        elif avg_resolution > 0.5:
            logger.warning("⚠️ Medium resolution images")
        else:
            logger.error("❌ Low resolution images")
    
    await scraper.close()

async def test_single_product():
    """Test a single product in detail"""
    
    scraper = MedEasyScraperLocal()
    
    # Test with the Freedom Heavy Flow Wings product
    test_url = "https://medeasy.health/medicines/freedom-heavy-flow-wings-16-pads-women-s-choice"
    
    try:
        logger.info(f"🔍 Testing single product: {test_url}")
        
        # Fetch page content
        content = await scraper.fetch_page_async(test_url)
        if not content:
            logger.error("Failed to fetch page content")
            return
        
        # Parse HTML
        soup = scraper.parse_html(content)
        
        # Look for all img tags to see what's available
        logger.info("🔍 Scanning all image tags on the page...")
        img_tags = soup.find_all('img')
        
        for i, img in enumerate(img_tags):
            src = img.get('src', '')
            alt = img.get('alt', '')
            width = img.get('width', '')
            height = img.get('height', '')
            
            if src:
                logger.info(f"  Image {i+1}: {src[:100]}...")
                if alt:
                    logger.info(f"    Alt: {alt}")
                if width and height:
                    logger.info(f"    Size: {width}x{height}")
                
                # Check if it's a Next.js image
                if '/_next/image?url=' in src:
                    logger.success(f"    ✅ This is a Next.js image!")
                    try:
                        original_url = scraper._extract_nextjs_image_url(src)
                        if original_url:
                            logger.success(f"    ✅ Extracted: {original_url}")
                        else:
                            logger.error(f"    ❌ Failed to extract original URL")
                    except Exception as e:
                        logger.error(f"    ❌ Error extracting: {e}")
        
        # Now test the actual extraction
        logger.info("\n🔍 Testing image extraction...")
        image_url = scraper.extract_image_url(soup)
        
        if image_url:
            logger.success(f"✅ Extracted image URL: {image_url}")
            
            # Test downloading
            image_processor = ImageProcessor()
            image_data = image_processor.download_and_convert_to_webp(image_url)
            
            if image_data:
                logger.success("✅ Image downloaded and processed successfully!")
                logger.info(f"  Original size: {image_data['original_size']}")
                logger.info(f"  Final size: {image_data['width']}x{image_data['height']}")
                logger.info(f"  File size: {image_data['file_size'] / 1024:.1f} KB")
            else:
                logger.error("❌ Failed to download/process image")
        else:
            logger.error("❌ No image URL extracted")
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    print("🧪 Testing Next.js Image Extraction")
    print("=" * 60)
    
    # Run single product test first
    asyncio.run(test_single_product())
    
    print("\n" + "=" * 60)
    print("🧪 Testing Multiple Products")
    print("=" * 60)
    
    # Run multiple product test
    asyncio.run(test_nextjs_image_extraction()) 
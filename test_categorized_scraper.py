import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.medeasy_scraper import MedEasyScraper
from loguru import logger

async def test_category_discovery():
    """Test the category discovery functionality"""
    scraper = MedEasyScraper()
    try:
        logger.info("Testing category discovery...")
        medicine_urls = await scraper.discover_medicine_urls()
        logger.info(f"Discovered {len(medicine_urls)} medicine URLs")
        # Group by category
        category_counts = {}
        for medicine_info in medicine_urls:
            category_slug = medicine_info.get('category_slug', 'unknown')
            category_counts[category_slug] = category_counts.get(category_slug, 0) + 1
        logger.info("Medicine counts by category:")
        for category, count in category_counts.items():
            logger.info(f"  {category}: {count} medicines")
        # Test scraping a few medicines from different categories
        if medicine_urls:
            logger.info("Testing medicine scraping with category information...")
            tested_categories = set()
            for medicine_info in medicine_urls:
                category_slug = medicine_info.get('category_slug')
                if category_slug not in tested_categories:
                    tested_categories.add(category_slug)
                    url = medicine_info['url']
                    category_id = medicine_info.get('category_id')
                    logger.info(f"Testing medicine from category {category_slug} (ID: {category_id}): {url}")
                    success = await scraper.scrape_medicine_page(url, category_id, category_slug)
                    logger.info(f"Scraping result: {'Success' if success else 'Failed'}")
                    if len(tested_categories) >= 3:
                        break
        logger.info("Category discovery test completed successfully!")
    except Exception as e:
        logger.error(f"Error in category discovery test: {e}")
        raise
    finally:
        await scraper.close()

async def main():
    logger.info("Starting MedEasy categorized scraper tests...")
    try:
        await test_category_discovery()
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 
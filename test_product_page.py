#!/usr/bin/env python3
"""
Test script to check individual product pages
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

async def test_product_page():
    """Test individual product page extraction"""
    # Test the URL you provided earlier
    test_url = "https://medeasy.health/freedom-heavy-flow-wings-16-pads-women-s-choice"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"Testing URL: {test_url}")
            
            async with session.get(test_url, headers=headers) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Page title: {soup.title.string if soup.title else 'No title'}")
                    print(f"Page length: {len(content)} characters")
                    
                    # Look for product information
                    print("\n=== Product Information ===")
                    
                    # Product name
                    name_selectors = [
                        'h1.product-title',
                        'h1.medicine-title',
                        '.product-name',
                        '.medicine-name',
                        'h1',
                        '.title'
                    ]
                    
                    for selector in name_selectors:
                        element = soup.select_one(selector)
                        if element:
                            print(f"Product name: {element.get_text(strip=True)}")
                            break
                    
                    # Price
                    price_selectors = [
                        '.price',
                        '.product-price',
                        '.medicine-price',
                        '[data-field="price"]',
                        '.cost'
                    ]
                    
                    for selector in price_selectors:
                        element = soup.select_one(selector)
                        if element:
                            print(f"Price: {element.get_text(strip=True)}")
                            break
                    
                    # Category
                    category_selectors = [
                        '.category',
                        '.product-category',
                        '.breadcrumb',
                        '.nav-category',
                        '.breadcrumb-item:last-child',
                        '.breadcrumb a:last-child'
                    ]
                    
                    for selector in category_selectors:
                        element = soup.select_one(selector)
                        if element:
                            print(f"Category: {element.get_text(strip=True)}")
                            break
                    
                    # Save the page for inspection
                    with open('test_product_page.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"\nSaved page to test_product_page.html")
                    
                else:
                    print(f"Failed to access page: {response.status}")
                    
    except Exception as e:
        print(f"Error testing product page: {e}")

if __name__ == "__main__":
    asyncio.run(test_product_page()) 
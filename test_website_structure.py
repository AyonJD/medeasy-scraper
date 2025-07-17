#!/usr/bin/env python3
"""
Test script to check the current website structure
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

async def test_website_structure():
    """Test the current website structure"""
    url = "https://medeasy.health/medicines"
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Page title: {soup.title.string if soup.title else 'No title'}")
                    print(f"Page length: {len(content)} characters")
                    
                    # Look for common medicine link patterns
                    print("\n=== Looking for medicine links ===")
                    
                    # Check for links with medicine-related patterns
                    medicine_links = []
                    
                    # Look for links containing medicine-related keywords
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if any(keyword in href.lower() for keyword in ['medicine', 'product', 'item', 'detail']):
                            medicine_links.append(href)
                    
                    print(f"Found {len(medicine_links)} potential medicine links:")
                    for link in medicine_links[:10]:  # Show first 10
                        print(f"  {link}")
                    
                    # Look for product cards or containers
                    print("\n=== Looking for product containers ===")
                    product_containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['product', 'medicine', 'item', 'card']))
                    print(f"Found {len(product_containers)} product containers")
                    
                    # Look for specific selectors that might contain medicine links
                    print("\n=== Testing specific selectors ===")
                    selectors_to_test = [
                        '.product-link',
                        '.medicine-link',
                        '.product-card a',
                        '.medicine-card a',
                        '.product-item a',
                        '.medicine-item a',
                        '[data-product]',
                        '[data-medicine]',
                        '.product a',
                        '.medicine a'
                    ]
                    
                    for selector in selectors_to_test:
                        elements = soup.select(selector)
                        if elements:
                            print(f"Selector '{selector}' found {len(elements)} elements")
                            for elem in elements[:3]:  # Show first 3
                                href = elem.get('href', 'No href')
                                text = elem.get_text(strip=True)[:50]
                                print(f"  - {href} | {text}")
                    
                    # Save a sample of the HTML for inspection
                    with open('sample_page.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"\nSaved sample HTML to sample_page.html")
                    
                else:
                    print(f"Failed to fetch page: {response.status}")
                    
    except Exception as e:
        print(f"Error testing website: {e}")

if __name__ == "__main__":
    asyncio.run(test_website_structure()) 
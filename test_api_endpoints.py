#!/usr/bin/env python3
"""
Test script to check for API endpoints that might provide medicine data
"""

import asyncio
import aiohttp
import json
from loguru import logger

async def test_api_endpoints():
    """Test various API endpoints that might provide medicine data"""
    base_url = "https://medeasy.health"
    
    # Common API endpoints to test
    api_endpoints = [
        "/api/products",
        "/api/medicines", 
        "/api/items",
        "/api/categories",
        "/api/category/medicines",
        "/api/category/womens-choice",
        "/api/category/sexual-wellness",
        "/api/category/skin-care",
        "/api/category/diabetic-care",
        "/api/category/devices",
        "/api/category/supplement",
        "/api/category/diapers",
        "/api/category/baby-care",
        "/api/category/personal-care",
        "/api/category/hygiene-and-freshness",
        "/api/category/dental-care",
        "/api/category/herbal-medicine",
        "/api/category/prescription-medicine",
        "/api/category/otc-medicine"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://medeasy.health/medicines'
    }
    
    async with aiohttp.ClientSession() as session:
        for endpoint in api_endpoints:
            try:
                url = base_url + endpoint
                print(f"\nTesting: {url}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            print(f"Response type: {type(data)}")
                            if isinstance(data, dict):
                                print(f"Keys: {list(data.keys())}")
                                if 'products' in data or 'medicines' in data or 'items' in data:
                                    items = data.get('products', data.get('medicines', data.get('items', [])))
                                    print(f"Found {len(items)} items")
                                    if items:
                                        print(f"First item: {items[0]}")
                            elif isinstance(data, list):
                                print(f"Found {len(data)} items")
                                if data:
                                    print(f"First item: {data[0]}")
                        except json.JSONDecodeError:
                            text = await response.text()
                            print(f"Not JSON, length: {len(text)}")
                            if len(text) < 200:
                                print(f"Content: {text}")
                    else:
                        print(f"Failed: {response.status}")
                        
            except Exception as e:
                print(f"Error testing {endpoint}: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints()) 
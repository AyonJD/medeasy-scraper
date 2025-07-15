#!/usr/bin/env python3
"""
Test script to explore MedEasy website structure
"""
import requests
from bs4 import BeautifulSoup
import json

def test_medeasy_website():
    """Test the MedEasy website structure"""
    base_url = "https://medeasy.health"
    
    print("🔍 Exploring MedEasy website structure...")
    print("=" * 50)
    
    # Test 1: Main page
    print("1. Testing main page...")
    try:
        response = requests.get(base_url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for navigation links
        nav_links = soup.find_all('a', href=True)
        medicine_links = [link for link in nav_links if 'medicine' in link.get('href', '').lower()]
        
        print(f"   Found {len(medicine_links)} potential medicine links:")
        for link in medicine_links[:5]:  # Show first 5
            print(f"     - {link.get('href')} -> {link.get_text(strip=True)}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Testing medicines page...")
    try:
        medicines_url = f"{base_url}/medicines"
        response = requests.get(medicines_url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for product containers
        product_selectors = [
            '.product',
            '.medicine',
            '.item',
            '[class*="product"]',
            '[class*="medicine"]',
            '[class*="item"]'
        ]
        
        for selector in product_selectors:
            products = soup.select(selector)
            if products:
                print(f"   Found {len(products)} products with selector '{selector}'")
                break
        
        # Look for any links that might be medicine products
        all_links = soup.find_all('a', href=True)
        product_links = []
        
        for link in all_links:
            href = link.get('href', '')
            if any(keyword in href.lower() for keyword in ['product', 'medicine', 'drug', 'med']):
                product_links.append(href)
        
        print(f"   Found {len(product_links)} potential product links")
        for link in product_links[:10]:  # Show first 10
            print(f"     - {link}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Testing search functionality...")
    try:
        # Try to find a search endpoint
        search_url = f"{base_url}/search"
        response = requests.get(search_url, timeout=10)
        print(f"   Search page status: {response.status_code}")
        
        # Try with a common medicine name
        search_params = {'q': 'paracetamol'}
        response = requests.get(f"{base_url}/search", params=search_params, timeout=10)
        print(f"   Search with 'paracetamol' status: {response.status_code}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n4. Testing category pages...")
    try:
        # Try common category URLs
        categories = ['antibiotics', 'pain-relief', 'vitamins', 'diabetes']
        
        for category in categories:
            cat_url = f"{base_url}/category/{category}"
            response = requests.get(cat_url, timeout=10)
            print(f"   {category}: {response.status_code}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n5. Looking for API endpoints...")
    try:
        # Check if there's a JSON API
        api_url = f"{base_url}/api/products"
        response = requests.get(api_url, timeout=10)
        print(f"   API endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   API response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print("   API response is not JSON")
                
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Website exploration completed!")

if __name__ == "__main__":
    test_medeasy_website() 
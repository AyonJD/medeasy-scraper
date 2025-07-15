#!/usr/bin/env python3
"""
Test script to extract data from a single medicine page
"""
import requests
from bs4 import BeautifulSoup
import json

def test_single_medicine():
    """Test extracting data from a single medicine page"""
    base_url = "https://medeasy.health"
    
    # Test with one of the medicine URLs we found
    medicine_url = f"{base_url}/medicines/freedom-heavy-flow-wings-16-pads-women-s-choice"
    
    print(f"🔍 Testing medicine page: {medicine_url}")
    print("=" * 60)
    
    try:
        response = requests.get(medicine_url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract medicine data
        medicine_data = {}
        
        # 1. Product name
        name_selectors = [
            'h1',
            '.product-title',
            '.medicine-title',
            '.title',
            '[class*="title"]'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                medicine_data['name'] = element.get_text(strip=True)
                print(f"✓ Name found: {medicine_data['name']}")
                break
        
        # 2. Price
        price_selectors = [
            '.price',
            '.product-price',
            '.medicine-price',
            '[class*="price"]',
            '.cost'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                medicine_data['price'] = price_text
                print(f"✓ Price found: {price_text}")
                break
        
        # 3. Manufacturer
        manufacturer_selectors = [
            '.manufacturer',
            '.brand',
            '.company',
            '[class*="manufacturer"]',
            '[class*="brand"]'
        ]
        
        for selector in manufacturer_selectors:
            element = soup.select_one(selector)
            if element:
                medicine_data['manufacturer'] = element.get_text(strip=True)
                print(f"✓ Manufacturer found: {medicine_data['manufacturer']}")
                break
        
        # 4. Description
        desc_selectors = [
            '.description',
            '.product-description',
            '.medicine-description',
            '[class*="description"]',
            '.details'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                medicine_data['description'] = element.get_text(strip=True)[:200] + "..."
                print(f"✓ Description found: {medicine_data['description']}")
                break
        
        # 5. Image
        img_selectors = [
            '.product-image img',
            '.medicine-image img',
            '.main-image img',
            'img[alt*="product"]',
            'img[alt*="medicine"]'
        ]
        
        for selector in img_selectors:
            element = soup.select_one(selector)
            if element:
                img_src = element.get('src')
                if img_src:
                    medicine_data['image_url'] = img_src
                    print(f"✓ Image found: {img_src}")
                    break
        
        # 6. Look for any other useful data
        print("\n🔍 Looking for additional data...")
        
        # Check for any structured data (JSON-LD)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                print(f"✓ Found structured data: {json.dumps(data, indent=2)[:200]}...")
            except:
                pass
        
        # Check for meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '') or meta.get('property', '')
            content = meta.get('content', '')
            if any(keyword in name.lower() for keyword in ['description', 'title', 'price', 'brand']):
                print(f"✓ Meta tag: {name} = {content}")
        
        # 7. Print all found data
        print("\n📊 Extracted Medicine Data:")
        print("=" * 40)
        for key, value in medicine_data.items():
            print(f"{key}: {value}")
        
        # 8. Save to file for inspection
        with open('sample_medicine_data.json', 'w', encoding='utf-8') as f:
            json.dump(medicine_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Data saved to sample_medicine_data.json")
        
        # 9. Save HTML for inspection
        with open('sample_medicine_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"💾 HTML saved to sample_medicine_page.html")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Single medicine test completed!")

if __name__ == "__main__":
    test_single_medicine() 
#!/usr/bin/env python3
"""
Improved test script to extract comprehensive data from medicine pages
"""
import requests
from bs4 import BeautifulSoup
import json
import re

def extract_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return None
    try:
        # Remove currency symbols and non-numeric characters except decimal point
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group())
    except (ValueError, AttributeError):
        pass
    return None

def test_improved_extraction():
    """Test improved data extraction from medicine pages"""
    base_url = "https://medeasy.health"
    
    # Test with multiple medicine URLs
    test_urls = [
        "/medicines/freedom-heavy-flow-wings-16-pads-women-s-choice",
        "/medicines/femicon-pill-0-30-mg-0-03-mg-women-s-care",
        "/medicines/senora-confidence-regular-flow-panty-system-15-pad-women-s-choice"
    ]
    
    all_medicines = []
    
    for i, url_path in enumerate(test_urls, 1):
        medicine_url = base_url + url_path
        print(f"\n🔍 Testing medicine {i}: {medicine_url}")
        print("-" * 60)
        
        try:
            response = requests.get(medicine_url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to load page")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            medicine_data = {'product_url': medicine_url}
            
            # 1. Extract from structured data (JSON-LD)
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Product':
                        print("✓ Found structured product data")
                        medicine_data['name'] = data.get('name', '')
                        medicine_data['description'] = data.get('description', '')
                        medicine_data['image_url'] = data.get('image', '')
                        if data.get('offers'):
                            offers = data['offers']
                            if isinstance(offers, list) and offers:
                                offers = offers[0]
                            medicine_data['price'] = offers.get('price', '')
                            medicine_data['currency'] = offers.get('priceCurrency', 'BDT')
                        break
                except:
                    pass
            
            # 2. Extract from meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name', '') or meta.get('property', '')
                content = meta.get('content', '')
                
                if 'description' in name.lower():
                    medicine_data['meta_description'] = content
                elif 'title' in name.lower():
                    medicine_data['meta_title'] = content
                elif 'price' in name.lower():
                    medicine_data['meta_price'] = content
            
            # 3. Extract from HTML elements (fallback)
            if not medicine_data.get('name'):
                # Try different selectors for name
                name_selectors = ['h1', '.product-title', '.title', '[class*="title"]']
                for selector in name_selectors:
                    element = soup.select_one(selector)
                    if element:
                        medicine_data['name'] = element.get_text(strip=True)
                        break
            
            # 4. Extract price from HTML
            if not medicine_data.get('price'):
                price_selectors = [
                    '.price',
                    '.product-price',
                    '.medicine-price',
                    '[class*="price"]',
                    '.cost',
                    '.amount'
                ]
                
                for selector in price_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        price_text = element.get_text(strip=True)
                        price = extract_price(price_text)
                        if price:
                            medicine_data['price'] = price
                            medicine_data['price_text'] = price_text
                            break
                    if medicine_data.get('price'):
                        break
            
            # 5. Extract manufacturer/brand
            manufacturer_selectors = [
                '.manufacturer',
                '.brand',
                '.company',
                '[class*="manufacturer"]',
                '[class*="brand"]',
                '.vendor'
            ]
            
            for selector in manufacturer_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) < 100:  # Avoid very long text
                        medicine_data['manufacturer'] = text
                        break
            
            # 6. Extract category
            # Look for breadcrumbs or category links
            breadcrumb_selectors = ['.breadcrumb', '.nav', '[class*="breadcrumb"]']
            for selector in breadcrumb_selectors:
                element = soup.select_one(selector)
                if element:
                    links = element.find_all('a')
                    if len(links) > 1:
                        medicine_data['category'] = links[-2].get_text(strip=True)  # Second to last
                        break
            
            # 7. Extract any additional useful information
            # Look for product details
            detail_selectors = ['.product-details', '.medicine-details', '.details']
            for selector in detail_selectors:
                element = soup.select_one(selector)
                if element:
                    medicine_data['details'] = element.get_text(strip=True)[:500]
                    break
            
            # 8. Print extracted data
            print("📊 Extracted Data:")
            for key, value in medicine_data.items():
                if value:
                    print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            
            all_medicines.append(medicine_data)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Save all extracted data
    with open('extracted_medicines.json', 'w', encoding='utf-8') as f:
        json.dump(all_medicines, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 All data saved to extracted_medicines.json")
    print(f"📈 Successfully extracted data from {len(all_medicines)} medicines")
    
    # Show summary
    print("\n📋 Data Summary:")
    print("=" * 40)
    for i, medicine in enumerate(all_medicines, 1):
        print(f"{i}. {medicine.get('name', 'Unknown')}")
        print(f"   Price: {medicine.get('price', 'N/A')} {medicine.get('currency', '')}")
        print(f"   Manufacturer: {medicine.get('manufacturer', 'N/A')}")
        print(f"   Category: {medicine.get('category', 'N/A')}")
        print()

if __name__ == "__main__":
    test_improved_extraction() 
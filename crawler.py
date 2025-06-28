# -*- coding: utf-8 -*-
"""
A complete web crawler script to scrape product data from a single URL.

Features:
- Loads configuration from a .env file.
- Handles lazy-loaded images by checking multiple attributes.
- Parses the 'Additional Information' table into a dictionary.
- Downloads the primary product image to a local folder.
- Prints all scraped data to the console in a clean format.
- Sends the structured JSON data to a specified API endpoint.
"""
import os
import json
import re
import time
import requests
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- 1. Configuration ---
load_dotenv()
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
DATA_SOURCE_URL = os.getenv("DATA_SOURCE_URL")
IMAGE_SAVE_DIR = 'downloaded_images'

if not os.path.exists(IMAGE_SAVE_DIR):
    os.makedirs(IMAGE_SAVE_DIR)

# --- 2. Helper Functions ---

def download_image(image_url, product_sku):
    """Downloads an image and saves it locally using the SKU as a filename."""
    if not image_url or not product_sku:
        return None
    try:
        print(f"  📥 Downloading image: {image_url}")
        img_response = requests.get(image_url, stream=True, timeout=20)
        img_response.raise_for_status()

        img_extension = os.path.splitext(image_url.split('?')[0])[1] or '.jpg'
        safe_sku = re.sub(r'[^a-zA-Z0-9_-]', '-', product_sku)
        image_path = os.path.join(IMAGE_SAVE_DIR, f"{safe_sku}{img_extension}")

        with open(image_path, 'wb') as img_file:
            for chunk in img_response.iter_content(8192):
                img_file.write(chunk)

        print(f"  ✅ Image saved: {image_path}")
        return image_path
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error downloading image: {e}")
        return None

def extract_product_data_from_soup(soup, url):
    """Parses the BeautifulSoup object to extract all product data."""
    try:
        product_data = {
            'sku': '', 'name': '', 'description': '', 'price': 0.00,
            'status': 'PendingReview', 'images': [], 'attributes': {},
            'category': '', 'source_url': url, 'brand': '', 'stock_quantity': 0,
            'crawler_payload': {} # You can add metadata here if needed
        }

        # --- Extract Name, Price, and Description ---
        name_selector = soup.select_one('h1.product_title')
        if name_selector: product_data['name'] = name_selector.get_text(strip=True)

        price_selector = soup.select_one('.price .woocommerce-Price-amount')
        if price_selector:
            price_match = re.search(r'[\d,]+\.?\d*', price_selector.get_text(strip=True).replace(',', ''))
            if price_match: product_data['price'] = float(price_match.group())

        desc_selector = soup.select_one('.woocommerce-product-details__short-description')
        if desc_selector: product_data['description'] = desc_selector.get_text(strip=True)
        
        # --- Extract Product Attributes from Table ---
        attributes = {}
        attributes_table = soup.find('table', class_='shop_attributes')
        if attributes_table:
            for row in attributes_table.find_all('tr'):
                label_tag = row.find('th', class_='woocommerce-product-attributes-item__label')
                value_tag = row.find('td', class_='woocommerce-product-attributes-item__value')
                if label_tag and value_tag:
                    key = label_tag.get_text(strip=True)
                    value = value_tag.get_text(strip=True)
                    attributes[key] = value
                    # If we find a "Brand" attribute, also populate the main brand field
                    if key == 'برند' and not product_data.get('brand'):
                        product_data['brand'] = value
        product_data['attributes'] = attributes

        # --- Handle Lazy-Loaded Images ---
        image_selectors = 'figure.woocommerce-product-gallery__image a, .woocommerce-product-gallery__image img'
        image_attribute_priority = ['href', 'data-large_image', 'data-src', 'src']
        found_image_urls = []
        for elem in soup.select(image_selectors):
            img_url = None
            for attr in image_attribute_priority:
                if elem.has_attr(attr) and elem[attr]:
                    img_url = urljoin(url, elem[attr]) # Make URL absolute
                    break
            if img_url and img_url not in found_image_urls:
                found_image_urls.append(img_url)
        product_data['images'] = found_image_urls

        # --- Extract SKU ---
        sku_selector = soup.select_one('.sku')
        if sku_selector and sku_selector.get_text(strip=True).lower() != 'n/a':
            product_data['sku'] = sku_selector.get_text(strip=True)
        else: # Generate SKU from URL if not found
            slug = unquote(url.rstrip('/').split('/')[-1])
            product_data['sku'] = re.sub(r'[\W_]+', '-', slug).strip('-')[:50]

        # --- Download Primary Image ---
        if product_data['images']:
            product_data['image_path'] = download_image(product_data['images'][0], product_data['sku'])
        
        if not product_data['name']:
            product_data['name'] = f"Unknown Product - {product_data['sku']}"

        return product_data
    except Exception as e:
        print(f"❌ An error occurred during HTML parsing: {e}")
        return None

def fetch_product_data(url):
    """Fetches the HTML from the URL and initiates parsing."""
    print(f"➡️  Fetching page: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"✅ Page fetched successfully (Status: {response.status_code})")
        
        with open("debug_output.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("   (HTML content saved to debug_output.html for inspection)")

        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_product_data_from_soup(soup, url)
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while fetching data: {e}")
        return None

def send_product_to_api(product_data):
    """Sends the final product data dictionary to the API."""
    if not API_URL or not API_KEY:
        print("❌ Error: API_URL or API_KEY not configured in .env file.")
        return False

    print(f"\n🚀 Sending product '{product_data.get('name')}' to API...")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-KEY': API_KEY
    }
    payload = {'products': [product_data]}
    
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload, indent=2, ensure_ascii=False), timeout=30)
        print(f"   API Response Status: {response.status_code}")
        print(f"   API Response Body: {response.text}")
        response.raise_for_status()
        print("✅ Product data accepted by API!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False

# --- 3. Main Execution Block ---

def main():
    """Main function to orchestrate the crawler's execution."""
    print("--- 🚀 Starting Product Crawler ---")
    if not DATA_SOURCE_URL:
        print("❌ Critical Error: DATA_SOURCE_URL is not set in .env. Exiting.")
        return

    # Step 1: Fetch and parse all data from the URL
    product = fetch_product_data(DATA_SOURCE_URL)
    
    if product:
        # --- ** NEW SECTION: PRINT ALL FOUND DATA ** ---
        # This section will print the entire product dictionary to the console
        # in a readable, pretty-printed JSON format.
        print("\n" + "="*50)
        print("--- 📜 Full Extracted Product Data (for console review) ---")
        print("="*50)
        # ensure_ascii=False is crucial for correctly printing non-English characters
        print(json.dumps(product, indent=2, ensure_ascii=False))
        print("="*50 + "\n")

        # Step 2: Send the data to the API (if configured)
        if API_URL and API_KEY:
            send_product_to_api(product)
        else:
            print("🔔 Skipping API submission: API_URL or API_KEY not found in .env file.")

    else:
        print("\n--- 🛑 Halting script: Failed to extract any product data. ---")

    print("\n--- ✅ Crawler script finished. ---")


if __name__ == "__main__":
    main()
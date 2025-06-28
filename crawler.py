# -*- coding: utf-8 -*-
"""
A dynamic web crawler that scrapes a product category page.

Features:
- The category URL is a REQUIRED command-line argument.
- Loads configuration from a .env file, including a CRAWL_LIMIT.
- Tracks previously scraped URLs to avoid duplicates.
- Scrapes a limited number of new products per run.
- Sends data for each product to a specified API endpoint.
"""
import os
import json
import re
import time
import requests
import argparse # Used to handle command-line arguments
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- 1. Configuration ---
load_dotenv()
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
# NOTE: DATA_SOURCE_URL is no longer read from the .env file.
IMAGE_SAVE_DIR = 'downloaded_images'
LOG_FILE = 'scraped_urls.log'
CRAWL_LIMIT = int(os.getenv("CRAWL_LIMIT", 5))

if not os.path.exists(IMAGE_SAVE_DIR):
    os.makedirs(IMAGE_SAVE_DIR)

# --- 2. Helper Functions (No changes in this section) ---

def load_scraped_urls(log_file_path):
    if not os.path.exists(log_file_path): return set()
    with open(log_file_path, 'r') as f:
        return set(line.strip() for line in f)

def log_scraped_url(url, log_file_path):
    with open(log_file_path, 'a') as f:
        f.write(url + '\n')

def download_image(image_url, product_sku):
    if not image_url or not product_sku: return None
    try:
        print(f"    📥 Downloading image: {image_url}")
        img_response = requests.get(image_url, stream=True, timeout=20)
        img_response.raise_for_status()
        img_extension = os.path.splitext(image_url.split('?')[0])[1] or '.jpg'
        safe_sku = re.sub(r'[^a-zA-Z0-9_-]', '-', product_sku)
        image_path = os.path.join(IMAGE_SAVE_DIR, f"{safe_sku}{img_extension}")
        with open(image_path, 'wb') as img_file:
            for chunk in img_response.iter_content(8192):
                img_file.write(chunk)
        print(f"    ✅ Image saved: {image_path}")
        return image_path
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error downloading image: {e}")
        return None

def extract_product_data_from_soup(soup, url):
    try:
        product_data = {
            'sku': '', 'name': '', 'description': '', 'price': 0.00, 'status': 'PendingReview',
            'images': [], 'attributes': {}, 'category': '', 'source_url': url, 'brand': '', 'stock_quantity': 0
        }
        name_selector = soup.select_one('h1.product_title')
        if name_selector: product_data['name'] = name_selector.get_text(strip=True)

        price_selector = soup.select_one('.price .woocommerce-Price-amount')
        if price_selector:
            price_match = re.search(r'[\d,]+\.?\d*', price_selector.get_text(strip=True).replace(',', ''))
            if price_match: product_data['price'] = float(price_match.group())

        desc_selectors = ['#tab-description .wc-tab-inner', '.woocommerce-product-details__short-description']
        for selector in desc_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                product_data['description'] = desc_element.get_text(separator='\n', strip=True)
                break
        
        attributes = {}
        attributes_table = soup.find('table', class_='shop_attributes')
        if attributes_table:
            for row in attributes_table.find_all('tr'):
                label_tag, value_tag = row.find('th'), row.find('td')
                if label_tag and value_tag:
                    key, value = label_tag.get_text(strip=True), value_tag.get_text(strip=True)
                    attributes[key] = value
                    if key == 'برند' and not product_data.get('brand'): product_data['brand'] = value
        product_data['attributes'] = attributes

        image_selectors = 'figure.woocommerce-product-gallery__image a, .woocommerce-product-gallery__image img'
        image_attribute_priority = ['href', 'data-large_image', 'data-src', 'src']
        found_image_urls = []
        for elem in soup.select(image_selectors):
            img_url = None
            for attr in image_attribute_priority:
                if elem.has_attr(attr) and elem[attr]:
                    img_url = urljoin(url, elem[attr])
                    break
            if img_url and img_url not in found_image_urls: found_image_urls.append(img_url)
        product_data['images'] = found_image_urls

        sku_selector = soup.select_one('.sku')
        if sku_selector and sku_selector.get_text(strip=True).lower() != 'n/a':
            product_data['sku'] = sku_selector.get_text(strip=True)
        else:
            slug = unquote(url.rstrip('/').split('/')[-1])
            product_data['sku'] = re.sub(r'[\W_]+', '-', slug).strip('-')[:50]

        if not product_data['name']: product_data['name'] = f"Unknown Product - {product_data['sku']}"
        return product_data
    except Exception as e:
        print(f"    ❌ An error occurred during product page parsing: {e}")
        return None

def fetch_product_data(product_url):
    print(f"  ➡️  Fetching product page: {product_url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(product_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_product_data_from_soup(soup, product_url)
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Network error fetching product data: {e}")
        return None

def send_product_to_api(product_data):
    if not API_URL or not API_KEY: return False
    print(f"    🚀 Sending product '{product_data.get('name')}' to API...")
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'X-API-KEY': API_KEY}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps({'products': [product_data]}, indent=2, ensure_ascii=False), timeout=30)
        print(f"      API Response Status: {response.status_code}")
        response.raise_for_status()
        print(f"    ✅ Product data for SKU '{product_data.get('sku')}' sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"    ❌ API request failed: {e}")
        if hasattr(e, 'response') and e.response: print(f"      API Response Body: {e.response.text}")
        return False

# --- 3. Main Execution Block (The updated logic is here) ---

def main():
    """Main function to orchestrate the category crawler."""
    
    # --- ** NEW: Set up command-line argument parsing ** ---
    # The URL is now a mandatory positional argument.
    parser = argparse.ArgumentParser(
        description="Scrape a product category page for new products.",
        epilog="Example: python crawler.py \"https://websitename.com/product-category/sunglasses/\""
    )
    parser.add_argument('url', help="The FULL URL of the product category page to scrape.")
    args = parser.parse_args()

    # The script will automatically exit with an error if the 'url' argument is not provided.
    category_url = args.url

    print("--- 🚀 Starting Category Crawler ---")
    print(f"🎯 Target URL: {category_url}")
    
    scraped_urls = load_scraped_urls(LOG_FILE)
    print(f"🔎 Found {len(scraped_urls)} previously scraped URLs in '{LOG_FILE}'.")

    try:
        print(f"➡️  Fetching category page...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(category_url, headers=headers, timeout=30)
        response.raise_for_status()
        category_soup = BeautifulSoup(response.text, 'html.parser')
        
        product_links = category_soup.select('h3.wd-entities-title a')
        all_urls_on_page = {a['href'] for a in product_links}
        
        new_urls_to_crawl = [url for url in all_urls_on_page if url not in scraped_urls]
        print(f"✅ Found {len(all_urls_on_page)} total products on page. {len(new_urls_to_crawl)} are new.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch category page: {e}. Halting script.")
        return

    products_scraped_this_run = 0
    for product_url in new_urls_to_crawl:
        if products_scraped_this_run >= CRAWL_LIMIT:
            print(f"\n--- 🏁 Crawl limit of {CRAWL_LIMIT} reached for this run. ---")
            break

        print(f"\n--- Scraping new product ({products_scraped_this_run + 1}/{CRAWL_LIMIT}) ---")
        product_data = fetch_product_data(product_url)
        
        if product_data:
            if send_product_to_api(product_data):
                log_scraped_url(product_url, LOG_FILE)
                products_scraped_this_run += 1
        
        time.sleep(2)

    if products_scraped_this_run == 0:
        print("\n--- ✅ No new products to scrape on this page. ---")

    print("\n--- ✅ Crawler script finished. ---")


if __name__ == "__main__":
    main()
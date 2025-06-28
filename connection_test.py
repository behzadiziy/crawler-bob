#!/usr/bin/env python3
"""
Connection Test Script
Run this to diagnose connection issues with the target website.
"""

import requests
import time
from urllib.parse import urlparse, quote, unquote
import socket

def test_dns_resolution(hostname):
    """Test if we can resolve the hostname."""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS Resolution: {hostname} -> {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        return False

def test_basic_connectivity(url):
    """Test basic connectivity to the website."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    print(f"🔍 Testing connectivity to: {hostname}")
    
    # Test DNS resolution
    if not test_dns_resolution(hostname):
        return False
    
    # Test different approaches
    headers_list = [
        # Standard browser headers
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        },
        # Minimal headers
        {
            'User-Agent': 'Mozilla/5.0 (compatible; Python-requests/2.31.0)',
        },
        # No custom headers
        {}
    ]
    
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    for i, headers in enumerate(headers_list, 1):
        print(f"\n--- Test {i}: {'Custom headers' if i == 1 else 'Minimal headers' if i == 2 else 'No headers'} ---")
        
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Response size: {len(response.content)} bytes")
            print(f"✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
            return True
        except requests.exceptions.Timeout:
            print("❌ Timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_specific_url(url):
    """Test the specific product URL."""
    print(f"\n🎯 Testing specific URL: {url}")
    
    # Decode the URL to see what it actually is
    decoded_url = unquote(url)
    print(f"📝 Decoded URL: {decoded_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Final URL: {response.url}")
        print(f"✅ Response size: {len(response.content)} bytes")
        print(f"✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        # Check if it's HTML
        if 'text/html' in response.headers.get('content-type', ''):
            print("✅ Received HTML content")
            
            # Look for common indicators
            content_preview = response.text[:500]
            if 'product' in content_preview.lower():
                print("✅ Content appears to contain product information")
            else:
                print("⚠️  Content may not be a product page")
                
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Timeout - website is too slow")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 50)
    print("🔍 CONNECTION DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # The URL from your .env file
    test_url = "https://bobesfanjishop.com/product/%d9%be%da%a9-%db%b5-%d8%aa%d8%a7%db%8c%db%8c-%d8%b9%db%8c%d9%86%da%a9-%d8%a2%d9%81%d8%aa%d8%a7%d8%a8%db%8c-%db%8c%d9%88%d9%88%db%8c-%db%b4%db%b0%db%b0-%d8%aa%d8%b1%d9%86%d8%af-%d8%b2%d9%86%d8%a7-7/"
    
    # Test basic connectivity
    if test_basic_connectivity(test_url):
        print("\n✅ Basic connectivity is working")
        
        # Test the specific URL
        if test_specific_url(test_url):
            print("\n🎉 SUCCESS: The URL is accessible!")
            print("Your original crawler should work now.")
        else:
            print("\n❌ The specific product URL is having issues")
            print("The product page might not exist or might be blocked")
    else:
        print("\n❌ Cannot connect to the website")
        print("Check your internet connection or try again later")
    
    print("\n" + "=" * 50)
    print("💡 TROUBLESHOOTING TIPS:")
    print("1. Check your internet connection")
    print("2. Try accessing the website in your browser")
    print("3. The website might be temporarily down")
    print("4. Your IP might be blocked (try using a VPN)")
    print("5. The specific product URL might not exist")
    print("=" * 50)

if __name__ == "__main__":
    main()
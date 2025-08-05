#!/usr/bin/env python3
"""
Test script for SQLModel-based API endpoints
"""

import requests
import json
import sys

def test_api_endpoint(url, description):
    """Test a single API endpoint"""
    print(f"\n🧪 Testing: {description}")
    print(f"📍 URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Response: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        else:
            print(f"❌ HTTP Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Test SQLModel API endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    # Test endpoints
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/info", "API info"),
        ("/api/v2/strategies/", "Get all strategies (new typed endpoint)"),
        ("/api/v2/strategies/enums/strategy-types", "Strategy types enum"),
        ("/api/v2/strategies/enums/investment-frequencies", "Investment frequencies enum"),
        ("/api/v2/strategies/schema/btc-settings", "BTC settings schema"),
        ("/api/v2/strategies/schema/portfolio-settings", "Portfolio settings schema"),
    ]
    
    print("🚀 Testing SQLModel-based DiveTrader API v2")
    print("=" * 50)
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint, description in endpoints:
        if test_api_endpoint(f"{base_url}{endpoint}", description):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📈 Results: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("🎉 All SQLModel API endpoints are working correctly!")
        return 0
    else:
        print("⚠️ Some endpoints need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
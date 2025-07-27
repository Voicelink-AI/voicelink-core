"""
Quick test to verify analytics endpoints are working
"""

import requests
import json
from datetime import datetime

def test_analytics_endpoints():
    """Test analytics endpoints"""
    
    base_url = "http://localhost:8001"
    
    # Test endpoints
    endpoints = [
        "/health",
        "/api/health", 
        "/api/v1/analytics/health",
        "/api/v1/analytics/processing/status",
        "/docs"
    ]
    
    print("🧪 Testing Analytics Endpoints")
    print("=" * 40)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response keys: {list(data.keys())}")
                except:
                    print(f"   Response length: {len(response.text)} chars")
            else:
                print(f"   Error: {response.text[:100]}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    print("\n📋 Available routes check:")
    try:
        # Check available routes through OpenAPI
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = list(openapi.get("paths", {}).keys())
            analytics_paths = [p for p in paths if "analytics" in p]
            print(f"Total API paths: {len(paths)}")
            print(f"Analytics paths: {len(analytics_paths)}")
            for path in analytics_paths:
                print(f"  - {path}")
        else:
            print("Could not fetch OpenAPI spec")
    except Exception as e:
        print(f"Error checking routes: {e}")

if __name__ == "__main__":
    test_analytics_endpoints()

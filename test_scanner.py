#!/usr/bin/env python3
import requests
import json
import time

def test_gtm_scanner():
    base_url = "http://localhost:8080"
    
    # Test 1: Health check
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Scan endpoint with simple domain
    print("\n🔍 Testing scan endpoint...")
    test_data = {
        "domain": "https://fastapi.tiangolo.com",
        "max_pages": 3,
        "timeout_sec": 15
    }
    
    try:
        response = requests.post(
            f"{base_url}/scan",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Scan completed successfully")
            
            # Check key fields in new order
            expected_fields = ["domain", "company_name", "context"]
            for field in expected_fields:
                if field in result:
                    print(f"✅ {field}: Present")
                else:
                    print(f"⚠️  {field}: Missing")
            
            # Check optional fields
            optional_fields = ["social", "industry", "tech_stack", "seo_metrics"]
            for field in optional_fields:
                if field in result and result[field]:
                    print(f"✅ {field}: {type(result[field]).__name__}")
                
            print(f"\n📊 Results Summary:")
            print(f"Domain: {result.get('domain', 'N/A')}")
            print(f"Company: {result.get('company_name', 'N/A')}")
            print(f"Industry: {result.get('industry', 'N/A')}")
            print(f"Tech Categories: {len(result.get('tech_stack', []))}")
            print(f"Social Networks: {len(result.get('social', {}))}")
            
            return True
        else:
            print(f"❌ Scan failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Scan error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 GTM Scanner Test Suite")
    print("=" * 50)
    
    success = test_gtm_scanner()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
#!/usr/bin/env python3

import requests
import json
import sys
import subprocess
import time

def test_scanner():
    print("🚀 Quick GTM Scanner Test")
    print("=" * 50)
    
    # Start server in background
    print("📡 Starting server...")
    server = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app.main:app", 
        "--host", "0.0.0.0", "--port", "8002"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        health_response = requests.get("http://localhost:8002/health", timeout=10)
        print(f"✅ Health status: {health_response.status_code}")
        
        # Test scan endpoint
        print("🔍 Testing scan endpoint...")
        scan_data = {
            "domain": "hospitalitaliano.org.ar",
            "timeout_sec": 10
        }
        
        scan_response = requests.post(
            "http://localhost:8002/scan", 
            json=scan_data, 
            timeout=30
        )
        
        if scan_response.status_code == 200:
            result = scan_response.json()
            print(f"✅ Scan successful!")
            print(f"   📊 Domain: {result.get('domain')}")
            print(f"   🏢 Company: {result.get('company_name')}")
            print(f"   🔧 Tech categories: {list(result.get('tech_stack', {}).keys())}")
            print(f"   🏭 Industry: {result.get('industry')}")
            print(f"   📱 Social: {list(result.get('social', {}).keys())}")
            print(f"   📈 SEO metrics: {'✅' if result.get('seo_metrics') else '❌'}")
            print(f"   📄 Pages: {len(result.get('pages_crawled', []))}")
            
            # Show tech stack structure  
            tech_stack = result.get('tech_stack', {})
            if tech_stack:
                print(f"   🛠️ Tech Stack Structure:")
                for category, tech_data in tech_stack.items():
                    tools = tech_data.get('tools', [])
                    print(f"      - {category}: {tools}")
            
            print("🎉 All tests passed!")
        else:
            print(f"❌ Scan failed: {scan_response.status_code}")
            print(f"   Response: {scan_response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
    finally:
        print("🛑 Stopping server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    test_scanner()
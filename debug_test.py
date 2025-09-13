#!/usr/bin/env python3

import requests
import json
import sys
import subprocess
import time

def test_with_logs():
    print("🚀 GTM Scanner Test with Logs")
    print("=" * 50)
    
    # Start server with logs
    print("📡 Starting server with logs...")
    with open('test_server.log', 'w') as log_file:
        server = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8003"
        ], stdout=log_file, stderr=subprocess.STDOUT)
        
        # Wait for server to start
        time.sleep(5)
        
        try:
            # Test health endpoint
            print("🏥 Testing health endpoint...")
            health_response = requests.get("http://localhost:8003/health", timeout=10)
            print(f"✅ Health status: {health_response.status_code}")
            
            # Test scan endpoint with a simple domain
            print("🔍 Testing scan endpoint...")
            scan_data = {
                "domain": "google.com",
                "timeout_sec": 5
            }
            
            scan_response = requests.post(
                "http://localhost:8003/scan", 
                json=scan_data, 
                timeout=20
            )
            
            print(f"📊 Scan response status: {scan_response.status_code}")
            if scan_response.status_code != 200:
                print(f"❌ Error response: {scan_response.text}")
            else:
                result = scan_response.json()
                print(f"✅ Success! Domain: {result.get('domain')}")
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
        finally:
            print("🛑 Stopping server...")
            server.terminate()
            server.wait()
            
            # Show logs
            print("\n📝 Server logs:")
            with open('test_server.log', 'r') as log_file:
                logs = log_file.read()
                print(logs[-2000:])  # Last 2000 chars

if __name__ == "__main__":
    test_with_logs()
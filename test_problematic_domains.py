#!/usr/bin/env python3

import requests
import json
import subprocess
import time
import sys

def test_problematic_domains():
    print("🔍 Testing Problematic Domains")
    print("=" * 50)
    
    # Domains that return empty results
    test_domains = [
        "galiciamaxica.eu",
        "acrylicosvallejo.com", 
        "kaioland.com"
    ]
    
    # Start server
    server = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "app.main:app", 
        "--host", "0.0.0.0", "--port", "8008"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(5)
    
    try:
        for domain in test_domains:
            print(f"\n🌐 Testing {domain}...")
            
            data = {
                "domain": domain,
                "timeout_sec": 15,  # Longer timeout for problematic domains
                "max_pages": 2      # Fewer pages to avoid timeout
            }
            
            try:
                response = requests.post(
                    "http://localhost:8008/scan", 
                    json=data, 
                    timeout=45  # Generous timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if result is actually empty or has content
                    company = result.get('company_name')
                    tech_stack = result.get('tech_stack', {})
                    social = result.get('social', {})
                    industry = result.get('industry')
                    pages = result.get('pages_crawled', [])
                    
                    print(f"  📊 Status: {'✅ SUCCESS' if any([company, tech_stack, social, industry]) else '⚠️ EMPTY'}")
                    print(f"  🏢 Company: {company or 'None'}")
                    print(f"  🏭 Industry: {industry or 'None'}")
                    print(f"  🔧 Tech categories: {len(tech_stack)}")
                    print(f"  📱 Social networks: {len(social)}")
                    print(f"  📄 Pages crawled: {len(pages)}")
                    
                    if pages:
                        print(f"  🌐 URLs accessed: {pages}")
                    
                    # Show any tech found
                    if tech_stack:
                        print(f"  🛠️ Technologies found:")
                        for cat, tech_data in tech_stack.items():
                            tools = tech_data.get('tools', [])
                            print(f"    - {cat}: {tools}")
                            
                else:
                    print(f"  ❌ Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⏰ TIMEOUT - Domain took too long to respond")
            except Exception as e:
                print(f"  💥 ERROR: {str(e)}")
                
    finally:
        print("\n🛑 Stopping server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    test_problematic_domains()
#!/usr/bin/env python3
"""
Debug script to test backend connection
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_backend_connection():
    print("="*60)
    print("🔍 Backend Connection Debugger")
    print("="*60)
    
    # Check environment variables
    print("\n1️⃣ Checking Environment Variables:")
    api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8001')
    backend_port = os.getenv('BACKEND_PORT', '8001')
    polygon_key = os.getenv('POLYGON_API_KEY', 'Not set')
    
    print(f"   API_BASE_URL: {api_base_url}")
    print(f"   BACKEND_PORT: {backend_port}")
    print(f"   POLYGON_API_KEY: {'Set ✅' if polygon_key != 'Not set' else 'Not set ❌'}")
    
    # Test various endpoints
    endpoints_to_test = [
        f"http://localhost:{backend_port}/",
        f"http://localhost:{backend_port}/health",
        f"{api_base_url}/",
        f"{api_base_url}/health",
        f"{api_base_url}/api/stock/price/AAPL",
    ]
    
    print("\n2️⃣ Testing Backend Endpoints:")
    for endpoint in endpoints_to_test:
        print(f"\n   Testing: {endpoint}")
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"   ✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   📦 Response: {data}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Failed - Backend not running on this endpoint")
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout - Backend is slow or not responding")
        except Exception as e:
            print(f"   ⚠️  Error: {str(e)}")
    
    # Check if process is running on port
    print(f"\n3️⃣ Checking Port {backend_port}:")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', int(backend_port)))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {backend_port} is OPEN (something is listening)")
        else:
            print(f"   ❌ Port {backend_port} is CLOSED (nothing is listening)")
            print(f"   💡 Start backend with: cd backend && python main.py")
    except Exception as e:
        print(f"   ⚠️  Could not check port: {e}")
    
    print("\n" + "="*60)
    print("📋 Recommendations:")
    print("="*60)
    
    # Give recommendations
    print("\n1. Make sure backend is running:")
    print("   cd backend && python main.py")
    print("\n2. Or use the startup script:")
    print("   ./start_backend.sh")
    print("\n3. Check backend logs for errors")
    print("\n4. Verify .env file exists in project root")
    print("="*60)

if __name__ == "__main__":
    test_backend_connection()
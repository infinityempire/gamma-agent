#!/usr/bin/env python3
"""Test script for SSE functionality"""
import requests
import time
import json

def test_sse():
    print("📡 Testing SSE Connection...")
    
    # Start task
    print("\n📤 Sending task...")
    response = requests.post('http://localhost:5000/execute', 
                            json={'task': 'Test real-time streaming'},
                            timeout=5)
    print(f"Response: {response.json()}")
    
    # Connect to SSE
    print("\n📡 Connecting to SSE...")
    with requests.get('http://localhost:5000/events', stream=True, timeout=10) as r:
        print(f"SSE Status: {r.status_code}")
        count = 0
        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    data = decoded[6:]
                    print(f"  Event #{count}: {data[:100]}...")
                    count += 1
                    if count >= 15:
                        break
    
    print(f"\n✅ Received {count} events")

if __name__ == '__main__':
    test_sse()
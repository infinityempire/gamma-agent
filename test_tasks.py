#!/usr/bin/env python3
import subprocess
import time
import requests
import sys

# Start server
print("Starting server...")
proc = subprocess.Popen(['python3', 'gamma_server.py'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
time.sleep(3)

# Test tasks
tasks = [
    "List all your active autonomous services",
    "Check system status and report to file",
    "Analyze and count all running processes",
    "Generate a summary of available resources",
    "Execute self-diagnostics and output report"
]

print("\n" + "="*60)
print("GAMMA AGENT v2.0 - TESTING 5 AUTONOMOUS TASKS")
print("="*60)

for i, task in enumerate(tasks, 1):
    print(f"\n{'='*60}")
    print(f"TASK {i}/5: {task}")
    print("-"*60)
    
    try:
        # Execute task
        resp = requests.post('http://localhost:5000/execute', 
                           json={'task': task}, 
                           timeout=5)
        print(f"Status: {resp.json()}")
        
        # Wait for completion
        time.sleep(4)
        
        # Check status
        status = requests.get('http://localhost:5000/status', timeout=5)
        print(f"Server Status: {status.json()}")
        
    except Exception as e:
        print(f"Error: {e}")

# Cleanup
proc.terminate()
print("\n" + "="*60)
print("TESTING COMPLETE")
print("="*60)
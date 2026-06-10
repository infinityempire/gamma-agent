#!/usr/bin/env python3
"""
Gamma Agent - Task Executor
This script is called by GitHub Actions workflow
"""
import os
import sys
from datetime import datetime

# Get task from environment or command line argument
task = os.environ.get('INPUT_TASK', '')
if not task and len(sys.argv) > 1:
    task = sys.argv[1]

if not task:
    task = "echo Hello"

print("=" * 50)
print("🤖 GAMMA AGENT v3.0 - CLOUD EXECUTION")
print("=" * 50)
print(f"📋 Task: {task}")
print(f"🔄 Max Retries: {os.environ.get('INPUT_MAX_RETRIES', '3')}")
print(f"🔁 Max Iterations: {os.environ.get('INPUT_MAX_ITERATIONS', '10')}")
print(f"⏰ Started: {datetime.now()}")
print()

# Import and run the agent
sys.path.insert(0, '.')
try:
    from gamma_server import answer_question
    
    print('🚀 Executing task...')
    print()
    
    result = answer_question(task)
    print(result)
    print()
    print('=' * 50)
    print(f'✅ Task completed at: {datetime.now()}')
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
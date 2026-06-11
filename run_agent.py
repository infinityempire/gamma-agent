#!/usr/bin/env python3
"""
Gamma Agent - Autonomous Execution Agent Runner
This script executes tasks using the autonomous agent with tool-calling.
"""
import os
import sys
import hashlib
from datetime import datetime

# Get task from environment or command line argument
task = os.environ.get('INPUT_TASK', '')
if not task and len(sys.argv) > 1:
    task = sys.argv[1]

if not task:
    task = "List files in current directory"

print("=" * 60)
print("🤖 GAMMA AGENT v4.0 - AUTONOMOUS EXECUTION")
print("=" * 60)
print(f"📋 Task: {task}")
print(f"🔄 Max Retries: {os.environ.get('INPUT_MAX_RETRIES', '3')}")
print(f"🔁 Max Iterations: {os.environ.get('INPUT_MAX_ITERATIONS', '10')}")
print(f"⏰ Started: {datetime.now()}")
print()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from gamma_server import execute_with_gemini, log_to_file, save_task_output, registry
    
    print(f'🛠️  Available Tools: {len(registry.get_schemas())}')
    print(f'   - {", ".join(t["name"] for t in registry.get_schemas()[:5])}...')
    print()
    print('🚀 Executing task...')
    print()
    
    result = execute_with_gemini(task)
    print(result)
    print()
    
    # Save output
    task_id = hashlib.md5(f"{task}{datetime.now()}".encode()).hexdigest()[:8] if 'hashlib' in dir() else 'local'
    output_file = save_task_output(task_id, result)
    
    print('=' * 60)
    print(f'✅ Task completed at: {datetime.now()}')
    print(f'📁 Output saved to: {output_file}')
    
    log_to_file(f"TASK_COMPLETED: {task}", "COMPLETION")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    log_to_file(f"TASK_ERROR: {task} - {str(e)}", "ERROR")
    sys.exit(1)
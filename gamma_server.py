#!/usr/bin/env python3
"""
Gamma Agent v4.0 - Autonomous Execution Agent
=============================================
An intelligent autonomous agent with tool-calling capabilities
using Google Generative AI.

Capabilities:
- Dynamic Tool Registry with function schemas
- Shell command execution
- File system management
- GitHub repository integration
- Persistence logging to archive/agent_log.txt
- Autonomous command file execution from commands/ directory
"""

import json
import time
import subprocess
import os
import re
import threading
import urllib.request
import urllib.parse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

# Flask setup
from flask import Flask, Response, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(REPO_DIR, 'archive')
COMMANDS_DIR = os.path.join(REPO_DIR, 'commands')
EVENTS_FILE = os.path.join(REPO_DIR, '.events')
LOG_FILE = os.path.join(ARCHIVE_DIR, 'agent_log.txt')
GITHUB_TOKEN = os.environ.get('GH_TOKEN', os.environ.get('GITHUB_TOKEN', ''))
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Ensure directories exist
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(COMMANDS_DIR, exist_ok=True)

# ============================================================================
# LOGGING SYSTEM
# ============================================================================

def log_to_file(message: str, level: str = "INFO"):
    """Log message to archive/agent_log.txt with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    
    print(f"[{timestamp}] [{level}] {message}")

def log_action(action: str, details: str = "", result: str = "SUCCESS"):
    """Log an agent action with full details"""
    log_to_file(f"ACTION: {action} | Details: {details} | Result: {result}", "ACTION")

def log_tool_call(tool_name: str, args: Dict, result: str):
    """Log a tool call"""
    args_str = json.dumps(args, ensure_ascii=False)[:200]
    log_to_file(f"TOOL_CALL: {tool_name} | Args: {args_str} | Result: {result[:200]}", "TOOL")

def save_task_output(task_id: str, output: str, error: str = None):
    """Save task output to a dedicated file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"task_{task_id}_{timestamp}.txt"
    filepath = os.path.join(ARCHIVE_DIR, filename)
    
    content = f"""Task ID: {task_id}
Timestamp: {datetime.now().isoformat()}
{'=' * 60}
OUTPUT:
{'=' * 60}
{output}
"""
    if error:
        content += f"""
{'=' * 60}
ERROR:
{'=' * 60}
{error}
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    log_action("TASK_OUTPUT_SAVED", f"Task {task_id}", f"Saved to {filename}")
    return filepath

# ============================================================================
# TOOL REGISTRY SYSTEM
# ============================================================================

class ToolRegistry:
    """Dynamic registry for agent tools with function schemas"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: List[Dict] = []
    
    def register(self, name: str, description: str, parameters: Dict, func: Callable):
        """Register a tool with its schema"""
        self.tools[name] = func
        self.schemas.append({
            "name": name,
            "description": description,
            "parameters": parameters
        })
        log_to_file(f"Tool registered: {name}", "REGISTRY")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_schemas(self) -> List[Dict]:
        """Get all tool schemas for AI model"""
        return self.schemas
    
    def execute(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool with given arguments"""
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            result = tool(**arguments)
            log_tool_call(tool_name, arguments, str(result)[:200])
            return result
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            log_tool_call(tool_name, arguments, f"ERROR: {error_msg}")
            return error_msg

# Global registry
registry = ToolRegistry()

# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

def run_command(command: str, timeout: int = 60, cwd: str = None) -> str:
    """Execute a shell command and return output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or REPO_DIR
        )
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        return output or "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"

# Tool: execute_shell
def tool_execute_shell(command: str, timeout: int = 60) -> str:
    """Execute a shell command on the system."""
    return run_command(command, timeout)

registry.register(
    "execute_shell",
    "Execute a shell command on the system. Returns command output.",
    {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default: 60)"}
        },
        "required": ["command"]
    },
    tool_execute_shell
)

# Tool: read_file
def tool_read_file(file_path: str, max_lines: int = 1000) -> str:
    """Read contents of a file."""
    full_path = os.path.join(REPO_DIR, file_path) if not os.path.isabs(file_path) else file_path
    
    if not os.path.exists(full_path):
        return f"Error: File not found: {file_path}"
    
    if not os.path.isfile(full_path):
        return f"Error: Path is not a file: {file_path}"
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        content = ''.join(lines[:max_lines])
        if len(lines) > max_lines:
            content += f"\n... (truncated, {len(lines) - max_lines} more lines)"
        
        return f"File: {file_path}\n{'=' * 40}\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

registry.register(
    "read_file",
    "Read the contents of a file. Returns file contents or error.",
    {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to read"},
            "max_lines": {"type": "integer", "description": "Maximum lines to read", "default": 1000}
        },
        "required": ["file_path"]
    },
    tool_read_file
)

# Tool: write_file
def tool_write_file(file_path: str, content: str, append: bool = False) -> str:
    """Write content to a file."""
    full_path = os.path.join(REPO_DIR, file_path) if not os.path.isabs(file_path) else file_path
    
    if not full_path.startswith(REPO_DIR):
        return f"Error: Cannot write outside repository directory"
    
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = 'a' if append else 'w'
        
        with open(full_path, mode, encoding='utf-8') as f:
            f.write(content)
        
        action = "Appended to" if append else "Written to"
        return f"Success: {action} {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

registry.register(
    "write_file",
    "Write content to a file. Creates file if needed.",
    {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to write"},
            "content": {"type": "string", "description": "Content to write"},
            "append": {"type": "boolean", "description": "Append to file", "default": False}
        },
        "required": ["file_path", "content"]
    },
    tool_write_file
)

# Tool: delete_file
def tool_delete_file(file_path: str) -> str:
    """Delete a file from the system."""
    full_path = os.path.join(REPO_DIR, file_path) if not os.path.isabs(file_path) else file_path
    
    if not full_path.startswith(REPO_DIR):
        return f"Error: Cannot delete files outside repository"
    
    if not os.path.exists(full_path):
        return f"Error: File not found: {file_path}"
    
    try:
        os.remove(full_path)
        return f"Success: Deleted {file_path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

registry.register(
    "delete_file",
    "Delete a file from the system.",
    {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to delete"}
        },
        "required": ["file_path"]
    },
    tool_delete_file
)

# Tool: list_directory
def tool_list_directory(directory: str = ".", include_hidden: bool = False) -> str:
    """List contents of a directory."""
    full_path = os.path.join(REPO_DIR, directory) if not os.path.isabs(directory) else directory
    
    if not os.path.exists(full_path):
        return f"Error: Directory not found: {directory}"
    
    if not os.path.isdir(full_path):
        return f"Error: Path is not a directory: {directory}"
    
    try:
        items = os.listdir(full_path)
        if not include_hidden:
            items = [i for i in items if not i.startswith('.')]
        
        items.sort()
        output = f"Directory: {directory}\n{'=' * 40}\n"
        
        for item in items:
            full_item_path = os.path.join(full_path, item)
            if os.path.isdir(full_item_path):
                output += f"📁 {item}/\n"
            else:
                size = os.path.getsize(full_item_path)
                output += f"📄 {item} ({size} bytes)\n"
        
        return output
    except Exception as e:
        return f"Error listing directory: {str(e)}"

registry.register(
    "list_directory",
    "List contents of a directory.",
    {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Directory path", "default": "."},
            "include_hidden": {"type": "boolean", "description": "Include hidden files", "default": False}
        },
        "required": []
    },
    tool_list_directory
)

# Tool: search_files
def tool_search_files(pattern: str, directory: str = ".", file_type: str = "") -> str:
    """Search for files matching a pattern."""
    full_path = os.path.join(REPO_DIR, directory) if not os.path.isabs(directory) else directory
    
    if not os.path.exists(full_path):
        return f"Error: Directory not found: {directory}"
    
    try:
        matches = []
        for root, dirs, files in os.walk(full_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
            
            for file in files:
                if pattern.lower() in file.lower() and (not file_type or file.endswith(f'.{file_type}')):
                    matches.append(os.path.join(root, file).replace(REPO_DIR + '/', ''))
        
        if matches:
            return f"Found {len(matches)} matches:\n" + "\n".join(f"• {m}" for m in matches[:50])
        return f"No files found matching '{pattern}'"
    except Exception as e:
        return f"Error searching files: {str(e)}"

registry.register(
    "search_files",
    "Search for files matching a pattern.",
    {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Pattern to search"},
            "directory": {"type": "string", "description": "Directory to search", "default": "."},
            "file_type": {"type": "string", "description": "File extension filter", "default": ""}
        },
        "required": ["pattern"]
    },
    tool_search_files
)

# Tool: github_list_repos
def tool_github_list_repos() -> str:
    """List repositories for the authenticated GitHub user."""
    if not GITHUB_TOKEN:
        return "Error: GitHub token not configured. Set GH_TOKEN environment variable."
    
    try:
        import requests
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get("https://api.github.com/user/repos", headers=headers, params={"per_page": 30})
        
        if response.status_code != 200:
            return f"Error: GitHub API returned {response.status_code}"
        
        repos = response.json()
        if not repos:
            return "No repositories found"
        
        output = "Your GitHub Repositories:\n" + "=" * 40 + "\n"
        for repo in repos:
            output += f"📦 {repo['full_name']}\n   {repo.get('description', 'No description')}\n   ⭐ {repo.get('stargazers_count', 0)} | 🔀 {repo.get('forks_count', 0)}\n\n"
        
        return output
    except Exception as e:
        return f"Error accessing GitHub: {str(e)}"

registry.register(
    "github_list_repos",
    "List repositories for the authenticated GitHub user.",
    {
        "type": "object",
        "properties": {}
    },
    tool_github_list_repos
)

# Tool: github_create_file
def tool_github_create_file(repo: str, path: str, content: str, message: str, branch: str = "main") -> str:
    """Create or update a file in a GitHub repository."""
    if not GITHUB_TOKEN:
        return "Error: GitHub token not configured. Set GH_TOKEN environment variable."
    
    try:
        import requests
        import base64
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        existing_url = f"https://api.github.com/repos/{repo}/contents/{path}"
        existing = requests.get(existing_url, headers=headers, params={"ref": branch})
        
        sha = None
        if existing.status_code == 200:
            sha = existing.json().get('sha')
            message = f"Update: {message}" if message else "Update file via Gamma Agent"
        else:
            message = f"Create: {message}" if message else "Create file via Gamma Agent"
        
        encoded_content = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": message,
            "content": encoded_content,
            "branch": branch
        }
        if sha:
            data["sha"] = sha
        
        response = requests.put(existing_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            return f"Success: File {'updated' if sha else 'created'} at {result['content']['path']}\nURL: {result['content']['html_url']}"
        else:
            return f"Error: GitHub API returned {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

registry.register(
    "github_create_file",
    "Create or update a file in a GitHub repository.",
    {
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repository (owner/repo)"},
            "path": {"type": "string", "description": "Path in repository"},
            "content": {"type": "string", "description": "File content"},
            "message": {"type": "string", "description": "Commit message"},
            "branch": {"type": "string", "description": "Branch name", "default": "main"}
        },
        "required": ["repo", "path", "content", "message"]
    },
    tool_github_create_file
)

# Tool: github_run_workflow
def tool_github_run_workflow(repo: str, workflow_id: str, inputs: Dict = None) -> str:
    """Trigger a GitHub Actions workflow dispatch."""
    if not GITHUB_TOKEN:
        return "Error: GitHub token not configured."
    
    try:
        import requests
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        data = {"ref": "main"}
        if inputs:
            data["inputs"] = inputs
        
        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 204:
            return f"Success: Workflow '{workflow_id}' triggered"
        else:
            return f"Error: {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

registry.register(
    "github_run_workflow",
    "Trigger a GitHub Actions workflow dispatch.",
    {
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repository (owner/repo)"},
            "workflow_id": {"type": "string", "description": "Workflow filename or ID"},
            "inputs": {"type": "object", "description": "Workflow inputs", "default": {}}
        },
        "required": ["repo", "workflow_id"]
    },
    tool_github_run_workflow
)

# Tool: get_system_info
def tool_get_system_info() -> str:
    """Get current system information."""
    try:
        output = f"""System Information:
{'=' * 40}
Repository: {REPO_DIR}
Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Git Status:
"""
        output += run_command("git status --short 2>/dev/null || echo 'Not a git repository'")
        output += f"\nGit Branch:\n"
        output += run_command("git branch --show-current 2>/dev/null || echo 'N/A'")
        output += f"\nDisk Usage:\n"
        output += run_command(f"du -sh {REPO_DIR} 2>/dev/null || echo 'N/A'")
        return output
    except Exception as e:
        return f"Error getting system info: {str(e)}"

registry.register(
    "get_system_info",
    "Get current system information.",
    {
        "type": "object",
        "properties": {}
    },
    tool_get_system_info
)

# Tool: search_web
def tool_search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information."""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'GammaAgent/4.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        results = []
        if data.get('RelatedTopics'):
            for item in data['RelatedTopics'][:max_results]:
                if 'Text' in item:
                    results.append(f"• {item['Text'][:300]}")
        
        if results:
            return f"Web search results for '{query}':\n\n" + "\n".join(results)
        return f"No results found for '{query}'"
    except Exception as e:
        return f"Web search error: {str(e)}"

registry.register(
    "search_web",
    "Search the web for information.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5}
        },
        "required": ["query"]
    },
    tool_search_web
)

# Tool: analyze_and_execute
def tool_analyze_and_execute(task: str) -> str:
    """Analyze a natural language task and execute appropriate commands."""
    task_lower = task.lower()
    results = []
    
    # Check for multiple commands
    commands_to_run = []
    
    if "git" in task_lower and "status" in task_lower:
        commands_to_run.append(("Git Status", "git status"))
    if "git" in task_lower and "log" in task_lower:
        commands_to_run.append(("Git Log", "git log --oneline -10"))
    if "git" in task_lower and "branch" in task_lower:
        commands_to_run.append(("Git Branch", "git branch -a"))
    if "git" in task_lower and "diff" in task_lower:
        commands_to_run.append(("Git Diff", "git diff --stat"))
    
    # Check for directory listing
    if "list" in task_lower and ("file" in task_lower or "directory" in task_lower or "folder" in task_lower or "current" in task_lower or "dir" in task_lower):
        path = "."
        for word in task.split():
            if word.startswith("/") or ("." in word and len(word) > 2):
                path = word
                break
        commands_to_run.append(("Directory Listing", f"ls -la {path}"))
    
    # Check for archive directory
    if "archive" in task_lower:
        commands_to_run.append(("Archive Contents", f"ls -la {os.path.join(REPO_DIR, 'archive')}"))
    
    # Check for commands directory
    if "command" in task_lower and "dir" in task_lower:
        commands_to_run.append(("Commands Contents", f"ls -la {os.path.join(REPO_DIR, 'commands')}"))
    
    # Check for find/search
    if "find" in task_lower or ("search" in task_lower and "file" in task_lower):
        pattern = ""
        for word in task.split():
            if len(word) > 3 and not word.lower() in ['find', 'search', 'for', 'in', 'the', 'and', 'file', 'files']:
                pattern = word
                break
        if pattern:
            commands_to_run.append(("Search Files", f"find . -name '*{pattern}*' 2>/dev/null | head -20"))
    
    # Check for process listing
    if "process" in task_lower or ("running" in task_lower and "task" not in task_lower):
        commands_to_run.append(("Running Processes", "ps aux | head -15"))
    
    # Check for disk usage
    if "disk" in task_lower or "space" in task_lower:
        commands_to_run.append(("Disk Usage", "df -h"))
    
    # Check for memory info
    if "memory" in task_lower or "ram" in task_lower:
        commands_to_run.append(("Memory Info", "free -h"))
    
    # Check for system info
    if "system" in task_lower or "info" in task_lower or "about" in task_lower:
        commands_to_run.append(("System Info", "uname -a && echo '---' && cat /etc/os-release 2>/dev/null | head -5"))
    
    # If no specific commands matched, use basic execution based on keywords
    if not commands_to_run:
        # Default behavior: list current directory
        commands_to_run.append(("Directory Listing", "ls -la"))
    
    # Execute all matched commands
    for desc, cmd in commands_to_run:
        results.append(f"### {desc}")
        results.append(f"$ {cmd}")
        results.append(run_command(cmd))
        results.append("")
    
    return "\n".join(results)

registry.register(
    "analyze_and_execute",
    "Analyze a natural language task and execute commands.",
    {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "Task description"}
        },
        "required": ["task"]
    },
    tool_analyze_and_execute
)

# ============================================================================
# GEMINI AI INTEGRATION
# ============================================================================

def get_gemini_model():
    """Get Google Gemini model with tool support"""
    if not GEMINI_API_KEY:
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=registry.get_schemas()
        )
        return model
    except Exception as e:
        log_to_file(f"Gemini initialization error: {e}", "ERROR")
        return None

def execute_with_gemini(task: str, max_iterations: int = 10) -> str:
    """Execute task using Gemini with tool calling"""
    model = get_gemini_model()
    
    if not model:
        log_action("GEMINI_UNAVAILABLE", task, "Falling back to analyze_and_execute")
        return tool_analyze_and_execute(task)
    
    try:
        import google.generativeai as genai
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        prompt = f"""You are Gamma Agent, an autonomous execution agent.
You have access to these tools:
{json.dumps(registry.get_schemas(), indent=2)}

Task: {task}

Execute this task using the available tools."""
        
        response = chat.send_message(prompt)
        all_results = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if hasattr(response, 'function_calls') and response.function_calls:
                for call in response.function_calls:
                    tool_name = call.name
                    tool_args = {k: v for k, v in call.args.items()}
                    
                    log_action("TOOL_CALL", f"{tool_name}({tool_args})", "EXECUTING")
                    result = registry.execute(tool_name, tool_args)
                    all_results.append(f"[{tool_name}] {result}")
                    
                    response = chat.send_message(
                        genai.protos.Content(
                            parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={'result': result}
                                )
                            )]
                        )
                    )
            else:
                text = response.text if hasattr(response, 'text') else str(response)
                all_results.append(f"[RESULT] {text}")
                break
        
        output = "\n".join(all_results)
        log_action("TASK_COMPLETED", task, f"Completed in {iteration} iterations")
        return output
        
    except Exception as e:
        error_msg = f"Gemini execution error: {str(e)}"
        log_to_file(error_msg, "ERROR")
        return tool_analyze_and_execute(task)

# ============================================================================
# AUTONOMOUS COMMAND FILE EXECUTOR
# ============================================================================

class CommandFileWatcher:
    """Watches commands/ directory for .txt files and executes them"""
    
    def __init__(self):
        self.processed_files = set()
        self.running = False
        self.thread = None
        self.last_check = {}
    
    def scan_commands(self):
        """Scan for new command files"""
        if not os.path.exists(COMMANDS_DIR):
            return []
        
        new_commands = []
        for filename in os.listdir(COMMANDS_DIR):
            if filename.endswith('.txt') and filename not in self.processed_files:
                filepath = os.path.join(COMMANDS_DIR, filename)
                mtime = os.path.getmtime(filepath)
                
                if filename not in self.last_check or self.last_check[filename] != mtime:
                    self.last_check[filename] = mtime
                    new_commands.append((filename, filepath))
        
        return new_commands
    
    def execute_command_file(self, filename: str, filepath: str) -> str:
        """Execute commands from a file"""
        log_action("AUTO_EXEC", f"Reading {filename}", "STARTED")
        
        try:
            with open(filepath, 'r') as f:
                commands = f.read().strip()
            
            if not commands:
                return "File is empty"
            
            task_id = hashlib.md5(f"{filename}{time.time()}".encode()).hexdigest()[:8]
            result = execute_with_gemini(commands)
            output_file = save_task_output(task_id, result)
            
            self.processed_files.add(filename)
            
            log_action("AUTO_EXEC", f"Completed {filename}", f"Output: {output_file}")
            
            return f"Executed: {filename}\nOutput saved to: {output_file}\n\n{result}"
            
        except Exception as e:
            error_msg = f"Error executing {filename}: {str(e)}"
            log_to_file(error_msg, "ERROR")
            return error_msg
    
    def start_watching(self):
        """Start watching for command files"""
        self.running = True
        log_action("WATCHER_STARTED", "Autonomous command watcher started", "ACTIVE")
        
        while self.running:
            try:
                new_commands = self.scan_commands()
                for filename, filepath in new_commands:
                    result = self.execute_command_file(filename, filepath)
                    print(f"\n{'=' * 60}")
                    print(f"AUTONOMOUS EXECUTION: {filename}")
                    print(f"{'=' * 60}")
                    print(result)
                    print(f"{'=' * 60}\n")
                
                time.sleep(5)
            except Exception as e:
                log_to_file(f"Watcher error: {e}", "ERROR")
                time.sleep(10)
    
    def start_background(self):
        """Start watching in background thread"""
        if self.thread and self.thread.is_alive():
            return
        
        self.thread = threading.Thread(target=self.start_watching, daemon=True)
        self.thread.start()
        log_to_file("Command file watcher started in background", "SYSTEM")
    
    def stop_watching(self):
        """Stop watching"""
        self.running = False
        log_to_file("Command file watcher stopped", "SYSTEM")

# Global watcher instance
command_watcher = CommandFileWatcher()

# ============================================================================
# EVENT SYSTEM
# ============================================================================

def emit_event(event_type: str, data: Dict):
    """Emit an event to SSE clients"""
    with open(EVENTS_FILE, 'a') as f:
        f.write(json.dumps({
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            **data
        }) + '\n')
    print(f"📡 EMIT: {event_type} -> {data}")

def log(msg: str):
    """Print to console with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

def answer_question(question: str) -> str:
    """Legacy function for backwards compatibility"""
    return execute_with_gemini(question)

def execute_process_task(task: str) -> str:
    """Legacy function for backwards compatibility"""
    return tool_execute_shell(task)

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the gamma-standalone.html"""
    return send_file(os.path.join(REPO_DIR, 'gamma-standalone.html'))

@app.route('/execute', methods=['POST'])
def execute():
    """Execute a task (async)"""
    data = request.get_json()
    task = data.get('task', '')
    
    if not task:
        return jsonify({'error': 'No task provided'}), 400
    
    log(f"📥 New task received: {task}")
    
    thread = threading.Thread(target=execute_task_streaming, args=(task,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'task': task})

def execute_task_streaming(task: str):
    """Execute task with streaming updates"""
    task_id = hashlib.md5(f"{task}{time.time()}".encode()).hexdigest()[:8]
    
    emit_event('task_started', {'task_id': task_id, 'task': task})
    
    try:
        result = execute_with_gemini(task)
        emit_event('task_completed', {'task_id': task_id, 'result': result[:500]})
        save_task_output(task_id, result)
    except Exception as e:
        emit_event('task_error', {'task_id': task_id, 'error': str(e)})

@app.route('/events')
def events():
    """SSE endpoint for real-time updates"""
    def generate():
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, 'r') as f:
                for line in f:
                    if line.strip():
                        yield f"data: {line.strip()}\n\n"
        
        last_pos = os.path.getsize(EVENTS_FILE) if os.path.exists(EVENTS_FILE) else 0
        while True:
            try:
                if os.path.exists(EVENTS_FILE):
                    with open(EVENTS_FILE, 'r') as f:
                        f.seek(last_pos)
                        for line in f:
                            if line.strip():
                                yield f"data: {line.strip()}\n\n"
                        last_pos = f.tell()
                time.sleep(0.1)
            except GeneratorExit:
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/status')
def status():
    """Get current status"""
    return jsonify({
        'status': 'running',
        'tools_count': len(registry.get_schemas()),
        'watcher_active': command_watcher.running,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/tools')
def list_tools():
    """List all available tools"""
    return jsonify({
        'tools': registry.get_schemas(),
        'count': len(registry.get_schemas())
    })

@app.route('/execute_tool', methods=['POST'])
def execute_tool():
    """Execute a specific tool directly"""
    data = request.get_json()
    tool_name = data.get('tool', '')
    arguments = data.get('arguments', {})
    
    if not tool_name:
        return jsonify({'error': 'No tool specified'}), 400
    
    result = registry.execute(tool_name, arguments)
    return jsonify({'result': result})

@app.route('/log')
def get_log():
    """Get the agent log"""
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE)
    return jsonify({'error': 'Log file not found'}), 404

@app.route('/report')
def get_report():
    """Download the empire_report.txt file"""
    report_path = os.path.join(REPO_DIR, 'empire_report.txt')
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    return jsonify({'error': 'Report not found'}), 404

@app.route('/watcher/start', methods=['POST'])
def start_watcher():
    """Start the autonomous command watcher"""
    command_watcher.start_background()
    return jsonify({'status': 'started'})

@app.route('/watcher/stop', methods=['POST'])
def stop_watcher():
    """Stop the autonomous command watcher"""
    command_watcher.stop_watching()
    return jsonify({'status': 'stopped'})

@app.route('/watcher/status')
def watcher_status():
    """Get watcher status"""
    return jsonify({
        'active': command_watcher.running,
        'processed_files': list(command_watcher.processed_files)
    })

@app.route('/process_command_file', methods=['POST'])
def process_command_file():
    """Manually process a command file"""
    data = request.get_json()
    filename = data.get('filename', '')
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    filepath = os.path.join(COMMANDS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    result = command_watcher.execute_command_file(filename, filepath)
    return jsonify({'result': result})

@app.route('/commands')
def list_commands():
    """List pending command files"""
    files = []
    for filename in os.listdir(COMMANDS_DIR):
        if filename.endswith('.txt'):
            filepath = os.path.join(COMMANDS_DIR, filename)
            files.append({
                'name': filename,
                'size': os.path.getsize(filepath),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                'processed': filename in command_watcher.processed_files
            })
    return jsonify({'files': files})

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    log_to_file("=" * 60, "SYSTEM")
    log_to_file("Gamma Agent v4.0 Starting", "SYSTEM")
    log_to_file(f"Repository: {REPO_DIR}", "SYSTEM")
    log_to_file(f"Commands Dir: {COMMANDS_DIR}", "SYSTEM")
    log_to_file(f"Archive Dir: {ARCHIVE_DIR}", "SYSTEM")
    log_to_file(f"Tools Registered: {len(registry.get_schemas())}", "SYSTEM")
    log_to_file(f"GitHub Token: {'Configured' if GITHUB_TOKEN else 'Not configured'}", "SYSTEM")
    log_to_file(f"Gemini API Key: {'Configured' if GEMINI_API_KEY else 'Not configured'}", "SYSTEM")
    log_to_file("=" * 60, "SYSTEM")
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                        GAMMA AGENT v4.0                              ║
║              Autonomous Execution Agent - Tool Registry              ║
╠══════════════════════════════════════════════════════════════════════╣
║  🚀 Server starting...                                              ║
║  📁 Repository: {REPO_DIR:<48}║
║  🛠️  Tools: {len(registry.get_schemas()):<50}║
║  👁️  Command Watcher: AUTONOMOUS                                     ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    command_watcher.start_background()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
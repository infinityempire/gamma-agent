#!/bin/bash

# Gamma Agent v3.0 - Start Script

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  GAMMA AGENT v3.0 - AUTONOMOUS AI           ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Starting server on http://localhost:5000                   ║"
echo "║  Opening browser automatically...                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python from: https://www.python.org/downloads/"
    exit 1
fi

# Check if required packages are installed
if ! pip3 show flask &> /dev/null; then
    echo "Installing required packages..."
    pip3 install flask flask-cors
fi

# Kill any existing server on port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Start the server in background
echo "Starting server..."
python3 gamma_server.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Open browser (works on Mac, Linux with GUI)
if command -v open &> /dev/null; then
    open http://localhost:5000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000
elif command -v start &> /dev/null; then
    start http://localhost:5000
fi

echo ""
echo "✅ Gamma Agent is running!"
echo ""
echo "Open your browser and go to: http://localhost:5000"
echo ""
echo "Press Ctrl+C in this terminal to stop the server."
echo ""

# Keep script running
wait $SERVER_PID
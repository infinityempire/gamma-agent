# Gamma Agent v2.0

Real-time autonomous task execution system with streaming UI updates.

## Files
- `gamma-standalone.html` - Main interface with real-time step display
- `gamma_server.py` - Flask backend server
- `empire_report.txt` - Sample output report

## Features
- Real-time step-by-step execution display
- SSE (Server-Sent Events) for live updates
- Progress tracking
- Status cards for each phase
- Final output display

## Usage
```bash
pip install flask flask-cors
python gamma_server.py
# Open http://localhost:5000
```

## Task Example
Enter this prompt in the interface:
```
Gamma, list all your active autonomous services, and output the current status of each one to empire_report.txt.
```
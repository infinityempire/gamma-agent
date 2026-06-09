#!/usr/bin/env python3
"""Simple server launcher"""
from gamma_server import app
app.run(host='0.0.0.0', port=5005, debug=False, threaded=True, use_reloader=False)
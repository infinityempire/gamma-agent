#!/usr/bin/env python3
"""Simple server launcher"""
from gamma_server import app
app.run(host='127.0.0.1', port=5006, debug=False, threaded=True, use_reloader=False)
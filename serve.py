#!/usr/bin/env python3
"""Simple HTTP server for the LUT viewer. Run this then open http://localhost:8080"""

import http.server
import os
import sys

PORT = 8080

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if not os.path.exists("data/metadata.json"):
    print("ERROR: data/metadata.json not found.")
    print("Run 'python preprocess.py' first to generate the data files.")
    sys.exit(1)

handler = http.server.SimpleHTTPRequestHandler
handler.extensions_map.update({".json": "application/json"})

print(f"Serving at http://localhost:{PORT}")
print("Press Ctrl+C to stop.")
with http.server.HTTPServer(("", PORT), handler) as httpd:
    httpd.serve_forever()

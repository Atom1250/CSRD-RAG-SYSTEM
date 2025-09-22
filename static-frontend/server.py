#!/usr/bin/env python3
"""
Simple HTTP server for CSRD RAG System static frontend
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

# Change to the directory containing this script
os.chdir(Path(__file__).parent)

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def find_free_port():
    """Find a free port to use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

if __name__ == "__main__":
    # Try port 3000 first, then find a free port
    try:
        port = 3000
        with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
            print(f"🌐 CSRD RAG System Frontend")
            print(f"📍 Serving at: http://localhost:{port}")
            print(f"📁 Directory: {os.getcwd()}")
            print(f"🔗 Open: http://localhost:{port}")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError:
        # Port 3000 is busy, find a free port
        port = find_free_port()
        with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
            print(f"🌐 CSRD RAG System Frontend")
            print(f"📍 Serving at: http://localhost:{port}")
            print(f"📁 Directory: {os.getcwd()}")
            print(f"🔗 Open: http://localhost:{port}")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
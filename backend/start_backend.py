#!/usr/bin/env python3
"""
Reliable backend startup script
"""
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def find_free_port():
    """Find a free port"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_backend():
    """Start the backend server"""
    print("🚀 Starting CSRD RAG Backend...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Find free port
    port = find_free_port()
    print(f"📍 Using port: {port}")
    
    # Set environment variables
    env = os.environ.copy()
    env['BACKEND_PORT'] = str(port)
    
    try:
        # Start the backend process
        process = subprocess.Popen([
            sys.executable, 'simple_main.py'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"🔄 Backend process started with PID: {process.pid}")
        print(f"🌐 Backend will be available at: http://localhost:{port}")
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend started successfully!")
            print(f"📊 Process PID: {process.pid}")
            
            # Write PID to file for easy management
            with open('backend.pid', 'w') as f:
                f.write(str(process.pid))
            
            # Write port to file
            with open('backend.port', 'w') as f:
                f.write(str(port))
                
            return process, port
        else:
            stdout, stderr = process.communicate()
            print("❌ Backend failed to start!")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return None, None
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None, None

def stop_backend():
    """Stop the backend if running"""
    pid_file = Path('backend.pid')
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            os.kill(pid, signal.SIGTERM)
            print(f"🛑 Stopped backend process {pid}")
            pid_file.unlink()
            
            port_file = Path('backend.port')
            if port_file.exists():
                port_file.unlink()
                
        except (ProcessLookupError, ValueError):
            print("⚠️ Backend process not found or already stopped")
            pid_file.unlink()
        except Exception as e:
            print(f"❌ Error stopping backend: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CSRD RAG Backend Manager')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'stop':
        stop_backend()
    elif args.action == 'restart':
        stop_backend()
        time.sleep(2)
        start_backend()
    elif args.action == 'status':
        pid_file = Path('backend.pid')
        port_file = Path('backend.port')
        
        if pid_file.exists() and port_file.exists():
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            with open(port_file, 'r') as f:
                port = f.read().strip()
            print(f"📊 Backend running - PID: {pid}, Port: {port}")
            print(f"🌐 URL: http://localhost:{port}")
        else:
            print("❌ Backend not running")
    else:  # start
        stop_backend()  # Stop any existing instance
        process, port = start_backend()
        
        if process and port:
            try:
                # Keep the process running
                print("🔄 Backend running... Press Ctrl+C to stop")
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping backend...")
                process.terminate()
                stop_backend()
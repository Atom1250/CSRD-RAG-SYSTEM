#!/bin/bash

echo "🚀 Starting CSRD RAG System Backend..."

# Kill any existing backend processes
pkill -f "simple_main.py" 2>/dev/null || true

# Wait a moment
sleep 2

# Start backend in background
cd backend
nohup python3 simple_main.py > ../backend.log 2>&1 &
BACKEND_PID=$!

echo "🔄 Backend started with PID: $BACKEND_PID"
echo "📝 Logs available in: backend.log"

# Wait for backend to start
sleep 3

# Find the port by checking the log
if [ -f "../backend.log" ]; then
    PORT=$(grep "Using port:" ../backend.log | tail -1 | awk '{print $NF}')
    if [ ! -z "$PORT" ]; then
        echo "🌐 Backend available at: http://localhost:$PORT"
        echo "📊 Frontend available at: http://localhost:62646"
        echo ""
        echo "To stop the backend: pkill -f simple_main.py"
        echo "To view logs: tail -f backend.log"
    else
        echo "⚠️ Could not determine backend port. Check backend.log for details."
    fi
else
    echo "⚠️ Backend log file not found. Check if backend started correctly."
fi
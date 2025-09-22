#!/bin/bash

case "$1" in
    start)
        echo "🚀 Starting CSRD RAG System..."
        ./start_simple.sh
        ;;
    stop)
        echo "🛑 Stopping CSRD RAG System..."
        pkill -f "simple_main.py" 2>/dev/null || true
        pkill -f "server.py" 2>/dev/null || true
        echo "✅ System stopped"
        ;;
    restart)
        echo "🔄 Restarting CSRD RAG System..."
        $0 stop
        sleep 3
        $0 start
        ;;
    status)
        echo "📊 CSRD RAG System Status:"
        echo ""
        
        # Check backend
        if pgrep -f "simple_main.py" > /dev/null; then
            BACKEND_PID=$(pgrep -f "simple_main.py")
            echo "✅ Backend: Running (PID: $BACKEND_PID)"
            
            # Try to find port from log
            if [ -f "backend.log" ]; then
                PORT=$(grep "Using port:" backend.log | tail -1 | awk '{print $NF}')
                if [ ! -z "$PORT" ]; then
                    echo "   🌐 Backend URL: http://localhost:$PORT"
                fi
            fi
        else
            echo "❌ Backend: Not running"
        fi
        
        # Check frontend
        if pgrep -f "server.py" > /dev/null; then
            FRONTEND_PID=$(pgrep -f "server.py")
            echo "✅ Frontend: Running (PID: $FRONTEND_PID)"
            echo "   🌐 Frontend URL: http://localhost:62646"
        else
            echo "❌ Frontend: Not running"
        fi
        
        # Check Docker services
        echo ""
        echo "🐳 Docker Services:"
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(postgres|redis|chroma)" > /dev/null 2>&1; then
            docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(postgres|redis|chroma)"
        else
            echo "❌ No Docker services running"
        fi
        ;;
    logs)
        echo "📝 Backend Logs:"
        if [ -f "backend.log" ]; then
            tail -f backend.log
        else
            echo "❌ No backend log file found"
        fi
        ;;
    *)
        echo "CSRD RAG System Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the backend and frontend"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show system status"
        echo "  logs    - Show backend logs"
        echo ""
        exit 1
        ;;
esac
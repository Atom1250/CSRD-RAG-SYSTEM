#!/usr/bin/env python3
"""
Celery worker startup script for CSRD RAG System
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables if not already set
if not os.getenv("PYTHONPATH"):
    os.environ["PYTHONPATH"] = str(backend_dir)

from app.core.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.start()
#!/usr/bin/env python3
"""
Minimal test version of main.py to identify hanging issues
"""
import logging
import time
from fastapi import FastAPI
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(
    title="CSRD RAG System Test",
    version="1.0.0",
    debug=True
)

@app.get("/")
async def root():
    return {"message": "Test backend is running", "status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database_url": settings.database_url,
        "redis_url": settings.redis_url,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting minimal test backend...")
    uvicorn.run(
        "test_main:app",
        host="0.0.0.0",
        port=8002,  # Use different port
        reload=False,
        log_level="info"
    )
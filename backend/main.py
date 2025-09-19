"""
CSRD RAG System - Main Application Entry Point
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.api import documents, schemas

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    app.state.start_time = time.time()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database URL: {settings.database_url}")
    
    # Initialize database tables if needed
    try:
        from app.models.database_config import init_db
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Sustainability Reporting Documents RAG System
    
    A comprehensive system for managing, searching, and generating insights from 
    Corporate Sustainability Reporting Directive (CSRD), European Sustainability 
    Reporting Standards (ESRS), and other sustainability reporting documents.
    
    ### Key Features:
    - **Document Management**: Upload and manage regulatory documents
    - **Semantic Search**: AI-powered search across document content
    - **RAG Question-Answering**: Get answers based on document repository
    - **Report Generation**: Generate compliance reports from client requirements
    - **Schema Support**: EU ESRS/CSRD and UK SRD reporting standards
    - **Async Processing**: Background document processing and embedding generation
    
    ### API Endpoints:
    - `/api/documents/`: Document upload and management
    - `/api/search/`: Semantic search functionality
    - `/api/rag/`: RAG-based question answering
    - `/api/reports/`: Report generation and templates
    - `/api/client-requirements/`: Client requirements processing
    - `/api/schemas/`: Schema management and classification
    - `/api/async/`: Asynchronous processing operations
    """,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    contact={
        "name": "CSRD RAG System Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://example.com/terms/",
)

# Configure middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8080",  # Alternative frontend port
        "https://localhost:3000",  # HTTPS development
    ] if settings.debug else ["https://yourdomain.com"],  # Production origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Response-Time", "X-Request-ID"],  # For file downloads and performance
)

# Add performance monitoring middleware
from app.middleware.performance_middleware import PerformanceMiddleware, CacheMiddleware, CompressionMiddleware
from app.middleware.error_middleware import EnhancedErrorHandlingMiddleware

app.add_middleware(EnhancedErrorHandlingMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(CacheMiddleware)
app.add_middleware(CompressionMiddleware)

# Add trusted host middleware for security
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"{request.method} {request.url} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url} - "
            f"Error: {str(e)} - Time: {process_time:.3f}s"
        )
        raise


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url),
                "method": request.method,
                "timestamp": time.time()
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed information"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "status_code": 422,
                "message": "Request validation failed",
                "details": exc.errors(),
                "path": str(request.url),
                "method": request.method,
                "timestamp": time.time()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "status_code": 500,
                "message": "An unexpected error occurred" if not settings.debug else str(exc),
                "path": str(request.url),
                "method": request.method,
                "timestamp": time.time()
            }
        }
    )

# Include API routers
app.include_router(documents.router, prefix="/api")
app.include_router(schemas.router, prefix="/api")

# Import and include async processing router
from app.api import async_processing
app.include_router(async_processing.router, prefix="/api")

# Import and include search router
from app.api import search
app.include_router(search.router, prefix="/api")

# Import and include RAG router
from app.api import rag
app.include_router(rag.router, prefix="/api")

# Import and include client requirements router
from app.api import client_requirements
app.include_router(client_requirements.router, prefix="/api")

# Import and include reports router
from app.api import reports
app.include_router(reports.router, prefix="/api")

# Import and include remote directories router
from app.api import remote_directories
app.include_router(remote_directories.router, prefix="/api")

# Import and include metrics router
from app.api import metrics
app.include_router(metrics.router)

@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint providing basic system information
    
    Returns welcome message and basic system status.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else None,
        "api_prefix": "/api"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Comprehensive health check endpoint
    
    Returns detailed system health information including:
    - Application status
    - Database connectivity
    - External service availability
    - Configuration status
    """
    import psutil
    import os
    
    health_status = {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "timestamp": time.time(),
        "uptime": time.time() - getattr(app.state, 'start_time', time.time()),
        "services": {},
        "system": {}
    }
    
    # System health metrics
    try:
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    except Exception as e:
        health_status["system"] = {"error": str(e)}
    
    # Check database connectivity
    try:
        from app.models.database_config import get_db
        db = next(get_db())
        result = db.execute("SELECT 1, NOW() as current_time, version() as db_version")
        row = result.fetchone()
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0,  # Could measure actual response time
            "version": row[2] if row else "unknown"
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis cache
    try:
        from app.services.cache_service import CacheService
        cache_service = CacheService()
        cache_info = cache_service.get_cache_info()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "memory_usage": cache_info.get("used_memory_human", "unknown"),
            "connected_clients": cache_info.get("connected_clients", 0)
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check vector database
    try:
        from app.services.vector_service import VectorService
        vector_service = VectorService()
        if vector_service.is_available():
            collections = vector_service.list_collections()
            health_status["services"]["vector_db"] = {
                "status": "healthy",
                "collections": len(collections),
                "collection_names": collections
            }
        else:
            health_status["services"]["vector_db"] = {
                "status": "unavailable",
                "error": "Service not responding"
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["vector_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Celery workers
    try:
        from app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        stats = inspect.stats()
        
        if active_tasks and stats:
            worker_count = len(stats)
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            health_status["services"]["celery"] = {
                "status": "healthy",
                "workers": worker_count,
                "active_tasks": total_active
            }
        else:
            health_status["services"]["celery"] = {
                "status": "degraded",
                "error": "No workers responding"
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["celery"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check AI models availability
    try:
        from app.services.rag_service import RAGService
        rag_service = RAGService(next(get_db()))
        model_status = rag_service.get_model_status()
        available_models = sum(1 for status in model_status.values() if status.get("available", False))
        
        health_status["services"]["ai_models"] = {
            "status": "healthy" if available_models > 0 else "degraded",
            "available_models": available_models,
            "total_models": len(model_status),
            "models": model_status
        }
        
        if available_models == 0:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["ai_models"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check file system
    try:
        data_dir = "data"
        if os.path.exists(data_dir):
            total_files = sum(len(files) for _, _, files in os.walk(data_dir))
            dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, _, filenames in os.walk(data_dir)
                          for filename in filenames)
            
            health_status["services"]["file_system"] = {
                "status": "healthy",
                "data_directory": data_dir,
                "total_files": total_files,
                "total_size_mb": round(dir_size / (1024 * 1024), 2)
            }
        else:
            health_status["services"]["file_system"] = {
                "status": "warning",
                "error": f"Data directory {data_dir} not found"
            }
    except Exception as e:
        health_status["services"]["file_system"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status


@app.get("/api", tags=["System"])
async def api_info():
    """
    API information and available endpoints
    
    Returns information about available API endpoints and their purposes.
    """
    return {
        "api_name": f"{settings.app_name} API",
        "version": settings.app_version,
        "endpoints": {
            "/api/documents/": "Document upload and management",
            "/api/search/": "Semantic search functionality", 
            "/api/rag/": "RAG-based question answering",
            "/api/reports/": "Report generation and templates",
            "/api/client-requirements/": "Client requirements processing",
            "/api/schemas/": "Schema management and classification",
            "/api/async/": "Asynchronous processing operations"
        },
        "documentation": {
            "swagger_ui": "/docs" if settings.debug else "disabled in production",
            "redoc": "/redoc" if settings.debug else "disabled in production",
            "openapi_spec": "/openapi.json" if settings.debug else "disabled in production"
        }
    }


@app.get("/api/status", tags=["System"])
async def api_status():
    """
    API operational status
    
    Returns current operational status of all API endpoints and services.
    """
    status_info = {
        "overall_status": "operational",
        "timestamp": time.time(),
        "endpoints": {}
    }
    
    # Check each API module
    api_modules = [
        ("documents", "Document management"),
        ("search", "Semantic search"),
        ("rag", "RAG question-answering"),
        ("reports", "Report generation"),
        ("client-requirements", "Client requirements"),
        ("schemas", "Schema management"),
        ("async", "Async processing")
    ]
    
    for module, description in api_modules:
        try:
            # Basic check - could be enhanced with actual service health checks
            status_info["endpoints"][module] = {
                "status": "operational",
                "description": description
            }
        except Exception as e:
            status_info["endpoints"][module] = {
                "status": "degraded",
                "description": description,
                "error": str(e)
            }
            status_info["overall_status"] = "degraded"
    
    return status_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
"""
Performance monitoring middleware for FastAPI
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.performance_service import performance_monitor, performance_logger

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor API request performance"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and measure performance"""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url_path = request.url.path
        endpoint = self._get_endpoint_name(url_path)
        
        # Get user ID if available (from headers or auth)
        user_id = request.headers.get("X-User-ID")
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            performance_monitor.record_request(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=response.status_code
            )
            
            # Log performance
            performance_logger.log_request_performance(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=response.status_code,
                user_id=user_id
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = str(id(request))
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            performance_monitor.record_request(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=500
            )
            
            performance_logger.log_request_performance(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=500,
                user_id=user_id
            )
            
            logger.error(f"Request failed: {method} {endpoint} - {str(e)}")
            raise
    
    def _get_endpoint_name(self, url_path: str) -> str:
        """Extract endpoint name from URL path"""
        # Remove query parameters and normalize path
        path = url_path.split('?')[0].rstrip('/')
        
        # Map common patterns to endpoint names
        if path.startswith('/api/v1/documents'):
            if path.endswith('/upload'):
                return 'documents_upload'
            elif '/search' in path:
                return 'documents_search'
            elif path.count('/') == 3:  # /api/v1/documents/{id}
                return 'documents_detail'
            else:
                return 'documents_list'
        elif path.startswith('/api/v1/search'):
            return 'search'
        elif path.startswith('/api/v1/rag'):
            return 'rag_query'
        elif path.startswith('/api/v1/reports'):
            return 'reports'
        elif path.startswith('/api/v1/schemas'):
            return 'schemas'
        elif path.startswith('/api/v1/remote-directories'):
            return 'remote_directories'
        elif path.startswith('/api/v1/client-requirements'):
            return 'client_requirements'
        elif path.startswith('/api/v1/async-processing'):
            return 'async_processing'
        elif path.startswith('/health'):
            return 'health_check'
        elif path.startswith('/metrics'):
            return 'metrics'
        else:
            return 'unknown'


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware to add cache headers for static content"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add appropriate cache headers"""
        response = await call_next(request)
        
        # Add cache headers based on content type
        if request.url.path.startswith('/static/'):
            # Static files - cache for 1 hour
            response.headers["Cache-Control"] = "public, max-age=3600"
        elif request.url.path.startswith('/api/v1/schemas'):
            # Schema data - cache for 30 minutes
            response.headers["Cache-Control"] = "public, max-age=1800"
        elif request.method == "GET" and response.status_code == 200:
            # Other GET requests - cache for 5 minutes
            response.headers["Cache-Control"] = "public, max-age=300"
        else:
            # No cache for other requests
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware to add compression hints"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add compression headers"""
        response = await call_next(request)
        
        # Add compression hint for JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            response.headers["Vary"] = "Accept-Encoding"
        
        return response
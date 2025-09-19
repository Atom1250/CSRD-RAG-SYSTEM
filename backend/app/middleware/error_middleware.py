"""
Enhanced error handling middleware for comprehensive error management
"""
import logging
import traceback
import time
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ErrorDetail:
    """Structured error detail for consistent error responses"""
    
    def __init__(
        self,
        error_type: str,
        status_code: int,
        message: str,
        details: Optional[Any] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[float] = None
    ):
        self.error_type = error_type
        self.status_code = status_code
        self.message = message
        self.details = details
        self.path = path
        self.method = method
        self.request_id = request_id
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error detail to dictionary for JSON response"""
        result = {
            "type": self.error_type,
            "status_code": self.status_code,
            "message": self.message,
            "timestamp": self.timestamp
        }
        
        if self.details is not None:
            result["details"] = self.details
        if self.path:
            result["path"] = self.path
        if self.method:
            result["method"] = self.method
        if self.request_id:
            result["request_id"] = self.request_id
            
        return result


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle any errors"""
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        start_time = time.time()
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Log the error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url} - "
                f"Error: {str(exc)} - Time: {process_time:.3f}s - "
                f"Request ID: {request_id}",
                exc_info=True
            )
            
            # Handle the error and return appropriate response
            error_detail = self._handle_exception(exc, request, request_id)
            return JSONResponse(
                status_code=error_detail.status_code,
                content={"error": error_detail.to_dict()}
            )
    
    def _handle_exception(self, exc: Exception, request: Request, request_id: str) -> ErrorDetail:
        """Handle different types of exceptions and return appropriate error details"""
        
        # HTTP Exceptions
        if isinstance(exc, (HTTPException, StarletteHTTPException)):
            return ErrorDetail(
                error_type="HTTPException",
                status_code=exc.status_code,
                message=exc.detail,
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        # Validation Errors
        if isinstance(exc, RequestValidationError):
            return ErrorDetail(
                error_type="ValidationError",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Request validation failed",
                details=exc.errors(),
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        if isinstance(exc, ValidationError):
            return ErrorDetail(
                error_type="ValidationError",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Data validation failed",
                details=exc.errors(),
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        # Database Errors
        if isinstance(exc, IntegrityError):
            return ErrorDetail(
                error_type="DatabaseIntegrityError",
                status_code=status.HTTP_409_CONFLICT,
                message="Database constraint violation",
                details=str(exc.orig) if hasattr(exc, 'orig') else str(exc),
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        if isinstance(exc, SQLAlchemyError):
            return ErrorDetail(
                error_type="DatabaseError",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database operation failed",
                details=str(exc) if logger.level <= logging.DEBUG else None,
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        # File-related errors
        if isinstance(exc, FileNotFoundError):
            return ErrorDetail(
                error_type="FileNotFoundError",
                status_code=status.HTTP_404_NOT_FOUND,
                message="Requested file not found",
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        if isinstance(exc, PermissionError):
            return ErrorDetail(
                error_type="PermissionError",
                status_code=status.HTTP_403_FORBIDDEN,
                message="Insufficient permissions to access resource",
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        # Timeout errors
        if isinstance(exc, TimeoutError):
            return ErrorDetail(
                error_type="TimeoutError",
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                message="Request timeout",
                path=str(request.url),
                method=request.method,
                request_id=request_id
            )
        
        # Generic exception
        return ErrorDetail(
            error_type="InternalServerError",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            details=str(exc) if logger.level <= logging.DEBUG else None,
            path=str(request.url),
            method=request.method,
            request_id=request_id
        )


# Custom exception classes for specific error scenarios
class DocumentProcessingError(Exception):
    """Raised when document processing fails"""
    pass


class VectorDatabaseError(Exception):
    """Raised when vector database operations fail"""
    pass


class AIModelError(Exception):
    """Raised when AI model operations fail"""
    pass


class SchemaValidationError(Exception):
    """Raised when schema validation fails"""
    pass


class RemoteDirectoryError(Exception):
    """Raised when remote directory operations fail"""
    pass


# Error handler functions for specific exception types
def handle_document_processing_error(exc: DocumentProcessingError, request: Request, request_id: str) -> ErrorDetail:
    """Handle document processing errors"""
    return ErrorDetail(
        error_type="DocumentProcessingError",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=f"Document processing failed: {str(exc)}",
        path=str(request.url),
        method=request.method,
        request_id=request_id
    )


def handle_vector_database_error(exc: VectorDatabaseError, request: Request, request_id: str) -> ErrorDetail:
    """Handle vector database errors"""
    return ErrorDetail(
        error_type="VectorDatabaseError",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message=f"Vector database operation failed: {str(exc)}",
        path=str(request.url),
        method=request.method,
        request_id=request_id
    )


def handle_ai_model_error(exc: AIModelError, request: Request, request_id: str) -> ErrorDetail:
    """Handle AI model errors"""
    return ErrorDetail(
        error_type="AIModelError",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message=f"AI model operation failed: {str(exc)}",
        path=str(request.url),
        method=request.method,
        request_id=request_id
    )


def handle_schema_validation_error(exc: SchemaValidationError, request: Request, request_id: str) -> ErrorDetail:
    """Handle schema validation errors"""
    return ErrorDetail(
        error_type="SchemaValidationError",
        status_code=status.HTTP_400_BAD_REQUEST,
        message=f"Schema validation failed: {str(exc)}",
        path=str(request.url),
        method=request.method,
        request_id=request_id
    )


def handle_remote_directory_error(exc: RemoteDirectoryError, request: Request, request_id: str) -> ErrorDetail:
    """Handle remote directory errors"""
    return ErrorDetail(
        error_type="RemoteDirectoryError",
        status_code=status.HTTP_502_BAD_GATEWAY,
        message=f"Remote directory operation failed: {str(exc)}",
        path=str(request.url),
        method=request.method,
        request_id=request_id
    )


# Enhanced error handling middleware with custom exception handlers
class EnhancedErrorHandlingMiddleware(ErrorHandlingMiddleware):
    """Enhanced error handling middleware with custom exception handlers"""
    
    def __init__(self, app):
        super().__init__(app)
        self.custom_handlers = {
            DocumentProcessingError: handle_document_processing_error,
            VectorDatabaseError: handle_vector_database_error,
            AIModelError: handle_ai_model_error,
            SchemaValidationError: handle_schema_validation_error,
            RemoteDirectoryError: handle_remote_directory_error,
        }
    
    def _handle_exception(self, exc: Exception, request: Request, request_id: str) -> ErrorDetail:
        """Handle exceptions with custom handlers"""
        
        # Check for custom handlers first
        for exc_type, handler in self.custom_handlers.items():
            if isinstance(exc, exc_type):
                return handler(exc, request, request_id)
        
        # Fall back to parent implementation
        return super()._handle_exception(exc, request, request_id)


# Utility functions for error handling
def create_error_response(
    status_code: int,
    message: str,
    error_type: str = "Error",
    details: Optional[Any] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """Create a standardized error response"""
    
    error_detail = ErrorDetail(
        error_type=error_type,
        status_code=status_code,
        message=message,
        details=details,
        path=str(request.url) if request else None,
        method=request.method if request else None,
        request_id=request.headers.get("X-Request-ID") if request else None
    )
    
    return JSONResponse(
        status_code=status_code,
        content={"error": error_detail.to_dict()}
    )


def log_error(
    exc: Exception,
    request: Optional[Request] = None,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Log error with context information"""
    
    context = {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
    }
    
    if request:
        context.update({
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "request_id": request.headers.get("X-Request-ID"),
        })
    
    if additional_context:
        context.update(additional_context)
    
    logger.error("Error occurred", extra=context, exc_info=True)
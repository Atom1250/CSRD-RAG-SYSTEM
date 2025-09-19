"""
Performance monitoring and logging service
"""
import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from app.services.cache_service import cache_service
from app.core.config import settings

# Optional psutil import for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring and metrics collection service"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record API request metrics"""
        self.request_count += 1
        
        # Record in cache for aggregation
        cache_service.increment_counter(f"requests_total")
        cache_service.increment_counter(f"requests_{endpoint}_{method}")
        
        if status_code >= 400:
            self.error_count += 1
            cache_service.increment_counter(f"errors_total")
            cache_service.increment_counter(f"errors_{endpoint}_{method}")
        
        # Record response time
        cache_service.set_gauge(f"response_time_{endpoint}_{method}", duration)
        
        # Log slow requests
        if duration > 5.0:  # Log requests taking more than 5 seconds
            logger.warning(f"Slow request: {method} {endpoint} took {duration:.2f}s")
    
    def record_operation(self, operation: str, duration: float, success: bool = True):
        """Record internal operation metrics"""
        cache_service.increment_counter(f"operations_{operation}")
        cache_service.set_gauge(f"operation_time_{operation}", duration)
        
        if not success:
            cache_service.increment_counter(f"operation_errors_{operation}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            base_metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
                "psutil_available": PSUTIL_AVAILABLE
            }
            
            if PSUTIL_AVAILABLE:
                # CPU and memory usage
                cpu_percent = psutil.cpu_percent(interval=0.1)  # Shorter interval for tests
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Process-specific metrics
                process = psutil.Process()
                process_memory = process.memory_info()
                
                base_metrics.update({
                    "cpu_percent": cpu_percent,
                    "memory_total_gb": memory.total / (1024**3),
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_percent": memory.percent,
                    "disk_total_gb": disk.total / (1024**3),
                    "disk_used_gb": disk.used / (1024**3),
                    "disk_percent": (disk.used / disk.total) * 100,
                    "process_memory_mb": process_memory.rss / (1024**2),
                    "process_cpu_percent": process.cpu_percent(),
                })
            else:
                # Fallback metrics when psutil is not available
                base_metrics.update({
                    "cpu_percent": 0.0,
                    "memory_total_gb": 0.0,
                    "memory_used_gb": 0.0,
                    "memory_percent": 0.0,
                    "disk_total_gb": 0.0,
                    "disk_used_gb": 0.0,
                    "disk_percent": 0.0,
                    "process_memory_mb": 0.0,
                    "process_cpu_percent": 0.0,
                })
            
            return base_metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e), "psutil_available": PSUTIL_AVAILABLE}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific performance metrics"""
        try:
            # Get cached metrics
            cached_metrics = cache_service.get_metrics()
            
            # Calculate derived metrics
            total_requests = cached_metrics.get("metrics:counter:requests_total", 0)
            total_errors = cached_metrics.get("metrics:counter:errors_total", 0)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate_percent": (total_errors / max(total_requests, 1)) * 100,
                "cache_metrics": cached_metrics,
                "uptime_seconds": time.time() - self.start_time
            }
        except Exception as e:
            logger.error(f"Failed to get application metrics: {e}")
            return {"error": str(e)}
    
    @contextmanager
    def measure_operation(self, operation_name: str):
        """Context manager to measure operation duration"""
        start_time = time.time()
        success = True
        try:
            yield
        except Exception as e:
            success = False
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self.record_operation(operation_name, duration, success)
    
    @asynccontextmanager
    async def measure_async_operation(self, operation_name: str):
        """Async context manager to measure operation duration"""
        start_time = time.time()
        success = True
        try:
            yield
        except Exception as e:
            success = False
            logger.error(f"Async operation {operation_name} failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self.record_operation(operation_name, duration, success)


def performance_timer(operation_name: str):
    """Decorator to measure function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with performance_monitor.measure_operation(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def async_performance_timer(operation_name: str):
    """Decorator to measure async function execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with performance_monitor.measure_async_operation(operation_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


class DatabaseConnectionPool:
    """Database connection pool manager for performance optimization"""
    
    def __init__(self):
        """Initialize connection pool settings"""
        self.pool_size = 20
        self.max_overflow = 30
        self.pool_timeout = 30
        self.pool_recycle = 3600  # 1 hour
        
    def get_engine_config(self) -> Dict[str, Any]:
        """Get optimized database engine configuration"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,  # Validate connections before use
            "echo": settings.database_echo,
            "future": True
        }
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get optimized session configuration"""
        return {
            "expire_on_commit": False,
            "autoflush": True,
            "autocommit": False
        }


class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def get_pagination_params(page: int = 1, size: int = 20) -> Dict[str, int]:
        """Get optimized pagination parameters"""
        # Limit page size to prevent memory issues
        max_size = 100
        size = min(size, max_size)
        offset = (page - 1) * size
        
        return {
            "limit": size,
            "offset": offset
        }
    
    @staticmethod
    def get_search_optimization_hints() -> Dict[str, Any]:
        """Get database-specific optimization hints for search queries"""
        return {
            "use_index": True,
            "force_index_scan": False,
            "parallel_workers": 2
        }


class PerformanceLogger:
    """Structured performance logging"""
    
    def __init__(self):
        """Initialize performance logger"""
        self.logger = logging.getLogger("performance")
        
        # Configure performance-specific logger
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_request_performance(self, endpoint: str, method: str, duration: float, 
                              status_code: int, user_id: Optional[str] = None):
        """Log API request performance"""
        self.logger.info(
            f"REQUEST_PERFORMANCE endpoint={endpoint} method={method} "
            f"duration={duration:.3f}s status={status_code} user_id={user_id}"
        )
    
    def log_operation_performance(self, operation: str, duration: float, 
                                success: bool, details: Optional[Dict] = None):
        """Log internal operation performance"""
        status = "SUCCESS" if success else "FAILURE"
        details_str = f" details={details}" if details else ""
        
        self.logger.info(
            f"OPERATION_PERFORMANCE operation={operation} duration={duration:.3f}s "
            f"status={status}{details_str}"
        )
    
    def log_cache_performance(self, operation: str, hit: bool, key: str, duration: float):
        """Log cache operation performance"""
        hit_status = "HIT" if hit else "MISS"
        self.logger.info(
            f"CACHE_PERFORMANCE operation={operation} status={hit_status} "
            f"key={key} duration={duration:.3f}s"
        )
    
    def log_system_alert(self, metric: str, value: float, threshold: float, severity: str = "WARNING"):
        """Log system performance alerts"""
        self.logger.warning(
            f"SYSTEM_ALERT metric={metric} value={value} threshold={threshold} "
            f"severity={severity}"
        )


# Global instances
performance_monitor = PerformanceMonitor()
db_pool = DatabaseConnectionPool()
query_optimizer = QueryOptimizer()
performance_logger = PerformanceLogger()
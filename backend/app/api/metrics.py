"""
API endpoints for performance metrics and monitoring
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models.database_config import get_db
from app.services.performance_service import performance_monitor
from app.services.cache_service import cache_service
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

# Global monitoring service instance
monitoring_service = MonitoringService()


@router.get("/health", response_model=Dict[str, Any])
async def get_health_status():
    """Get comprehensive system health status"""
    try:
        # Use the enhanced monitoring service
        health_report = monitoring_service.get_system_health()
        return health_report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/simple", response_model=Dict[str, Any])
async def get_simple_health_status():
    """Get simplified health status (legacy endpoint)"""
    try:
        # Check cache service health
        cache_health = cache_service.health_check()
        
        # Get basic system metrics
        system_metrics = performance_monitor.get_system_metrics()
        
        # Determine overall health
        overall_status = "healthy"
        if cache_health.get("status") != "healthy":
            overall_status = "degraded"
        
        if system_metrics.get("error"):
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": system_metrics.get("timestamp"),
            "cache_service": cache_health,
            "system": {
                "uptime_seconds": system_metrics.get("uptime_seconds"),
                "cpu_percent": system_metrics.get("cpu_percent"),
                "memory_percent": system_metrics.get("memory_percent"),
                "error_rate": system_metrics.get("error_rate", 0)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/system", response_model=Dict[str, Any])
async def get_system_metrics():
    """Get detailed system performance metrics"""
    try:
        return performance_monitor.get_system_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/application", response_model=Dict[str, Any])
async def get_application_metrics():
    """Get application-specific performance metrics"""
    try:
        return performance_monitor.get_application_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application metrics: {str(e)}"
        )


@router.get("/cache", response_model=Dict[str, Any])
async def get_cache_metrics():
    """Get cache performance metrics"""
    try:
        cache_health = cache_service.health_check()
        cache_metrics = cache_service.get_metrics("metrics:*")
        
        return {
            "health": cache_health,
            "metrics": cache_metrics,
            "cache_operations": {
                key: value for key, value in cache_metrics.items()
                if "cache" in key.lower()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache metrics: {str(e)}"
        )


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_summary():
    """Get comprehensive performance summary"""
    try:
        system_metrics = performance_monitor.get_system_metrics()
        app_metrics = performance_monitor.get_application_metrics()
        cache_health = cache_service.health_check()
        
        # Calculate performance indicators
        performance_indicators = {
            "response_time_status": "good" if system_metrics.get("cpu_percent", 0) < 80 else "warning",
            "memory_status": "good" if system_metrics.get("memory_percent", 0) < 85 else "warning",
            "error_rate_status": "good" if system_metrics.get("error_rate", 0) < 5 else "warning",
            "cache_status": cache_health.get("status", "unknown")
        }
        
        return {
            "timestamp": system_metrics.get("timestamp"),
            "overall_status": "healthy" if all(
                status in ["good", "healthy"] for status in performance_indicators.values()
            ) else "warning",
            "indicators": performance_indicators,
            "summary": {
                "uptime_seconds": system_metrics.get("uptime_seconds", 0),
                "total_requests": app_metrics.get("total_requests", 0),
                "error_rate_percent": app_metrics.get("error_rate_percent", 0),
                "cpu_percent": system_metrics.get("cpu_percent", 0),
                "memory_percent": system_metrics.get("memory_percent", 0),
                "cache_connected": cache_health.get("status") == "healthy"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance summary: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache_pattern(pattern: str = "*"):
    """Clear cache entries matching pattern"""
    try:
        if not pattern or pattern == "*":
            # Don't allow clearing all cache without explicit confirmation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use specific pattern or 'all' to clear entire cache"
            )
        
        if pattern == "all":
            pattern = "*"
        
        cleared_count = cache_service.clear_pattern(pattern)
        
        return {
            "message": f"Cleared {cleared_count} cache entries",
            "pattern": pattern,
            "cleared_count": cleared_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/database", response_model=Dict[str, Any])
async def get_database_metrics(db: Session = Depends(get_db)):
    """Get database performance metrics"""
    try:
        from sqlalchemy import text
        
        # Get database connection info
        db_info = {}
        
        # Try to get database-specific metrics
        try:
            # For PostgreSQL
            result = db.execute(text("SELECT version()"))
            version = result.scalar()
            db_info["version"] = version
            
            # Get connection count (PostgreSQL specific)
            result = db.execute(text("""
                SELECT count(*) as active_connections 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """))
            db_info["active_connections"] = result.scalar()
            
        except Exception:
            # For SQLite or other databases
            db_info["version"] = "SQLite (development)"
            db_info["active_connections"] = 1
        
        # Get table sizes and counts
        from app.models.database import Document, TextChunk
        
        document_count = db.query(Document).count()
        chunk_count = db.query(TextChunk).count()
        
        return {
            "database_info": db_info,
            "table_counts": {
                "documents": document_count,
                "text_chunks": chunk_count
            },
            "performance": {
                "connection_pool_size": 20,  # From configuration
                "max_overflow": 30
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database metrics: {str(e)}"
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_metrics_history(
    hours: int = Query(24, ge=1, le=168, description="Number of hours of history to retrieve")
):
    """Get historical metrics data"""
    try:
        history = monitoring_service.get_metrics_history(hours=hours)
        
        return {
            "timestamp": performance_monitor.get_system_metrics().get("timestamp"),
            "hours_requested": hours,
            "data_points": len(history),
            "metrics": history
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics history: {str(e)}"
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_current_alerts():
    """Get current system alerts and warnings"""
    try:
        health_report = monitoring_service.get_system_health()
        alerts = health_report.get("alerts", [])
        
        # Categorize alerts by level
        categorized_alerts = {
            "critical": [a for a in alerts if a.get("level") == "critical"],
            "warning": [a for a in alerts if a.get("level") == "warning"],
            "info": [a for a in alerts if a.get("level") == "info"]
        }
        
        return {
            "timestamp": performance_monitor.get_system_metrics().get("timestamp"),
            "total_alerts": len(alerts),
            "alerts": categorized_alerts,
            "overall_status": health_report.get("overall_status", "unknown")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get("/services/{service_name}", response_model=Dict[str, Any])
async def get_service_metrics(service_name: str):
    """Get detailed metrics for a specific service"""
    try:
        health_report = monitoring_service.get_system_health()
        services = health_report.get("services", {})
        
        if service_name not in services:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_name}' not found"
            )
        
        service_data = services[service_name]
        
        # Add uptime information
        uptime_data = monitoring_service.get_service_uptime(service_name)
        service_data.update(uptime_data)
        
        return {
            "timestamp": performance_monitor.get_system_metrics().get("timestamp"),
            "service": service_name,
            "data": service_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service metrics: {str(e)}"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_metrics_summary():
    """Get a summary of key system metrics and status"""
    try:
        health_report = monitoring_service.get_system_health()
        system_metrics = health_report.get("system_metrics", {})
        
        # Count services by status
        services = health_report.get("services", {})
        service_status_counts = {}
        for service_data in services.values():
            status = service_data.get("status", "unknown")
            service_status_counts[status] = service_status_counts.get(status, 0) + 1
        
        # Count alerts by level
        alerts = health_report.get("alerts", [])
        alert_counts = {}
        for alert in alerts:
            level = alert.get("level", "unknown")
            alert_counts[level] = alert_counts.get(level, 0) + 1
        
        return {
            "timestamp": performance_monitor.get_system_metrics().get("timestamp"),
            "overall_status": health_report.get("overall_status", "unknown"),
            "system_summary": {
                "cpu_percent": system_metrics.get("cpu", {}).get("percent", 0),
                "memory_percent": system_metrics.get("memory", {}).get("percent", 0),
                "disk_percent": system_metrics.get("disk", {}).get("percent", 0)
            },
            "services_summary": {
                "total_services": len(services),
                "status_counts": service_status_counts
            },
            "alerts_summary": {
                "total_alerts": len(alerts),
                "alert_counts": alert_counts
            },
            "uptime_seconds": health_report.get("uptime", 0)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics summary: {str(e)}"
        )
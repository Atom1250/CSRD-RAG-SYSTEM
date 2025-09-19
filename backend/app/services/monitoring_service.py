"""
Monitoring Service for CSRD RAG System

Provides comprehensive monitoring capabilities including:
- System health checks
- Performance metrics
- Service availability monitoring
- Alert generation
"""

import time
import psutil
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    last_check: Optional[datetime] = None


@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: Optional[List[float]]
    network_io: Optional[Dict[str, int]]
    disk_io: Optional[Dict[str, int]]


class MonitoringService:
    """Comprehensive monitoring service for system health and performance"""
    
    def __init__(self):
        self.service_checks = {}
        self.metrics_history = []
        self.max_history_size = 1000
        
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        start_time = time.time()
        
        health_report = {
            "overall_status": HealthStatus.HEALTHY.value,
            "timestamp": datetime.utcnow().isoformat(),
            "check_duration_ms": 0,
            "services": {},
            "system_metrics": self._get_system_metrics(),
            "alerts": []
        }
        
        # Check all services
        services_to_check = [
            ("database", self._check_database),
            ("redis", self._check_redis),
            ("vector_db", self._check_vector_db),
            ("celery", self._check_celery),
            ("ai_models", self._check_ai_models),
            ("file_system", self._check_file_system)
        ]
        
        degraded_services = 0
        unhealthy_services = 0
        
        for service_name, check_function in services_to_check:
            try:
                service_health = check_function()
                health_report["services"][service_name] = service_health.__dict__
                
                if service_health.status == HealthStatus.DEGRADED:
                    degraded_services += 1
                elif service_health.status == HealthStatus.UNHEALTHY:
                    unhealthy_services += 1
                    
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_report["services"][service_name] = {
                    "name": service_name,
                    "status": HealthStatus.UNHEALTHY.value,
                    "error_message": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
                unhealthy_services += 1
        
        # Determine overall status
        if unhealthy_services > 0:
            health_report["overall_status"] = HealthStatus.UNHEALTHY.value
        elif degraded_services > 0:
            health_report["overall_status"] = HealthStatus.DEGRADED.value
        
        # Generate alerts
        health_report["alerts"] = self._generate_alerts(health_report)
        
        health_report["check_duration_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return health_report
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Load average (Unix systems)
            load_avg = None
            if hasattr(os, 'getloadavg'):
                load_avg = list(os.getloadavg())
            
            # Network I/O
            network_io = psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
            
            metrics = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": load_avg
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent": memory.percent,
                    "used_gb": round(memory.used / (1024**3), 2)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": round((disk.used / disk.total) * 100, 2),
                    "used_gb": round(disk.used / (1024**3), 2)
                },
                "network_io": network_io,
                "disk_io": disk_io
            }
            
            # Store metrics in history
            system_metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=metrics["disk"]["percent"],
                load_average=load_avg,
                network_io=network_io,
                disk_io=disk_io
            )
            
            self._store_metrics(system_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    def _check_database(self) -> ServiceHealth:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            from app.models.database_config import get_db
            
            db = next(get_db())
            result = db.execute("SELECT 1, NOW() as current_time, version() as db_version")
            row = result.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check for slow queries (>100ms is concerning)
            status = HealthStatus.HEALTHY
            if response_time > 500:
                status = HealthStatus.DEGRADED
            elif response_time > 1000:
                status = HealthStatus.UNHEALTHY
            
            return ServiceHealth(
                name="database",
                status=status,
                response_time_ms=round(response_time, 2),
                metadata={
                    "version": row[2] if row else "unknown",
                    "current_time": str(row[1]) if row else None
                },
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            return ServiceHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e),
                last_check=datetime.utcnow()
            )
    
    def _check_redis(self) -> ServiceHealth:
        """Check Redis cache connectivity and performance"""
        start_time = time.time()
        
        try:
            from app.services.cache_service import CacheService
            
            cache_service = CacheService()
            cache_info = cache_service.get_cache_info()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check Redis memory usage
            memory_usage = cache_info.get("used_memory", 0)
            max_memory = cache_info.get("maxmemory", 0)
            
            status = HealthStatus.HEALTHY
            if max_memory > 0 and (memory_usage / max_memory) > 0.9:
                status = HealthStatus.DEGRADED
            
            return ServiceHealth(
                name="redis",
                status=status,
                response_time_ms=round(response_time, 2),
                metadata={
                    "memory_usage": cache_info.get("used_memory_human", "unknown"),
                    "connected_clients": cache_info.get("connected_clients", 0),
                    "total_commands_processed": cache_info.get("total_commands_processed", 0)
                },
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            return ServiceHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e),
                last_check=datetime.utcnow()
            )
    
    def _check_vector_db(self) -> ServiceHealth:
        """Check vector database connectivity and performance"""
        start_time = time.time()
        
        try:
            from app.services.vector_service import VectorService
            
            vector_service = VectorService()
            
            if not vector_service.is_available():
                return ServiceHealth(
                    name="vector_db",
                    status=HealthStatus.UNHEALTHY,
                    error_message="Vector database not available",
                    last_check=datetime.utcnow()
                )
            
            collections = vector_service.list_collections()
            response_time = (time.time() - start_time) * 1000
            
            # Check response time
            status = HealthStatus.HEALTHY
            if response_time > 1000:
                status = HealthStatus.DEGRADED
            elif response_time > 5000:
                status = HealthStatus.UNHEALTHY
            
            return ServiceHealth(
                name="vector_db",
                status=status,
                response_time_ms=round(response_time, 2),
                metadata={
                    "collections": len(collections),
                    "collection_names": collections
                },
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            return ServiceHealth(
                name="vector_db",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e),
                last_check=datetime.utcnow()
            )
    
    def _check_celery(self) -> ServiceHealth:
        """Check Celery workers status"""
        try:
            from app.core.celery_app import celery_app
            
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            stats = inspect.stats()
            
            if not active_tasks or not stats:
                return ServiceHealth(
                    name="celery",
                    status=HealthStatus.DEGRADED,
                    error_message="No workers responding",
                    last_check=datetime.utcnow()
                )
            
            worker_count = len(stats)
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            
            # Check for overloaded workers
            status = HealthStatus.HEALTHY
            if total_active > worker_count * 10:  # More than 10 tasks per worker
                status = HealthStatus.DEGRADED
            
            return ServiceHealth(
                name="celery",
                status=status,
                metadata={
                    "workers": worker_count,
                    "active_tasks": total_active,
                    "worker_stats": stats
                },
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            return ServiceHealth(
                name="celery",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e),
                last_check=datetime.utcnow()
            )
    
    def _check_ai_models(self) -> ServiceHealth:
        """Check AI models availability"""
        try:
            from app.services.rag_service import RAGService
            from app.models.database_config import get_db
            
            rag_service = RAGService(next(get_db()))
            model_status = rag_service.get_model_status()
            
            available_models = sum(1 for status in model_status.values() 
                                 if status.get("available", False))
            total_models = len(model_status)
            
            if available_models == 0:
                status = HealthStatus.UNHEALTHY
            elif available_models < total_models:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return ServiceHealth(
                name="ai_models",
                status=status,
                metadata={
                    "available_models": available_models,
                    "total_models": total_models,
                    "models": model_status
                },
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            return ServiceHealth(
                name="ai_models",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e),
                last_check=datetime.utcnow()
            )
    
    def _check_file_system(self) -> ServiceHealth:
        """Check file system health"""
        try:
            data_dir = "data"
            
            if not os.path.exists(data_dir):
                return ServiceHealth(
                    name="file_system",
                    status=HealthStatus.DEGRADED,
                    error_message=f"Data directory {data_dir} not found",
                    last_check=datetime.utcnow()
                )
            
            # Count files and calculate size
            total_files = 0
            total_size = 0
            
            for dirpath, _, filenames in os.walk(data_dir):
                total_files += len(filenames)
                for filename in filenames:
                    try:
                        file_path = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue
            
            # Check disk space
            disk_usage = psutil.disk_usage(data_dir)
            free_space_gb = disk_usage.free / (1024**3)
            
            status = HealthStatus.HEALTHY
            if free_space_gb < 1:  # Less than 1GB free
                status = HealthStatus.UNHEALTHY
            elif free_space_gb < 5:  # Less than 5GB free
                status = HealthStatus.DEGRADED
            
            return ServiceHealth(
                name="file_system",
                status=status,
                metadata={
                    "data_directory": data_dir,
                    "total_files": total_files,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "free_space_gb": round(free_space_gb, 2)
                },
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            return ServiceHealth(
                name="file_system",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e),
                last_check=datetime.utcnow()
            )
    
    def _generate_alerts(self, health_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on health report"""
        alerts = []
        
        # System resource alerts
        system_metrics = health_report.get("system_metrics", {})
        
        # CPU alert
        cpu_percent = system_metrics.get("cpu", {}).get("percent", 0)
        if cpu_percent > 90:
            alerts.append({
                "level": "critical",
                "message": f"High CPU usage: {cpu_percent}%",
                "service": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif cpu_percent > 80:
            alerts.append({
                "level": "warning",
                "message": f"Elevated CPU usage: {cpu_percent}%",
                "service": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Memory alert
        memory_percent = system_metrics.get("memory", {}).get("percent", 0)
        if memory_percent > 90:
            alerts.append({
                "level": "critical",
                "message": f"High memory usage: {memory_percent}%",
                "service": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif memory_percent > 80:
            alerts.append({
                "level": "warning",
                "message": f"Elevated memory usage: {memory_percent}%",
                "service": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Disk alert
        disk_percent = system_metrics.get("disk", {}).get("percent", 0)
        if disk_percent > 95:
            alerts.append({
                "level": "critical",
                "message": f"Very low disk space: {disk_percent}% used",
                "service": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif disk_percent > 85:
            alerts.append({
                "level": "warning",
                "message": f"Low disk space: {disk_percent}% used",
                "service": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Service alerts
        for service_name, service_data in health_report.get("services", {}).items():
            status = service_data.get("status")
            
            if status == HealthStatus.UNHEALTHY.value:
                alerts.append({
                    "level": "critical",
                    "message": f"Service {service_name} is unhealthy: {service_data.get('error_message', 'Unknown error')}",
                    "service": service_name,
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif status == HealthStatus.DEGRADED.value:
                alerts.append({
                    "level": "warning",
                    "message": f"Service {service_name} is degraded",
                    "service": service_name,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Response time alerts
            response_time = service_data.get("response_time_ms", 0)
            if response_time > 5000:
                alerts.append({
                    "level": "warning",
                    "message": f"Slow response from {service_name}: {response_time}ms",
                    "service": service_name,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in history"""
        self.metrics_history.append(metrics)
        
        # Keep only recent metrics
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for the specified number of hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "disk_percent": m.disk_percent,
                "load_average": m.load_average
            }
            for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        return recent_metrics
    
    def get_service_uptime(self, service_name: str) -> Dict[str, Any]:
        """Get uptime statistics for a specific service"""
        # This would require persistent storage of health check results
        # For now, return basic information
        return {
            "service": service_name,
            "uptime_percent": 99.9,  # Placeholder
            "last_downtime": None,
            "total_checks": 0,
            "failed_checks": 0
        }
"""
Celery tasks for remote directory synchronization
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from celery import Celery
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.models.database_config import get_db
from app.services.remote_directory_service import RemoteDirectoryService
from app.core.config import settings


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="sync_remote_directory")
def sync_remote_directory_task(self, config_id: str) -> Dict[str, Any]:
    """
    Celery task to synchronize a specific remote directory
    
    Args:
        config_id: Remote directory configuration ID
        
    Returns:
        Dict containing sync results
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Create service instance
        service = RemoteDirectoryService(db)
        
        # Perform synchronization
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            sync_result = loop.run_until_complete(
                service.sync_remote_directory(config_id)
            )
            
            logger.info(f"Remote directory sync completed for config {config_id}")
            
            return {
                "status": "success",
                "config_id": config_id,
                "sync_id": sync_result.id,
                "files_processed": sync_result.files_processed,
                "files_added": sync_result.files_added,
                "files_failed": sync_result.files_failed,
                "sync_start_time": sync_result.sync_start_time.isoformat(),
                "sync_end_time": sync_result.sync_end_time.isoformat() if sync_result.sync_end_time else None
            }
        finally:
            loop.close()
            db.close()
            
    except Exception as e:
        logger.error(f"Remote directory sync failed for config {config_id}: {str(e)}")
        
        # Update task state
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "config_id": config_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "status": "failed",
            "config_id": config_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, name="sync_all_remote_directories")
def sync_all_remote_directories_task(self) -> Dict[str, Any]:
    """
    Celery task to synchronize all active remote directories
    
    Returns:
        Dict containing overall sync results
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Create service instance
        service = RemoteDirectoryService(db)
        
        # Perform synchronization for all active directories
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            sync_results = loop.run_until_complete(
                service.sync_all_active_directories()
            )
            
            # Aggregate results
            total_configs = len(sync_results)
            total_files_processed = sum(result.files_processed for result in sync_results)
            total_files_added = sum(result.files_added for result in sync_results)
            total_files_failed = sum(result.files_failed for result in sync_results)
            
            logger.info(f"Completed sync for {total_configs} remote directories")
            
            return {
                "status": "success",
                "total_configs": total_configs,
                "total_files_processed": total_files_processed,
                "total_files_added": total_files_added,
                "total_files_failed": total_files_failed,
                "sync_results": [
                    {
                        "config_id": result.config_id,
                        "sync_id": result.id,
                        "files_processed": result.files_processed,
                        "files_added": result.files_added,
                        "files_failed": result.files_failed,
                        "sync_status": result.sync_status
                    }
                    for result in sync_results
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            loop.close()
            db.close()
            
    except Exception as e:
        logger.error(f"Batch remote directory sync failed: {str(e)}")
        
        # Update task state
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name="schedule_remote_directory_sync")
def schedule_remote_directory_sync() -> Dict[str, Any]:
    """
    Periodic task to schedule remote directory synchronization
    
    This task runs on a schedule and triggers sync for directories
    that are due for synchronization based on their sync intervals.
    
    Returns:
        Dict containing scheduling results
    """
    try:
        if not settings.enable_remote_directory_monitoring:
            logger.info("Remote directory monitoring is disabled")
            return {
                "status": "skipped",
                "reason": "monitoring_disabled",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get database session
        db = next(get_db())
        
        try:
            # Create service instance
            service = RemoteDirectoryService(db)
            
            # Get all active configurations
            active_configs = service.get_remote_directory_configs(
                filters={"is_active": True}
            )
            
            scheduled_syncs = []
            
            for config in active_configs:
                # Check if sync is due
                if service._is_sync_due(config):
                    # Schedule sync task
                    task = sync_remote_directory_task.delay(config.id)
                    
                    scheduled_syncs.append({
                        "config_id": config.id,
                        "config_name": config.name,
                        "task_id": task.id,
                        "scheduled_at": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"Scheduled sync for remote directory: {config.name}")
            
            return {
                "status": "success",
                "scheduled_syncs": len(scheduled_syncs),
                "sync_details": scheduled_syncs,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to schedule remote directory syncs: {str(e)}")
        
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Periodic task configuration
from celery.schedules import crontab

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'sync-remote-directories': {
        'task': 'schedule_remote_directory_sync',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
}

celery_app.conf.timezone = 'UTC'
"""
Remote directory management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.models.database_config import get_db
from app.models.schemas import (
    RemoteDirectoryConfigCreate,
    RemoteDirectoryConfigUpdate,
    RemoteDirectoryConfigResponse,
    RemoteDirectorySyncResponse,
    RemoteDirectoryFilters,
    RemoteDirectorySyncFilters
)
from app.services.remote_directory_service import RemoteDirectoryService


router = APIRouter(prefix="/remote-directories", tags=["remote-directories"])


@router.post("/", response_model=RemoteDirectoryConfigResponse)
async def create_remote_directory_config(
    config_data: RemoteDirectoryConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new remote directory configuration
    
    Args:
        config_data: Remote directory configuration data
        db: Database session
        
    Returns:
        Created remote directory configuration
    """
    service = RemoteDirectoryService(db)
    return service.create_remote_directory_config(config_data)


@router.get("/", response_model=List[RemoteDirectoryConfigResponse])
async def get_remote_directory_configs(
    is_active: Optional[bool] = None,
    schema_type: Optional[str] = None,
    name_contains: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve remote directory configurations with optional filtering
    
    Args:
        is_active: Filter by active status
        schema_type: Filter by schema type
        name_contains: Filter by name containing text
        db: Database session
        
    Returns:
        List of remote directory configurations
    """
    filters = RemoteDirectoryFilters(
        is_active=is_active,
        schema_type=schema_type,
        name_contains=name_contains
    )
    
    service = RemoteDirectoryService(db)
    return service.get_remote_directory_configs(filters)


@router.get("/{config_id}", response_model=RemoteDirectoryConfigResponse)
async def get_remote_directory_config(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific remote directory configuration
    
    Args:
        config_id: Configuration ID
        db: Database session
        
    Returns:
        Remote directory configuration
    """
    service = RemoteDirectoryService(db)
    config = service.get_remote_directory_config_by_id(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Remote directory configuration not found")
    
    return config


@router.put("/{config_id}", response_model=RemoteDirectoryConfigResponse)
async def update_remote_directory_config(
    config_id: str,
    config_update: RemoteDirectoryConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Update remote directory configuration
    
    Args:
        config_id: Configuration ID
        config_update: Configuration update data
        db: Database session
        
    Returns:
        Updated remote directory configuration
    """
    service = RemoteDirectoryService(db)
    config = service.update_remote_directory_config(config_id, config_update)
    
    if not config:
        raise HTTPException(status_code=404, detail="Remote directory configuration not found")
    
    return config


@router.delete("/{config_id}")
async def delete_remote_directory_config(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete remote directory configuration
    
    Args:
        config_id: Configuration ID
        db: Database session
        
    Returns:
        Success message
    """
    service = RemoteDirectoryService(db)
    success = service.delete_remote_directory_config(config_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Remote directory configuration not found")
    
    return {"message": "Remote directory configuration deleted successfully"}


@router.post("/{config_id}/sync", response_model=RemoteDirectorySyncResponse)
async def sync_remote_directory(
    config_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger synchronization for a specific remote directory
    
    Args:
        config_id: Configuration ID
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Sync operation result
    """
    service = RemoteDirectoryService(db)
    return await service.sync_remote_directory(config_id)


@router.post("/sync-all", response_model=List[RemoteDirectorySyncResponse])
async def sync_all_remote_directories(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger synchronization for all active remote directories
    
    Args:
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        List of sync operation results
    """
    service = RemoteDirectoryService(db)
    return await service.sync_all_active_directories()


@router.get("/{config_id}/sync-logs", response_model=List[RemoteDirectorySyncResponse])
async def get_sync_logs_for_config(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve sync logs for a specific remote directory configuration
    
    Args:
        config_id: Configuration ID
        db: Database session
        
    Returns:
        List of sync logs
    """
    filters = RemoteDirectorySyncFilters(config_id=config_id)
    
    service = RemoteDirectoryService(db)
    return service.get_sync_logs(filters)


@router.get("/sync-logs/", response_model=List[RemoteDirectorySyncResponse])
async def get_all_sync_logs(
    config_id: Optional[str] = None,
    sync_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all sync logs with optional filtering
    
    Args:
        config_id: Filter by configuration ID
        sync_status: Filter by sync status
        db: Database session
        
    Returns:
        List of sync logs
    """
    filters = RemoteDirectorySyncFilters(
        config_id=config_id,
        sync_status=sync_status
    )
    
    service = RemoteDirectoryService(db)
    return service.get_sync_logs(filters)
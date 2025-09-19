"""
Remote directory monitoring and synchronization service
"""
import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.database import (
    RemoteDirectoryConfig, 
    RemoteDirectorySync, 
    Document, 
    DocumentType, 
    ProcessingStatus
)
from app.models.schemas import (
    RemoteDirectoryConfigCreate,
    RemoteDirectoryConfigUpdate,
    RemoteDirectoryConfigResponse,
    RemoteDirectorySyncCreate,
    RemoteDirectorySyncUpdate,
    RemoteDirectorySyncResponse,
    RemoteDirectoryFilters,
    RemoteDirectorySyncFilters,
    DocumentCreate
)
from app.core.config import settings
from app.services.document_service import DocumentService


logger = logging.getLogger(__name__)


class RemoteDirectoryService:
    """Service for managing remote directory monitoring and synchronization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.document_service = DocumentService(db)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def create_remote_directory_config(
        self, 
        config_data: RemoteDirectoryConfigCreate
    ) -> RemoteDirectoryConfigResponse:
        """
        Create a new remote directory configuration
        
        Args:
            config_data: Remote directory configuration data
            
        Returns:
            RemoteDirectoryConfigResponse: Created configuration
        """
        # Check if name already exists
        existing = self.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.name == config_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Remote directory configuration with name '{config_data.name}' already exists"
            )
        
        # Validate directory path exists and is accessible
        logger.debug(f"Validating directory path: {config_data.directory_path}")
        validation_result = self._validate_directory_path(config_data.directory_path)
        logger.debug(f"Validation result: {validation_result}")
        
        if not validation_result:
            raise HTTPException(
                status_code=400,
                detail=f"Directory path '{config_data.directory_path}' is not accessible"
            )
        
        # Create configuration
        db_config = RemoteDirectoryConfig(
            name=config_data.name,
            directory_path=config_data.directory_path,
            is_active=config_data.is_active,
            sync_interval=config_data.sync_interval,
            file_patterns=config_data.file_patterns,
            exclude_patterns=config_data.exclude_patterns,
            schema_type=config_data.schema_type
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        
        logger.info(f"Created remote directory configuration: {config_data.name}")
        return RemoteDirectoryConfigResponse.model_validate(db_config)
    
    def get_remote_directory_configs(
        self, 
        filters: Optional[RemoteDirectoryFilters] = None
    ) -> List[RemoteDirectoryConfigResponse]:
        """
        Retrieve remote directory configurations with optional filtering
        
        Args:
            filters: Optional filters for configuration retrieval
            
        Returns:
            List of RemoteDirectoryConfigResponse objects
        """
        query = self.db.query(RemoteDirectoryConfig)
        
        if filters:
            if filters.is_active is not None:
                query = query.filter(RemoteDirectoryConfig.is_active == filters.is_active)
            if filters.schema_type:
                query = query.filter(RemoteDirectoryConfig.schema_type == filters.schema_type)
            if filters.name_contains:
                query = query.filter(RemoteDirectoryConfig.name.contains(filters.name_contains))
        
        configs = query.order_by(RemoteDirectoryConfig.created_at.desc()).all()
        return [RemoteDirectoryConfigResponse.model_validate(config) for config in configs]
    
    def get_remote_directory_config_by_id(self, config_id: str) -> Optional[RemoteDirectoryConfigResponse]:
        """
        Retrieve a specific remote directory configuration by ID
        
        Args:
            config_id: Configuration ID
            
        Returns:
            RemoteDirectoryConfigResponse or None if not found
        """
        config = self.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == config_id
        ).first()
        
        if config:
            return RemoteDirectoryConfigResponse.model_validate(config)
        return None
    
    def update_remote_directory_config(
        self, 
        config_id: str, 
        config_update: RemoteDirectoryConfigUpdate
    ) -> Optional[RemoteDirectoryConfigResponse]:
        """
        Update remote directory configuration
        
        Args:
            config_id: Configuration ID
            config_update: Configuration update data
            
        Returns:
            Updated RemoteDirectoryConfigResponse or None if not found
        """
        config = self.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == config_id
        ).first()
        
        if not config:
            return None
        
        # Update fields
        update_data = config_update.model_dump(exclude_unset=True)
        
        # Validate directory path if being updated
        if 'directory_path' in update_data:
            if not self._validate_directory_path(update_data['directory_path']):
                raise HTTPException(
                    status_code=400,
                    detail=f"Directory path '{update_data['directory_path']}' is not accessible"
                )
        
        # Check name uniqueness if being updated
        if 'name' in update_data and update_data['name'] != config.name:
            existing = self.db.query(RemoteDirectoryConfig).filter(
                RemoteDirectoryConfig.name == update_data['name'],
                RemoteDirectoryConfig.id != config_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Remote directory configuration with name '{update_data['name']}' already exists"
                )
        
        for field, value in update_data.items():
            setattr(config, field, value)
        
        self.db.commit()
        self.db.refresh(config)
        
        logger.info(f"Updated remote directory configuration: {config.name}")
        return RemoteDirectoryConfigResponse.model_validate(config)
    
    def delete_remote_directory_config(self, config_id: str) -> bool:
        """
        Delete remote directory configuration
        
        Args:
            config_id: Configuration ID
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        config = self.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == config_id
        ).first()
        
        if not config:
            return False
        
        # Delete associated sync logs
        self.db.query(RemoteDirectorySync).filter(
            RemoteDirectorySync.config_id == config_id
        ).delete()
        
        # Delete configuration
        self.db.delete(config)
        self.db.commit()
        
        logger.info(f"Deleted remote directory configuration: {config.name}")
        return True
    
    async def sync_remote_directory(self, config_id: str) -> RemoteDirectorySyncResponse:
        """
        Synchronize files from a remote directory
        
        Args:
            config_id: Remote directory configuration ID
            
        Returns:
            RemoteDirectorySyncResponse: Sync operation result
        """
        config = self.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == config_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Remote directory configuration not found")
        
        if not config.is_active:
            raise HTTPException(status_code=400, detail="Remote directory configuration is inactive")
        
        # Create sync log
        sync_log = RemoteDirectorySync(
            config_id=config_id,
            sync_start_time=datetime.utcnow(),
            sync_status="running"
        )
        
        self.db.add(sync_log)
        self.db.commit()
        self.db.refresh(sync_log)
        
        try:
            # Perform synchronization
            sync_result = await self._perform_sync(config, sync_log)
            
            # Update sync log with results
            sync_log.sync_end_time = datetime.utcnow()
            sync_log.files_processed = sync_result['files_processed']
            sync_log.files_added = sync_result['files_added']
            sync_log.files_updated = sync_result['files_updated']
            sync_log.files_failed = sync_result['files_failed']
            sync_log.sync_status = "completed"
            sync_log.sync_metadata = sync_result['metadata']
            
            # Update config last sync time
            config.last_sync_time = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sync_log)
            
            logger.info(f"Completed sync for {config.name}: {sync_result}")
            return RemoteDirectorySyncResponse.model_validate(sync_log)
            
        except Exception as e:
            # Update sync log with error
            sync_log.sync_end_time = datetime.utcnow()
            sync_log.sync_status = "failed"
            sync_log.error_message = str(e)
            
            self.db.commit()
            self.db.refresh(sync_log)
            
            logger.error(f"Sync failed for {config.name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
    
    async def sync_all_active_directories(self) -> List[RemoteDirectorySyncResponse]:
        """
        Synchronize all active remote directories
        
        Returns:
            List of RemoteDirectorySyncResponse objects
        """
        active_configs = self.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.is_active == True
        ).all()
        
        sync_results = []
        
        for config in active_configs:
            # Check if sync is due based on interval
            if self._is_sync_due(config):
                try:
                    sync_result = await self.sync_remote_directory(config.id)
                    sync_results.append(sync_result)
                except Exception as e:
                    logger.error(f"Failed to sync {config.name}: {str(e)}")
        
        return sync_results
    
    def get_sync_logs(
        self, 
        filters: Optional[RemoteDirectorySyncFilters] = None
    ) -> List[RemoteDirectorySyncResponse]:
        """
        Retrieve sync logs with optional filtering
        
        Args:
            filters: Optional filters for sync log retrieval
            
        Returns:
            List of RemoteDirectorySyncResponse objects
        """
        query = self.db.query(RemoteDirectorySync)
        
        if filters:
            if filters.config_id:
                query = query.filter(RemoteDirectorySync.config_id == filters.config_id)
            if filters.sync_status:
                query = query.filter(RemoteDirectorySync.sync_status == filters.sync_status)
            if filters.sync_date_from:
                query = query.filter(RemoteDirectorySync.sync_start_time >= filters.sync_date_from)
            if filters.sync_date_to:
                query = query.filter(RemoteDirectorySync.sync_start_time <= filters.sync_date_to)
        
        sync_logs = query.order_by(RemoteDirectorySync.sync_start_time.desc()).all()
        return [RemoteDirectorySyncResponse.model_validate(log) for log in sync_logs]
    
    def _validate_directory_path(self, directory_path: str) -> bool:
        """
        Validate that directory path exists and is accessible
        
        Args:
            directory_path: Path to validate
            
        Returns:
            bool: True if valid and accessible
        """
        try:
            path = Path(directory_path)
            result = path.exists() and path.is_dir() and os.access(path, os.R_OK)
            logger.debug(f"Directory validation for {directory_path}: {result}")
            return result
        except Exception as e:
            logger.debug(f"Directory validation exception for {directory_path}: {str(e)}")
            return False
    
    def _is_sync_due(self, config: RemoteDirectoryConfig) -> bool:
        """
        Check if synchronization is due for a configuration
        
        Args:
            config: Remote directory configuration
            
        Returns:
            bool: True if sync is due
        """
        if not config.last_sync_time:
            return True
        
        time_since_last_sync = datetime.utcnow() - config.last_sync_time
        return time_since_last_sync.total_seconds() >= config.sync_interval
    
    async def _perform_sync(
        self, 
        config: RemoteDirectoryConfig, 
        sync_log: RemoteDirectorySync
    ) -> Dict[str, Any]:
        """
        Perform the actual synchronization operation
        
        Args:
            config: Remote directory configuration
            sync_log: Sync log to update
            
        Returns:
            Dict containing sync results
        """
        files_processed = 0
        files_added = 0
        files_updated = 0
        files_failed = 0
        
        try:
            # Get list of files to process
            files_to_process = self._get_files_to_process(config)
            
            # Process files in batches
            batch_size = settings.remote_directory_batch_size
            
            for i in range(0, len(files_to_process), batch_size):
                batch = files_to_process[i:i + batch_size]
                
                # Process batch
                batch_results = await self._process_file_batch(batch, config)
                
                files_processed += batch_results['processed']
                files_added += batch_results['added']
                files_updated += batch_results['updated']
                files_failed += batch_results['failed']
                
                # Update sync log progress
                sync_log.files_processed = files_processed
                sync_log.files_added = files_added
                sync_log.files_updated = files_updated
                sync_log.files_failed = files_failed
                self.db.commit()
        
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
            raise
        
        return {
            'files_processed': files_processed,
            'files_added': files_added,
            'files_updated': files_updated,
            'files_failed': files_failed,
            'metadata': {
                'sync_duration_seconds': (datetime.utcnow() - sync_log.sync_start_time).total_seconds(),
                'batch_size': batch_size,
                'directory_path': config.directory_path
            }
        }
    
    def _get_files_to_process(self, config: RemoteDirectoryConfig) -> List[Path]:
        """
        Get list of files to process from remote directory
        
        Args:
            config: Remote directory configuration
            
        Returns:
            List of file paths to process
        """
        directory_path = Path(config.directory_path)
        files_to_process = []
        
        # Get all files in directory (recursively)
        for file_path in directory_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Check file patterns
            if not self._matches_file_patterns(file_path, config):
                continue
            
            # Check if file is recent enough
            if not self._is_file_recent_enough(file_path):
                continue
            
            # Check if file already exists in database
            if not self._should_process_file(file_path):
                continue
            
            files_to_process.append(file_path)
        
        return files_to_process
    
    def _matches_file_patterns(self, file_path: Path, config: RemoteDirectoryConfig) -> bool:
        """
        Check if file matches include/exclude patterns
        
        Args:
            file_path: File path to check
            config: Remote directory configuration
            
        Returns:
            bool: True if file should be processed
        """
        filename = file_path.name
        
        # Check exclude patterns first
        if config.exclude_patterns:
            for pattern in config.exclude_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    return False
        
        # Check include patterns
        if config.file_patterns:
            for pattern in config.file_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    return True
            return False  # No include patterns matched
        
        # Default include patterns for supported file types
        default_patterns = ['*.pdf', '*.docx', '*.txt']
        for pattern in default_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False
    
    def _is_file_recent_enough(self, file_path: Path) -> bool:
        """
        Check if file is recent enough to process
        
        Args:
            file_path: File path to check
            
        Returns:
            bool: True if file is recent enough
        """
        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            max_age = timedelta(seconds=settings.remote_directory_max_file_age)
            return datetime.utcnow() - file_mtime <= max_age
        except Exception:
            return False
    
    def _should_process_file(self, file_path: Path) -> bool:
        """
        Check if file should be processed (not already in database)
        
        Args:
            file_path: File path to check
            
        Returns:
            bool: True if file should be processed
        """
        # Calculate file hash
        try:
            file_hash = self.document_service._calculate_file_hash(file_path)
            
            # Check if file with same hash already exists
            existing = self.db.query(Document).filter(
                Document.document_metadata.op('->>')('file_hash') == file_hash
            ).first()
            
            return existing is None
        except Exception:
            return True  # Process if we can't determine
    
    async def _process_file_batch(
        self, 
        file_batch: List[Path], 
        config: RemoteDirectoryConfig
    ) -> Dict[str, int]:
        """
        Process a batch of files
        
        Args:
            file_batch: List of file paths to process
            config: Remote directory configuration
            
        Returns:
            Dict containing batch processing results
        """
        processed = 0
        added = 0
        updated = 0
        failed = 0
        
        for file_path in file_batch:
            try:
                # Create a mock UploadFile object for the document service
                mock_file = self._create_mock_upload_file(file_path)
                
                # Upload document using document service
                document_response = await self.document_service.upload_document(
                    file=mock_file,
                    schema_type=config.schema_type.value if config.schema_type else None
                )
                
                processed += 1
                added += 1
                
                logger.debug(f"Successfully processed file: {file_path}")
                
            except Exception as e:
                failed += 1
                logger.error(f"Failed to process file {file_path}: {str(e)}")
        
        return {
            'processed': processed,
            'added': added,
            'updated': updated,
            'failed': failed
        }
    
    def _create_mock_upload_file(self, file_path: Path):
        """
        Create a mock UploadFile object for existing files
        
        Args:
            file_path: Path to the file
            
        Returns:
            Mock UploadFile object
        """
        class MockUploadFile:
            def __init__(self, path: Path):
                self.filename = path.name
                self.content_type = self._get_content_type(path)
                self.size = path.stat().st_size
                self._path = path
            
            async def read(self) -> bytes:
                with open(self._path, 'rb') as f:
                    return f.read()
            
            def _get_content_type(self, path: Path) -> str:
                suffix = path.suffix.lower()
                content_types = {
                    '.pdf': 'application/pdf',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.txt': 'text/plain'
                }
                return content_types.get(suffix, 'application/octet-stream')
        
        return MockUploadFile(file_path)
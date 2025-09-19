"""
Tests for remote directory service functionality
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.remote_directory_service import RemoteDirectoryService
from app.models.database import RemoteDirectoryConfig, RemoteDirectorySync, Document
from app.models.schemas import (
    RemoteDirectoryConfigCreate,
    RemoteDirectoryConfigUpdate,
    RemoteDirectoryFilters,
    RemoteDirectorySyncFilters,
    SchemaType
)


class TestRemoteDirectoryService:
    """Test cases for RemoteDirectoryService"""
    
    @pytest.fixture
    def service(self, db_session: Session):
        """Create RemoteDirectoryService instance"""
        return RemoteDirectoryService(db_session)
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_config_data(self, temp_directory):
        """Sample remote directory configuration data"""
        return RemoteDirectoryConfigCreate(
            name="test_config",
            directory_path=str(temp_directory),
            is_active=True,
            sync_interval=300,
            file_patterns=["*.pdf", "*.txt"],
            exclude_patterns=["*temp*"],
            schema_type=SchemaType.EU_ESRS_CSRD
        )
    
    def test_create_remote_directory_config_success(self, service, sample_config_data):
        """Test successful creation of remote directory configuration"""
        result = service.create_remote_directory_config(sample_config_data)
        
        assert result.name == sample_config_data.name
        assert result.directory_path == sample_config_data.directory_path
        assert result.is_active == sample_config_data.is_active
        assert result.sync_interval == sample_config_data.sync_interval
        assert result.file_patterns == sample_config_data.file_patterns
        assert result.exclude_patterns == sample_config_data.exclude_patterns
        assert result.schema_type == sample_config_data.schema_type
        assert result.id is not None
        assert result.created_at is not None
    
    def test_create_remote_directory_config_duplicate_name(self, service, sample_config_data):
        """Test creation with duplicate name fails"""
        # Create first configuration
        service.create_remote_directory_config(sample_config_data)
        
        # Try to create another with same name
        with pytest.raises(HTTPException) as exc_info:
            service.create_remote_directory_config(sample_config_data)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)
    
    def test_create_remote_directory_config_invalid_path(self, service, sample_config_data):
        """Test creation with invalid directory path fails"""
        sample_config_data.directory_path = "/nonexistent/path"
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_remote_directory_config(sample_config_data)
        
        assert exc_info.value.status_code == 400
        assert "not accessible" in str(exc_info.value.detail)
    
    def test_get_remote_directory_configs_no_filters(self, service, sample_config_data):
        """Test retrieving all configurations without filters"""
        # Create test configuration
        created = service.create_remote_directory_config(sample_config_data)
        
        # Retrieve all configurations
        configs = service.get_remote_directory_configs()
        
        assert len(configs) == 1
        assert configs[0].id == created.id
    
    def test_get_remote_directory_configs_with_filters(self, service, sample_config_data, temp_directory):
        """Test retrieving configurations with filters"""
        # Create active configuration
        active_config = service.create_remote_directory_config(sample_config_data)
        
        # Create inactive configuration
        inactive_data = RemoteDirectoryConfigCreate(
            name="inactive_config",
            directory_path=str(temp_directory),
            is_active=False,
            sync_interval=600
        )
        service.create_remote_directory_config(inactive_data)
        
        # Filter by active status
        filters = RemoteDirectoryFilters(is_active=True)
        active_configs = service.get_remote_directory_configs(filters)
        
        assert len(active_configs) == 1
        assert active_configs[0].id == active_config.id
        assert active_configs[0].is_active is True
        
        # Filter by inactive status
        filters = RemoteDirectoryFilters(is_active=False)
        inactive_configs = service.get_remote_directory_configs(filters)
        
        assert len(inactive_configs) == 1
        assert inactive_configs[0].is_active is False
    
    def test_get_remote_directory_config_by_id(self, service, sample_config_data):
        """Test retrieving configuration by ID"""
        created = service.create_remote_directory_config(sample_config_data)
        
        retrieved = service.get_remote_directory_config_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
    
    def test_get_remote_directory_config_by_id_not_found(self, service):
        """Test retrieving non-existent configuration returns None"""
        result = service.get_remote_directory_config_by_id("nonexistent-id")
        assert result is None
    
    def test_update_remote_directory_config_success(self, service, sample_config_data):
        """Test successful update of remote directory configuration"""
        created = service.create_remote_directory_config(sample_config_data)
        
        update_data = RemoteDirectoryConfigUpdate(
            name="updated_name",
            sync_interval=600,
            is_active=False
        )
        
        updated = service.update_remote_directory_config(created.id, update_data)
        
        assert updated is not None
        assert updated.name == "updated_name"
        assert updated.sync_interval == 600
        assert updated.is_active is False
        assert updated.directory_path == sample_config_data.directory_path  # Unchanged
    
    def test_update_remote_directory_config_not_found(self, service):
        """Test updating non-existent configuration returns None"""
        update_data = RemoteDirectoryConfigUpdate(name="new_name")
        result = service.update_remote_directory_config("nonexistent-id", update_data)
        assert result is None
    
    def test_delete_remote_directory_config_success(self, service, sample_config_data):
        """Test successful deletion of remote directory configuration"""
        created = service.create_remote_directory_config(sample_config_data)
        
        success = service.delete_remote_directory_config(created.id)
        assert success is True
        
        # Verify deletion
        retrieved = service.get_remote_directory_config_by_id(created.id)
        assert retrieved is None
    
    def test_delete_remote_directory_config_not_found(self, service):
        """Test deleting non-existent configuration returns False"""
        success = service.delete_remote_directory_config("nonexistent-id")
        assert success is False
    
    def test_validate_directory_path_valid(self, service, temp_directory):
        """Test directory path validation with valid path"""
        assert service._validate_directory_path(str(temp_directory)) is True
    
    def test_validate_directory_path_invalid(self, service):
        """Test directory path validation with invalid path"""
        assert service._validate_directory_path("/nonexistent/path") is False
        assert service._validate_directory_path("not_a_directory.txt") is False
    
    def test_is_sync_due_no_previous_sync(self, service, db_session, sample_config_data):
        """Test sync due check when no previous sync exists"""
        created = service.create_remote_directory_config(sample_config_data)
        
        # Get the database object
        config = db_session.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == created.id
        ).first()
        
        assert service._is_sync_due(config) is True
    
    def test_is_sync_due_recent_sync(self, service, db_session, sample_config_data):
        """Test sync due check when recent sync exists"""
        created = service.create_remote_directory_config(sample_config_data)
        
        # Get the database object and update last sync time
        config = db_session.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == created.id
        ).first()
        config.last_sync_time = datetime.utcnow()
        db_session.commit()
        
        assert service._is_sync_due(config) is False
    
    def test_is_sync_due_old_sync(self, service, db_session, sample_config_data):
        """Test sync due check when old sync exists"""
        created = service.create_remote_directory_config(sample_config_data)
        
        # Get the database object and set old last sync time
        config = db_session.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == created.id
        ).first()
        config.last_sync_time = datetime.utcnow() - timedelta(seconds=400)  # Older than sync_interval
        db_session.commit()
        
        assert service._is_sync_due(config) is True
    
    def test_matches_file_patterns_include_patterns(self, service, db_session, sample_config_data):
        """Test file pattern matching with include patterns"""
        created = service.create_remote_directory_config(sample_config_data)
        config = db_session.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == created.id
        ).first()
        
        # Test matching files
        assert service._matches_file_patterns(Path("document.pdf"), config) is True
        assert service._matches_file_patterns(Path("text.txt"), config) is True
        
        # Test non-matching files
        assert service._matches_file_patterns(Path("document.docx"), config) is False
        assert service._matches_file_patterns(Path("image.jpg"), config) is False
    
    def test_matches_file_patterns_exclude_patterns(self, service, db_session, sample_config_data):
        """Test file pattern matching with exclude patterns"""
        created = service.create_remote_directory_config(sample_config_data)
        config = db_session.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == created.id
        ).first()
        
        # Test excluded files
        assert service._matches_file_patterns(Path("temp_document.pdf"), config) is False
        assert service._matches_file_patterns(Path("document_temp.txt"), config) is False
        
        # Test non-excluded files
        assert service._matches_file_patterns(Path("document.pdf"), config) is True
    
    def test_matches_file_patterns_no_patterns(self, service, db_session, temp_directory):
        """Test file pattern matching with no patterns (default behavior)"""
        config_data = RemoteDirectoryConfigCreate(
            name="no_patterns_config",
            directory_path=str(temp_directory),
            is_active=True,
            sync_interval=300
        )
        created = service.create_remote_directory_config(config_data)
        config = db_session.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == created.id
        ).first()
        
        # Test default supported file types
        assert service._matches_file_patterns(Path("document.pdf"), config) is True
        assert service._matches_file_patterns(Path("document.docx"), config) is True
        assert service._matches_file_patterns(Path("document.txt"), config) is True
        
        # Test unsupported file types
        assert service._matches_file_patterns(Path("image.jpg"), config) is False
    
    def test_is_file_recent_enough_recent_file(self, service, temp_directory):
        """Test file age check with recent file"""
        # Create a test file
        test_file = temp_directory / "recent_file.txt"
        test_file.write_text("test content")
        
        assert service._is_file_recent_enough(test_file) is True
    
    def test_is_file_recent_enough_old_file(self, service, temp_directory):
        """Test file age check with old file"""
        # Create a test file
        test_file = temp_directory / "old_file.txt"
        test_file.write_text("test content")
        
        # Mock the file modification time to be very old
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_mtime = (datetime.utcnow() - timedelta(days=2)).timestamp()
            assert service._is_file_recent_enough(test_file) is False
    
    @pytest.mark.asyncio
    async def test_sync_remote_directory_success(self, service, sample_config_data, temp_directory):
        """Test successful remote directory synchronization"""
        # Create test files
        (temp_directory / "test1.pdf").write_text("test content 1")
        (temp_directory / "test2.txt").write_text("test content 2")
        
        created = service.create_remote_directory_config(sample_config_data)
        
        # Mock the document service upload method
        with patch.object(service.document_service, 'upload_document', new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = Mock(id="doc-id", filename="test.pdf")
            
            result = await service.sync_remote_directory(created.id)
            
            assert result.config_id == created.id
            assert result.sync_status == "completed"
            assert result.sync_end_time is not None
    
    @pytest.mark.asyncio
    async def test_sync_remote_directory_not_found(self, service):
        """Test sync with non-existent configuration"""
        with pytest.raises(HTTPException) as exc_info:
            await service.sync_remote_directory("nonexistent-id")
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_sync_remote_directory_inactive(self, service, sample_config_data):
        """Test sync with inactive configuration"""
        sample_config_data.is_active = False
        created = service.create_remote_directory_config(sample_config_data)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.sync_remote_directory(created.id)
        
        assert exc_info.value.status_code == 400
        assert "inactive" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_sync_all_active_directories(self, service, sample_config_data, temp_directory):
        """Test synchronization of all active directories"""
        # Create active configuration
        created = service.create_remote_directory_config(sample_config_data)
        
        # Create inactive configuration
        inactive_data = RemoteDirectoryConfigCreate(
            name="inactive_config",
            directory_path=str(temp_directory),
            is_active=False,
            sync_interval=300
        )
        service.create_remote_directory_config(inactive_data)
        
        # Mock the sync method
        with patch.object(service, 'sync_remote_directory', new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = Mock(
                config_id=created.id,
                sync_status="completed",
                files_processed=2,
                files_added=2,
                files_failed=0
            )
            
            results = await service.sync_all_active_directories()
            
            # Should only sync active configuration
            assert len(results) == 1
            assert results[0].config_id == created.id
    
    def test_get_sync_logs_no_filters(self, service, db_session, sample_config_data):
        """Test retrieving sync logs without filters"""
        created = service.create_remote_directory_config(sample_config_data)
        
        # Create test sync log
        sync_log = RemoteDirectorySync(
            config_id=created.id,
            sync_start_time=datetime.utcnow(),
            sync_status="completed",
            files_processed=5,
            files_added=3,
            files_failed=0
        )
        db_session.add(sync_log)
        db_session.commit()
        
        logs = service.get_sync_logs()
        
        assert len(logs) == 1
        assert logs[0].config_id == created.id
        assert logs[0].sync_status == "completed"
    
    def test_get_sync_logs_with_filters(self, service, db_session, sample_config_data):
        """Test retrieving sync logs with filters"""
        created = service.create_remote_directory_config(sample_config_data)
        
        # Create completed sync log
        completed_log = RemoteDirectorySync(
            config_id=created.id,
            sync_start_time=datetime.utcnow(),
            sync_status="completed",
            files_processed=5
        )
        db_session.add(completed_log)
        
        # Create failed sync log
        failed_log = RemoteDirectorySync(
            config_id=created.id,
            sync_start_time=datetime.utcnow(),
            sync_status="failed",
            files_processed=0
        )
        db_session.add(failed_log)
        db_session.commit()
        
        # Filter by status
        filters = RemoteDirectorySyncFilters(sync_status="completed")
        completed_logs = service.get_sync_logs(filters)
        
        assert len(completed_logs) == 1
        assert completed_logs[0].sync_status == "completed"
        
        # Filter by config ID
        filters = RemoteDirectorySyncFilters(config_id=created.id)
        config_logs = service.get_sync_logs(filters)
        
        assert len(config_logs) == 2  # Both logs for this config
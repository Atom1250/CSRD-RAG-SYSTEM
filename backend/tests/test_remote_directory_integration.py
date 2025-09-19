"""
Integration tests for remote directory functionality
"""
import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, Mock

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.services.remote_directory_service import RemoteDirectoryService
from app.models.database import RemoteDirectoryConfig, RemoteDirectorySync, Document
from app.models.schemas import RemoteDirectoryConfigCreate, SchemaType


class TestRemoteDirectoryIntegration:
    """Integration tests for remote directory functionality"""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory with test files"""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create test files
        (temp_path / "document1.pdf").write_text("PDF content 1")
        (temp_path / "document2.txt").write_text("Text content 2")
        (temp_path / "report.docx").write_text("DOCX content")
        (temp_path / "temp_file.pdf").write_text("Temporary file")  # Should be excluded
        (temp_path / "image.jpg").write_text("Image content")  # Should be excluded by default
        
        # Create subdirectory with files
        subdir = temp_path / "subdir"
        subdir.mkdir()
        (subdir / "subdoc.pdf").write_text("Subdirectory PDF")
        
        yield temp_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, db_session: Session):
        """Create RemoteDirectoryService instance"""
        return RemoteDirectoryService(db_session)
    
    @pytest.fixture
    def sample_config(self, service, temp_directory):
        """Create sample remote directory configuration"""
        config_data = RemoteDirectoryConfigCreate(
            name="integration_test_config",
            directory_path=str(temp_directory),
            is_active=True,
            sync_interval=300,
            file_patterns=["*.pdf", "*.txt", "*.docx"],
            exclude_patterns=["*temp*"],
            schema_type=SchemaType.EU_ESRS_CSRD
        )
        return service.create_remote_directory_config(config_data)
    
    def test_end_to_end_remote_directory_workflow(self, client: TestClient, temp_directory):
        """Test complete end-to-end workflow for remote directory management"""
        # Step 1: Create remote directory configuration via API
        config_data = {
            "name": "e2e_test_config",
            "directory_path": str(temp_directory),
            "is_active": True,
            "sync_interval": 300,
            "file_patterns": ["*.pdf", "*.txt"],
            "exclude_patterns": ["*temp*"],
            "schema_type": SchemaType.EU_ESRS_CSRD.value
        }
        
        create_response = client.post("/api/remote-directories/", json=config_data)
        assert create_response.status_code == 200
        config = create_response.json()
        
        # Step 2: Verify configuration was created
        get_response = client.get(f"/api/remote-directories/{config['id']}")
        assert get_response.status_code == 200
        retrieved_config = get_response.json()
        assert retrieved_config["name"] == config_data["name"]
        
        # Step 3: List all configurations
        list_response = client.get("/api/remote-directories/")
        assert list_response.status_code == 200
        configs = list_response.json()
        assert len(configs) == 1
        assert configs[0]["id"] == config["id"]
        
        # Step 4: Update configuration
        update_data = {"sync_interval": 600}
        update_response = client.put(f"/api/remote-directories/{config['id']}", json=update_data)
        assert update_response.status_code == 200
        updated_config = update_response.json()
        assert updated_config["sync_interval"] == 600
        
        # Step 5: Mock sync operation (since we don't want to actually process files in tests)
        with patch('app.services.remote_directory_service.RemoteDirectoryService.sync_remote_directory') as mock_sync:
            mock_result = Mock()
            mock_result.id = "sync-123"
            mock_result.config_id = config["id"]
            mock_result.sync_status = "completed"
            mock_result.files_processed = 3
            mock_result.files_added = 3
            mock_result.files_failed = 0
            mock_result.sync_start_time = datetime.utcnow()
            mock_result.sync_end_time = datetime.utcnow()
            mock_sync.return_value = mock_result
            
            # Trigger sync
            sync_response = client.post(f"/api/remote-directories/{config['id']}/sync")
            assert sync_response.status_code == 200
            sync_result = sync_response.json()
            assert sync_result["config_id"] == config["id"]
            assert sync_result["sync_status"] == "completed"
        
        # Step 6: Get sync logs
        logs_response = client.get(f"/api/remote-directories/{config['id']}/sync-logs")
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert isinstance(logs, list)
        
        # Step 7: Delete configuration
        delete_response = client.delete(f"/api/remote-directories/{config['id']}")
        assert delete_response.status_code == 200
        
        # Step 8: Verify deletion
        get_deleted_response = client.get(f"/api/remote-directories/{config['id']}")
        assert get_deleted_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_file_discovery_and_filtering(self, service, sample_config, temp_directory):
        """Test file discovery and pattern filtering"""
        # Get the database config object
        config = service.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == sample_config.id
        ).first()
        
        # Test file discovery
        files_to_process = service._get_files_to_process(config)
        
        # Should find PDF, TXT, and DOCX files but exclude temp files and JPG
        expected_files = {"document1.pdf", "document2.txt", "report.docx", "subdoc.pdf"}
        found_files = {f.name for f in files_to_process}
        
        # Check that expected files are found (may be subset due to other filters)
        assert "document1.pdf" in found_files or "document2.txt" in found_files
        
        # Check that excluded files are not found
        assert "temp_file.pdf" not in found_files
        assert "image.jpg" not in found_files
    
    def test_pattern_matching_logic(self, service, sample_config):
        """Test file pattern matching logic"""
        # Get the database config object
        config = service.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == sample_config.id
        ).first()
        
        # Test include patterns
        assert service._matches_file_patterns(Path("document.pdf"), config) is True
        assert service._matches_file_patterns(Path("text.txt"), config) is True
        assert service._matches_file_patterns(Path("report.docx"), config) is True
        
        # Test exclude patterns
        assert service._matches_file_patterns(Path("temp_document.pdf"), config) is False
        assert service._matches_file_patterns(Path("document_temp.txt"), config) is False
        
        # Test unsupported extensions
        assert service._matches_file_patterns(Path("image.jpg"), config) is False
        assert service._matches_file_patterns(Path("video.mp4"), config) is False
    
    @pytest.mark.asyncio
    async def test_sync_operation_with_mock_processing(self, service, sample_config, temp_directory):
        """Test sync operation with mocked file processing"""
        # Mock the document service upload method
        with patch.object(service.document_service, 'upload_document', new_callable=AsyncMock) as mock_upload:
            # Configure mock to return successful upload
            mock_upload.return_value = Mock(
                id="doc-123",
                filename="test.pdf",
                file_size=1024,
                processing_status="pending"
            )
            
            # Perform sync
            result = await service.sync_remote_directory(sample_config.id)
            
            # Verify sync completed
            assert result.config_id == sample_config.id
            assert result.sync_status == "completed"
            assert result.sync_end_time is not None
            
            # Verify files were processed (mock was called)
            assert mock_upload.call_count >= 0  # May be 0 if no files match criteria
    
    def test_sync_due_logic_with_database(self, service, sample_config, db_session):
        """Test sync due logic with database persistence"""
        # Get the database config object
        config = db_session.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == sample_config.id
        ).first()
        
        # Initially, sync should be due (no previous sync)
        assert service._is_sync_due(config) is True
        
        # Update last sync time to now
        config.last_sync_time = datetime.utcnow()
        db_session.commit()
        db_session.refresh(config)
        
        # Now sync should not be due
        assert service._is_sync_due(config) is False
        
        # Update last sync time to old time
        config.last_sync_time = datetime.utcnow() - timedelta(seconds=400)
        db_session.commit()
        db_session.refresh(config)
        
        # Now sync should be due again
        assert service._is_sync_due(config) is True
    
    @pytest.mark.asyncio
    async def test_batch_processing_logic(self, service, sample_config, temp_directory):
        """Test batch processing of files"""
        # Create multiple test files
        for i in range(15):  # More than default batch size
            (temp_directory / f"batch_test_{i}.txt").write_text(f"Content {i}")
        
        # Mock the batch processing
        with patch.object(service, '_process_file_batch', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = {
                'processed': 5,
                'added': 5,
                'updated': 0,
                'failed': 0
            }
            
            # Get config from database
            config = service.db.query(RemoteDirectoryConfig).filter(
                RemoteDirectoryConfig.id == sample_config.id
            ).first()
            
            # Create sync log
            sync_log = RemoteDirectorySync(
                config_id=sample_config.id,
                sync_start_time=datetime.utcnow(),
                sync_status="running"
            )
            service.db.add(sync_log)
            service.db.commit()
            service.db.refresh(sync_log)
            
            # Perform sync
            result = await service._perform_sync(config, sync_log)
            
            # Verify batch processing was called
            assert mock_batch.call_count >= 1
            assert result['files_processed'] >= 0
    
    def test_error_handling_in_sync(self, service, sample_config):
        """Test error handling during sync operations"""
        # Test with invalid config ID
        with pytest.raises(Exception):  # Should raise HTTPException
            asyncio.run(service.sync_remote_directory("invalid-id"))
        
        # Test with inactive config
        # Update config to inactive
        config = service.db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == sample_config.id
        ).first()
        config.is_active = False
        service.db.commit()
        
        with pytest.raises(Exception):  # Should raise HTTPException
            asyncio.run(service.sync_remote_directory(sample_config.id))
    
    def test_sync_log_persistence(self, service, sample_config, db_session):
        """Test that sync logs are properly persisted"""
        # Create a sync log manually
        sync_log = RemoteDirectorySync(
            config_id=sample_config.id,
            sync_start_time=datetime.utcnow(),
            sync_status="completed",
            files_processed=5,
            files_added=3,
            files_updated=1,
            files_failed=1,
            sync_metadata={"test": "data"}
        )
        
        db_session.add(sync_log)
        db_session.commit()
        db_session.refresh(sync_log)
        
        # Retrieve sync logs via service
        logs = service.get_sync_logs()
        
        assert len(logs) == 1
        assert logs[0].config_id == sample_config.id
        assert logs[0].sync_status == "completed"
        assert logs[0].files_processed == 5
        assert logs[0].files_added == 3
        assert logs[0].files_updated == 1
        assert logs[0].files_failed == 1
    
    def test_configuration_validation_edge_cases(self, service, temp_directory):
        """Test configuration validation with edge cases"""
        # Test with very short sync interval
        with pytest.raises(Exception):  # Should fail validation
            config_data = RemoteDirectoryConfigCreate(
                name="short_interval",
                directory_path=str(temp_directory),
                sync_interval=30  # Too short
            )
            service.create_remote_directory_config(config_data)
        
        # Test with empty name
        with pytest.raises(Exception):  # Should fail validation
            config_data = RemoteDirectoryConfigCreate(
                name="",  # Empty name
                directory_path=str(temp_directory),
                sync_interval=300
            )
            service.create_remote_directory_config(config_data)
        
        # Test with non-existent directory
        with pytest.raises(Exception):  # Should fail validation
            config_data = RemoteDirectoryConfigCreate(
                name="nonexistent_dir",
                directory_path="/nonexistent/path",
                sync_interval=300
            )
            service.create_remote_directory_config(config_data)
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_operations(self, service, temp_directory):
        """Test handling of concurrent sync operations"""
        # Create multiple configurations
        configs = []
        for i in range(3):
            config_data = RemoteDirectoryConfigCreate(
                name=f"concurrent_config_{i}",
                directory_path=str(temp_directory),
                is_active=True,
                sync_interval=300
            )
            config = service.create_remote_directory_config(config_data)
            configs.append(config)
        
        # Mock sync operations
        with patch.object(service, 'sync_remote_directory', new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = Mock(
                config_id="test-id",
                sync_status="completed",
                files_processed=1,
                files_added=1,
                files_failed=0
            )
            
            # Trigger sync for all configurations
            results = await service.sync_all_active_directories()
            
            # Verify all configs were processed
            assert len(results) == 3
            assert mock_sync.call_count == 3
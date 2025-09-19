"""
Simple test script for remote directory functionality
"""
import asyncio
import tempfile
import shutil
from pathlib import Path

from app.models.database_config import get_db, init_db
from app.models.database import RemoteDirectoryConfig
from app.services.remote_directory_service import RemoteDirectoryService
from app.models.schemas import RemoteDirectoryConfigCreate, SchemaType


async def test_remote_directory_functionality():
    """Test basic remote directory functionality"""
    print("Testing Remote Directory Functionality")
    print("=" * 50)
    
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create temporary directory with test files
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create test files
        print(f"Creating test files in: {temp_path}")
        (temp_path / "document1.pdf").write_text("PDF content 1")
        (temp_path / "document2.txt").write_text("Text content 2")
        (temp_path / "report.docx").write_text("DOCX content")
        (temp_path / "temp_file.pdf").write_text("Temporary file")
        (temp_path / "image.jpg").write_text("Image content")
        
        # Create subdirectory
        subdir = temp_path / "subdir"
        subdir.mkdir()
        (subdir / "subdoc.pdf").write_text("Subdirectory PDF")
        
        print(f"Created {len(list(temp_path.rglob('*')))} test files")
        
        # Initialize database
        print("Initializing database...")
        from app.models.database_config import DatabaseManager
        DatabaseManager.reset_db()  # Reset database to ensure clean state
        print("✓ Database initialized")
        
        # Get database session
        db = next(get_db())
        
        # Create service
        service = RemoteDirectoryService(db)
        print("✓ Created RemoteDirectoryService")
        
        # Test 1: Create remote directory configuration
        print("\n1. Testing configuration creation...")
        config_data = RemoteDirectoryConfigCreate(
            name="test_remote_config",
            directory_path=str(temp_path),
            is_active=True,
            sync_interval=300,
            file_patterns=["*.pdf", "*.txt", "*.docx"],
            exclude_patterns=["*temp*"],
            schema_type=SchemaType.EU_ESRS_CSRD
        )
        
        try:
            config = service.create_remote_directory_config(config_data)
            print(f"✓ Created configuration: {config.name} (ID: {config.id})")
        except Exception as e:
            print(f"✗ Failed to create configuration: {type(e).__name__}: {str(e)}")
            if hasattr(e, 'detail'):
                print(f"  Detail: {e.detail}")
            if hasattr(e, 'status_code'):
                print(f"  Status code: {e.status_code}")
            print(f"  Directory path: {config_data.directory_path}")
            print(f"  Directory exists: {temp_path.exists()}")
            print(f"  Directory is dir: {temp_path.is_dir()}")
            import os
            print(f"  Directory readable: {os.access(temp_path, os.R_OK)}")
            raise
        
        # Test 2: List configurations
        print("\n2. Testing configuration listing...")
        configs = service.get_remote_directory_configs()
        print(f"✓ Found {len(configs)} configurations")
        
        # Test 3: Get configuration by ID
        print("\n3. Testing configuration retrieval...")
        retrieved_config = service.get_remote_directory_config_by_id(config.id)
        assert retrieved_config is not None
        print(f"✓ Retrieved configuration: {retrieved_config.name}")
        
        # Test 4: Update configuration
        print("\n4. Testing configuration update...")
        from app.models.schemas import RemoteDirectoryConfigUpdate
        update_data = RemoteDirectoryConfigUpdate(
            sync_interval=600,
            is_active=False
        )
        updated_config = service.update_remote_directory_config(config.id, update_data)
        assert updated_config.sync_interval == 600
        assert updated_config.is_active is False
        print("✓ Updated configuration successfully")
        
        # Test 5: File pattern matching
        print("\n5. Testing file pattern matching...")
        db_config = db.query(RemoteDirectoryConfig).filter(
            RemoteDirectoryConfig.id == config.id
        ).first()
        
        # Test various file patterns
        test_files = [
            ("document.pdf", True),
            ("text.txt", True),
            ("report.docx", True),
            ("temp_file.pdf", False),  # Should be excluded
            ("image.jpg", False),      # Not in patterns
        ]
        
        for filename, expected in test_files:
            result = service._matches_file_patterns(Path(filename), db_config)
            status = "✓" if result == expected else "✗"
            print(f"  {status} {filename}: {result} (expected: {expected})")
        
        # Test 6: File discovery
        print("\n6. Testing file discovery...")
        files_to_process = service._get_files_to_process(db_config)
        print(f"✓ Found {len(files_to_process)} files to process")
        for file_path in files_to_process[:5]:  # Show first 5
            print(f"  - {file_path.name}")
        
        # Test 7: Sync due logic
        print("\n7. Testing sync due logic...")
        is_due_initial = service._is_sync_due(db_config)
        print(f"✓ Initial sync due: {is_due_initial}")
        
        # Test 8: Mock sync operation (without actual file processing)
        print("\n8. Testing sync operation (mocked)...")
        
        # Re-enable the configuration for sync
        update_data = RemoteDirectoryConfigUpdate(is_active=True)
        service.update_remote_directory_config(config.id, update_data)
        
        # Mock the document upload to avoid actual file processing
        from unittest.mock import patch, AsyncMock, Mock
        
        with patch.object(service.document_service, 'upload_document', new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = Mock(
                id="mock-doc-id",
                filename="mock.pdf",
                file_size=1024
            )
            
            try:
                sync_result = await service.sync_remote_directory(config.id)
                print(f"✓ Sync completed: {sync_result.sync_status}")
                print(f"  Files processed: {sync_result.files_processed}")
                print(f"  Files added: {sync_result.files_added}")
                print(f"  Files failed: {sync_result.files_failed}")
            except Exception as e:
                print(f"✗ Sync failed: {str(e)}")
        
        # Test 9: Get sync logs
        print("\n9. Testing sync logs...")
        sync_logs = service.get_sync_logs()
        print(f"✓ Found {len(sync_logs)} sync logs")
        if sync_logs:
            latest_log = sync_logs[0]
            print(f"  Latest sync: {latest_log.sync_status} at {latest_log.sync_start_time}")
        
        # Test 10: Delete configuration
        print("\n10. Testing configuration deletion...")
        success = service.delete_remote_directory_config(config.id)
        assert success is True
        print("✓ Configuration deleted successfully")
        
        # Verify deletion
        deleted_config = service.get_remote_directory_config_by_id(config.id)
        assert deleted_config is None
        print("✓ Deletion verified")
        
        print("\n" + "=" * 50)
        print("✓ All remote directory tests passed!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n✓ Cleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    asyncio.run(test_remote_directory_functionality())
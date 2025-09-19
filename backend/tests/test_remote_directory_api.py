"""
Tests for remote directory API endpoints
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock, Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.schemas import SchemaType


class TestRemoteDirectoryAPI:
    """Test cases for remote directory API endpoints"""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_config_data(self, temp_directory):
        """Sample remote directory configuration data"""
        return {
            "name": "test_config",
            "directory_path": str(temp_directory),
            "is_active": True,
            "sync_interval": 300,
            "file_patterns": ["*.pdf", "*.txt"],
            "exclude_patterns": ["*temp*"],
            "schema_type": SchemaType.EU_ESRS_CSRD.value
        }
    
    def test_create_remote_directory_config_success(self, client: TestClient, sample_config_data):
        """Test successful creation of remote directory configuration via API"""
        response = client.post("/api/remote-directories/", json=sample_config_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == sample_config_data["name"]
        assert data["directory_path"] == sample_config_data["directory_path"]
        assert data["is_active"] == sample_config_data["is_active"]
        assert data["sync_interval"] == sample_config_data["sync_interval"]
        assert data["file_patterns"] == sample_config_data["file_patterns"]
        assert data["exclude_patterns"] == sample_config_data["exclude_patterns"]
        assert data["schema_type"] == sample_config_data["schema_type"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_remote_directory_config_invalid_data(self, client: TestClient):
        """Test creation with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "directory_path": "/nonexistent/path",
            "sync_interval": 30  # Too short
        }
        
        response = client.post("/api/remote-directories/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_remote_directory_config_duplicate_name(self, client: TestClient, sample_config_data):
        """Test creation with duplicate name"""
        # Create first configuration
        response1 = client.post("/api/remote-directories/", json=sample_config_data)
        assert response1.status_code == 200
        
        # Try to create another with same name
        response2 = client.post("/api/remote-directories/", json=sample_config_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    def test_get_remote_directory_configs_empty(self, client: TestClient):
        """Test retrieving configurations when none exist"""
        response = client.get("/api/remote-directories/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_remote_directory_configs_with_data(self, client: TestClient, sample_config_data):
        """Test retrieving configurations with data"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Retrieve configurations
        response = client.get("/api/remote-directories/")
        
        assert response.status_code == 200
        configs = response.json()
        assert len(configs) == 1
        assert configs[0]["id"] == created_config["id"]
    
    def test_get_remote_directory_configs_with_filters(self, client: TestClient, sample_config_data, temp_directory):
        """Test retrieving configurations with filters"""
        # Create active configuration
        active_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert active_response.status_code == 200
        
        # Create inactive configuration
        inactive_data = {
            "name": "inactive_config",
            "directory_path": str(temp_directory),
            "is_active": False,
            "sync_interval": 600
        }
        inactive_response = client.post("/api/remote-directories/", json=inactive_data)
        assert inactive_response.status_code == 200
        
        # Filter by active status
        response = client.get("/api/remote-directories/?is_active=true")
        assert response.status_code == 200
        configs = response.json()
        assert len(configs) == 1
        assert configs[0]["is_active"] is True
        
        # Filter by inactive status
        response = client.get("/api/remote-directories/?is_active=false")
        assert response.status_code == 200
        configs = response.json()
        assert len(configs) == 1
        assert configs[0]["is_active"] is False
    
    def test_get_remote_directory_config_by_id_success(self, client: TestClient, sample_config_data):
        """Test retrieving specific configuration by ID"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Retrieve by ID
        response = client.get(f"/api/remote-directories/{created_config['id']}")
        
        assert response.status_code == 200
        config = response.json()
        assert config["id"] == created_config["id"]
        assert config["name"] == sample_config_data["name"]
    
    def test_get_remote_directory_config_by_id_not_found(self, client: TestClient):
        """Test retrieving non-existent configuration"""
        response = client.get("/api/remote-directories/nonexistent-id")
        assert response.status_code == 404
    
    def test_update_remote_directory_config_success(self, client: TestClient, sample_config_data):
        """Test successful update of remote directory configuration"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Update configuration
        update_data = {
            "name": "updated_name",
            "sync_interval": 600,
            "is_active": False
        }
        
        response = client.put(f"/api/remote-directories/{created_config['id']}", json=update_data)
        
        assert response.status_code == 200
        updated_config = response.json()
        assert updated_config["name"] == "updated_name"
        assert updated_config["sync_interval"] == 600
        assert updated_config["is_active"] is False
        assert updated_config["directory_path"] == sample_config_data["directory_path"]  # Unchanged
    
    def test_update_remote_directory_config_not_found(self, client: TestClient):
        """Test updating non-existent configuration"""
        update_data = {"name": "new_name"}
        response = client.put("/api/remote-directories/nonexistent-id", json=update_data)
        assert response.status_code == 404
    
    def test_delete_remote_directory_config_success(self, client: TestClient, sample_config_data):
        """Test successful deletion of remote directory configuration"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Delete configuration
        response = client.delete(f"/api/remote-directories/{created_config['id']}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        get_response = client.get(f"/api/remote-directories/{created_config['id']}")
        assert get_response.status_code == 404
    
    def test_delete_remote_directory_config_not_found(self, client: TestClient):
        """Test deleting non-existent configuration"""
        response = client.delete("/api/remote-directories/nonexistent-id")
        assert response.status_code == 404
    
    @patch('app.services.remote_directory_service.RemoteDirectoryService.sync_remote_directory')
    def test_sync_remote_directory_success(self, mock_sync, client: TestClient, sample_config_data):
        """Test successful remote directory synchronization"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Mock sync result
        mock_sync_result = Mock()
        mock_sync_result.id = "sync-id"
        mock_sync_result.config_id = created_config["id"]
        mock_sync_result.sync_status = "completed"
        mock_sync_result.files_processed = 5
        mock_sync_result.files_added = 3
        mock_sync_result.files_failed = 0
        mock_sync_result.sync_start_time = "2023-01-01T00:00:00"
        mock_sync_result.sync_end_time = "2023-01-01T00:01:00"
        
        mock_sync.return_value = mock_sync_result
        
        # Trigger sync
        response = client.post(f"/api/remote-directories/{created_config['id']}/sync")
        
        assert response.status_code == 200
        sync_data = response.json()
        assert sync_data["config_id"] == created_config["id"]
        assert sync_data["sync_status"] == "completed"
        assert sync_data["files_processed"] == 5
        
        mock_sync.assert_called_once_with(created_config["id"])
    
    def test_sync_remote_directory_not_found(self, client: TestClient):
        """Test sync with non-existent configuration"""
        response = client.post("/api/remote-directories/nonexistent-id/sync")
        assert response.status_code == 404
    
    @patch('app.services.remote_directory_service.RemoteDirectoryService.sync_all_active_directories')
    def test_sync_all_remote_directories(self, mock_sync_all, client: TestClient, sample_config_data):
        """Test synchronization of all active directories"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Mock sync results
        mock_sync_result = Mock()
        mock_sync_result.id = "sync-id"
        mock_sync_result.config_id = created_config["id"]
        mock_sync_result.sync_status = "completed"
        mock_sync_result.files_processed = 5
        mock_sync_result.files_added = 3
        mock_sync_result.files_failed = 0
        
        mock_sync_all.return_value = [mock_sync_result]
        
        # Trigger sync all
        response = client.post("/api/remote-directories/sync-all")
        
        assert response.status_code == 200
        sync_results = response.json()
        assert len(sync_results) == 1
        assert sync_results[0]["config_id"] == created_config["id"]
        
        mock_sync_all.assert_called_once()
    
    def test_get_sync_logs_for_config(self, client: TestClient, sample_config_data):
        """Test retrieving sync logs for specific configuration"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Get sync logs (should be empty initially)
        response = client.get(f"/api/remote-directories/{created_config['id']}/sync-logs")
        
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
    
    def test_get_all_sync_logs(self, client: TestClient):
        """Test retrieving all sync logs"""
        response = client.get("/api/remote-directories/sync-logs/")
        
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
    
    def test_get_all_sync_logs_with_filters(self, client: TestClient, sample_config_data):
        """Test retrieving sync logs with filters"""
        # Create configuration
        create_response = client.post("/api/remote-directories/", json=sample_config_data)
        assert create_response.status_code == 200
        created_config = create_response.json()
        
        # Get sync logs with config filter
        response = client.get(f"/api/remote-directories/sync-logs/?config_id={created_config['id']}")
        
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        
        # Get sync logs with status filter
        response = client.get("/api/remote-directories/sync-logs/?sync_status=completed")
        
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
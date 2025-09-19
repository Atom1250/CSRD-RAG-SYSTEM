"""
Tests for document API endpoints
"""
import pytest
import tempfile
import io
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from app.models.schemas import DocumentResponse, DocumentType, ProcessingStatus


class TestDocumentAPI:
    """Test cases for document API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_document_response(self):
        """Mock document response"""
        return DocumentResponse(
            id="test-id",
            filename="test.pdf",
            file_size=1024,
            file_path="/path/to/test.pdf",
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.PENDING,
            upload_date="2024-01-01T00:00:00",
            document_metadata={"test": "metadata"}
        )
    
    def create_test_file(self, filename: str, content: bytes = b"test content"):
        """Create test file for upload"""
        return (filename, io.BytesIO(content), "application/octet-stream")
    
    @patch('app.api.documents.get_document_service')
    def test_upload_document_success(self, mock_get_service, client, mock_document_response):
        """Test successful document upload"""
        mock_service = Mock()
        mock_service.upload_document.return_value = mock_document_response
        mock_get_service.return_value = mock_service
        
        files = {"file": self.create_test_file("test.pdf")}
        
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "test-id"
        assert data["filename"] == "test.pdf"
        assert data["document_type"] == "pdf"
    
    @patch('app.api.documents.get_document_service')
    def test_upload_document_with_schema_type(self, mock_get_service, client, mock_document_response):
        """Test document upload with schema type"""
        mock_service = Mock()
        mock_service.upload_document.return_value = mock_document_response
        mock_get_service.return_value = mock_service
        
        files = {"file": self.create_test_file("test.pdf")}
        params = {"schema_type": "EU_ESRS_CSRD"}
        
        response = client.post("/api/documents/upload", files=files, params=params)
        
        assert response.status_code == status.HTTP_200_OK
        mock_service.upload_document.assert_called_once()
        # Verify schema_type was passed
        call_args = mock_service.upload_document.call_args
        assert call_args[0][1] == "EU_ESRS_CSRD"  # Second argument should be schema_type
    
    @patch('app.api.documents.get_document_service')
    def test_upload_document_validation_error(self, mock_get_service, client):
        """Test document upload with validation error"""
        from fastapi import HTTPException
        
        mock_service = Mock()
        mock_service.upload_document.side_effect = HTTPException(
            status_code=400, 
            detail="File type not supported"
        )
        mock_get_service.return_value = mock_service
        
        files = {"file": self.create_test_file("test.jpg")}
        
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "File type not supported" in response.json()["detail"]
    
    def test_upload_document_no_file(self, client):
        """Test document upload without file"""
        response = client.post("/api/documents/upload")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.api.documents.get_document_service')
    def test_get_documents_success(self, mock_get_service, client, mock_document_response):
        """Test successful document retrieval"""
        mock_service = Mock()
        mock_service.get_documents.return_value = [mock_document_response]
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/documents/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "test-id"
    
    @patch('app.api.documents.get_document_service')
    def test_get_documents_with_filters(self, mock_get_service, client):
        """Test document retrieval with filters"""
        mock_service = Mock()
        mock_service.get_documents.return_value = []
        mock_get_service.return_value = mock_service
        
        params = {
            "document_type": "pdf",
            "schema_type": "EU_ESRS_CSRD",
            "processing_status": "completed",
            "filename_contains": "test"
        }
        
        response = client.get("/api/documents/", params=params)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify filters were passed to service
        mock_service.get_documents.assert_called_once()
        filters = mock_service.get_documents.call_args[0][0]
        assert filters.document_type == DocumentType.PDF
        assert filters.filename_contains == "test"
    
    @patch('app.api.documents.get_document_service')
    def test_get_document_by_id_success(self, mock_get_service, client, mock_document_response):
        """Test successful document retrieval by ID"""
        mock_service = Mock()
        mock_service.get_document_by_id.return_value = mock_document_response
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/documents/test-id")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "test-id"
    
    @patch('app.api.documents.get_document_service')
    def test_get_document_by_id_not_found(self, mock_get_service, client):
        """Test document retrieval by ID when not found"""
        mock_service = Mock()
        mock_service.get_document_by_id.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/documents/nonexistent-id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Document not found" in response.json()["detail"]
    
    @patch('app.api.documents.get_document_service')
    def test_delete_document_success(self, mock_get_service, client):
        """Test successful document deletion"""
        mock_service = Mock()
        mock_service.delete_document.return_value = True
        mock_get_service.return_value = mock_service
        
        response = client.delete("/api/documents/test-id")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Document deleted successfully"
        assert data["document_id"] == "test-id"
    
    @patch('app.api.documents.get_document_service')
    def test_delete_document_not_found(self, mock_get_service, client):
        """Test document deletion when not found"""
        mock_service = Mock()
        mock_service.delete_document.return_value = False
        mock_get_service.return_value = mock_service
        
        response = client.delete("/api/documents/nonexistent-id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Document not found" in response.json()["detail"]
    
    @patch('app.api.documents.get_document_service')
    def test_get_document_metadata_success(self, mock_get_service, client, mock_document_response):
        """Test successful metadata retrieval"""
        mock_service = Mock()
        mock_service.get_document_by_id.return_value = mock_document_response
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/documents/test-id/metadata")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {"test": "metadata"}
    
    @patch('app.api.documents.get_document_service')
    def test_get_document_metadata_not_found(self, mock_get_service, client):
        """Test metadata retrieval when document not found"""
        mock_service = Mock()
        mock_service.get_document_by_id.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/documents/nonexistent-id/metadata")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.api.documents.get_document_service')
    def test_get_document_metadata_empty(self, mock_get_service, client):
        """Test metadata retrieval when metadata is empty"""
        mock_response = DocumentResponse(
            id="test-id",
            filename="test.pdf",
            file_size=1024,
            file_path="/path/to/test.pdf",
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.PENDING,
            upload_date="2024-01-01T00:00:00",
            document_metadata=None
        )
        
        mock_service = Mock()
        mock_service.get_document_by_id.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/documents/test-id/metadata")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {}
    
    @patch('app.api.documents.get_document_service')
    def test_update_document_metadata_success(self, mock_get_service, client, mock_document_response):
        """Test successful metadata update"""
        updated_response = mock_document_response.model_copy()
        updated_response.document_metadata = {"test": "metadata", "updated": "value"}
        
        mock_service = Mock()
        mock_service.update_document_metadata.return_value = updated_response
        mock_get_service.return_value = mock_service
        
        update_data = {"updated": "value"}
        
        response = client.put("/api/documents/test-id/metadata", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["document_metadata"]["updated"] == "value"
    
    @patch('app.api.documents.get_document_service')
    def test_update_document_metadata_not_found(self, mock_get_service, client):
        """Test metadata update when document not found"""
        mock_service = Mock()
        mock_service.update_document_metadata.return_value = None
        mock_get_service.return_value = mock_service
        
        update_data = {"test": "value"}
        
        response = client.put("/api/documents/test-id/metadata", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Document not found" in response.json()["detail"]
    
    def test_api_documentation_includes_documents(self, client):
        """Test that API documentation includes document endpoints"""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        
        # Test OpenAPI schema includes document endpoints
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        # Check that document endpoints are included
        assert "/api/documents/upload" in paths
        assert "/api/documents/" in paths
        assert "/api/documents/{document_id}" in paths
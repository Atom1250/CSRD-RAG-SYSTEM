"""
Tests for Schema API endpoints
"""
import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from main import app
from app.models.schemas import SchemaType


class TestSchemaAPI:
    """Test cases for Schema API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for API requests"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_schema_data(self):
        """Sample schema data for testing"""
        return {
            "schema_name": "Test API Schema",
            "version": "1.0",
            "elements": [
                {
                    "code": "API-1",
                    "name": "API Test Element",
                    "description": "Test element for API testing",
                    "requirements": ["API requirement 1"],
                    "children": []
                }
            ]
        }
    
    def test_get_schema_types(self, client):
        """Test getting available schema types"""
        response = client.get("/api/schemas/types")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert SchemaType.EU_ESRS_CSRD.value in data
        assert SchemaType.UK_SRD.value in data
    
    def test_initialize_schemas_success(self, client, sample_schema_data):
        """Test successful schema initialization"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_schema_data, f)
            temp_file = Path(f.name)
        
        try:
            with patch('app.services.schema_service.SchemaService.initialize_schemas') as mock_init:
                mock_init.return_value = {
                    SchemaType.EU_ESRS_CSRD.value: 5,
                    SchemaType.UK_SRD.value: 3
                }
                
                response = client.post("/api/schemas/initialize")
                
                assert response.status_code == 200
                data = response.json()
                assert data[SchemaType.EU_ESRS_CSRD.value] == 5
                assert data[SchemaType.UK_SRD.value] == 3
        finally:
            temp_file.unlink()
    
    def test_initialize_schemas_error(self, client):
        """Test schema initialization with error"""
        with patch('app.services.schema_service.SchemaService.initialize_schemas') as mock_init:
            mock_init.side_effect = Exception("Schema file not found")
            
            response = client.post("/api/schemas/initialize")
            
            assert response.status_code == 500
            assert "Failed to initialize schemas" in response.json()["detail"]
    
    def test_get_schema_elements_success(self, client):
        """Test getting schema elements successfully"""
        mock_elements = [
            {
                "id": "element-1",
                "schema_type": SchemaType.EU_ESRS_CSRD,
                "element_code": "E1",
                "element_name": "Climate Change",
                "description": "Climate related disclosures",
                "parent_element_id": None,
                "requirements": ["GHG emissions"],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "children": None
            }
        ]
        
        with patch('app.services.schema_service.SchemaService.get_schema_elements') as mock_get:
            mock_get.return_value = mock_elements
            
            response = client.get(f"/api/schemas/elements/{SchemaType.EU_ESRS_CSRD.value}")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["element_code"] == "E1"
    
    def test_get_schema_elements_with_parent(self, client):
        """Test getting schema elements with parent filter"""
        with patch('app.services.schema_service.SchemaService.get_schema_elements') as mock_get:
            mock_get.return_value = []
            
            response = client.get(
                f"/api/schemas/elements/{SchemaType.EU_ESRS_CSRD.value}?parent_id=parent-1"
            )
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(SchemaType.EU_ESRS_CSRD, "parent-1")
    
    def test_classify_document_success(self, client):
        """Test successful document classification"""
        document_id = "test-doc-1"
        
        with patch('app.services.schema_service.SchemaService.classify_text_chunks') as mock_classify:
            mock_classify.return_value = 5
            
            response = client.post(f"/api/schemas/classify/document/{document_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == document_id
            assert data["classified_chunks"] == 5
    
    def test_classify_document_error(self, client):
        """Test document classification with error"""
        document_id = "test-doc-1"
        
        with patch('app.services.schema_service.SchemaService.classify_text_chunks') as mock_classify:
            mock_classify.side_effect = Exception("Document not found")
            
            response = client.post(f"/api/schemas/classify/document/{document_id}")
            
            assert response.status_code == 500
            assert "Failed to classify document" in response.json()["detail"]
    
    def test_update_document_schema_success(self, client):
        """Test successful document schema update"""
        document_id = "test-doc-1"
        schema_type = SchemaType.EU_ESRS_CSRD
        
        with patch('app.services.schema_service.SchemaService.update_document_schema_classification') as mock_update:
            mock_update.return_value = True
            
            response = client.put(f"/api/schemas/document/{document_id}/schema/{schema_type.value}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == document_id
            assert data["schema_type"] == schema_type.value
    
    def test_update_document_schema_not_found(self, client):
        """Test document schema update for non-existent document"""
        document_id = "nonexistent-doc"
        schema_type = SchemaType.EU_ESRS_CSRD
        
        with patch('app.services.schema_service.SchemaService.update_document_schema_classification') as mock_update:
            mock_update.return_value = False
            
            response = client.put(f"/api/schemas/document/{document_id}/schema/{schema_type.value}")
            
            assert response.status_code == 404
            assert "Document not found" in response.json()["detail"]
    
    def test_get_unclassified_documents(self, client):
        """Test getting unclassified documents"""
        from datetime import datetime
        from app.models.schemas import DocumentType, ProcessingStatus
        
        mock_documents = [
            Mock(
                id="doc-1", 
                filename="test1.pdf", 
                schema_type=None,
                document_type=DocumentType.PDF,
                file_size=1000,
                upload_date=datetime.now(),
                processing_status=ProcessingStatus.COMPLETED,
                file_path="/test/path1.pdf",
                document_metadata={}
            ),
            Mock(
                id="doc-2", 
                filename="test2.pdf", 
                schema_type=None,
                document_type=DocumentType.PDF,
                file_size=2000,
                upload_date=datetime.now(),
                processing_status=ProcessingStatus.COMPLETED,
                file_path="/test/path2.pdf",
                document_metadata={}
            )
        ]
        
        with patch('app.services.schema_service.SchemaService.get_unclassified_documents') as mock_get:
            mock_get.return_value = mock_documents
            
            response = client.get("/api/schemas/unclassified")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
    
    def test_map_client_requirements_success(self, client):
        """Test successful client requirements mapping"""
        schema_type = SchemaType.EU_ESRS_CSRD
        requirements_text = "We need climate change emissions reporting"
        
        mock_mappings = [
            {
                "schema_element_id": "element-1",
                "element_code": "E1",
                "element_name": "Climate Change",
                "confidence_score": 0.8
            }
        ]
        
        with patch('app.services.schema_service.SchemaService.get_schema_mapping_for_requirements') as mock_map:
            mock_map.return_value = mock_mappings
            
            response = client.post(
                f"/api/schemas/map-requirements/{schema_type.value}",
                params={"requirements_text": requirements_text}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["schema_type"] == schema_type.value
            assert data["total_mappings"] == 1
            assert len(data["mappings"]) == 1
    
    def test_map_client_requirements_empty_text(self, client):
        """Test client requirements mapping with empty text"""
        schema_type = SchemaType.EU_ESRS_CSRD
        
        response = client.post(
            f"/api/schemas/map-requirements/{schema_type.value}",
            params={"requirements_text": ""}
        )
        
        assert response.status_code == 400
        assert "Requirements text cannot be empty" in response.json()["detail"]
    
    def test_get_schema_statistics(self, client):
        """Test getting schema statistics"""
        schema_type = SchemaType.EU_ESRS_CSRD
        
        with patch('app.services.schema_service.SchemaService.get_schema_elements') as mock_elements:
            mock_elements.return_value = [Mock(), Mock(), Mock()]  # 3 elements
            
            with patch('app.services.schema_service.SchemaService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                mock_service.get_schema_elements.return_value = [Mock(), Mock(), Mock()]
                
                # Mock the database session
                mock_db = Mock()
                mock_service.db = mock_db
                mock_db.query.return_value.filter.return_value.count.return_value = 10  # documents
                mock_db.query.return_value.join.return_value.filter.return_value.count.side_effect = [8, 10]  # chunks
                
                response = client.get(f"/api/schemas/stats/{schema_type.value}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["schema_type"] == schema_type.value
                assert data["total_elements"] == 3
                assert data["documents_using_schema"] == 10
                assert data["classification_rate_percent"] == 80.0


class TestSchemaAPIIntegration:
    """Integration tests for Schema API with real database"""
    
    @pytest.fixture
    def client(self):
        """Test client for API requests"""
        return TestClient(app)
    
    def test_full_schema_workflow(self, client):
        """Test complete schema workflow from initialization to classification"""
        # This would require a real database setup and schema files
        # For now, we'll test the API structure
        
        # Test getting schema types
        response = client.get("/api/schemas/types")
        assert response.status_code == 200
        
        # Test getting unclassified documents (should work even with empty DB)
        response = client.get("/api/schemas/unclassified")
        assert response.status_code == 200
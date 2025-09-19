"""
Tests for search API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from main import app
from app.models.schemas import SearchResult, DocumentType, SchemaType


class TestSearchAPI:
    """Test cases for search API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing"""
        return [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Climate change adaptation strategies for business resilience",
                relevance_score=0.95,
                document_filename="climate_report.pdf",
                schema_elements=["E1", "E1-1"]
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc2",
                content="Greenhouse gas emissions reporting requirements",
                relevance_score=0.87,
                document_filename="emissions_guide.pdf",
                schema_elements=["E1", "E1-2"]
            )
        ]
    
    def test_search_documents_post(self, client, sample_search_results):
        """Test POST /api/search/ endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_documents = AsyncMock(return_value=sample_search_results)
            mock_get_service.return_value = mock_service
            
            request_data = {
                "query": "climate change adaptation",
                "top_k": 10,
                "min_relevance_score": 0.5,
                "enable_reranking": True,
                "document_type": "pdf",
                "schema_type": "EU_ESRS_CSRD"
            }
            
            response = client.post("/api/search/", json=request_data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
            assert results[0]["chunk_id"] == "chunk1"
            assert results[0]["relevance_score"] == 0.95
            assert results[0]["document_filename"] == "climate_report.pdf"
    
    def test_search_documents_get(self, client, sample_search_results):
        """Test GET /api/search/ endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_documents = AsyncMock(return_value=sample_search_results)
            mock_get_service.return_value = mock_service
            
            params = {
                "query": "climate change",
                "top_k": 5,
                "min_relevance_score": 0.7,
                "enable_reranking": True,
                "document_type": "pdf"
            }
            
            response = client.get("/api/search/", params=params)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
            assert results[0]["chunk_id"] == "chunk1"
    
    def test_search_documents_validation_error(self, client):
        """Test search with invalid parameters"""
        # Empty query
        response = client.post("/api/search/", json={"query": ""})
        assert response.status_code == 422
        
        # Invalid top_k
        response = client.post("/api/search/", json={"query": "test", "top_k": 0})
        assert response.status_code == 422
        
        # Invalid relevance score
        response = client.post("/api/search/", json={"query": "test", "min_relevance_score": 1.5})
        assert response.status_code == 422
    
    def test_search_with_embedding(self, client, sample_search_results):
        """Test POST /api/search/embedding endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_with_custom_embedding = AsyncMock(return_value=sample_search_results)
            mock_get_service.return_value = mock_service
            
            request_data = {
                "query_embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "top_k": 10,
                "min_relevance_score": 0.0,
                "document_type": "pdf"
            }
            
            response = client.post("/api/search/embedding", json=request_data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
            assert results[0]["chunk_id"] == "chunk1"
    
    def test_search_by_schema_elements(self, client, sample_search_results):
        """Test POST /api/search/schema endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_by_schema_elements = AsyncMock(return_value=sample_search_results)
            mock_get_service.return_value = mock_service
            
            request_data = {
                "schema_elements": ["E1", "E1-1"],
                "top_k": 10,
                "schema_type": "EU_ESRS_CSRD"
            }
            
            response = client.post("/api/search/schema", json=request_data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
            assert results[0]["schema_elements"] == ["E1", "E1-1"]
    
    def test_find_similar_chunks(self, client, sample_search_results):
        """Test POST /api/search/similar endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_similar_to_chunk = AsyncMock(return_value=sample_search_results)
            mock_get_service.return_value = mock_service
            
            request_data = {
                "chunk_id": "reference_chunk_id",
                "top_k": 5,
                "exclude_same_document": True
            }
            
            response = client.post("/api/search/similar", json=request_data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
    
    def test_get_search_suggestions(self, client):
        """Test GET /api/search/suggestions endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_search_suggestions = AsyncMock(return_value=[
                "climate change adaptation",
                "climate change mitigation",
                "climate risk assessment"
            ])
            mock_get_service.return_value = mock_service
            
            params = {
                "partial_query": "climate",
                "max_suggestions": 5
            }
            
            response = client.get("/api/search/suggestions", params=params)
            
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "climate"
            assert len(data["suggestions"]) == 3
            assert "climate change adaptation" in data["suggestions"]
    
    def test_generate_query_embedding(self, client):
        """Test POST /api/search/embedding/generate endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_query_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_get_service.return_value = mock_service
            
            params = {"query": "climate change adaptation"}
            
            response = client.post("/api/search/embedding/generate", params=params)
            
            assert response.status_code == 200
            embedding = response.json()
            assert embedding == [0.1, 0.2, 0.3]
    
    def test_generate_query_embedding_failure(self, client):
        """Test embedding generation failure"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_query_embedding = AsyncMock(return_value=None)
            mock_get_service.return_value = mock_service
            
            params = {"query": "test query"}
            
            response = client.post("/api/search/embedding/generate", params=params)
            
            assert response.status_code == 500
            assert "Failed to generate embedding" in response.json()["detail"]
    
    def test_get_search_performance_metrics(self, client):
        """Test GET /api/search/performance endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_search_performance_metrics = AsyncMock(return_value={
                "query": "test query",
                "total_time_ms": 150.5,
                "embedding_time_ms": 25.3,
                "vector_search_time_ms": 125.2,
                "results_count": 5,
                "avg_relevance_score": 0.85,
                "top_relevance_score": 0.95,
                "embedding_dimension": 384
            })
            mock_get_service.return_value = mock_service
            
            params = {
                "query": "test query",
                "top_k": 10
            }
            
            response = client.get("/api/search/performance", params=params)
            
            assert response.status_code == 200
            metrics = response.json()
            assert metrics["query"] == "test query"
            assert metrics["total_time_ms"] == 150.5
            assert metrics["results_count"] == 5
            assert metrics["embedding_dimension"] == 384
    
    def test_get_search_performance_metrics_error(self, client):
        """Test performance metrics with error"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_search_performance_metrics = AsyncMock(return_value={
                "error": "Vector service unavailable"
            })
            mock_get_service.return_value = mock_service
            
            params = {"query": "test query"}
            
            response = client.get("/api/search/performance", params=params)
            
            assert response.status_code == 500
            assert "Vector service unavailable" in response.json()["detail"]
    
    def test_get_search_statistics(self, client):
        """Test GET /api/search/statistics endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_search_statistics.return_value = {
                "total_documents": 100,
                "total_chunks": 500,
                "chunks_with_embeddings": 450,
                "completed_documents": 95,
                "embedding_coverage": 90.0,
                "completion_rate": 95.0,
                "avg_chunk_size": 750.0,
                "document_types": {"pdf": 60, "docx": 30, "txt": 10},
                "schema_types": {"EU_ESRS_CSRD": 70, "UK_SRD": 30},
                "processing_status": {"completed": 95, "processing": 3, "pending": 1, "failed": 1},
                "searchable_documents": True,
                "vector_service_available": True
            }
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/search/statistics")
            
            assert response.status_code == 200
            stats = response.json()
            assert stats["total_documents"] == 100
            assert stats["embedding_coverage"] == 90.0
            assert stats["searchable_documents"] is True
            assert stats["vector_service_available"] is True
    
    def test_search_health_check(self, client):
        """Test GET /api/search/health endpoint"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_search_statistics.return_value = {
                "vector_service_available": True,
                "searchable_documents": True,
                "total_documents": 100,
                "chunks_with_embeddings": 450,
                "embedding_coverage": 90.0
            }
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/search/health")
            
            assert response.status_code == 200
            health = response.json()
            assert health["status"] == "healthy"
            assert health["vector_service_available"] is True
            assert health["searchable_documents"] is True
            assert health["total_documents"] == 100
    
    def test_search_health_check_degraded(self, client):
        """Test health check when vector service is unavailable"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_search_statistics.return_value = {
                "vector_service_available": False,
                "searchable_documents": False,
                "total_documents": 100,
                "chunks_with_embeddings": 0,
                "embedding_coverage": 0.0
            }
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/search/health")
            
            assert response.status_code == 200
            health = response.json()
            assert health["status"] == "degraded"
            assert health["vector_service_available"] is False
            assert health["searchable_documents"] is False
    
    def test_search_health_check_error(self, client):
        """Test health check with exception"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_search_statistics.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/search/health")
            
            assert response.status_code == 200
            health = response.json()
            assert health["status"] == "unhealthy"
            assert "Database error" in health["error"]
            assert health["vector_service_available"] is False
    
    def test_search_service_exception_handling(self, client):
        """Test API error handling when search service fails"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_documents = AsyncMock(side_effect=Exception("Search service error"))
            mock_get_service.return_value = mock_service
            
            request_data = {
                "query": "test query",
                "top_k": 10
            }
            
            response = client.post("/api/search/", json=request_data)
            
            assert response.status_code == 500
            assert "Search failed" in response.json()["detail"]
    
    def test_search_parameter_validation(self, client):
        """Test comprehensive parameter validation"""
        # Test query length limits
        long_query = "a" * 1001
        response = client.get("/api/search/", params={"query": long_query})
        assert response.status_code == 422
        
        # Test top_k limits
        response = client.get("/api/search/", params={"query": "test", "top_k": 101})
        assert response.status_code == 422
        
        # Test relevance score limits
        response = client.get("/api/search/", params={"query": "test", "min_relevance_score": -0.1})
        assert response.status_code == 422
        
        # Test suggestions query length
        response = client.get("/api/search/suggestions", params={"partial_query": "a"})
        assert response.status_code == 422
        
        # Test max_suggestions limits
        response = client.get("/api/search/suggestions", params={"partial_query": "test", "max_suggestions": 21})
        assert response.status_code == 422
    
    def test_search_with_all_filters(self, client, sample_search_results):
        """Test search with all possible filters"""
        with patch('app.api.search.get_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_documents = AsyncMock(return_value=sample_search_results)
            mock_get_service.return_value = mock_service
            
            request_data = {
                "query": "sustainability reporting",
                "top_k": 20,
                "min_relevance_score": 0.3,
                "enable_reranking": False,
                "document_type": "pdf",
                "schema_type": "EU_ESRS_CSRD",
                "processing_status": "completed",
                "filename_contains": "report"
            }
            
            response = client.post("/api/search/", json=request_data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
            
            # Verify the service was called with correct filters
            mock_service.search_documents.assert_called_once()
            call_args = mock_service.search_documents.call_args
            assert call_args[1]["query"] == "sustainability reporting"
            assert call_args[1]["top_k"] == 20
            assert call_args[1]["min_relevance_score"] == 0.3
            assert call_args[1]["enable_reranking"] is False
            
            filters = call_args[1]["filters"]
            assert filters.document_type == DocumentType.PDF
            assert filters.schema_type == SchemaType.EU_ESRS_CSRD
            assert filters.filename_contains == "report"
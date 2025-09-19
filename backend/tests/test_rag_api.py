"""
Tests for RAG API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from main import app
from app.services.rag_service import RAGService, AIModelType
from app.models.schemas import RAGResponseResponse
from app.api.rag import get_rag_service


class TestRAGAPI:
    """Test RAG API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAG service"""
        service = Mock(spec=RAGService)
        service.generate_rag_response = AsyncMock()
        service.batch_generate_responses = AsyncMock()
        service.get_available_models = Mock()
        service.get_model_status = Mock()
        service.validate_response_quality = AsyncMock()
        return service
    
    def test_generate_rag_response_success(self, client):
        """Test successful RAG response generation"""
        mock_response = RAGResponseResponse(
            id="test_response_123",
            query="What is CSRD?",
            response_text="CSRD is the Corporate Sustainability Reporting Directive...",
            model_used="openai_gpt35",
            confidence_score=0.85,
            source_chunks=["chunk1", "chunk2"],
            generation_timestamp=datetime.utcnow()
        )
        
        def mock_get_rag_service():
            mock_service = Mock()
            mock_service.generate_rag_response = AsyncMock(return_value=mock_response)
            return mock_service
        
        app.dependency_overrides[get_rag_service] = mock_get_rag_service
        
        try:
            response = client.post(
                "/api/rag/query",
                json={
                    "question": "What is CSRD?",
                    "model_type": "openai_gpt35",
                    "max_context_chunks": 10,
                    "min_relevance_score": 0.3
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["query"] == "What is CSRD?"
            assert data["response_text"] == "CSRD is the Corporate Sustainability Reporting Directive..."
            assert data["model_used"] == "openai_gpt35"
            assert data["confidence_score"] == 0.85
            assert len(data["source_chunks"]) == 2
        finally:
            app.dependency_overrides.clear()
    
    def test_generate_rag_response_validation_error(self, client):
        """Test RAG response generation with validation error"""
        response = client.post(
            "/api/rag/query",
            json={
                "question": "",  # Empty question should fail validation
                "model_type": "openai_gpt35"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_rag_response_service_error(self, client):
        """Test RAG response generation with service error"""
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_rag_response = AsyncMock(side_effect=Exception("Service error"))
            mock_get_service.return_value = mock_service
            
            response = client.post(
                "/api/rag/query",
                json={
                    "question": "What is CSRD?",
                    "model_type": "openai_gpt35"
                }
            )
            
            assert response.status_code == 500
            assert "Service error" in response.json()["detail"]
    
    def test_batch_generate_responses_success(self, client):
        """Test successful batch RAG response generation"""
        mock_responses = [
            RAGResponseResponse(
                id="batch_response_1",
                query="Question 1",
                response_text="Response 1",
                model_used="openai_gpt35",
                confidence_score=0.8,
                source_chunks=["chunk1"],
                generation_timestamp=datetime.utcnow()
            ),
            RAGResponseResponse(
                id="batch_response_2",
                query="Question 2",
                response_text="Response 2",
                model_used="openai_gpt35",
                confidence_score=0.7,
                source_chunks=["chunk2"],
                generation_timestamp=datetime.utcnow()
            )
        ]
        
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.batch_generate_responses = AsyncMock(return_value=mock_responses)
            mock_get_service.return_value = mock_service
            
            response = client.post(
                "/api/rag/batch-query",
                json={
                    "questions": ["Question 1", "Question 2"],
                    "model_type": "openai_gpt35",
                    "max_concurrent": 2
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2
            assert data[0]["query"] == "Question 1"
            assert data[1]["query"] == "Question 2"
    
    def test_batch_generate_responses_validation_error(self, client):
        """Test batch RAG response generation with validation error"""
        response = client.post(
            "/api/rag/batch-query",
            json={
                "questions": [],  # Empty questions list should fail validation
                "model_type": "openai_gpt35"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_batch_generate_responses_too_many_questions(self, client):
        """Test batch RAG response generation with too many questions"""
        response = client.post(
            "/api/rag/batch-query",
            json={
                "questions": [f"Question {i}" for i in range(15)],  # More than max allowed
                "model_type": "openai_gpt35"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_available_models_success(self, client):
        """Test getting available models"""
        mock_models = [
            {
                "type": "openai_gpt4",
                "provider": "OpenAI",
                "model": "gpt-4",
                "available": True,
                "capabilities": ["text_generation", "reasoning"],
                "max_tokens": 4096
            },
            {
                "type": "openai_gpt35",
                "provider": "OpenAI",
                "model": "gpt-3.5-turbo",
                "available": True,
                "capabilities": ["text_generation"],
                "max_tokens": 2048
            }
        ]
        
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_available_models = Mock(return_value=mock_models)
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/rag/models")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2
            assert data[0]["type"] == "openai_gpt4"
            assert data[1]["type"] == "openai_gpt35"
    
    def test_get_model_status_success(self, client):
        """Test getting model status"""
        mock_status = {
            "openai_gpt4": {
                "available": True,
                "info": {"provider": "OpenAI", "model": "gpt-4"}
            },
            "openai_gpt35": {
                "available": True,
                "info": {"provider": "OpenAI", "model": "gpt-3.5-turbo"}
            },
            "anthropic_claude": {
                "available": False,
                "info": {"provider": "Anthropic", "model": "claude-3-sonnet"}
            }
        }
        
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_model_status = Mock(return_value=mock_status)
            mock_service.default_model = AIModelType.OPENAI_GPT35
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/rag/models/status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "models" in data
            assert "default_model" in data
            assert "available_count" in data
            assert data["default_model"] == "openai_gpt35"
            assert data["available_count"] == 2
    
    def test_validate_response_quality_success(self, client):
        """Test response quality validation"""
        response = client.post(
            "/api/rag/validate-quality",
            json={
                "response_id": "test_response_123",
                "expected_topics": ["sustainability", "reporting"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response_id" in data
        assert "quality_score" in data
        assert "metrics" in data
        assert data["response_id"] == "test_response_123"
    
    def test_health_check_success(self, client):
        """Test RAG service health check"""
        mock_status = {
            "openai_gpt35": {"available": True},
            "openai_gpt4": {"available": True},
            "anthropic_claude": {"available": False}
        }
        
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_model_status = Mock(return_value=mock_status)
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/rag/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "available_models" in data
            assert "total_models" in data
            assert data["status"] == "healthy"
            assert len(data["available_models"]) == 2
    
    def test_health_check_degraded(self, client):
        """Test RAG service health check when degraded"""
        mock_status = {
            "openai_gpt35": {"available": False},
            "openai_gpt4": {"available": False},
            "anthropic_claude": {"available": False}
        }
        
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_model_status = Mock(return_value=mock_status)
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/rag/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert len(data["available_models"]) == 0
    
    def test_health_check_error(self, client):
        """Test RAG service health check with error"""
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_model_status = Mock(side_effect=Exception("Health check failed"))
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/rag/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert "error" in data
    
    def test_example_sustainability_question(self, client):
        """Test example sustainability question endpoint"""
        mock_response = RAGResponseResponse(
            id="example_response",
            query="What are the key requirements for climate change adaptation reporting under CSRD?",
            response_text="Climate change adaptation reporting under CSRD requires...",
            model_used="openai_gpt35",
            confidence_score=0.9,
            source_chunks=["chunk1", "chunk2"],
            generation_timestamp=datetime.utcnow()
        )
        
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_rag_response = AsyncMock(return_value=mock_response)
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/rag/examples/sustainability-question")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "example_question" in data
            assert "response" in data
            assert "note" in data
            assert "climate change adaptation" in data["example_question"]
    
    def test_example_batch_questions(self, client):
        """Test example batch questions endpoint"""
        mock_responses = [
            RAGResponseResponse(
                id=f"example_batch_{i}",
                query=f"Example question {i}",
                response_text=f"Example response {i}",
                model_used="openai_gpt35",
                confidence_score=0.8,
                source_chunks=[f"chunk{i}"],
                generation_timestamp=datetime.utcnow()
            )
            for i in range(3)
        ]
        
        with patch('app.api.rag.get_rag_service') as mock_get_service:
            mock_service = Mock()
            mock_service.batch_generate_responses = AsyncMock(return_value=mock_responses)
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/rag/examples/batch-questions")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "example_questions" in data
            assert "responses" in data
            assert "note" in data
            assert len(data["example_questions"]) == 3
            assert len(data["responses"]) == 3
    
    def test_rag_query_request_validation(self, client):
        """Test RAG query request validation"""
        # Test minimum question length
        response = client.post(
            "/api/rag/query",
            json={"question": ""}
        )
        assert response.status_code == 422
        
        # Test maximum question length
        long_question = "x" * 2001
        response = client.post(
            "/api/rag/query",
            json={"question": long_question}
        )
        assert response.status_code == 422
        
        # Test invalid model type
        response = client.post(
            "/api/rag/query",
            json={
                "question": "Valid question",
                "model_type": "invalid_model"
            }
        )
        assert response.status_code == 422
        
        # Test invalid max_context_chunks
        response = client.post(
            "/api/rag/query",
            json={
                "question": "Valid question",
                "max_context_chunks": 0
            }
        )
        assert response.status_code == 422
        
        response = client.post(
            "/api/rag/query",
            json={
                "question": "Valid question",
                "max_context_chunks": 51
            }
        )
        assert response.status_code == 422
        
        # Test invalid relevance score
        response = client.post(
            "/api/rag/query",
            json={
                "question": "Valid question",
                "min_relevance_score": -0.1
            }
        )
        assert response.status_code == 422
        
        response = client.post(
            "/api/rag/query",
            json={
                "question": "Valid question",
                "min_relevance_score": 1.1
            }
        )
        assert response.status_code == 422
        
        # Test invalid temperature
        response = client.post(
            "/api/rag/query",
            json={
                "question": "Valid question",
                "temperature": -0.1
            }
        )
        assert response.status_code == 422
        
        response = client.post(
            "/api/rag/query",
            json={
                "question": "Valid question",
                "temperature": 2.1
            }
        )
        assert response.status_code == 422
    
    def test_batch_rag_query_request_validation(self, client):
        """Test batch RAG query request validation"""
        # Test empty questions list
        response = client.post(
            "/api/rag/batch-query",
            json={"questions": []}
        )
        assert response.status_code == 422
        
        # Test too many questions
        response = client.post(
            "/api/rag/batch-query",
            json={"questions": [f"Question {i}" for i in range(11)]}
        )
        assert response.status_code == 422
        
        # Test invalid max_concurrent
        response = client.post(
            "/api/rag/batch-query",
            json={
                "questions": ["Question 1"],
                "max_concurrent": 0
            }
        )
        assert response.status_code == 422
        
        response = client.post(
            "/api/rag/batch-query",
            json={
                "questions": ["Question 1"],
                "max_concurrent": 6
            }
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
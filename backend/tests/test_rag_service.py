"""
Tests for RAG (Retrieval-Augmented Generation) service
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.rag_service import (
    RAGService, 
    AIModelType, 
    OpenAIProvider, 
    AnthropicProvider, 
    LocalLlamaProvider,
    get_rag_service
)
from app.models.schemas import SearchResult, RAGResponseResponse
from app.services.search_service import SearchService


class TestAIModelProviders:
    """Test AI model provider implementations"""
    
    def test_openai_provider_initialization(self):
        """Test OpenAI provider initialization"""
        provider = OpenAIProvider("gpt-3.5-turbo")
        assert provider.model_name == "gpt-3.5-turbo"
        
        model_info = provider.get_model_info()
        assert model_info["provider"] == "OpenAI"
        assert model_info["model"] == "gpt-3.5-turbo"
        assert "capabilities" in model_info
    
    def test_anthropic_provider_initialization(self):
        """Test Anthropic provider initialization"""
        provider = AnthropicProvider("claude-3-sonnet-20240229")
        assert provider.model_name == "claude-3-sonnet-20240229"
        
        model_info = provider.get_model_info()
        assert model_info["provider"] == "Anthropic"
        assert model_info["model"] == "claude-3-sonnet-20240229"
        assert "capabilities" in model_info
    
    def test_local_llama_provider_initialization(self):
        """Test Local Llama provider initialization"""
        provider = LocalLlamaProvider()
        assert not provider.is_available()  # Placeholder implementation
        
        model_info = provider.get_model_info()
        assert model_info["provider"] == "Local Llama"
        assert not model_info["available"]
    
    @pytest.mark.asyncio
    async def test_openai_provider_without_api_key(self):
        """Test OpenAI provider behavior without API key"""
        with patch('app.services.rag_service.settings.openai_api_key', None):
            provider = OpenAIProvider()
            assert not provider.is_available()
    
    @pytest.mark.asyncio
    async def test_anthropic_provider_without_api_key(self):
        """Test Anthropic provider behavior without API key"""
        with patch('app.services.rag_service.settings.anthropic_api_key', None):
            provider = AnthropicProvider()
            assert not provider.is_available()
    
    def test_openai_prompt_creation(self):
        """Test OpenAI sustainability prompt creation"""
        provider = OpenAIProvider()
        question = "What are CSRD requirements?"
        context = "CSRD requires companies to report on sustainability matters."
        
        prompt = provider._create_sustainability_prompt(question, context)
        
        assert question in prompt
        assert context in prompt
        assert "CSRD" in prompt
        assert "INSTRUCTIONS:" in prompt
    
    def test_anthropic_prompt_creation(self):
        """Test Anthropic sustainability prompt creation"""
        provider = AnthropicProvider()
        question = "What are ESRS standards?"
        context = "ESRS standards define sustainability reporting requirements."
        
        prompt = provider._create_sustainability_prompt(question, context)
        
        assert question in prompt
        assert context in prompt
        assert "<context>" in prompt
        assert "<question>" in prompt
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        provider = OpenAIProvider()
        
        # High quality response
        good_response = "Based on the CSRD regulation, companies must report on climate change adaptation measures. This includes: 1. Risk assessment 2. Adaptation strategies"
        context = "CSRD climate requirements"
        
        confidence = provider._calculate_confidence(good_response, context)
        assert 0.5 <= confidence <= 1.0
        
        # Low quality response
        poor_response = "Yes."
        poor_confidence = provider._calculate_confidence(poor_response, context)
        assert poor_confidence < confidence


class TestRAGService:
    """Test RAG service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_search_service(self):
        """Mock search service"""
        search_service = Mock(spec=SearchService)
        search_service.search_documents = AsyncMock()
        return search_service
    
    @pytest.fixture
    def rag_service(self, mock_db):
        """Create RAG service instance for testing"""
        with patch('app.services.rag_service.SearchService') as mock_search_class:
            mock_search_class.return_value = Mock(spec=SearchService)
            mock_search_class.return_value.search_documents = AsyncMock()
            
            service = RAGService(mock_db)
            return service
    
    def test_rag_service_initialization(self, mock_db):
        """Test RAG service initialization"""
        with patch('app.services.rag_service.SearchService'):
            service = RAGService(mock_db)
            
            assert service.db == mock_db
            assert isinstance(service.model_providers, dict)
            assert service.default_model == AIModelType.OPENAI_GPT35
    
    def test_model_provider_initialization(self, rag_service):
        """Test model provider initialization in RAG service"""
        providers = rag_service.model_providers
        
        # Should have all model types
        expected_types = [
            AIModelType.OPENAI_GPT4,
            AIModelType.OPENAI_GPT35,
            AIModelType.ANTHROPIC_CLAUDE,
            AIModelType.LOCAL_LLAMA
        ]
        
        for model_type in expected_types:
            assert model_type in providers
    
    def test_get_available_models(self, rag_service):
        """Test getting available models"""
        models = rag_service.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        
        for model in models:
            assert "type" in model
            assert "provider" in model
            assert "available" in model
            assert "capabilities" in model
    
    def test_get_model_status(self, rag_service):
        """Test getting model status"""
        status = rag_service.get_model_status()
        
        assert isinstance(status, dict)
        
        for model_type in AIModelType:
            assert model_type.value in status
            assert "available" in status[model_type.value]
            assert "info" in status[model_type.value]
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_no_context(self, rag_service):
        """Test RAG response generation when no context is found"""
        # Mock search service to return no results
        rag_service.search_service.search_documents.return_value = []
        
        # Mock at least one provider as available
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        rag_service.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
        
        response = await rag_service.generate_rag_response("Test question")
        
        assert isinstance(response, RAGResponseResponse)
        assert response.query == "Test question"
        assert response.confidence_score == 0.0
        assert len(response.source_chunks) == 0
        assert "couldn't find relevant information" in response.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_with_context(self, rag_service):
        """Test RAG response generation with context"""
        # Mock search results
        mock_search_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="CSRD requires sustainability reporting",
                relevance_score=0.8,
                document_filename="csrd_guide.pdf",
                schema_elements=["E1", "E2"]
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc2",
                content="ESRS standards define reporting requirements",
                relevance_score=0.7,
                document_filename="esrs_standards.pdf",
                schema_elements=["S1"]
            )
        ]
        
        rag_service.search_service.search_documents.return_value = mock_search_results
        
        # Mock AI provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.generate_response = AsyncMock(return_value=("Test response", 0.8))
        
        rag_service.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
        
        response = await rag_service.generate_rag_response("What is CSRD?")
        
        assert isinstance(response, RAGResponseResponse)
        assert response.query == "What is CSRD?"
        assert response.response_text == "Test response"
        assert response.confidence_score == 0.8
        assert len(response.source_chunks) == 2
        assert "chunk1" in response.source_chunks
        assert "chunk2" in response.source_chunks
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_model_fallback(self, rag_service):
        """Test RAG response generation with model fallback"""
        # Mock search results
        mock_search_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Test content",
                relevance_score=0.8,
                document_filename="test.pdf",
                schema_elements=[]
            )
        ]
        
        rag_service.search_service.search_documents.return_value = mock_search_results
        
        # Mock primary model as unavailable
        mock_unavailable_provider = Mock()
        mock_unavailable_provider.is_available.return_value = False
        
        # Mock fallback model as available
        mock_available_provider = Mock()
        mock_available_provider.is_available.return_value = True
        mock_available_provider.generate_response = AsyncMock(return_value=("Fallback response", 0.6))
        
        rag_service.model_providers[AIModelType.OPENAI_GPT35] = mock_unavailable_provider
        rag_service.model_providers[AIModelType.OPENAI_GPT4] = mock_available_provider
        
        response = await rag_service.generate_rag_response(
            "Test question", 
            model_type=AIModelType.OPENAI_GPT35
        )
        
        assert response.response_text == "Fallback response"
        assert response.model_used == AIModelType.OPENAI_GPT4.value
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_no_models_available(self, rag_service):
        """Test RAG response generation when no models are available"""
        # Mock all providers as unavailable
        for provider in rag_service.model_providers.values():
            provider.is_available = Mock(return_value=False)
        
        # Mock search results
        rag_service.search_service.search_documents.return_value = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Test content",
                relevance_score=0.8,
                document_filename="test.pdf",
                schema_elements=[]
            )
        ]
        
        response = await rag_service.generate_rag_response("Test question")
        
        assert "error" in response.response_text.lower()
        assert response.confidence_score == 0.0
    
    def test_prepare_context(self, rag_service):
        """Test context preparation from search results"""
        search_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="First chunk content",
                relevance_score=0.9,
                document_filename="doc1.pdf",
                schema_elements=["E1", "E2"]
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc2",
                content="Second chunk content",
                relevance_score=0.7,
                document_filename="doc2.pdf",
                schema_elements=["S1"]
            )
        ]
        
        context = rag_service._prepare_context(search_results)
        
        assert "First chunk content" in context
        assert "Second chunk content" in context
        assert "doc1.pdf" in context
        assert "doc2.pdf" in context
        assert "E1, E2" in context
        assert "S1" in context
        assert "0.9" in context
        assert "0.7" in context
    
    @pytest.mark.asyncio
    async def test_batch_generate_responses(self, rag_service):
        """Test batch response generation"""
        questions = ["Question 1", "Question 2", "Question 3"]
        
        # Mock individual response generation
        async def mock_generate_response(question, model_type=None):
            return RAGResponseResponse(
                id=f"response_{hash(question)}",
                query=question,
                response_text=f"Response to {question}",
                model_used="test_model",
                confidence_score=0.8,
                source_chunks=[],
                generation_timestamp="2024-01-01T00:00:00Z"
            )
        
        rag_service.generate_rag_response = mock_generate_response
        
        responses = await rag_service.batch_generate_responses(questions)
        
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert response.query == questions[i]
            assert f"Response to {questions[i]}" in response.response_text
    
    @pytest.mark.asyncio
    async def test_batch_generate_responses_with_errors(self, rag_service):
        """Test batch response generation with some failures"""
        questions = ["Good question", "Bad question"]
        
        async def mock_generate_response(question, model_type=None):
            if "Bad" in question:
                raise Exception("Test error")
            return RAGResponseResponse(
                id=f"response_{hash(question)}",
                query=question,
                response_text=f"Response to {question}",
                model_used="test_model",
                confidence_score=0.8,
                source_chunks=[],
                generation_timestamp="2024-01-01T00:00:00Z"
            )
        
        rag_service.generate_rag_response = mock_generate_response
        
        responses = await rag_service.batch_generate_responses(questions)
        
        assert len(responses) == 2
        assert responses[0].query == "Good question"
        assert responses[1].query == "Bad question"
        assert "error" in responses[1].response_text.lower()
    
    @pytest.mark.asyncio
    async def test_validate_response_quality(self, rag_service):
        """Test response quality validation"""
        response = RAGResponseResponse(
            id="test_response",
            query="What is CSRD?",
            response_text="CSRD is a sustainability reporting directive that requires companies to report on environmental, social, and governance matters.",
            model_used="gpt-3.5-turbo",
            confidence_score=0.8,
            source_chunks=["chunk1", "chunk2"],
            generation_timestamp="2024-01-01T00:00:00Z"
        )
        
        quality_metrics = await rag_service.validate_response_quality(
            response,
            expected_topics=["sustainability", "reporting"]
        )
        
        assert "confidence_score" in quality_metrics
        assert "has_sources" in quality_metrics
        assert "source_count" in quality_metrics
        assert "response_length" in quality_metrics
        assert "contains_regulatory_terms" in quality_metrics
        assert "topic_coverage" in quality_metrics
        assert "overall_quality" in quality_metrics
        assert "quality_score" in quality_metrics
        
        assert quality_metrics["has_sources"] is True
        assert quality_metrics["source_count"] == 2
        assert quality_metrics["contains_regulatory_terms"] is True
        assert quality_metrics["topic_coverage"] > 0.0


class TestRAGServiceFactory:
    """Test RAG service factory function"""
    
    def test_get_rag_service(self):
        """Test RAG service factory function"""
        mock_db = Mock(spec=Session)
        
        with patch('app.services.rag_service.SearchService'):
            service = get_rag_service(mock_db)
            
            assert isinstance(service, RAGService)
            assert service.db == mock_db


class TestRAGServiceIntegration:
    """Integration tests for RAG service"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_rag_flow(self):
        """Test complete RAG flow from question to response"""
        # This would be a more comprehensive integration test
        # that tests the entire flow with real or more realistic mocks
        
        mock_db = Mock(spec=Session)
        
        with patch('app.services.rag_service.SearchService') as mock_search_class:
            # Setup mock search service
            mock_search_service = Mock()
            mock_search_service.search_documents = AsyncMock(return_value=[
                SearchResult(
                    chunk_id="integration_chunk",
                    document_id="integration_doc",
                    content="Integration test content about CSRD requirements",
                    relevance_score=0.85,
                    document_filename="integration_test.pdf",
                    schema_elements=["E1"]
                )
            ])
            mock_search_class.return_value = mock_search_service
            
            # Create RAG service
            rag_service = RAGService(mock_db)
            
            # Mock a provider to be available
            mock_provider = Mock()
            mock_provider.is_available.return_value = True
            mock_provider.generate_response = AsyncMock(
                return_value=("Integration test response about CSRD", 0.85)
            )
            rag_service.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
            
            # Generate response
            response = await rag_service.generate_rag_response(
                "What are the CSRD requirements?",
                model_type=AIModelType.OPENAI_GPT35
            )
            
            # Verify response
            assert response.query == "What are the CSRD requirements?"
            assert response.response_text == "Integration test response about CSRD"
            assert response.confidence_score == 0.85
            assert len(response.source_chunks) == 1
            assert response.source_chunks[0] == "integration_chunk"
            assert response.model_used == AIModelType.OPENAI_GPT35.value
    
    @pytest.mark.asyncio
    async def test_rag_service_error_handling(self):
        """Test RAG service error handling"""
        mock_db = Mock(spec=Session)
        
        with patch('app.services.rag_service.SearchService') as mock_search_class:
            # Setup search service to raise an exception
            mock_search_service = Mock()
            mock_search_service.search_documents = AsyncMock(side_effect=Exception("Search failed"))
            mock_search_class.return_value = mock_search_service
            
            rag_service = RAGService(mock_db)
            
            response = await rag_service.generate_rag_response("Test question")
            
            assert "error" in response.response_text.lower()
            assert response.confidence_score == 0.0
            assert response.model_used == "error"


if __name__ == "__main__":
    pytest.main([__file__])
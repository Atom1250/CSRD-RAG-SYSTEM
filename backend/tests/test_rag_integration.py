"""
Integration tests for RAG service functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.rag_service import RAGService, AIModelType
from app.services.search_service import SearchService
from app.models.schemas import SearchResult, RAGResponseResponse


class TestRAGIntegration:
    """Integration tests for RAG service with search service"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_search_service(self):
        """Mock search service with realistic behavior"""
        search_service = Mock(spec=SearchService)
        
        # Mock search results for different queries
        def mock_search_documents(query, top_k=10, **kwargs):
            if "csrd" in query.lower():
                return [
                    SearchResult(
                        chunk_id="csrd_chunk_1",
                        document_id="csrd_doc_1",
                        content="The Corporate Sustainability Reporting Directive (CSRD) requires large companies to report on sustainability matters. Companies must disclose information about their environmental, social and governance impacts.",
                        relevance_score=0.92,
                        document_filename="csrd_directive_2022.pdf",
                        schema_elements=["CSRD-1", "CSRD-2"]
                    ),
                    SearchResult(
                        chunk_id="csrd_chunk_2",
                        document_id="csrd_doc_1",
                        content="CSRD reporting must follow the European Sustainability Reporting Standards (ESRS). The directive applies to companies with more than 500 employees or €40 million in net turnover.",
                        relevance_score=0.88,
                        document_filename="csrd_directive_2022.pdf",
                        schema_elements=["CSRD-3"]
                    )
                ]
            elif "esrs" in query.lower():
                return [
                    SearchResult(
                        chunk_id="esrs_chunk_1",
                        document_id="esrs_doc_1",
                        content="European Sustainability Reporting Standards (ESRS) provide detailed requirements for sustainability reporting under CSRD. ESRS covers environmental (E1-E5), social (S1-S4), and governance (G1) standards.",
                        relevance_score=0.90,
                        document_filename="esrs_standards_2023.pdf",
                        schema_elements=["ESRS-E1", "ESRS-S1", "ESRS-G1"]
                    )
                ]
            elif "climate" in query.lower():
                return [
                    SearchResult(
                        chunk_id="climate_chunk_1",
                        document_id="climate_doc_1",
                        content="Climate change adaptation reporting under ESRS E1 requires companies to disclose their climate-related risks and opportunities, adaptation strategies, and resilience measures.",
                        relevance_score=0.85,
                        document_filename="esrs_e1_climate.pdf",
                        schema_elements=["ESRS-E1-1", "ESRS-E1-2"]
                    )
                ]
            elif "comply" in query.lower() or "compliance" in query.lower():
                return [
                    SearchResult(
                        chunk_id="compliance_chunk_1",
                        document_id="compliance_doc_1",
                        content="Companies must comply with sustainability reporting requirements by following established frameworks, conducting regular assessments, and ensuring accurate disclosure of environmental and social impacts.",
                        relevance_score=0.80,
                        document_filename="compliance_guide.pdf",
                        schema_elements=["COMP-1"]
                    )
                ]
            else:
                return []
        
        search_service.search_documents = AsyncMock(side_effect=mock_search_documents)
        return search_service
    
    @pytest.fixture
    def rag_service_with_mock_search(self, mock_db, mock_search_service):
        """Create RAG service with mocked search service"""
        with patch('app.services.rag_service.SearchService') as mock_search_class:
            mock_search_class.return_value = mock_search_service
            
            service = RAGService(mock_db)
            service.search_service = mock_search_service
            return service
    
    @pytest.mark.asyncio
    async def test_rag_csrd_question_integration(self, rag_service_with_mock_search):
        """Test RAG service with CSRD-related question"""
        # Mock OpenAI provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        
        async def mock_generate_response(prompt, context, **kwargs):
            # Simulate realistic AI response based on context
            if "CSRD" in context and "sustainability" in context:
                response = """Based on the provided regulatory documents, the Corporate Sustainability Reporting Directive (CSRD) is a comprehensive EU regulation that requires large companies to report on sustainability matters.

Key requirements include:

1. **Scope**: Companies with more than 500 employees or €40 million in net turnover must comply
2. **Standards**: Reporting must follow the European Sustainability Reporting Standards (ESRS)
3. **Coverage**: Companies must disclose information about environmental, social, and governance (ESG) impacts
4. **Framework**: ESRS covers environmental standards (E1-E5), social standards (S1-S4), and governance standards (G1)

The directive aims to increase transparency and accountability in corporate sustainability reporting across the European Union."""
                return response, 0.88
            else:
                return "I don't have sufficient information to answer this question.", 0.2
        
        mock_provider.generate_response = mock_generate_response
        rag_service_with_mock_search.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
        
        # Test the question
        response = await rag_service_with_mock_search.generate_rag_response(
            "What is CSRD and what are its key requirements?",
            model_type=AIModelType.OPENAI_GPT35
        )
        
        # Verify response
        assert isinstance(response, RAGResponseResponse)
        assert response.query == "What is CSRD and what are its key requirements?"
        assert "Corporate Sustainability Reporting Directive" in response.response_text
        assert "ESRS" in response.response_text
        assert response.confidence_score > 0.8
        assert len(response.source_chunks) == 2
        assert "csrd_chunk_1" in response.source_chunks
        assert "csrd_chunk_2" in response.source_chunks
        assert response.model_used == AIModelType.OPENAI_GPT35.value
    
    @pytest.mark.asyncio
    async def test_rag_esrs_question_integration(self, rag_service_with_mock_search):
        """Test RAG service with ESRS-related question"""
        # Mock Anthropic provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        
        async def mock_generate_response(prompt, context, **kwargs):
            if "ESRS" in context and "environmental" in context:
                response = """The European Sustainability Reporting Standards (ESRS) are comprehensive standards that provide detailed requirements for sustainability reporting under the Corporate Sustainability Reporting Directive (CSRD).

ESRS Structure:
- **Environmental Standards (E1-E5)**: Cover climate change, pollution, water, biodiversity, and circular economy
- **Social Standards (S1-S4)**: Address workforce, value chain workers, affected communities, and consumers
- **Governance Standards (G1)**: Focus on business conduct and governance practices

These standards ensure consistent and comparable sustainability reporting across EU companies subject to CSRD requirements."""
                return response, 0.85
            else:
                return "I don't have sufficient information about ESRS standards.", 0.3
        
        mock_provider.generate_response = mock_generate_response
        rag_service_with_mock_search.model_providers[AIModelType.ANTHROPIC_CLAUDE] = mock_provider
        
        # Test the question
        response = await rag_service_with_mock_search.generate_rag_response(
            "What are the ESRS standards and how are they structured?",
            model_type=AIModelType.ANTHROPIC_CLAUDE
        )
        
        # Verify response
        assert isinstance(response, RAGResponseResponse)
        assert "European Sustainability Reporting Standards" in response.response_text
        assert "E1-E5" in response.response_text
        assert "S1-S4" in response.response_text
        assert response.confidence_score > 0.8
        assert len(response.source_chunks) == 1
        assert response.model_used == AIModelType.ANTHROPIC_CLAUDE.value
    
    @pytest.mark.asyncio
    async def test_rag_climate_question_integration(self, rag_service_with_mock_search):
        """Test RAG service with climate-specific question"""
        # Mock OpenAI provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        
        async def mock_generate_response(prompt, context, **kwargs):
            if "climate" in context and "adaptation" in context:
                response = """Climate change adaptation reporting under ESRS E1 requires companies to provide comprehensive disclosures about their climate-related risks and opportunities.

Key reporting requirements include:

1. **Risk Assessment**: Companies must identify and assess climate-related physical and transition risks
2. **Adaptation Strategies**: Disclosure of strategies to adapt to climate change impacts
3. **Resilience Measures**: Description of measures taken to build resilience against climate risks
4. **Opportunities**: Identification of climate-related opportunities and how they are being pursued

This reporting helps stakeholders understand how companies are preparing for and adapting to climate change impacts on their business operations."""
                return response, 0.82
            else:
                return "I don't have specific information about climate adaptation reporting.", 0.25
        
        mock_provider.generate_response = mock_generate_response
        rag_service_with_mock_search.model_providers[AIModelType.OPENAI_GPT4] = mock_provider
        
        # Test the question
        response = await rag_service_with_mock_search.generate_rag_response(
            "What are the climate change adaptation reporting requirements?",
            model_type=AIModelType.OPENAI_GPT4
        )
        
        # Verify response
        assert isinstance(response, RAGResponseResponse)
        assert "climate change adaptation" in response.response_text.lower()
        assert "ESRS E1" in response.response_text
        assert "risks and opportunities" in response.response_text.lower()
        assert response.confidence_score > 0.8
        assert len(response.source_chunks) == 1
        assert response.model_used == AIModelType.OPENAI_GPT4.value
    
    @pytest.mark.asyncio
    async def test_rag_no_relevant_context_integration(self, rag_service_with_mock_search):
        """Test RAG service when no relevant context is found"""
        # Mock provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        rag_service_with_mock_search.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
        
        # Test question with no matching context
        response = await rag_service_with_mock_search.generate_rag_response(
            "What is the weather like today?",  # Unrelated to sustainability
            model_type=AIModelType.OPENAI_GPT35
        )
        
        # Verify response
        assert isinstance(response, RAGResponseResponse)
        assert response.confidence_score == 0.0
        assert len(response.source_chunks) == 0
        assert "couldn't find relevant information" in response.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_rag_model_fallback_integration(self, rag_service_with_mock_search):
        """Test RAG service model fallback functionality"""
        # Mock primary model as unavailable
        mock_unavailable_provider = Mock()
        mock_unavailable_provider.is_available.return_value = False
        
        # Mock fallback model as available
        mock_available_provider = Mock()
        mock_available_provider.is_available.return_value = True
        mock_available_provider.generate_response = AsyncMock(
            return_value=("Fallback model response about CSRD requirements.", 0.75)
        )
        
        rag_service_with_mock_search.model_providers[AIModelType.OPENAI_GPT4] = mock_unavailable_provider
        rag_service_with_mock_search.model_providers[AIModelType.OPENAI_GPT35] = mock_available_provider
        
        # Request primary model that's unavailable
        response = await rag_service_with_mock_search.generate_rag_response(
            "What is CSRD?",
            model_type=AIModelType.OPENAI_GPT4  # This model is unavailable
        )
        
        # Verify fallback occurred
        assert response.model_used == AIModelType.OPENAI_GPT35.value
        assert "Fallback model response" in response.response_text
        assert response.confidence_score == 0.75
    
    @pytest.mark.asyncio
    async def test_rag_batch_processing_integration(self, rag_service_with_mock_search):
        """Test RAG service batch processing functionality"""
        # Mock provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        
        async def mock_generate_response(prompt, context, **kwargs):
            if "CSRD" in context:
                return f"Response about CSRD for: {prompt}", 0.8
            elif "ESRS" in context:
                return f"Response about ESRS for: {prompt}", 0.85
            else:
                return f"General response for: {prompt}", 0.5
        
        mock_provider.generate_response = mock_generate_response
        rag_service_with_mock_search.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
        
        # Test batch questions
        questions = [
            "What is CSRD?",
            "What are ESRS standards?",
            "How do companies comply with sustainability reporting?"
        ]
        
        responses = await rag_service_with_mock_search.batch_generate_responses(
            questions,
            model_type=AIModelType.OPENAI_GPT35,
            max_concurrent=2
        )
        
        # Verify batch responses
        assert len(responses) == 3
        
        for i, response in enumerate(responses):
            assert response.query == questions[i]
            assert questions[i] in response.response_text
            assert response.model_used == AIModelType.OPENAI_GPT35.value
            assert response.confidence_score > 0.0
    
    @pytest.mark.asyncio
    async def test_rag_quality_validation_integration(self, rag_service_with_mock_search):
        """Test RAG service response quality validation"""
        # Create a realistic response
        response = RAGResponseResponse(
            id="quality_test_response",
            query="What are the CSRD disclosure requirements?",
            response_text="The Corporate Sustainability Reporting Directive (CSRD) requires companies to disclose comprehensive information about their sustainability impacts. Key disclosure areas include environmental impacts, social responsibility measures, and governance practices. Companies must follow ESRS standards for consistent reporting.",
            model_used="openai_gpt35",
            confidence_score=0.85,
            source_chunks=["csrd_chunk_1", "csrd_chunk_2", "esrs_chunk_1"],
            generation_timestamp="2024-01-01T00:00:00Z"
        )
        
        # Validate quality
        quality_metrics = await rag_service_with_mock_search.validate_response_quality(
            response,
            expected_topics=["sustainability", "disclosure", "CSRD"]
        )
        
        # Verify quality metrics
        assert "confidence_score" in quality_metrics
        assert "has_sources" in quality_metrics
        assert "source_count" in quality_metrics
        assert "contains_regulatory_terms" in quality_metrics
        assert "topic_coverage" in quality_metrics
        assert "overall_quality" in quality_metrics
        assert "quality_score" in quality_metrics
        
        assert quality_metrics["has_sources"] is True
        assert quality_metrics["source_count"] == 3
        assert quality_metrics["contains_regulatory_terms"] is True
        assert quality_metrics["topic_coverage"] > 0.5
        assert quality_metrics["overall_quality"] in ["good", "excellent"]
    
    @pytest.mark.asyncio
    async def test_rag_error_handling_integration(self, rag_service_with_mock_search):
        """Test RAG service error handling in integration scenario"""
        # Mock search service to raise an exception
        rag_service_with_mock_search.search_service.search_documents = AsyncMock(
            side_effect=Exception("Search service unavailable")
        )
        
        response = await rag_service_with_mock_search.generate_rag_response(
            "What is CSRD?",
            model_type=AIModelType.OPENAI_GPT35
        )
        
        # Verify error handling
        assert isinstance(response, RAGResponseResponse)
        assert "error" in response.response_text.lower()
        assert response.confidence_score == 0.0
        assert response.model_used == "error"
        assert len(response.source_chunks) == 0
    
    @pytest.mark.asyncio
    async def test_rag_context_preparation_integration(self, rag_service_with_mock_search):
        """Test context preparation with realistic search results"""
        # Mock provider to capture the context
        captured_context = None
        
        async def mock_generate_response(prompt, context, **kwargs):
            nonlocal captured_context
            captured_context = context
            return "Test response", 0.8
        
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.generate_response = mock_generate_response
        rag_service_with_mock_search.model_providers[AIModelType.OPENAI_GPT35] = mock_provider
        
        # Generate response to capture context
        await rag_service_with_mock_search.generate_rag_response(
            "What is CSRD?",
            model_type=AIModelType.OPENAI_GPT35
        )
        
        # Verify context preparation
        assert captured_context is not None
        assert "Corporate Sustainability Reporting Directive" in captured_context
        assert "csrd_directive_2022.pdf" in captured_context
        assert "CSRD-1" in captured_context
        assert "0.92" in captured_context  # Relevance score
        assert "---" in captured_context  # Context separator


if __name__ == "__main__":
    pytest.main([__file__])
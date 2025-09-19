"""
Tests for search service functionality
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List
import time

from app.services.search_service import SearchService
from app.models.database import Document, TextChunk, DocumentType, SchemaType, ProcessingStatus
from app.models.schemas import SearchResult, DocumentFilters


class TestSearchService:
    """Test cases for SearchService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def search_service(self, mock_db):
        """Create SearchService instance for testing"""
        return SearchService(mock_db)
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing"""
        return [
            Document(
                id="doc1",
                filename="climate_report.pdf",
                document_type=DocumentType.PDF,
                schema_type=SchemaType.EU_ESRS_CSRD,
                processing_status=ProcessingStatus.COMPLETED,
                upload_date=datetime(2023, 1, 1)
            ),
            Document(
                id="doc2",
                filename="social_metrics.docx",
                document_type=DocumentType.DOCX,
                schema_type=SchemaType.UK_SRD,
                processing_status=ProcessingStatus.COMPLETED,
                upload_date=datetime(2023, 2, 1)
            )
        ]
    
    @pytest.fixture
    def sample_chunks(self, sample_documents):
        """Sample text chunks for testing"""
        return [
            TextChunk(
                id="chunk1",
                document_id="doc1",
                content="Climate change adaptation strategies",
                chunk_index=0,
                schema_elements=["E1", "E1-1"]
            ),
            TextChunk(
                id="chunk2",
                document_id="doc1",
                content="Greenhouse gas emissions reporting",
                chunk_index=1,
                schema_elements=["E1", "E1-2"]
            ),
            TextChunk(
                id="chunk3",
                document_id="doc2",
                content="Employee diversity metrics",
                chunk_index=0,
                schema_elements=["S1", "S1-1"]
            )
        ]
    
    @pytest.mark.asyncio
    async def test_search_documents_success(self, search_service, mock_db, sample_documents, sample_chunks):
        """Test successful document search"""
        # Mock vector search results
        vector_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Climate change adaptation strategies",
                relevance_score=0.9,
                document_filename="climate_report.pdf",
                schema_elements=["E1"]
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc1",
                content="Greenhouse gas emissions reporting",
                relevance_score=0.8,
                document_filename="climate_report.pdf",
                schema_elements=["E1"]
            )
        ]
        
        # Mock database query
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            (sample_chunks[0], sample_documents[0]),
            (sample_chunks[1], sample_documents[0])
        ]
        mock_db.query.return_value = mock_query
        
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.search_similar_chunks = AsyncMock(return_value=vector_results)
            
            results = await search_service.search_documents("climate change", top_k=2)
            
            assert len(results) == 2
            assert results[0].chunk_id == "chunk1"
            assert results[0].relevance_score == 0.9
            assert results[0].document_filename == "climate_report.pdf"
            assert results[1].chunk_id == "chunk2"
            assert results[1].relevance_score == 0.8
    
    @pytest.mark.asyncio
    async def test_search_documents_with_filters(self, search_service, mock_db, sample_documents, sample_chunks):
        """Test document search with filters"""
        vector_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Climate change adaptation strategies",
                relevance_score=0.9,
                document_filename="climate_report.pdf"
            )
        ]
        
        # Mock database query with filter calls
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(sample_chunks[0], sample_documents[0])]
        mock_db.query.return_value = mock_query
        
        filters = DocumentFilters(
            document_type=DocumentType.PDF,
            schema_type=SchemaType.EU_ESRS_CSRD
        )
        
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.search_similar_chunks = AsyncMock(return_value=vector_results)
            
            results = await search_service.search_documents("climate", top_k=5, filters=filters)
            
            assert len(results) == 1
            assert results[0].chunk_id == "chunk1"
            
            # Verify filters were applied
            assert mock_query.filter.call_count >= 2  # At least for document_type and schema_type
    
    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self, search_service):
        """Test search with empty query"""
        results = await search_service.search_documents("", top_k=5)
        assert results == []
        
        results = await search_service.search_documents("   ", top_k=5)
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_documents_no_vector_results(self, search_service):
        """Test search when vector search returns no results"""
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.search_similar_chunks = AsyncMock(return_value=[])
            
            results = await search_service.search_documents("nonexistent query", top_k=5)
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_documents_with_relevance_threshold(self, search_service, mock_db, sample_documents, sample_chunks):
        """Test search with minimum relevance score threshold"""
        vector_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="High relevance content",
                relevance_score=0.9,
                document_filename="test.pdf"
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc1",
                content="Low relevance content",
                relevance_score=0.3,
                document_filename="test.pdf"
            )
        ]
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            (sample_chunks[0], sample_documents[0]),
            (sample_chunks[1], sample_documents[0])
        ]
        mock_db.query.return_value = mock_query
        
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.search_similar_chunks = AsyncMock(return_value=vector_results)
            
            results = await search_service.search_documents(
                "test query", 
                top_k=5, 
                min_relevance_score=0.5
            )
            
            # Should only return the high relevance result
            assert len(results) == 1
            assert results[0].relevance_score == 0.9
    
    @pytest.mark.asyncio
    async def test_search_by_schema_elements(self, search_service, mock_db, sample_documents, sample_chunks):
        """Test search by schema elements"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [(sample_chunks[0], sample_documents[0])]
        mock_db.query.return_value = mock_query
        
        results = await search_service.search_by_schema_elements(
            schema_elements=["E1", "E1-1"],
            top_k=5,
            schema_type=SchemaType.EU_ESRS_CSRD
        )
        
        assert len(results) == 1
        assert results[0].chunk_id == "chunk1"
        assert results[0].relevance_score == 1.0  # Perfect match for schema elements
        assert "E1" in results[0].schema_elements
    
    @pytest.mark.asyncio
    async def test_search_similar_to_chunk(self, search_service, mock_db, sample_chunks):
        """Test finding chunks similar to a reference chunk"""
        # Mock getting the reference chunk
        mock_db.query.return_value.filter.return_value.first.return_value = sample_chunks[0]
        
        # Mock the search results (excluding the reference chunk)
        search_results = [
            SearchResult(
                chunk_id="chunk1",  # This should be filtered out (reference chunk)
                document_id="doc1",
                content="Climate change adaptation strategies",
                relevance_score=1.0,
                document_filename="test.pdf"
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc1",
                content="Similar climate content",
                relevance_score=0.8,
                document_filename="test.pdf"
            ),
            SearchResult(
                chunk_id="chunk3",
                document_id="doc2",
                content="Related environmental content",
                relevance_score=0.7,
                document_filename="other.pdf"
            )
        ]
        
        with patch.object(search_service, 'search_documents', return_value=search_results) as mock_search:
            results = await search_service.search_similar_to_chunk(
                chunk_id="chunk1",
                top_k=5,
                exclude_same_document=False
            )
            
            # Should exclude the reference chunk itself but include others
            assert len(results) == 2
            assert all(r.chunk_id != "chunk1" for r in results)
            assert results[0].chunk_id == "chunk2"
            assert results[1].chunk_id == "chunk3"
    
    @pytest.mark.asyncio
    async def test_search_similar_to_chunk_exclude_same_document(self, search_service, mock_db, sample_chunks):
        """Test finding similar chunks excluding same document"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_chunks[0]
        
        search_results = [
            SearchResult(
                chunk_id="chunk2",
                document_id="doc1",  # Same document as reference
                content="Same document content",
                relevance_score=0.8,
                document_filename="test.pdf"
            ),
            SearchResult(
                chunk_id="chunk3",
                document_id="doc2",  # Different document
                content="Different document content",
                relevance_score=0.7,
                document_filename="other.pdf"
            )
        ]
        
        with patch.object(search_service, 'search_documents', return_value=search_results):
            results = await search_service.search_similar_to_chunk(
                chunk_id="chunk1",
                top_k=5,
                exclude_same_document=True
            )
            
            # Should only include chunks from different documents
            assert len(results) == 1
            assert results[0].chunk_id == "chunk3"
            assert results[0].document_id == "doc2"
    
    @pytest.mark.asyncio
    async def test_search_similar_to_nonexistent_chunk(self, search_service, mock_db):
        """Test search similar to chunk that doesn't exist"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        results = await search_service.search_similar_to_chunk("nonexistent", top_k=5)
        assert results == []
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, search_service):
        """Test getting search suggestions"""
        suggestions = await search_service.get_search_suggestions("climate", max_suggestions=3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        assert all("climate" in suggestion.lower() for suggestion in suggestions)
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions_short_query(self, search_service):
        """Test search suggestions with very short query"""
        suggestions = await search_service.get_search_suggestions("c", max_suggestions=5)
        assert suggestions == []  # Too short
        
        suggestions = await search_service.get_search_suggestions("", max_suggestions=5)
        assert suggestions == []  # Empty
    
    def test_get_search_statistics(self, search_service, mock_db):
        """Test getting search statistics"""
        # Mock database counts
        mock_db.query.return_value.count.side_effect = [100, 500, 450]  # docs, chunks, chunks_with_embeddings
        
        # Mock document type counts
        mock_db.query.return_value.filter.return_value.count.side_effect = [60, 30, 10, 70, 30]
        
        stats = search_service.get_search_statistics()
        
        assert stats["total_documents"] == 100
        assert stats["total_chunks"] == 500
        assert stats["chunks_with_embeddings"] == 450
        assert stats["embedding_coverage"] == 90.0
        assert stats["searchable_documents"] is True
        assert "document_types" in stats
        assert "schema_types" in stats
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_service):
        """Test error handling in search operations"""
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.search_similar_chunks = AsyncMock(side_effect=Exception("Vector search failed"))
            
            results = await search_service.search_documents("test query", top_k=5)
            assert results == []  # Should return empty list on error
    
    def test_search_statistics_error_handling(self, search_service, mock_db):
        """Test error handling in statistics"""
        mock_db.query.side_effect = Exception("Database error")
        
        stats = search_service.get_search_statistics()
        assert stats == {}  # Should return empty dict on error
    
    @pytest.mark.asyncio
    async def test_generate_query_embedding(self, search_service):
        """Test query embedding generation"""
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
            
            embedding = await search_service.generate_query_embedding("test query")
            
            assert embedding == [0.1, 0.2, 0.3]
            mock_embedding_service.generate_embedding.assert_called_once_with("test query")
    
    @pytest.mark.asyncio
    async def test_generate_query_embedding_empty_query(self, search_service):
        """Test query embedding generation with empty query"""
        embedding = await search_service.generate_query_embedding("")
        assert embedding is None
        
        embedding = await search_service.generate_query_embedding("   ")
        assert embedding is None
    
    @pytest.mark.asyncio
    async def test_search_with_custom_embedding(self, search_service, mock_db, sample_documents, sample_chunks):
        """Test search using pre-computed embedding"""
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        
        vector_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Test content",
                relevance_score=0.9,
                document_filename="test.pdf"
            )
        ]
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(sample_chunks[0], sample_documents[0])]
        mock_db.query.return_value = mock_query
        
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.vector_db.search_similar = AsyncMock(return_value=vector_results)
            
            results = await search_service.search_with_custom_embedding(
                query_embedding, 
                top_k=5
            )
            
            assert len(results) == 1
            assert results[0].chunk_id == "chunk1"
            mock_embedding_service.vector_db.search_similar.assert_called_once_with(query_embedding, 10)
    
    @pytest.mark.asyncio
    async def test_search_with_custom_embedding_empty(self, search_service):
        """Test search with empty embedding"""
        results = await search_service.search_with_custom_embedding([], top_k=5)
        assert results == []
        
        results = await search_service.search_with_custom_embedding(None, top_k=5)
        assert results == []
    
    def test_rerank_results(self, search_service):
        """Test result reranking functionality"""
        query = "climate change adaptation"
        
        results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Climate change adaptation strategies for businesses",
                relevance_score=0.7,
                document_filename="test1.pdf",
                schema_elements=["E1"]
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc2",
                content="Some other content about weather",
                relevance_score=0.8,
                document_filename="test2.pdf"
            ),
            SearchResult(
                chunk_id="chunk3",
                document_id="doc3",
                content="Climate change is important for adaptation planning",
                relevance_score=0.6,
                document_filename="test3.pdf"
            )
        ]
        
        reranked = search_service._rerank_results(query, results.copy())
        
        # Should be sorted by enhanced relevance score
        assert len(reranked) == 3
        assert all(isinstance(r, SearchResult) for r in reranked)
        
        # First result should have highest score after reranking
        # (exact phrase match + schema elements should boost chunk1)
        assert reranked[0].chunk_id == "chunk1"
    
    @pytest.mark.asyncio
    async def test_get_search_performance_metrics(self, search_service):
        """Test search performance metrics collection"""
        query = "test query"
        
        with patch.object(search_service, 'generate_query_embedding') as mock_gen_embedding, \
             patch.object(search_service, 'search_with_custom_embedding') as mock_search:
            
            mock_gen_embedding.return_value = [0.1, 0.2, 0.3]
            mock_search.return_value = [
                SearchResult(
                    chunk_id="chunk1",
                    document_id="doc1",
                    content="Test content",
                    relevance_score=0.9,
                    document_filename="test.pdf"
                )
            ]
            
            metrics = await search_service.get_search_performance_metrics(query, top_k=5)
            
            assert "total_time_ms" in metrics
            assert "embedding_time_ms" in metrics
            assert "vector_search_time_ms" in metrics
            assert "results_count" in metrics
            assert "avg_relevance_score" in metrics
            assert "top_relevance_score" in metrics
            assert "embedding_dimension" in metrics
            
            assert metrics["query"] == query
            assert metrics["results_count"] == 1
            assert metrics["avg_relevance_score"] == 0.9
            assert metrics["top_relevance_score"] == 0.9
            assert metrics["embedding_dimension"] == 3
    
    @pytest.mark.asyncio
    async def test_get_search_performance_metrics_no_embedding(self, search_service):
        """Test performance metrics when embedding generation fails"""
        with patch.object(search_service, 'generate_query_embedding') as mock_gen_embedding:
            mock_gen_embedding.return_value = None
            
            metrics = await search_service.get_search_performance_metrics("test query")
            
            assert "error" in metrics
            assert metrics["error"] == "Failed to generate query embedding"
    
    @pytest.mark.asyncio
    async def test_search_documents_with_reranking(self, search_service, mock_db, sample_documents, sample_chunks):
        """Test search with reranking enabled"""
        vector_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Climate change adaptation strategies",
                relevance_score=0.7,
                document_filename="climate_report.pdf",
                schema_elements=["E1"]
            ),
            SearchResult(
                chunk_id="chunk2",
                document_id="doc1",
                content="Other climate content",
                relevance_score=0.8,
                document_filename="climate_report.pdf"
            )
        ]
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            (sample_chunks[0], sample_documents[0]),
            (sample_chunks[1], sample_documents[0])
        ]
        mock_db.query.return_value = mock_query
        
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.search_similar_chunks = AsyncMock(return_value=vector_results)
            
            results = await search_service.search_documents(
                "climate change adaptation", 
                top_k=2, 
                enable_reranking=True
            )
            
            # Should return results (exact count depends on reranking)
            assert isinstance(results, list)
            assert all(isinstance(r, SearchResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_search_documents_performance_timing(self, search_service, mock_db, sample_documents, sample_chunks):
        """Test that search completes within reasonable time"""
        vector_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Test content",
                relevance_score=0.9,
                document_filename="test.pdf"
            )
        ]
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [(sample_chunks[0], sample_documents[0])]
        mock_db.query.return_value = mock_query
        
        with patch('app.services.search_service.embedding_service') as mock_embedding_service:
            mock_embedding_service.search_similar_chunks = AsyncMock(return_value=vector_results)
            
            start_time = time.time()
            results = await search_service.search_documents("test query", top_k=5)
            end_time = time.time()
            
            # Should complete within 1 second (generous for testing)
            assert (end_time - start_time) < 1.0
            assert len(results) >= 0  # Should return some results or empty list
    
    def test_enhanced_search_statistics(self, search_service, mock_db):
        """Test enhanced search statistics with additional metrics"""
        # Mock database counts for enhanced statistics
        mock_db.query.return_value.count.side_effect = [
            100,  # total_documents
            500,  # total_chunks  
            450,  # chunks_with_embeddings
            95,   # completed_documents
            60, 30, 10,  # document type counts
            70, 30,      # schema type counts
            95, 3, 1, 1  # processing status counts
        ]
        
        # Mock average chunk size
        mock_db.query.return_value.scalar.return_value = 750.5
        
        stats = search_service.get_search_statistics()
        
        assert stats["total_documents"] == 100
        assert stats["total_chunks"] == 500
        assert stats["chunks_with_embeddings"] == 450
        assert stats["completed_documents"] == 95
        assert stats["embedding_coverage"] == 90.0
        assert stats["completion_rate"] == 95.0
        assert stats["avg_chunk_size"] == 751.0
        assert "document_types" in stats
        assert "schema_types" in stats
        assert "processing_status" in stats
        assert stats["searchable_documents"] is True
        assert "vector_service_available" in stats
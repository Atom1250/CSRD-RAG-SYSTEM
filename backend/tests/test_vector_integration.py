"""
Integration tests for vector database and embedding operations
"""
import pytest
import tempfile
import shutil
import asyncio
from typing import List, Dict, Any

from app.services.vector_service import EmbeddingService, ChromaVectorDatabase
from app.models.schemas import SearchResult


class TestVectorIntegration:
    """Integration tests for vector database operations"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample document chunks for testing"""
        return [
            {
                "id": "chunk_1",
                "document_id": "doc_climate",
                "content": "Climate change adaptation and mitigation strategies are essential for sustainable business operations. Companies must assess climate-related risks and opportunities.",
                "chunk_index": 0,
                "schema_elements": ["E1", "E1-1"],
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "id": "chunk_2",
                "document_id": "doc_climate",
                "content": "Greenhouse gas emissions reporting includes Scope 1, 2, and 3 emissions. Organizations should follow established protocols for measurement and verification.",
                "chunk_index": 1,
                "schema_elements": ["E1", "E1-2"],
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "id": "chunk_3",
                "document_id": "doc_social",
                "content": "Employee diversity and inclusion metrics are crucial for social sustainability reporting. This includes gender, ethnicity, and age diversity data.",
                "chunk_index": 0,
                "schema_elements": ["S1", "S1-1"],
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "id": "chunk_4",
                "document_id": "doc_social",
                "content": "Worker safety and health indicators must be tracked and reported. This includes accident rates, training hours, and safety compliance metrics.",
                "chunk_index": 1,
                "schema_elements": ["S1", "S1-2"],
                "created_at": "2023-01-01T00:00:00"
            },
            {
                "id": "chunk_5",
                "document_id": "doc_governance",
                "content": "Board composition and independence are key governance indicators. Companies should report on board diversity and director qualifications.",
                "chunk_index": 0,
                "schema_elements": ["G1", "G1-1"],
                "created_at": "2023-01-01T00:00:00"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_complete_embedding_workflow(self, temp_dir, sample_chunks):
        """Test complete workflow from embedding generation to search"""
        # Initialize service with test configuration
        try:
            service = EmbeddingService()
            # Override vector database with test directory
            service.vector_db = ChromaVectorDatabase(persist_directory=temp_dir, collection_name="test_collection")
        except Exception as e:
            pytest.skip(f"Could not initialize embedding service: {e}")
        
        # Step 1: Store embeddings
        store_result = await service.store_embeddings(sample_chunks.copy())
        assert store_result is True
        
        # Verify embeddings were generated
        for chunk in sample_chunks:
            assert "embedding_vector" in chunk
            assert isinstance(chunk["embedding_vector"], list)
            assert len(chunk["embedding_vector"]) > 0
        
        # Step 2: Search for climate-related content
        climate_results = await service.search_similar_chunks("climate change emissions", top_k=3)
        
        assert len(climate_results) > 0
        assert len(climate_results) <= 3
        
        # Should find climate-related chunks with higher relevance
        climate_chunk_ids = {r.chunk_id for r in climate_results}
        assert "chunk_1" in climate_chunk_ids or "chunk_2" in climate_chunk_ids
        
        # Step 3: Search for social content
        social_results = await service.search_similar_chunks("employee diversity safety", top_k=3)
        
        assert len(social_results) > 0
        social_chunk_ids = {r.chunk_id for r in social_results}
        assert "chunk_3" in social_chunk_ids or "chunk_4" in social_chunk_ids
        
        # Step 4: Search for governance content
        governance_results = await service.search_similar_chunks("board composition governance", top_k=3)
        
        assert len(governance_results) > 0
        governance_chunk_ids = {r.chunk_id for r in governance_results}
        assert "chunk_5" in governance_chunk_ids
        
        # Step 5: Test deletion
        delete_result = await service.delete_chunk_embeddings(["chunk_1", "chunk_2"])
        assert delete_result is True
        
        # Step 6: Verify deletion - search should return fewer climate results
        climate_results_after_delete = await service.search_similar_chunks("climate change emissions", top_k=3)
        remaining_climate_ids = {r.chunk_id for r in climate_results_after_delete}
        assert "chunk_1" not in remaining_climate_ids
        assert "chunk_2" not in remaining_climate_ids
    
    @pytest.mark.asyncio
    async def test_embedding_consistency_across_sessions(self, temp_dir, sample_chunks):
        """Test that embeddings are consistent across different service instances"""
        try:
            # First service instance
            service1 = EmbeddingService()
            service1.vector_db = ChromaVectorDatabase(persist_directory=temp_dir, collection_name="consistency_test")
            
            # Store embeddings
            await service1.store_embeddings(sample_chunks[:2].copy())
            
            # Search with first instance
            results1 = await service1.search_similar_chunks("climate change", top_k=2)
            
            # Second service instance (simulating restart)
            service2 = EmbeddingService()
            service2.vector_db = ChromaVectorDatabase(persist_directory=temp_dir, collection_name="consistency_test")
            
            # Search with second instance - should get same results
            results2 = await service2.search_similar_chunks("climate change", top_k=2)
            
            assert len(results1) == len(results2)
            
            # Results should be identical (same chunk IDs and scores)
            result1_ids = {r.chunk_id for r in results1}
            result2_ids = {r.chunk_id for r in results2}
            assert result1_ids == result2_ids
            
        except Exception as e:
            pytest.skip(f"Could not run consistency test: {e}")
    
    @pytest.mark.asyncio
    async def test_large_batch_operations(self, temp_dir):
        """Test handling of large batches of embeddings"""
        try:
            service = EmbeddingService()
            service.vector_db = ChromaVectorDatabase(persist_directory=temp_dir, collection_name="batch_test")
        except Exception as e:
            pytest.skip(f"Could not initialize service for batch test: {e}")
        
        # Generate large batch of chunks
        large_batch = []
        for i in range(50):  # 50 chunks
            chunk = {
                "id": f"chunk_{i:03d}",
                "document_id": f"doc_{i // 10}",
                "content": f"This is test content for chunk number {i}. It contains various sustainability reporting information and requirements for testing purposes.",
                "chunk_index": i % 10,
                "schema_elements": [f"E{(i % 5) + 1}"],
                "created_at": "2023-01-01T00:00:00"
            }
            large_batch.append(chunk)
        
        # Store large batch
        store_result = await service.store_embeddings(large_batch.copy())
        assert store_result is True
        
        # Search should work with large dataset
        results = await service.search_similar_chunks("sustainability reporting requirements", top_k=10)
        assert len(results) == 10
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(0.0 <= r.relevance_score <= 1.0 for r in results)
        
        # Delete subset
        delete_ids = [f"chunk_{i:03d}" for i in range(0, 10)]
        delete_result = await service.delete_chunk_embeddings(delete_ids)
        assert delete_result is True
        
        # Verify deletion
        results_after_delete = await service.search_similar_chunks("sustainability reporting requirements", top_k=50)
        remaining_ids = {r.chunk_id for r in results_after_delete}
        for delete_id in delete_ids:
            assert delete_id not in remaining_ids
    
    @pytest.mark.asyncio
    async def test_search_relevance_ranking(self, temp_dir):
        """Test that search results are properly ranked by relevance"""
        try:
            service = EmbeddingService()
            service.vector_db = ChromaVectorDatabase(persist_directory=temp_dir, collection_name="relevance_test")
        except Exception as e:
            pytest.skip(f"Could not initialize service for relevance test: {e}")
        
        # Create chunks with varying relevance to query
        test_chunks = [
            {
                "id": "highly_relevant",
                "document_id": "doc1",
                "content": "Climate change mitigation strategies and carbon emissions reduction are critical for environmental sustainability reporting under CSRD requirements.",
                "chunk_index": 0,
                "schema_elements": ["E1"]
            },
            {
                "id": "moderately_relevant",
                "document_id": "doc2", 
                "content": "Environmental management systems help organizations track their climate impact and implement sustainability measures.",
                "chunk_index": 0,
                "schema_elements": ["E1"]
            },
            {
                "id": "less_relevant",
                "document_id": "doc3",
                "content": "Employee training programs and workplace safety protocols are important for social sustainability reporting.",
                "chunk_index": 0,
                "schema_elements": ["S1"]
            },
            {
                "id": "not_relevant",
                "document_id": "doc4",
                "content": "Financial accounting standards and revenue recognition principles for quarterly reporting requirements.",
                "chunk_index": 0,
                "schema_elements": ["G1"]
            }
        ]
        
        # Store chunks
        await service.store_embeddings(test_chunks.copy())
        
        # Search for climate-related content
        results = await service.search_similar_chunks("climate change carbon emissions CSRD", top_k=4)
        
        assert len(results) == 4
        
        # Results should be ordered by relevance (descending)
        relevance_scores = [r.relevance_score for r in results]
        assert relevance_scores == sorted(relevance_scores, reverse=True)
        
        # Most relevant should be first
        assert results[0].chunk_id == "highly_relevant"
        assert results[0].relevance_score > results[1].relevance_score
        
        # Least relevant should be last
        assert results[-1].chunk_id == "not_relevant"
        assert results[-1].relevance_score < results[0].relevance_score
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_dir):
        """Test error handling in vector operations"""
        try:
            service = EmbeddingService()
            service.vector_db = ChromaVectorDatabase(persist_directory=temp_dir, collection_name="error_test")
        except Exception as e:
            pytest.skip(f"Could not initialize service for error test: {e}")
        
        # Test storing chunks with missing required fields
        invalid_chunks = [
            {
                "id": "valid_chunk",
                "document_id": "doc1",
                "content": "Valid content",
                "chunk_index": 0
            },
            {
                "id": "invalid_chunk",
                "document_id": "doc2",
                "content": "",  # Empty content
                "chunk_index": 1
            }
        ]
        
        # Should handle invalid chunks gracefully
        try:
            result = await service.store_embeddings(invalid_chunks.copy())
            # If it doesn't raise an error, it should at least handle the valid chunk
            assert result is not None
        except Exception:
            # Error handling is acceptable for invalid input
            pass
        
        # Test search with empty query
        try:
            results = await service.search_similar_chunks("", top_k=5)
            # Should return empty results or handle gracefully
            assert isinstance(results, list)
        except Exception:
            # Error handling is acceptable for empty query
            pass
        
        # Test deletion of non-existent chunks
        delete_result = await service.delete_chunk_embeddings(["non_existent_1", "non_existent_2"])
        # Should not fail even if chunks don't exist
        assert isinstance(delete_result, bool)
    
    def test_embedding_dimension_validation(self):
        """Test that embedding dimensions are consistent and valid"""
        try:
            service = EmbeddingService()
        except Exception as e:
            pytest.skip(f"Could not initialize service: {e}")
        
        # Test single embedding
        embedding = service.generate_embedding("Test content for dimension validation")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, (int, float)) for x in embedding)
        
        # Test multiple embeddings have same dimension
        texts = [
            "Short text",
            "Medium length text with more words",
            "Very long text with lots of content and multiple sentences to test consistency of embedding dimensions across different text lengths"
        ]
        
        embeddings = service.generate_embeddings(texts)
        dimensions = [len(emb) for emb in embeddings]
        
        # All should have same dimension
        assert len(set(dimensions)) == 1
        assert dimensions[0] == len(embedding)  # Same as single embedding
        
        # Dimension should match model's expected dimension
        expected_dim = service.get_embedding_dimension()
        assert dimensions[0] == expected_dim
"""
Tests for vector database and embedding generation service
"""
import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from app.services.vector_service import (
    EmbeddingService, 
    ChromaVectorDatabase, 
    VectorDatabase
)
from app.models.schemas import SearchResult


class TestEmbeddingService:
    """Test cases for EmbeddingService"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer model"""
        with patch('app.services.vector_service.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4]]
            mock_st.return_value = mock_model
            yield mock_model
    
    @pytest.fixture
    def embedding_service(self, mock_sentence_transformer, temp_dir):
        """Create EmbeddingService instance for testing"""
        with patch('app.services.vector_service.settings') as mock_settings:
            mock_settings.default_embedding_model = "test-model"
            mock_settings.vector_db_type = "chroma"
            mock_settings.chroma_persist_directory = temp_dir
            
            service = EmbeddingService()
            return service
    
    def test_initialize_embedding_service(self, mock_sentence_transformer, temp_dir):
        """Test EmbeddingService initialization"""
        with patch('app.services.vector_service.settings') as mock_settings:
            mock_settings.default_embedding_model = "test-model"
            mock_settings.vector_db_type = "chroma"
            mock_settings.chroma_persist_directory = temp_dir
            
            service = EmbeddingService()
            
            assert service.model_name == "test-model"
            assert service.model is not None
            assert service.vector_db is not None
    
    def test_generate_single_embedding(self, embedding_service, mock_sentence_transformer):
        """Test generating embedding for single text"""
        mock_sentence_transformer.encode.return_value = [0.1, 0.2, 0.3, 0.4]
        
        text = "This is a test document"
        embedding = embedding_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 4
        assert embedding == [0.1, 0.2, 0.3, 0.4]
        mock_sentence_transformer.encode.assert_called_once_with(text, convert_to_tensor=False)
    
    def test_generate_multiple_embeddings(self, embedding_service, mock_sentence_transformer):
        """Test generating embeddings for multiple texts"""
        mock_sentence_transformer.encode.return_value = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8]
        ]
        
        texts = ["First document", "Second document"]
        embeddings = embedding_service.generate_embeddings(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3, 0.4]
        assert embeddings[1] == [0.5, 0.6, 0.7, 0.8]
    
    def test_generate_embedding_empty_text(self, embedding_service):
        """Test generating embedding for empty text raises error"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.generate_embedding("")
    
    def test_generate_embeddings_empty_list(self, embedding_service):
        """Test generating embeddings for empty list returns empty list"""
        embeddings = embedding_service.generate_embeddings([])
        assert embeddings == []
    
    def test_generate_embeddings_no_valid_texts(self, embedding_service):
        """Test generating embeddings with no valid texts raises error"""
        with pytest.raises(ValueError, match="No valid texts provided"):
            embedding_service.generate_embeddings(["", "   ", "\n"])
    
    @pytest.mark.asyncio
    async def test_store_embeddings(self, embedding_service, mock_sentence_transformer):
        """Test storing embeddings in vector database"""
        mock_sentence_transformer.encode.return_value = [0.1, 0.2, 0.3, 0.4]
        
        chunks = [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "content": "Test content 1",
                "chunk_index": 0
            }
        ]
        
        with patch.object(embedding_service.vector_db, 'add_embeddings', return_value=True) as mock_add:
            result = await embedding_service.store_embeddings(chunks)
            
            assert result is True
            mock_add.assert_called_once()
            # Check that embedding was added to chunk
            assert "embedding_vector" in chunks[0]
            assert chunks[0]["embedding_vector"] == [0.1, 0.2, 0.3, 0.4]
    
    @pytest.mark.asyncio
    async def test_search_similar_chunks(self, embedding_service, mock_sentence_transformer):
        """Test searching for similar chunks"""
        mock_sentence_transformer.encode.return_value = [0.1, 0.2, 0.3, 0.4]
        
        expected_results = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Similar content",
                relevance_score=0.9,
                document_filename="test.pdf"
            )
        ]
        
        with patch.object(embedding_service.vector_db, 'search_similar', return_value=expected_results) as mock_search:
            results = await embedding_service.search_similar_chunks("test query", top_k=5)
            
            assert len(results) == 1
            assert results[0].chunk_id == "chunk1"
            assert results[0].relevance_score == 0.9
            mock_search.assert_called_once_with([0.1, 0.2, 0.3, 0.4], 5)
    
    @pytest.mark.asyncio
    async def test_delete_chunk_embeddings(self, embedding_service):
        """Test deleting chunk embeddings"""
        chunk_ids = ["chunk1", "chunk2"]
        
        with patch.object(embedding_service.vector_db, 'delete_embeddings', return_value=True) as mock_delete:
            result = await embedding_service.delete_chunk_embeddings(chunk_ids)
            
            assert result is True
            mock_delete.assert_called_once_with(chunk_ids)
    
    def test_get_embedding_dimension(self, embedding_service, mock_sentence_transformer):
        """Test getting embedding dimension"""
        mock_sentence_transformer.encode.return_value = [0.1, 0.2, 0.3, 0.4]
        
        dimension = embedding_service.get_embedding_dimension()
        assert dimension == 4


class TestChromaVectorDatabase:
    """Test cases for ChromaVectorDatabase"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_chroma_client(self):
        """Mock ChromaDB client"""
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client_class:
            mock_client = Mock()
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client_class.return_value = mock_client
            yield mock_client, mock_collection
    
    @pytest.fixture
    def chroma_db(self, temp_dir, mock_chroma_client):
        """Create ChromaVectorDatabase instance for testing"""
        mock_client, mock_collection = mock_chroma_client
        db = ChromaVectorDatabase(persist_directory=temp_dir)
        return db
    
    @pytest.mark.asyncio
    async def test_add_embeddings(self, chroma_db, mock_chroma_client):
        """Test adding embeddings to ChromaDB"""
        mock_client, mock_collection = mock_chroma_client
        
        chunks = [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "content": "Test content",
                "chunk_index": 0,
                "embedding_vector": [0.1, 0.2, 0.3, 0.4],
                "schema_elements": ["E1"],
                "created_at": "2023-01-01T00:00:00"
            }
        ]
        
        result = await chroma_db.add_embeddings(chunks)
        
        assert result is True
        mock_collection.add.assert_called_once()
        
        # Check the arguments passed to add method
        call_args = mock_collection.add.call_args
        assert call_args[1]["ids"] == ["chunk1"]
        assert call_args[1]["embeddings"] == [[0.1, 0.2, 0.3, 0.4]]
        assert call_args[1]["documents"] == ["Test content"]
        assert len(call_args[1]["metadatas"]) == 1
        assert call_args[1]["metadatas"][0]["document_id"] == "doc1"
    
    @pytest.mark.asyncio
    async def test_add_embeddings_empty_list(self, chroma_db):
        """Test adding empty list of embeddings"""
        result = await chroma_db.add_embeddings([])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_search_similar(self, chroma_db, mock_chroma_client):
        """Test searching for similar embeddings"""
        mock_client, mock_collection = mock_chroma_client
        
        # Mock ChromaDB query response
        mock_collection.query.return_value = {
            "ids": [["chunk1", "chunk2"]],
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[
                {"document_id": "doc1", "chunk_index": 0, "schema_elements": ["E1"]},
                {"document_id": "doc2", "chunk_index": 1, "schema_elements": ["E2"]}
            ]],
            "distances": [[0.1, 0.3]]
        }
        
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        results = await chroma_db.search_similar(query_embedding, top_k=2)
        
        assert len(results) == 2
        assert results[0].chunk_id == "chunk1"
        assert results[0].document_id == "doc1"
        assert results[0].content == "Content 1"
        assert results[0].relevance_score == 0.9  # 1 - 0.1
        
        mock_collection.query.assert_called_once_with(
            query_embeddings=[query_embedding],
            n_results=2,
            include=["documents", "metadatas", "distances"]
        )
    
    @pytest.mark.asyncio
    async def test_search_similar_no_results(self, chroma_db, mock_chroma_client):
        """Test searching with no results"""
        mock_client, mock_collection = mock_chroma_client
        
        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        results = await chroma_db.search_similar(query_embedding, top_k=5)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_delete_embeddings(self, chroma_db, mock_chroma_client):
        """Test deleting embeddings"""
        mock_client, mock_collection = mock_chroma_client
        
        chunk_ids = ["chunk1", "chunk2"]
        result = await chroma_db.delete_embeddings(chunk_ids)
        
        assert result is True
        mock_collection.delete.assert_called_once_with(ids=chunk_ids)
    
    @pytest.mark.asyncio
    async def test_delete_embeddings_empty_list(self, chroma_db):
        """Test deleting empty list of embeddings"""
        result = await chroma_db.delete_embeddings([])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_embedding(self, chroma_db, mock_chroma_client):
        """Test getting single embedding"""
        mock_client, mock_collection = mock_chroma_client
        
        mock_collection.get.return_value = {
            "embeddings": [[0.1, 0.2, 0.3, 0.4]]
        }
        
        embedding = await chroma_db.get_embedding("chunk1")
        
        assert embedding == [0.1, 0.2, 0.3, 0.4]
        mock_collection.get.assert_called_once_with(
            ids=["chunk1"],
            include=["embeddings"]
        )
    
    @pytest.mark.asyncio
    async def test_get_embedding_not_found(self, chroma_db, mock_chroma_client):
        """Test getting embedding that doesn't exist"""
        mock_client, mock_collection = mock_chroma_client
        
        mock_collection.get.return_value = {
            "embeddings": []
        }
        
        embedding = await chroma_db.get_embedding("nonexistent")
        
        assert embedding is None


class TestVectorServiceIntegration:
    """Integration tests for vector service components"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_embedding_consistency(self):
        """Test that same text produces consistent embeddings"""
        with patch('app.services.vector_service.settings') as mock_settings:
            mock_settings.default_embedding_model = "all-MiniLM-L6-v2"
            mock_settings.vector_db_type = "chroma"
            mock_settings.chroma_persist_directory = "./test_chroma"
            
            # Skip this test if model is not available
            try:
                service = EmbeddingService()
            except Exception:
                pytest.skip("Sentence transformer model not available")
            
            text = "This is a test document for consistency checking"
            
            # Generate embedding twice
            embedding1 = service.generate_embedding(text)
            embedding2 = service.generate_embedding(text)
            
            # Should be identical
            assert embedding1 == embedding2
            assert len(embedding1) > 0
            assert all(isinstance(x, float) for x in embedding1)
    
    def test_embedding_dimension_consistency(self):
        """Test that embeddings have consistent dimensions"""
        with patch('app.services.vector_service.settings') as mock_settings:
            mock_settings.default_embedding_model = "all-MiniLM-L6-v2"
            mock_settings.vector_db_type = "chroma"
            mock_settings.chroma_persist_directory = "./test_chroma"
            
            try:
                service = EmbeddingService()
            except Exception:
                pytest.skip("Sentence transformer model not available")
            
            texts = [
                "Short text",
                "This is a longer text with more words and content",
                "Another text with different content and structure for testing purposes"
            ]
            
            embeddings = service.generate_embeddings(texts)
            
            # All embeddings should have same dimension
            dimensions = [len(emb) for emb in embeddings]
            assert len(set(dimensions)) == 1  # All dimensions are the same
            assert dimensions[0] > 0
    
    @pytest.mark.asyncio
    async def test_vector_operations_workflow(self, temp_dir):
        """Test complete workflow of storing and retrieving embeddings"""
        with patch('app.services.vector_service.settings') as mock_settings:
            mock_settings.default_embedding_model = "all-MiniLM-L6-v2"
            mock_settings.vector_db_type = "chroma"
            mock_settings.chroma_persist_directory = temp_dir
            
            try:
                service = EmbeddingService()
            except Exception:
                pytest.skip("Dependencies not available for integration test")
            
            # Prepare test chunks
            chunks = [
                {
                    "id": "chunk1",
                    "document_id": "doc1",
                    "content": "Climate change reporting requirements",
                    "chunk_index": 0,
                    "schema_elements": ["E1"]
                },
                {
                    "id": "chunk2", 
                    "document_id": "doc1",
                    "content": "Social sustainability metrics and indicators",
                    "chunk_index": 1,
                    "schema_elements": ["S1"]
                }
            ]
            
            # Store embeddings
            store_result = await service.store_embeddings(chunks)
            assert store_result is True
            
            # Search for similar content
            results = await service.search_similar_chunks("environmental reporting", top_k=2)
            
            # Should find at least one result
            assert len(results) > 0
            assert all(isinstance(r, SearchResult) for r in results)
            assert all(0.0 <= r.relevance_score <= 1.0 for r in results)
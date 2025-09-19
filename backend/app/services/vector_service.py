"""
Vector database service for embedding storage and retrieval with caching
"""
from typing import List, Optional, Dict, Any, Tuple
import logging
import hashlib
from abc import ABC, abstractmethod
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..core.config import settings
from ..models.schemas import TextChunkResponse, SearchResult
from .cache_service import cache_service
from .performance_service import performance_timer, async_performance_timer

logger = logging.getLogger(__name__)


class VectorDatabase(ABC):
    """Abstract base class for vector database implementations"""
    
    @abstractmethod
    async def add_embeddings(self, chunks: List[Dict[str, Any]]) -> bool:
        """Add embeddings to the vector database"""
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: List[float], top_k: int = 10) -> List[SearchResult]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    async def delete_embeddings(self, chunk_ids: List[str]) -> bool:
        """Delete embeddings by chunk IDs"""
        pass
    
    @abstractmethod
    async def get_embedding(self, chunk_id: str) -> Optional[List[float]]:
        """Get embedding by chunk ID"""
        pass


class ChromaVectorDatabase(VectorDatabase):
    """ChromaDB implementation of vector database"""
    
    def __init__(self, persist_directory: str = None, collection_name: str = "csrd_documents"):
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "CSRD document embeddings"}
            )
            
            logger.info(f"ChromaDB initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
    
    async def add_embeddings(self, chunks: List[Dict[str, Any]]) -> bool:
        """Add embeddings to ChromaDB collection"""
        try:
            if not chunks:
                return True
            
            # Prepare data for ChromaDB
            ids = [chunk["id"] for chunk in chunks]
            embeddings = [chunk["embedding_vector"] for chunk in chunks]
            documents = [chunk["content"] for chunk in chunks]
            metadatas = [
                {
                    "document_id": chunk["document_id"],
                    "chunk_index": chunk["chunk_index"],
                    "schema_elements": chunk.get("schema_elements", []),
                    "created_at": chunk.get("created_at", "")
                }
                for chunk in chunks
            ]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} embeddings to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embeddings to ChromaDB: {str(e)}")
            return False
    
    @async_performance_timer("vector_search")
    async def search_similar(self, query_embedding: List[float], top_k: int = 10) -> List[SearchResult]:
        """Search for similar embeddings in ChromaDB with caching"""
        try:
            # Create cache key from query embedding and parameters
            embedding_hash = hashlib.md5(str(query_embedding).encode()).hexdigest()
            cache_key = f"vector_search:{embedding_hash}:{top_k}"
            
            # Try to get cached results
            cached_results = cache_service.get(cache_key)
            if cached_results:
                logger.info(f"Retrieved {len(cached_results)} cached search results")
                return [SearchResult(**result) for result in cached_results]
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert results to SearchResult objects
            search_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for i, chunk_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Convert distance to similarity score (1 - normalized distance)
                    relevance_score = max(0.0, 1.0 - distance)
                    
                    search_result = SearchResult(
                        chunk_id=chunk_id,
                        document_id=metadata["document_id"],
                        content=results["documents"][0][i],
                        relevance_score=relevance_score,
                        document_filename=metadata.get("document_filename", ""),
                        schema_elements=metadata.get("schema_elements", [])
                    )
                    search_results.append(search_result)
            
            # Cache the results (convert to dict for serialization)
            cache_data = [result.dict() for result in search_results]
            cache_service.set(cache_key, cache_data, ttl=1800)  # 30 minutes
            
            logger.info(f"Found {len(search_results)} similar chunks")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {str(e)}")
            return []
    
    async def delete_embeddings(self, chunk_ids: List[str]) -> bool:
        """Delete embeddings from ChromaDB collection"""
        try:
            if not chunk_ids:
                return True
            
            self.collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} embeddings from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embeddings from ChromaDB: {str(e)}")
            return False
    
    async def get_embedding(self, chunk_id: str) -> Optional[List[float]]:
        """Get embedding by chunk ID from ChromaDB"""
        try:
            results = self.collection.get(
                ids=[chunk_id],
                include=["embeddings"]
            )
            
            if results["embeddings"] and len(results["embeddings"]) > 0:
                return results["embeddings"][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get embedding from ChromaDB: {str(e)}")
            return None


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.default_embedding_model
        self.model = None
        self.vector_db = None
        self._initialize_model()
        self._initialize_vector_db()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise
    
    def _initialize_vector_db(self):
        """Initialize the vector database"""
        try:
            if settings.vector_db_type.lower() == "chroma":
                self.vector_db = ChromaVectorDatabase()
            else:
                raise ValueError(f"Unsupported vector database type: {settings.vector_db_type}")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {str(e)}")
            raise
    
    @performance_timer("embedding_generation")
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text with caching"""
        try:
            if not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Check cache first
            cached_embedding = cache_service.get_cached_embedding(text, self.model_name)
            if cached_embedding:
                logger.debug(f"Retrieved cached embedding for text (length: {len(text)})")
                return cached_embedding
            
            # Generate new embedding
            embedding = self.model.encode(text, convert_to_tensor=False)
            embedding_list = embedding.tolist()
            
            # Cache the embedding
            cache_service.cache_embedding(text, self.model_name, embedding_list)
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    @performance_timer("batch_embedding_generation")
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with caching"""
        try:
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                raise ValueError("No valid texts provided")
            
            # Check cache for each text
            embeddings = []
            texts_to_generate = []
            text_indices = []
            
            for i, text in enumerate(valid_texts):
                cached_embedding = cache_service.get_cached_embedding(text, self.model_name)
                if cached_embedding:
                    embeddings.append(cached_embedding)
                else:
                    embeddings.append(None)  # Placeholder
                    texts_to_generate.append(text)
                    text_indices.append(i)
            
            # Generate embeddings for uncached texts
            if texts_to_generate:
                new_embeddings = self.model.encode(texts_to_generate, convert_to_tensor=False)
                
                # Cache new embeddings and fill placeholders
                for i, (text_idx, text) in enumerate(zip(text_indices, texts_to_generate)):
                    embedding_list = new_embeddings[i].tolist()
                    embeddings[text_idx] = embedding_list
                    cache_service.cache_embedding(text, self.model_name, embedding_list)
            
            logger.info(f"Generated embeddings for {len(texts_to_generate)} texts, used cache for {len(valid_texts) - len(texts_to_generate)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    async def store_embeddings(self, chunks: List[Dict[str, Any]]) -> bool:
        """Store embeddings in vector database"""
        try:
            # Generate embeddings for chunks that don't have them
            chunks_to_embed = []
            for chunk in chunks:
                if "embedding_vector" not in chunk or not chunk["embedding_vector"]:
                    embedding = self.generate_embedding(chunk["content"])
                    chunk["embedding_vector"] = embedding
                chunks_to_embed.append(chunk)
            
            # Store in vector database
            return await self.vector_db.add_embeddings(chunks_to_embed)
            
        except Exception as e:
            logger.error(f"Failed to store embeddings: {str(e)}")
            return False
    
    async def search_similar_chunks(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search for similar chunks using query text"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Search in vector database
            return await self.vector_db.search_similar(query_embedding, top_k)
            
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {str(e)}")
            return []
    
    async def delete_chunk_embeddings(self, chunk_ids: List[str]) -> bool:
        """Delete embeddings for specific chunks"""
        try:
            return await self.vector_db.delete_embeddings(chunk_ids)
        except Exception as e:
            logger.error(f"Failed to delete chunk embeddings: {str(e)}")
            return False
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model"""
        try:
            # Generate a test embedding to get dimension
            test_embedding = self.generate_embedding("test")
            return len(test_embedding)
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {str(e)}")
            return 384  # Default dimension for all-MiniLM-L6-v2


# Global embedding service instance
embedding_service = EmbeddingService()
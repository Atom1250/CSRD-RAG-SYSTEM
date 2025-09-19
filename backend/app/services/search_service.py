"""
Search service for semantic document search using vector embeddings with caching
"""
import logging
import time
import json
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import Document, TextChunk, SchemaType, DocumentType, ProcessingStatus
from app.models.schemas import SearchResult, DocumentFilters
from app.core.config import settings
from app.services.cache_service import cache_service
from app.services.performance_service import async_performance_timer

# Conditional import for vector service to avoid dependency issues during testing
try:
    from app.services.vector_service import embedding_service
    VECTOR_SERVICE_AVAILABLE = True
except ImportError as e:
    # Logger is defined below, so we'll set a flag and log later
    embedding_service = None
    VECTOR_SERVICE_AVAILABLE = False
    _vector_import_error = str(e)

logger = logging.getLogger(__name__)


class SearchService:
    """Service for semantic search operations"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Log vector service availability
        if not VECTOR_SERVICE_AVAILABLE:
            logger.warning(f"Vector service not available: {_vector_import_error if '_vector_import_error' in globals() else 'Unknown error'}")
    
    @async_performance_timer("document_search")
    async def search_documents(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[DocumentFilters] = None,
        min_relevance_score: float = 0.0,
        enable_reranking: bool = True
    ) -> List[SearchResult]:
        """
        Search for relevant document chunks using semantic similarity with advanced ranking and caching
        
        Args:
            query: Search query text
            top_k: Maximum number of results to return
            filters: Optional filters for document types, schemas, etc.
            min_relevance_score: Minimum relevance score threshold
            enable_reranking: Whether to apply additional ranking algorithms
            
        Returns:
            List[SearchResult]: Ranked search results with relevance scores
        """
        start_time = time.time()
        
        try:
            if not query.strip():
                return []
            
            if not VECTOR_SERVICE_AVAILABLE:
                logger.warning("Vector service not available for search")
                return []
            
            # Create cache key from search parameters
            filters_dict = filters.dict() if filters else {}
            cache_params = {
                "query": query,
                "top_k": top_k,
                "filters": filters_dict,
                "min_relevance_score": min_relevance_score,
                "enable_reranking": enable_reranking
            }
            
            # Check cache first
            cached_results = cache_service.get_cached_search_results(query, cache_params)
            if cached_results:
                logger.info(f"Retrieved {len(cached_results)} cached search results for query: '{query[:50]}...'")
                return [SearchResult(**result) for result in cached_results]
            
            # Generate query embedding for semantic search
            logger.debug(f"Generating embedding for query: '{query[:50]}...'")
            
            # Get initial results from vector database with expanded search
            search_multiplier = 3 if enable_reranking else 2
            vector_results = await embedding_service.search_similar_chunks(
                query, 
                min(top_k * search_multiplier, 100)  # Cap at 100 to avoid performance issues
            )
            
            if not vector_results:
                logger.info(f"No vector results found for query: '{query}'")
                return []
            
            # Get chunk IDs for database filtering
            chunk_ids = [result.chunk_id for result in vector_results]
            
            # Query database for additional metadata and apply filters
            db_query = (
                self.db.query(TextChunk, Document)
                .join(Document, TextChunk.document_id == Document.id)
                .filter(TextChunk.id.in_(chunk_ids))
                .filter(Document.processing_status == ProcessingStatus.COMPLETED)  # Only completed documents
            )
            
            # Apply filters if provided
            if filters:
                if filters.document_type:
                    db_query = db_query.filter(Document.document_type == filters.document_type)
                if filters.schema_type:
                    db_query = db_query.filter(Document.schema_type == filters.schema_type)
                if filters.processing_status:
                    db_query = db_query.filter(Document.processing_status == filters.processing_status)
                if filters.filename_contains:
                    db_query = db_query.filter(Document.filename.ilike(f"%{filters.filename_contains}%"))
                if filters.upload_date_from:
                    db_query = db_query.filter(Document.upload_date >= filters.upload_date_from)
                if filters.upload_date_to:
                    db_query = db_query.filter(Document.upload_date <= filters.upload_date_to)
            
            db_results = db_query.all()
            
            # Create mapping of chunk_id to database data
            chunk_db_data = {chunk.id: (chunk, document) for chunk, document in db_results}
            
            # Combine vector results with database metadata and apply initial filtering
            candidate_results = []
            for vector_result in vector_results:
                if vector_result.chunk_id in chunk_db_data:
                    chunk, document = chunk_db_data[vector_result.chunk_id]
                    
                    # Apply relevance score filter
                    if vector_result.relevance_score < min_relevance_score:
                        continue
                    
                    # Create enhanced result with database metadata
                    enhanced_result = SearchResult(
                        chunk_id=vector_result.chunk_id,
                        document_id=vector_result.document_id,
                        content=vector_result.content,
                        relevance_score=vector_result.relevance_score,
                        document_filename=document.filename,
                        schema_elements=chunk.schema_elements or []
                    )
                    
                    candidate_results.append(enhanced_result)
            
            # Apply advanced ranking if enabled
            if enable_reranking and candidate_results:
                candidate_results = self._rerank_results(query, candidate_results)
            
            # Return top_k results
            final_results = candidate_results[:top_k]
            
            # Cache the results
            cache_data = [result.dict() for result in final_results]
            cache_service.cache_search_results(query, cache_params, cache_data)
            
            search_time = time.time() - start_time
            logger.info(f"Search for '{query}' returned {len(final_results)} results in {search_time:.3f}s")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            return []
    
    async def search_by_schema_elements(
        self,
        schema_elements: List[str],
        top_k: int = 10,
        schema_type: Optional[SchemaType] = None
    ) -> List[SearchResult]:
        """
        Search for chunks that match specific schema elements
        
        Args:
            schema_elements: List of schema element codes to search for
            top_k: Maximum number of results to return
            schema_type: Optional schema type filter
            
        Returns:
            List[SearchResult]: Matching chunks
        """
        try:
            # Query database for chunks with matching schema elements
            db_query = (
                self.db.query(TextChunk, Document)
                .join(Document, TextChunk.document_id == Document.id)
                .filter(TextChunk.schema_elements.op('&&')(schema_elements))  # PostgreSQL array overlap
            )
            
            if schema_type:
                db_query = db_query.filter(Document.schema_type == schema_type)
            
            db_results = db_query.limit(top_k).all()
            
            # Convert to SearchResult objects
            results = []
            for chunk, document in db_results:
                result = SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    relevance_score=1.0,  # Perfect match for schema elements
                    document_filename=document.filename,
                    schema_elements=chunk.schema_elements or []
                )
                results.append(result)
            
            logger.info(f"Schema element search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Schema element search failed: {str(e)}")
            return []
    
    async def search_similar_to_chunk(
        self,
        chunk_id: str,
        top_k: int = 10,
        exclude_same_document: bool = True
    ) -> List[SearchResult]:
        """
        Find chunks similar to a given chunk
        
        Args:
            chunk_id: ID of the reference chunk
            top_k: Maximum number of results to return
            exclude_same_document: Whether to exclude chunks from the same document
            
        Returns:
            List[SearchResult]: Similar chunks
        """
        try:
            # Get the reference chunk
            reference_chunk = self.db.query(TextChunk).filter(TextChunk.id == chunk_id).first()
            if not reference_chunk:
                logger.warning(f"Reference chunk not found: {chunk_id}")
                return []
            
            # Use the chunk content as query
            results = await self.search_documents(
                query=reference_chunk.content,
                top_k=top_k + (1 if not exclude_same_document else 10),  # Get extra to account for filtering
                min_relevance_score=0.1
            )
            
            # Filter out the reference chunk itself and optionally same document
            filtered_results = []
            for result in results:
                if result.chunk_id == chunk_id:
                    continue  # Skip the reference chunk itself
                
                if exclude_same_document and result.document_id == reference_chunk.document_id:
                    continue  # Skip chunks from same document
                
                filtered_results.append(result)
                
                if len(filtered_results) >= top_k:
                    break
            
            logger.info(f"Similar chunk search returned {len(filtered_results)} results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Similar chunk search failed for chunk {chunk_id}: {str(e)}")
            return []
    
    async def get_search_suggestions(
        self,
        partial_query: str,
        max_suggestions: int = 5
    ) -> List[str]:
        """
        Get search suggestions based on partial query
        
        Args:
            partial_query: Partial search query
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List[str]: Search suggestions
        """
        try:
            if len(partial_query.strip()) < 2:
                return []
            
            # For now, return common sustainability reporting terms
            # In a full implementation, this could use a more sophisticated approach
            common_terms = [
                "climate change adaptation",
                "greenhouse gas emissions",
                "carbon footprint",
                "renewable energy",
                "biodiversity conservation",
                "water management",
                "waste reduction",
                "employee diversity",
                "workplace safety",
                "human rights",
                "supply chain sustainability",
                "board governance",
                "risk management",
                "stakeholder engagement",
                "sustainability reporting",
                "CSRD compliance",
                "ESRS standards",
                "environmental impact",
                "social responsibility",
                "governance practices"
            ]
            
            # Filter terms that contain the partial query
            suggestions = [
                term for term in common_terms
                if partial_query.lower() in term.lower()
            ]
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Search suggestions failed for query '{partial_query}': {str(e)}")
            return []
    
    def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """
        Apply advanced ranking algorithms to improve result relevance
        
        Args:
            query: Original search query
            results: Initial search results to rerank
            
        Returns:
            List[SearchResult]: Reranked results
        """
        try:
            query_lower = query.lower()
            query_terms = set(query_lower.split())
            
            # Calculate additional ranking factors
            for result in results:
                content_lower = result.content.lower()
                
                # Factor 1: Exact phrase match bonus
                phrase_bonus = 0.1 if query_lower in content_lower else 0.0
                
                # Factor 2: Term frequency bonus
                content_terms = set(content_lower.split())
                term_overlap = len(query_terms.intersection(content_terms))
                term_bonus = (term_overlap / len(query_terms)) * 0.05 if query_terms else 0.0
                
                # Factor 3: Schema element relevance bonus
                schema_bonus = 0.02 if result.schema_elements else 0.0
                
                # Factor 4: Content length penalty (prefer concise, relevant content)
                length_penalty = max(0.0, (len(result.content) - 500) / 10000) * 0.01
                
                # Apply combined ranking score
                result.relevance_score = min(1.0, result.relevance_score + phrase_bonus + term_bonus + schema_bonus - length_penalty)
            
            # Sort by enhanced relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to rerank results: {str(e)}")
            return results
    
    async def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query text
            
        Returns:
            List[float]: Query embedding vector or None if failed
        """
        try:
            if not query.strip():
                return None
            
            if not VECTOR_SERVICE_AVAILABLE:
                logger.warning("Vector service not available for embedding generation")
                return None
            
            return embedding_service.generate_embedding(query)
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            return None
    
    async def search_with_custom_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[DocumentFilters] = None,
        min_relevance_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Search using a pre-computed query embedding
        
        Args:
            query_embedding: Pre-computed query embedding vector
            top_k: Maximum number of results to return
            filters: Optional filters for document types, schemas, etc.
            min_relevance_score: Minimum relevance score threshold
            
        Returns:
            List[SearchResult]: Ranked search results
        """
        try:
            if not query_embedding:
                return []
            
            if not VECTOR_SERVICE_AVAILABLE:
                logger.warning("Vector service not available for search")
                return []
            
            # Search using the provided embedding
            vector_results = await embedding_service.vector_db.search_similar(query_embedding, top_k * 2)
            
            if not vector_results:
                return []
            
            # Apply database filtering and metadata enrichment (similar to search_documents)
            chunk_ids = [result.chunk_id for result in vector_results]
            
            db_query = (
                self.db.query(TextChunk, Document)
                .join(Document, TextChunk.document_id == Document.id)
                .filter(TextChunk.id.in_(chunk_ids))
                .filter(Document.processing_status == ProcessingStatus.COMPLETED)
            )
            
            # Apply filters
            if filters:
                if filters.document_type:
                    db_query = db_query.filter(Document.document_type == filters.document_type)
                if filters.schema_type:
                    db_query = db_query.filter(Document.schema_type == filters.schema_type)
                if filters.processing_status:
                    db_query = db_query.filter(Document.processing_status == filters.processing_status)
                if filters.filename_contains:
                    db_query = db_query.filter(Document.filename.ilike(f"%{filters.filename_contains}%"))
                if filters.upload_date_from:
                    db_query = db_query.filter(Document.upload_date >= filters.upload_date_from)
                if filters.upload_date_to:
                    db_query = db_query.filter(Document.upload_date <= filters.upload_date_to)
            
            db_results = db_query.all()
            chunk_db_data = {chunk.id: (chunk, document) for chunk, document in db_results}
            
            # Combine and filter results
            final_results = []
            for vector_result in vector_results:
                if vector_result.chunk_id in chunk_db_data:
                    chunk, document = chunk_db_data[vector_result.chunk_id]
                    
                    if vector_result.relevance_score < min_relevance_score:
                        continue
                    
                    enhanced_result = SearchResult(
                        chunk_id=vector_result.chunk_id,
                        document_id=vector_result.document_id,
                        content=vector_result.content,
                        relevance_score=vector_result.relevance_score,
                        document_filename=document.filename,
                        schema_elements=chunk.schema_elements or []
                    )
                    
                    final_results.append(enhanced_result)
                    
                    if len(final_results) >= top_k:
                        break
            
            return final_results
            
        except Exception as e:
            logger.error(f"Custom embedding search failed: {str(e)}")
            return []
    
    async def get_search_performance_metrics(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Get performance metrics for a search query
        
        Args:
            query: Search query to benchmark
            top_k: Number of results to retrieve
            
        Returns:
            Dict containing performance metrics
        """
        try:
            start_time = time.time()
            
            # Perform search and measure timing
            embedding_start = time.time()
            query_embedding = await self.generate_query_embedding(query)
            embedding_time = time.time() - embedding_start
            
            if not query_embedding:
                return {"error": "Failed to generate query embedding"}
            
            vector_search_start = time.time()
            results = await self.search_with_custom_embedding(query_embedding, top_k)
            vector_search_time = time.time() - vector_search_start
            
            total_time = time.time() - start_time
            
            return {
                "query": query,
                "total_time_ms": round(total_time * 1000, 2),
                "embedding_time_ms": round(embedding_time * 1000, 2),
                "vector_search_time_ms": round(vector_search_time * 1000, 2),
                "results_count": len(results),
                "avg_relevance_score": round(sum(r.relevance_score for r in results) / len(results), 3) if results else 0.0,
                "top_relevance_score": round(max(r.relevance_score for r in results), 3) if results else 0.0,
                "embedding_dimension": len(query_embedding) if query_embedding else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get search performance metrics: {str(e)}")
            return {"error": str(e)}
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive search-related statistics
        
        Returns:
            Dict containing search statistics
        """
        try:
            # Count total documents and chunks
            total_documents = self.db.query(Document).count()
            total_chunks = self.db.query(TextChunk).count()
            
            # Count chunks with embeddings
            chunks_with_embeddings = (
                self.db.query(TextChunk)
                .filter(TextChunk.embedding_vector.isnot(None))
                .count()
            )
            
            # Count completed documents
            completed_documents = (
                self.db.query(Document)
                .filter(Document.processing_status == ProcessingStatus.COMPLETED)
                .count()
            )
            
            # Count by document type
            doc_type_counts = {}
            for doc_type in DocumentType:
                count = self.db.query(Document).filter(Document.document_type == doc_type).count()
                doc_type_counts[doc_type.value] = count
            
            # Count by schema type
            schema_type_counts = {}
            for schema_type in SchemaType:
                count = self.db.query(Document).filter(Document.schema_type == schema_type).count()
                schema_type_counts[schema_type.value] = count
            
            # Count by processing status
            status_counts = {}
            for status in ProcessingStatus:
                count = self.db.query(Document).filter(Document.processing_status == status).count()
                status_counts[status.value] = count
            
            # Calculate average chunk size
            avg_chunk_size = (
                self.db.query(func.avg(func.length(TextChunk.content)))
                .scalar() or 0
            )
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
                "completed_documents": completed_documents,
                "embedding_coverage": round(chunks_with_embeddings / total_chunks * 100, 2) if total_chunks > 0 else 0,
                "completion_rate": round(completed_documents / total_documents * 100, 2) if total_documents > 0 else 0,
                "avg_chunk_size": round(avg_chunk_size, 0) if avg_chunk_size else 0,
                "document_types": doc_type_counts,
                "schema_types": schema_type_counts,
                "processing_status": status_counts,
                "searchable_documents": chunks_with_embeddings > 0,
                "vector_service_available": VECTOR_SERVICE_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Failed to get search statistics: {str(e)}")
            return {}


# Global search service factory
def get_search_service(db: Session) -> SearchService:
    """Factory function to create SearchService instance"""
    return SearchService(db)
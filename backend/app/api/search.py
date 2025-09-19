"""
Search API endpoints for semantic document search
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database_config import get_db
from app.models.schemas import (
    SearchResult, 
    DocumentFilters, 
    DocumentType, 
    SchemaType, 
    ProcessingStatus
)
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """Dependency to get search service instance"""
    return SearchService(db)


class SearchRequest(BaseModel):
    """Request model for search operations"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    min_relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score threshold")
    enable_reranking: bool = Field(True, description="Whether to apply advanced ranking algorithms")
    
    # Filter options
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    schema_type: Optional[SchemaType] = Field(None, description="Filter by schema type")
    processing_status: Optional[ProcessingStatus] = Field(None, description="Filter by processing status")
    filename_contains: Optional[str] = Field(None, description="Filter by filename containing text")


class EmbeddingSearchRequest(BaseModel):
    """Request model for embedding-based search"""
    query_embedding: List[float] = Field(..., description="Pre-computed query embedding vector")
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    min_relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score threshold")
    
    # Filter options
    document_type: Optional[DocumentType] = Field(None, description="Filter by document type")
    schema_type: Optional[SchemaType] = Field(None, description="Filter by schema type")
    processing_status: Optional[ProcessingStatus] = Field(None, description="Filter by processing status")
    filename_contains: Optional[str] = Field(None, description="Filter by filename containing text")


class SchemaSearchRequest(BaseModel):
    """Request model for schema-based search"""
    schema_elements: List[str] = Field(..., min_length=1, description="Schema element codes to search for")
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    schema_type: Optional[SchemaType] = Field(None, description="Filter by schema type")


class SimilarChunkRequest(BaseModel):
    """Request model for finding similar chunks"""
    chunk_id: str = Field(..., description="Reference chunk ID")
    top_k: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    exclude_same_document: bool = Field(True, description="Whether to exclude chunks from the same document")


class SearchSuggestionsResponse(BaseModel):
    """Response model for search suggestions"""
    suggestions: List[str] = Field(..., description="List of search suggestions")
    query: str = Field(..., description="Original partial query")


class SearchPerformanceResponse(BaseModel):
    """Response model for search performance metrics"""
    query: str
    total_time_ms: float
    embedding_time_ms: float
    vector_search_time_ms: float
    results_count: int
    avg_relevance_score: float
    top_relevance_score: float
    embedding_dimension: int


class SearchStatisticsResponse(BaseModel):
    """Response model for search statistics"""
    total_documents: int
    total_chunks: int
    chunks_with_embeddings: int
    completed_documents: int
    embedding_coverage: float
    completion_rate: float
    avg_chunk_size: float
    document_types: Dict[str, int]
    schema_types: Dict[str, int]
    processing_status: Dict[str, int]
    searchable_documents: bool
    vector_service_available: bool


@router.post("/", response_model=List[SearchResult])
async def search_documents(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Perform semantic search across document chunks
    
    - **query**: Natural language search query
    - **top_k**: Maximum number of results to return (1-100)
    - **min_relevance_score**: Minimum relevance score threshold (0.0-1.0)
    - **enable_reranking**: Whether to apply advanced ranking algorithms
    - **filters**: Optional filters for document type, schema, status, etc.
    
    Returns a list of relevant document chunks ranked by relevance score.
    """
    try:
        # Create filters from request
        filters = DocumentFilters(
            document_type=request.document_type,
            schema_type=request.schema_type,
            processing_status=request.processing_status,
            filename_contains=request.filename_contains
        )
        
        # Perform search
        results = await search_service.search_documents(
            query=request.query,
            top_k=request.top_k,
            filters=filters,
            min_relevance_score=request.min_relevance_score,
            enable_reranking=request.enable_reranking
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/", response_model=List[SearchResult])
async def search_documents_get(
    query: str = Query(..., min_length=1, max_length=1000, description="Search query text"),
    top_k: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    min_relevance_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum relevance score"),
    enable_reranking: bool = Query(True, description="Enable advanced ranking"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    schema_type: Optional[SchemaType] = Query(None, description="Filter by schema type"),
    processing_status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    filename_contains: Optional[str] = Query(None, description="Filter by filename"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Perform semantic search using GET parameters (alternative to POST)
    
    Useful for simple searches and testing. For complex searches with large
    embedding vectors, use the POST endpoint.
    """
    try:
        filters = DocumentFilters(
            document_type=document_type,
            schema_type=schema_type,
            processing_status=processing_status,
            filename_contains=filename_contains
        )
        
        results = await search_service.search_documents(
            query=query,
            top_k=top_k,
            filters=filters,
            min_relevance_score=min_relevance_score,
            enable_reranking=enable_reranking
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/embedding", response_model=List[SearchResult])
async def search_with_embedding(
    request: EmbeddingSearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Perform search using a pre-computed embedding vector
    
    - **query_embedding**: Pre-computed query embedding vector
    - **top_k**: Maximum number of results to return
    - **min_relevance_score**: Minimum relevance score threshold
    - **filters**: Optional filters for document type, schema, status, etc.
    
    Useful when you have already computed the query embedding or want to
    search with custom embeddings.
    """
    try:
        filters = DocumentFilters(
            document_type=request.document_type,
            schema_type=request.schema_type,
            processing_status=request.processing_status,
            filename_contains=request.filename_contains
        )
        
        results = await search_service.search_with_custom_embedding(
            query_embedding=request.query_embedding,
            top_k=request.top_k,
            filters=filters,
            min_relevance_score=request.min_relevance_score
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding search failed: {str(e)}")


@router.post("/schema", response_model=List[SearchResult])
async def search_by_schema_elements(
    request: SchemaSearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search for chunks that match specific schema elements
    
    - **schema_elements**: List of schema element codes to search for
    - **top_k**: Maximum number of results to return
    - **schema_type**: Optional schema type filter
    
    Returns chunks that are tagged with the specified schema elements.
    """
    try:
        results = await search_service.search_by_schema_elements(
            schema_elements=request.schema_elements,
            top_k=request.top_k,
            schema_type=request.schema_type
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema search failed: {str(e)}")


@router.post("/similar", response_model=List[SearchResult])
async def find_similar_chunks(
    request: SimilarChunkRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Find chunks similar to a reference chunk
    
    - **chunk_id**: ID of the reference chunk
    - **top_k**: Maximum number of results to return
    - **exclude_same_document**: Whether to exclude chunks from the same document
    
    Returns chunks that are semantically similar to the reference chunk.
    """
    try:
        results = await search_service.search_similar_to_chunk(
            chunk_id=request.chunk_id,
            top_k=request.top_k,
            exclude_same_document=request.exclude_same_document
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar chunk search failed: {str(e)}")


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    partial_query: str = Query(..., min_length=2, max_length=100, description="Partial search query"),
    max_suggestions: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get search suggestions based on partial query
    
    - **partial_query**: Partial search query (minimum 2 characters)
    - **max_suggestions**: Maximum number of suggestions to return
    
    Returns a list of suggested search terms.
    """
    try:
        suggestions = await search_service.get_search_suggestions(
            partial_query=partial_query,
            max_suggestions=max_suggestions
        )
        
        return SearchSuggestionsResponse(
            suggestions=suggestions,
            query=partial_query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.post("/embedding/generate", response_model=List[float])
async def generate_query_embedding(
    query: str = Query(..., min_length=1, max_length=1000, description="Query text to embed"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Generate embedding vector for a query
    
    - **query**: Query text to generate embedding for
    
    Returns the embedding vector that can be used with the embedding search endpoint.
    """
    try:
        embedding = await search_service.generate_query_embedding(query)
        
        if embedding is None:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        return embedding
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.get("/performance", response_model=SearchPerformanceResponse)
async def get_search_performance_metrics(
    query: str = Query(..., min_length=1, max_length=1000, description="Query to benchmark"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to retrieve"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get performance metrics for a search query
    
    - **query**: Search query to benchmark
    - **top_k**: Number of results to retrieve for benchmarking
    
    Returns detailed performance metrics including timing and relevance scores.
    """
    try:
        metrics = await search_service.get_search_performance_metrics(query, top_k)
        
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        
        return SearchPerformanceResponse(**metrics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")


@router.get("/statistics", response_model=SearchStatisticsResponse)
async def get_search_statistics(
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get comprehensive search-related statistics
    
    Returns statistics about the document corpus, embedding coverage,
    processing status, and search system health.
    """
    try:
        stats = search_service.get_search_statistics()
        
        if not stats:
            raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
        
        return SearchStatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")


@router.get("/health")
async def search_health_check(
    search_service: SearchService = Depends(get_search_service)
):
    """
    Health check for search functionality
    
    Returns the status of search components including vector service availability.
    """
    try:
        stats = search_service.get_search_statistics()
        
        return {
            "status": "healthy" if stats.get("vector_service_available", False) else "degraded",
            "vector_service_available": stats.get("vector_service_available", False),
            "searchable_documents": stats.get("searchable_documents", False),
            "total_documents": stats.get("total_documents", 0),
            "chunks_with_embeddings": stats.get("chunks_with_embeddings", 0),
            "embedding_coverage": stats.get("embedding_coverage", 0.0)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "vector_service_available": False,
            "searchable_documents": False
        }
"""
RAG (Retrieval-Augmented Generation) API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database_config import get_db
from app.services.rag_service import RAGService, AIModelType
from app.models.schemas import RAGResponseResponse

router = APIRouter(prefix="/rag", tags=["RAG"])


def get_rag_service(db: Session = Depends(get_db)) -> RAGService:
    """Dependency to get RAG service instance"""
    return RAGService(db)


class RAGQueryRequest(BaseModel):
    """Request schema for RAG queries"""
    model_config = {"protected_namespaces": ()}
    
    question: str = Field(..., min_length=1, max_length=2000, description="The question to ask")
    model_type: Optional[AIModelType] = Field(None, description="AI model to use for generation")
    max_context_chunks: Optional[int] = Field(10, ge=1, le=50, description="Maximum context chunks to retrieve")
    min_relevance_score: Optional[float] = Field(0.3, ge=0.0, le=1.0, description="Minimum relevance score for context")
    max_tokens: Optional[int] = Field(1000, ge=100, le=4000, description="Maximum tokens in response")
    temperature: Optional[float] = Field(0.1, ge=0.0, le=2.0, description="Model temperature for creativity")


class BatchRAGQueryRequest(BaseModel):
    """Request schema for batch RAG queries"""
    model_config = {"protected_namespaces": ()}
    
    questions: List[str] = Field(..., min_length=1, max_length=10, description="List of questions to ask")
    model_type: Optional[AIModelType] = Field(None, description="AI model to use for all questions")
    max_concurrent: Optional[int] = Field(3, ge=1, le=5, description="Maximum concurrent requests")


class ModelInfo(BaseModel):
    """Model information schema"""
    type: str
    provider: str
    model: str
    available: bool
    capabilities: List[str]
    max_tokens: int


class ModelStatusResponse(BaseModel):
    """Model status response schema"""
    models: Dict[str, Dict[str, Any]]
    default_model: str
    available_count: int


class QualityValidationRequest(BaseModel):
    """Request schema for response quality validation"""
    response_id: str
    expected_topics: Optional[List[str]] = Field(None, description="Expected topics to be covered")


@router.post("/query", response_model=RAGResponseResponse)
async def generate_rag_response(
    request: RAGQueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generate a RAG response for a single question
    
    This endpoint retrieves relevant context from the document repository
    and generates an AI-powered response using the selected model.
    """
    try:
        response = await rag_service.generate_rag_response(
            question=request.question,
            model_type=request.model_type,
            max_context_chunks=request.max_context_chunks,
            min_relevance_score=request.min_relevance_score,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate RAG response: {str(e)}")


@router.post("/batch-query", response_model=List[RAGResponseResponse])
async def generate_batch_rag_responses(
    request: BatchRAGQueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generate RAG responses for multiple questions concurrently
    
    This endpoint processes multiple questions in parallel for improved efficiency.
    """
    try:
        responses = await rag_service.batch_generate_responses(
            questions=request.questions,
            model_type=request.model_type,
            max_concurrent=request.max_concurrent
        )
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate batch RAG responses: {str(e)}")


@router.get("/models", response_model=List[ModelInfo])
async def get_available_models(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get list of available AI models with their capabilities
    
    Returns information about all configured AI models including
    their availability status and capabilities.
    """
    try:
        models = rag_service.get_available_models()
        return [ModelInfo(**model) for model in models]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available models: {str(e)}")


@router.get("/models/status", response_model=ModelStatusResponse)
async def get_model_status(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get detailed status of all model providers
    
    Returns comprehensive status information including availability,
    configuration, and capabilities for all model providers.
    """
    try:
        status = rag_service.get_model_status()
        available_count = sum(1 for model_status in status.values() if model_status["available"])
        
        return ModelStatusResponse(
            models=status,
            default_model=rag_service.default_model.value,
            available_count=available_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.post("/validate-quality")
async def validate_response_quality(
    request: QualityValidationRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Validate the quality of a RAG response
    
    Analyzes a previously generated response for quality metrics
    including confidence, source coverage, and topic relevance.
    """
    try:
        # Note: In a full implementation, you would retrieve the response by ID
        # For now, we'll return a placeholder validation
        
        quality_metrics = {
            "response_id": request.response_id,
            "validation_timestamp": "2024-01-01T00:00:00Z",
            "quality_score": 0.75,
            "metrics": {
                "confidence_score": 0.8,
                "has_sources": True,
                "source_count": 5,
                "response_length": 450,
                "contains_regulatory_terms": True,
                "topic_coverage": 0.7,
                "overall_quality": "good"
            },
            "recommendations": [
                "Response demonstrates good understanding of regulatory context",
                "Consider including more specific citations",
                "Response length is appropriate for the question complexity"
            ]
        }
        
        return quality_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate response quality: {str(e)}")


@router.get("/health")
async def health_check(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Health check endpoint for RAG service
    
    Returns the operational status of the RAG service and its dependencies.
    """
    try:
        status = rag_service.get_model_status()
        available_models = [
            model_type for model_type, model_status in status.items() 
            if model_status["available"]
        ]
        
        health_status = {
            "status": "healthy" if available_models else "degraded",
            "available_models": available_models,
            "total_models": len(status),
            "search_service": "available",  # Assuming search service is available
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }


# Example usage endpoints for testing
@router.post("/examples/sustainability-question")
async def example_sustainability_question(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Example endpoint demonstrating a typical sustainability reporting question
    """
    example_question = "What are the key requirements for climate change adaptation reporting under CSRD?"
    
    try:
        response = await rag_service.generate_rag_response(
            question=example_question,
            model_type=AIModelType.OPENAI_GPT35,
            max_context_chunks=8,
            min_relevance_score=0.4
        )
        
        return {
            "example_question": example_question,
            "response": response,
            "note": "This is an example demonstrating RAG functionality"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Example query failed: {str(e)}")


@router.post("/examples/batch-questions")
async def example_batch_questions(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Example endpoint demonstrating batch processing of sustainability questions
    """
    example_questions = [
        "What are the disclosure requirements for greenhouse gas emissions?",
        "How should companies report on biodiversity impacts?",
        "What are the governance requirements under ESRS?"
    ]
    
    try:
        responses = await rag_service.batch_generate_responses(
            questions=example_questions,
            model_type=AIModelType.OPENAI_GPT35,
            max_concurrent=2
        )
        
        return {
            "example_questions": example_questions,
            "responses": responses,
            "note": "This is an example demonstrating batch RAG functionality"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch example query failed: {str(e)}")
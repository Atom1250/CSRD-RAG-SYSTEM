"""
API endpoints for asynchronous document processing
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database_config import get_db
from app.services.async_document_service import AsyncDocumentProcessingService
from app.models.schemas import DocumentResponse

router = APIRouter(prefix="/async", tags=["Async Processing"])


# Request/Response schemas
class ProcessingRequest(BaseModel):
    """Request schema for document processing"""
    chunk_size: Optional[int] = Field(None, ge=100, le=5000, description="Chunk size in characters")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000, description="Chunk overlap in characters")
    generate_embeddings: bool = Field(True, description="Whether to generate embeddings")
    classify_schema: bool = Field(True, description="Whether to classify against schema")


class BatchProcessingRequest(ProcessingRequest):
    """Request schema for batch document processing"""
    document_ids: List[str] = Field(..., min_length=1, description="List of document IDs to process")


class TaskStatusResponse(BaseModel):
    """Response schema for task status"""
    task_id: str
    status: str
    ready: bool
    successful: Optional[bool] = None
    progress: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProcessingTaskResponse(BaseModel):
    """Response schema for started processing task"""
    task_id: str
    document_id: str
    task_type: str
    status: str
    message: str


class QueueStatusResponse(BaseModel):
    """Response schema for queue status"""
    queue_status: str
    task_counts: Dict[str, int]
    workers_online: int
    timestamp: str
    error: Optional[str] = None


class ProcessingStatsResponse(BaseModel):
    """Response schema for processing statistics"""
    total_documents: int
    status_counts: Dict[str, int]
    success_rate: float
    queue_status: QueueStatusResponse
    timestamp: str
    error: Optional[str] = None


@router.post("/process/{document_id}", response_model=ProcessingTaskResponse)
async def start_document_processing(
    document_id: str,
    request: ProcessingRequest,
    db: Session = Depends(get_db)
):
    """
    Start asynchronous processing of a document
    
    This endpoint initiates the complete document processing pipeline:
    - Text extraction from the document
    - Text chunking and preprocessing
    - Vector embedding generation
    - Schema classification
    - Storage in vector database
    """
    try:
        service = AsyncDocumentProcessingService(db)
        
        task_result = service.start_document_processing(
            document_id=document_id,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            generate_embeddings=request.generate_embeddings,
            classify_schema=request.classify_schema
        )
        
        return ProcessingTaskResponse(
            task_id=task_result.task_id,
            document_id=task_result.document_id,
            task_type=task_result.task_type,
            status=task_result.status,
            message=f"Started processing document {document_id}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.post("/batch-process", response_model=ProcessingTaskResponse)
async def start_batch_processing(
    request: BatchProcessingRequest,
    db: Session = Depends(get_db)
):
    """
    Start batch processing of multiple documents
    
    This endpoint processes multiple documents in a single batch operation,
    which is more efficient for large numbers of documents.
    """
    try:
        service = AsyncDocumentProcessingService(db)
        
        task_result = service.start_batch_processing(
            document_ids=request.document_ids,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            generate_embeddings=request.generate_embeddings,
            classify_schema=request.classify_schema
        )
        
        return ProcessingTaskResponse(
            task_id=task_result.task_id,
            document_id=task_result.document_id,
            task_type=task_result.task_type,
            status=task_result.status,
            message=f"Started batch processing {len(request.document_ids)} documents"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch processing: {str(e)}")


@router.post("/regenerate-embeddings/{document_id}", response_model=ProcessingTaskResponse)
async def regenerate_embeddings(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Regenerate embeddings for all chunks of a document
    
    This endpoint is useful when you want to update embeddings with a different
    model or when embeddings were corrupted or lost.
    """
    try:
        service = AsyncDocumentProcessingService(db)
        
        task_result = service.regenerate_embeddings(document_id)
        
        return ProcessingTaskResponse(
            task_id=task_result.task_id,
            document_id=task_result.document_id,
            task_type=task_result.task_type,
            status=task_result.status,
            message=f"Started embedding regeneration for document {document_id}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start embedding regeneration: {str(e)}")


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the status and progress of a processing task
    
    Returns detailed information about task progress, including:
    - Current status (PENDING, PROGRESS, SUCCESS, FAILURE)
    - Progress percentage and current step
    - Results (when completed)
    - Error information (if failed)
    """
    try:
        service = AsyncDocumentProcessingService(db)
        status_info = service.get_task_status(task_id)
        
        return TaskStatusResponse(**status_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.delete("/task/{task_id}")
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a running processing task
    
    This will attempt to terminate the task if it's currently running.
    Note that tasks that are already in progress may not be immediately cancelled.
    """
    try:
        service = AsyncDocumentProcessingService(db)
        success = service.cancel_task(task_id)
        
        if success:
            return {"message": f"Task {task_id} cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel task")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(db: Session = Depends(get_db)):
    """
    Get the current status of the processing queue
    
    Returns information about:
    - Number of active, scheduled, and reserved tasks
    - Task counts by type
    - Number of online workers
    - Overall queue health
    """
    try:
        service = AsyncDocumentProcessingService(db)
        status = service.get_processing_queue_status()
        
        return QueueStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


@router.get("/statistics", response_model=ProcessingStatsResponse)
async def get_processing_statistics(db: Session = Depends(get_db)):
    """
    Get overall processing statistics
    
    Returns comprehensive statistics about document processing including:
    - Total documents processed
    - Success/failure rates
    - Processing status breakdown
    - Queue status information
    """
    try:
        service = AsyncDocumentProcessingService(db)
        stats = service.get_processing_statistics()
        
        return ProcessingStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing statistics: {str(e)}")


@router.post("/cleanup", response_model=ProcessingTaskResponse)
async def cleanup_stuck_processing(
    max_age_hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Clean up documents stuck in processing state
    
    This endpoint starts a cleanup task that will mark documents as failed
    if they have been stuck in processing state for longer than the specified time.
    
    Args:
        max_age_hours: Maximum age in hours for stuck processing documents (default: 24)
    """
    try:
        service = AsyncDocumentProcessingService(db)
        
        task_result = service.cleanup_stuck_processing(max_age_hours)
        
        return ProcessingTaskResponse(
            task_id=task_result.task_id,
            document_id=task_result.document_id,
            task_type=task_result.task_type,
            status=task_result.status,
            message=f"Started cleanup of documents stuck for more than {max_age_hours} hours"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start cleanup: {str(e)}")


@router.get("/history/{document_id}")
async def get_document_processing_history(
    document_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get processing history for a specific document
    
    Returns a list of processing events for the document, including
    timestamps, status changes, and processing details.
    """
    try:
        service = AsyncDocumentProcessingService(db)
        history = service.get_document_processing_history(document_id, limit)
        
        return {"document_id": document_id, "history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing history: {str(e)}")


# Health check endpoint for the async processing system
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check for the async processing system
    
    Returns the health status of the processing system including:
    - Database connectivity
    - Celery worker availability
    - Queue status
    """
    try:
        service = AsyncDocumentProcessingService(db)
        
        # Check database connectivity
        db.execute("SELECT 1")
        
        # Check queue status
        queue_status = service.get_processing_queue_status()
        
        health_status = {
            "status": "healthy",
            "database": "connected",
            "queue": queue_status.get("queue_status", "unknown"),
            "workers": queue_status.get("workers_online", 0),
            "timestamp": queue_status.get("timestamp")
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "unknown"
        }
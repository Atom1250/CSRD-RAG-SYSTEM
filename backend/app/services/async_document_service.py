"""
Async document processing service that orchestrates the complete document processing pipeline
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.models.database import Document, ProcessingStatus
from app.models.schemas import DocumentResponse, ProcessingStatus as ProcessingStatusEnum
from app.tasks.document_processing import (
    process_document_async,
    batch_process_documents,
    regenerate_document_embeddings,
    cleanup_failed_processing
)

logger = logging.getLogger(__name__)


class ProcessingTaskResult:
    """Wrapper for Celery task results with additional metadata"""
    
    def __init__(self, task_id: str, document_id: str, task_type: str):
        self.task_id = task_id
        self.document_id = document_id
        self.task_type = task_type
        self.celery_result = AsyncResult(task_id, app=celery_app)
    
    @property
    def status(self) -> str:
        """Get current task status"""
        return self.celery_result.status
    
    @property
    def result(self) -> Any:
        """Get task result (blocks until complete)"""
        return self.celery_result.result
    
    @property
    def info(self) -> Dict[str, Any]:
        """Get task info/progress"""
        return self.celery_result.info or {}
    
    @property
    def progress(self) -> Dict[str, Any]:
        """Get task progress information"""
        if self.status == "PROGRESS":
            return self.info
        elif self.status == "SUCCESS":
            return {"current": 100, "total": 100, "status": "Completed"}
        elif self.status == "FAILURE":
            return {"current": 0, "total": 100, "status": f"Failed: {self.info.get('error', 'Unknown error')}"}
        else:
            return {"current": 0, "total": 100, "status": self.status}
    
    def is_ready(self) -> bool:
        """Check if task is complete"""
        return self.celery_result.ready()
    
    def is_successful(self) -> bool:
        """Check if task completed successfully"""
        return self.celery_result.successful()
    
    def get_result_safe(self) -> Optional[Dict[str, Any]]:
        """Get result without blocking, returns None if not ready"""
        if self.is_ready():
            try:
                return self.result
            except Exception as e:
                logger.error(f"Error getting task result for {self.task_id}: {str(e)}")
                return {"error": str(e)}
        return None


class AsyncDocumentProcessingService:
    """Service for managing asynchronous document processing tasks"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_document_processing(
        self,
        document_id: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        generate_embeddings: bool = True,
        classify_schema: bool = True
    ) -> ProcessingTaskResult:
        """
        Start asynchronous processing of a document
        
        Args:
            document_id: Document ID to process
            chunk_size: Optional chunk size override
            chunk_overlap: Optional chunk overlap override
            generate_embeddings: Whether to generate embeddings
            classify_schema: Whether to classify against schema
            
        Returns:
            ProcessingTaskResult: Task result wrapper
            
        Raises:
            ValueError: If document not found or already processing
        """
        # Verify document exists and is not already processing
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        if document.processing_status == ProcessingStatus.PROCESSING:
            raise ValueError(f"Document {document_id} is already being processed")
        
        # Start async task
        task = process_document_async.delay(
            document_id=document_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            generate_embeddings=generate_embeddings,
            classify_schema=classify_schema
        )
        
        logger.info(f"Started async processing for document {document_id}, task ID: {task.id}")
        
        return ProcessingTaskResult(
            task_id=task.id,
            document_id=document_id,
            task_type="document_processing"
        )
    
    def start_batch_processing(
        self,
        document_ids: List[str],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        generate_embeddings: bool = True,
        classify_schema: bool = True
    ) -> ProcessingTaskResult:
        """
        Start batch processing of multiple documents
        
        Args:
            document_ids: List of document IDs to process
            chunk_size: Optional chunk size override
            chunk_overlap: Optional chunk overlap override
            generate_embeddings: Whether to generate embeddings
            classify_schema: Whether to classify against schema
            
        Returns:
            ProcessingTaskResult: Task result wrapper
            
        Raises:
            ValueError: If no valid documents found
        """
        if not document_ids:
            raise ValueError("No document IDs provided for batch processing")
        
        # Verify documents exist
        existing_docs = (
            self.db.query(Document.id)
            .filter(Document.id.in_(document_ids))
            .all()
        )
        existing_ids = [doc.id for doc in existing_docs]
        
        if not existing_ids:
            raise ValueError("No valid documents found for batch processing")
        
        # Start batch task
        task = batch_process_documents.delay(
            document_ids=existing_ids,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            generate_embeddings=generate_embeddings,
            classify_schema=classify_schema
        )
        
        logger.info(f"Started batch processing for {len(existing_ids)} documents, task ID: {task.id}")
        
        return ProcessingTaskResult(
            task_id=task.id,
            document_id=f"batch_{len(existing_ids)}_docs",
            task_type="batch_processing"
        )
    
    def regenerate_embeddings(self, document_id: str) -> ProcessingTaskResult:
        """
        Start regeneration of embeddings for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            ProcessingTaskResult: Task result wrapper
            
        Raises:
            ValueError: If document not found
        """
        # Verify document exists
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        # Start regeneration task
        task = regenerate_document_embeddings.delay(document_id=document_id)
        
        logger.info(f"Started embedding regeneration for document {document_id}, task ID: {task.id}")
        
        return ProcessingTaskResult(
            task_id=task.id,
            document_id=document_id,
            task_type="embedding_regeneration"
        )
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status and progress of a processing task
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Dict containing task status and progress information
        """
        try:
            result = AsyncResult(task_id, app=celery_app)
            
            status_info = {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "progress": {},
                "result": None,
                "error": None
            }
            
            if result.status == "PROGRESS":
                status_info["progress"] = result.info or {}
            elif result.status == "SUCCESS":
                status_info["result"] = result.result
                status_info["progress"] = {"current": 100, "total": 100, "status": "Completed"}
            elif result.status == "FAILURE":
                status_info["error"] = str(result.info) if result.info else "Unknown error"
                status_info["progress"] = {"current": 0, "total": 100, "status": f"Failed: {status_info['error']}"}
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": str(e),
                "ready": False,
                "successful": False,
                "progress": {"current": 0, "total": 100, "status": "Error retrieving status"}
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task
        
        Args:
            task_id: Celery task ID
            
        Returns:
            bool: True if cancellation was successful
        """
        try:
            celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False
    
    def get_processing_queue_status(self) -> Dict[str, Any]:
        """
        Get status of the processing queue
        
        Returns:
            Dict containing queue status information
        """
        try:
            # Get active tasks
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            # Count tasks by type
            task_counts = {
                "active": 0,
                "scheduled": 0,
                "reserved": 0,
                "document_processing": 0,
                "batch_processing": 0,
                "embedding_regeneration": 0
            }
            
            # Count active tasks
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    task_counts["active"] += len(tasks)
                    for task in tasks:
                        task_name = task.get("name", "")
                        if "process_document_async" in task_name:
                            task_counts["document_processing"] += 1
                        elif "batch_process_documents" in task_name:
                            task_counts["batch_processing"] += 1
                        elif "regenerate_document_embeddings" in task_name:
                            task_counts["embedding_regeneration"] += 1
            
            # Count scheduled tasks
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    task_counts["scheduled"] += len(tasks)
            
            # Count reserved tasks
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    task_counts["reserved"] += len(tasks)
            
            return {
                "queue_status": "healthy",
                "task_counts": task_counts,
                "workers_online": len(active_tasks) if active_tasks else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {
                "queue_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def cleanup_stuck_processing(self, max_age_hours: int = 24) -> ProcessingTaskResult:
        """
        Start cleanup of documents stuck in processing state
        
        Args:
            max_age_hours: Maximum age in hours for stuck processing documents
            
        Returns:
            ProcessingTaskResult: Task result wrapper
        """
        task = cleanup_failed_processing.delay(max_age_hours=max_age_hours)
        
        logger.info(f"Started cleanup of stuck processing documents, task ID: {task.id}")
        
        return ProcessingTaskResult(
            task_id=task.id,
            document_id="cleanup_task",
            task_type="cleanup"
        )
    
    def get_document_processing_history(
        self,
        document_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get processing history for a document
        
        Args:
            document_id: Document ID
            limit: Maximum number of history entries to return
            
        Returns:
            List of processing history entries
        """
        # This would typically query a task history table
        # For now, return current document status
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return []
        
        return [{
            "document_id": document_id,
            "status": document.processing_status.value,
            "timestamp": document.upload_date.isoformat(),
            "details": {
                "filename": document.filename,
                "file_size": document.file_size,
                "document_type": document.document_type.value,
                "schema_type": document.schema_type.value if document.schema_type else None
            }
        }]
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get overall processing statistics
        
        Returns:
            Dict containing processing statistics
        """
        try:
            # Query document processing statistics
            total_documents = self.db.query(Document).count()
            
            status_counts = {}
            for status in ProcessingStatus:
                count = self.db.query(Document).filter(Document.processing_status == status).count()
                status_counts[status.value] = count
            
            # Calculate processing rates
            completed_docs = status_counts.get("completed", 0)
            failed_docs = status_counts.get("failed", 0)
            processing_docs = status_counts.get("processing", 0)
            pending_docs = status_counts.get("pending", 0)
            
            success_rate = (completed_docs / total_documents * 100) if total_documents > 0 else 0
            
            return {
                "total_documents": total_documents,
                "status_counts": status_counts,
                "success_rate": round(success_rate, 2),
                "queue_status": self.get_processing_queue_status(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting processing statistics: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
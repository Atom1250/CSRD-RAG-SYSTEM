"""
Integration tests for async document processing service
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from app.models.database import Document, DocumentType, ProcessingStatus
from app.services.async_document_service import AsyncDocumentProcessingService, ProcessingTaskResult


class TestAsyncDocumentProcessingService:
    """Test cases for AsyncDocumentProcessingService"""
    
    def test_init(self, db_session: Session):
        """Test service initialization"""
        service = AsyncDocumentProcessingService(db_session)
        assert service.db == db_session
    
    def test_start_document_processing_success(self, db_session: Session, sample_document: Document):
        """Test starting document processing successfully"""
        service = AsyncDocumentProcessingService(db_session)
        
        with patch('app.tasks.document_processing.process_document_async.delay') as mock_delay:
            mock_task = Mock()
            mock_task.id = "test-task-id"
            mock_delay.return_value = mock_task
            
            result = service.start_document_processing(
                document_id=sample_document.id,
                chunk_size=500,
                generate_embeddings=True
            )
            
            assert isinstance(result, ProcessingTaskResult)
            assert result.task_id == "test-task-id"
            assert result.document_id == sample_document.id
            assert result.task_type == "document_processing"
            
            mock_delay.assert_called_once_with(
                document_id=sample_document.id,
                chunk_size=500,
                chunk_overlap=None,
                generate_embeddings=True,
                classify_schema=True
            )
    
    def test_start_document_processing_not_found(self, db_session: Session):
        """Test starting processing for non-existent document"""
        service = AsyncDocumentProcessingService(db_session)
        
        with pytest.raises(ValueError, match="Document not found"):
            service.start_document_processing("non-existent-id")
    
    def test_start_document_processing_already_processing(self, db_session: Session, sample_document: Document):
        """Test starting processing for document already being processed"""
        # Set document status to processing
        sample_document.processing_status = ProcessingStatus.PROCESSING
        db_session.commit()
        
        service = AsyncDocumentProcessingService(db_session)
        
        with pytest.raises(ValueError, match="already being processed"):
            service.start_document_processing(sample_document.id)
    
    def test_start_batch_processing_success(self, db_session: Session, sample_documents: list):
        """Test starting batch processing successfully"""
        service = AsyncDocumentProcessingService(db_session)
        document_ids = [doc.id for doc in sample_documents]
        
        with patch('app.tasks.document_processing.batch_process_documents.delay') as mock_delay:
            mock_task = Mock()
            mock_task.id = "batch-task-id"
            mock_delay.return_value = mock_task
            
            result = service.start_batch_processing(
                document_ids=document_ids,
                chunk_size=800
            )
            
            assert isinstance(result, ProcessingTaskResult)
            assert result.task_id == "batch-task-id"
            assert result.task_type == "batch_processing"
            
            mock_delay.assert_called_once_with(
                document_ids=document_ids,
                chunk_size=800,
                chunk_overlap=None,
                generate_embeddings=True,
                classify_schema=True
            )
    
    def test_start_batch_processing_empty_list(self, db_session: Session):
        """Test starting batch processing with empty document list"""
        service = AsyncDocumentProcessingService(db_session)
        
        with pytest.raises(ValueError, match="No document IDs provided"):
            service.start_batch_processing([])
    
    def test_regenerate_embeddings_success(self, db_session: Session, sample_document: Document):
        """Test regenerating embeddings successfully"""
        service = AsyncDocumentProcessingService(db_session)
        
        with patch('app.tasks.document_processing.regenerate_document_embeddings.delay') as mock_delay:
            mock_task = Mock()
            mock_task.id = "regen-task-id"
            mock_delay.return_value = mock_task
            
            result = service.regenerate_embeddings(sample_document.id)
            
            assert isinstance(result, ProcessingTaskResult)
            assert result.task_id == "regen-task-id"
            assert result.document_id == sample_document.id
            assert result.task_type == "embedding_regeneration"
    
    def test_get_task_status_progress(self, db_session: Session):
        """Test getting task status for task in progress"""
        service = AsyncDocumentProcessingService(db_session)
        
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.status = "PROGRESS"
            mock_result.ready.return_value = False
            mock_result.info = {"current": 50, "total": 100, "status": "Processing chunks"}
            mock_result_class.return_value = mock_result
            
            status = service.get_task_status("test-task-id")
            
            assert status["task_id"] == "test-task-id"
            assert status["status"] == "PROGRESS"
            assert status["ready"] is False
            assert status["progress"]["current"] == 50
            assert status["progress"]["total"] == 100
    
    def test_get_task_status_success(self, db_session: Session):
        """Test getting task status for successful task"""
        service = AsyncDocumentProcessingService(db_session)
        
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.status = "SUCCESS"
            mock_result.ready.return_value = True
            mock_result.successful.return_value = True
            mock_result.result = {"document_id": "test-doc", "total_chunks": 5}
            mock_result_class.return_value = mock_result
            
            status = service.get_task_status("test-task-id")
            
            assert status["status"] == "SUCCESS"
            assert status["ready"] is True
            assert status["successful"] is True
            assert status["result"]["total_chunks"] == 5
            assert status["progress"]["current"] == 100
    
    def test_get_task_status_failure(self, db_session: Session):
        """Test getting task status for failed task"""
        service = AsyncDocumentProcessingService(db_session)
        
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.status = "FAILURE"
            mock_result.ready.return_value = True
            mock_result.successful.return_value = False
            mock_result.info = "Processing failed"
            mock_result_class.return_value = mock_result
            
            status = service.get_task_status("test-task-id")
            
            assert status["status"] == "FAILURE"
            assert status["ready"] is True
            assert status["successful"] is False
            assert status["error"] == "Processing failed"
    
    def test_cancel_task_success(self, db_session: Session):
        """Test cancelling a task successfully"""
        service = AsyncDocumentProcessingService(db_session)
        
        with patch('app.core.celery_app.celery_app.control.revoke') as mock_revoke:
            result = service.cancel_task("test-task-id")
            
            assert result is True
            mock_revoke.assert_called_once_with("test-task-id", terminate=True)
    
    def test_cancel_task_failure(self, db_session: Session):
        """Test cancelling a task with failure"""
        service = AsyncDocumentProcessingService(db_session)
        
        with patch('app.core.celery_app.celery_app.control.revoke') as mock_revoke:
            mock_revoke.side_effect = Exception("Revoke failed")
            
            result = service.cancel_task("test-task-id")
            
            assert result is False
    
    def test_get_processing_statistics(self, db_session: Session, sample_documents: list):
        """Test getting processing statistics"""
        # Set different statuses for documents
        sample_documents[0].processing_status = ProcessingStatus.COMPLETED
        sample_documents[1].processing_status = ProcessingStatus.FAILED
        if len(sample_documents) > 2:
            sample_documents[2].processing_status = ProcessingStatus.PROCESSING
        db_session.commit()
        
        service = AsyncDocumentProcessingService(db_session)
        
        with patch.object(service, 'get_processing_queue_status') as mock_queue_status:
            mock_queue_status.return_value = {
                "queue_status": "healthy",
                "task_counts": {"active": 1},
                "workers_online": 1,
                "timestamp": "2023-01-01T00:00:00"
            }
            
            stats = service.get_processing_statistics()
            
            assert stats["total_documents"] == len(sample_documents)
            assert "completed" in stats["status_counts"]
            assert "failed" in stats["status_counts"]
            assert stats["success_rate"] >= 0
            assert "queue_status" in stats


class TestProcessingTaskResult:
    """Test cases for ProcessingTaskResult wrapper"""
    
    def test_init(self):
        """Test ProcessingTaskResult initialization"""
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result_class.return_value = mock_result
            
            task_result = ProcessingTaskResult("task-id", "doc-id", "processing")
            
            assert task_result.task_id == "task-id"
            assert task_result.document_id == "doc-id"
            assert task_result.task_type == "processing"
            assert task_result.celery_result == mock_result
    
    def test_status_property(self):
        """Test status property"""
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.status = "PROGRESS"
            mock_result_class.return_value = mock_result
            
            task_result = ProcessingTaskResult("task-id", "doc-id", "processing")
            
            assert task_result.status == "PROGRESS"
    
    def test_progress_property_in_progress(self):
        """Test progress property for task in progress"""
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.status = "PROGRESS"
            mock_result.info = {"current": 75, "total": 100, "status": "Almost done"}
            mock_result_class.return_value = mock_result
            
            task_result = ProcessingTaskResult("task-id", "doc-id", "processing")
            progress = task_result.progress
            
            assert progress["current"] == 75
            assert progress["total"] == 100
            assert progress["status"] == "Almost done"
    
    def test_progress_property_success(self):
        """Test progress property for successful task"""
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.status = "SUCCESS"
            mock_result_class.return_value = mock_result
            
            task_result = ProcessingTaskResult("task-id", "doc-id", "processing")
            progress = task_result.progress
            
            assert progress["current"] == 100
            assert progress["total"] == 100
            assert progress["status"] == "Completed"
    
    def test_is_ready(self):
        """Test is_ready method"""
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.ready.return_value = True
            mock_result_class.return_value = mock_result
            
            task_result = ProcessingTaskResult("task-id", "doc-id", "processing")
            
            assert task_result.is_ready() is True
    
    def test_get_result_safe_ready(self):
        """Test get_result_safe when task is ready"""
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.ready.return_value = True
            mock_result.result = {"status": "completed"}
            mock_result_class.return_value = mock_result
            
            task_result = ProcessingTaskResult("task-id", "doc-id", "processing")
            result = task_result.get_result_safe()
            
            assert result == {"status": "completed"}
    
    def test_get_result_safe_not_ready(self):
        """Test get_result_safe when task is not ready"""
        with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.ready.return_value = False
            mock_result_class.return_value = mock_result
            
            task_result = ProcessingTaskResult("task-id", "doc-id", "processing")
            result = task_result.get_result_safe()
            
            assert result is None


class TestAsyncProcessingAPI:
    """Test cases for async processing API endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_start_document_processing_success(self, sample_document: Document):
        """Test starting document processing via API"""
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.start_document_processing') as mock_start:
            mock_task_result = Mock()
            mock_task_result.task_id = "api-task-id"
            mock_task_result.document_id = sample_document.id
            mock_task_result.task_type = "document_processing"
            mock_task_result.status = "PENDING"
            mock_start.return_value = mock_task_result
            
            response = self.client.post(
                f"/api/async/process/{sample_document.id}",
                json={
                    "chunk_size": 1000,
                    "generate_embeddings": True,
                    "classify_schema": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "api-task-id"
            assert data["document_id"] == sample_document.id
            assert data["task_type"] == "document_processing"
    
    def test_start_document_processing_not_found(self):
        """Test starting processing for non-existent document"""
        response = self.client.post(
            "/api/async/process/non-existent-id",
            json={"generate_embeddings": True}
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_start_batch_processing_success(self, sample_documents: list):
        """Test starting batch processing via API"""
        document_ids = [doc.id for doc in sample_documents[:2]]
        
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.start_batch_processing') as mock_start:
            mock_task_result = Mock()
            mock_task_result.task_id = "batch-api-task-id"
            mock_task_result.document_id = f"batch_{len(document_ids)}_docs"
            mock_task_result.task_type = "batch_processing"
            mock_task_result.status = "PENDING"
            mock_start.return_value = mock_task_result
            
            response = self.client.post(
                "/api/async/batch-process",
                json={
                    "document_ids": document_ids,
                    "chunk_size": 800,
                    "generate_embeddings": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "batch-api-task-id"
            assert data["task_type"] == "batch_processing"
    
    def test_get_task_status_success(self):
        """Test getting task status via API"""
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.get_task_status') as mock_get_status:
            mock_get_status.return_value = {
                "task_id": "test-task-id",
                "status": "PROGRESS",
                "ready": False,
                "successful": None,
                "progress": {"current": 60, "total": 100},
                "result": None,
                "error": None
            }
            
            response = self.client.get("/api/async/task/test-task-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["status"] == "PROGRESS"
            assert data["progress"]["current"] == 60
    
    def test_cancel_task_success(self):
        """Test cancelling task via API"""
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.cancel_task') as mock_cancel:
            mock_cancel.return_value = True
            
            response = self.client.delete("/api/async/task/test-task-id")
            
            assert response.status_code == 200
            assert "cancelled successfully" in response.json()["message"]
    
    def test_get_queue_status_success(self):
        """Test getting queue status via API"""
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.get_processing_queue_status') as mock_get_queue:
            mock_get_queue.return_value = {
                "queue_status": "healthy",
                "task_counts": {"active": 2, "scheduled": 1},
                "workers_online": 1,
                "timestamp": "2023-01-01T00:00:00"
            }
            
            response = self.client.get("/api/async/queue/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["queue_status"] == "healthy"
            assert data["task_counts"]["active"] == 2
    
    def test_get_processing_statistics_success(self):
        """Test getting processing statistics via API"""
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.get_processing_statistics') as mock_get_stats:
            mock_get_stats.return_value = {
                "total_documents": 10,
                "status_counts": {"completed": 8, "failed": 1, "processing": 1},
                "success_rate": 80.0,
                "queue_status": {"queue_status": "healthy"},
                "timestamp": "2023-01-01T00:00:00"
            }
            
            response = self.client.get("/api/async/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_documents"] == 10
            assert data["success_rate"] == 80.0
    
    def test_health_check_success(self):
        """Test health check endpoint"""
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.get_processing_queue_status') as mock_get_queue:
            mock_get_queue.return_value = {
                "queue_status": "healthy",
                "workers_online": 1,
                "timestamp": "2023-01-01T00:00:00"
            }
            
            response = self.client.get("/api/async/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"


# Fixtures for testing
@pytest.fixture
def sample_document(db_session: Session) -> Document:
    """Create a sample document for testing"""
    document = Document(
        filename="test_document.pdf",
        file_path="/tmp/test_document.pdf",
        file_size=1024,
        document_type=DocumentType.PDF,
        processing_status=ProcessingStatus.PENDING
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def sample_documents(db_session: Session) -> list:
    """Create multiple sample documents for testing"""
    documents = []
    for i in range(3):
        document = Document(
            filename=f"test_document_{i}.pdf",
            file_path=f"/tmp/test_document_{i}.pdf",
            file_size=1024 * (i + 1),
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.PENDING
        )
        db_session.add(document)
        documents.append(document)
    
    db_session.commit()
    for doc in documents:
        db_session.refresh(doc)
    
    return documents
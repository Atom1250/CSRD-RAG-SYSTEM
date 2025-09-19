"""
End-to-end integration tests for the complete document processing pipeline
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import Document, DocumentType, ProcessingStatus, TextChunk
from app.services.document_service import DocumentService
from app.services.async_document_service import AsyncDocumentProcessingService
from app.services.text_processing_service import TextProcessingService


class TestDocumentProcessingPipeline:
    """End-to-end tests for the complete document processing pipeline"""
    
    def setup_method(self):
        """Set up test client and temporary files"""
        self.client = TestClient(app)
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_pdf(self, content: str = "Test PDF content") -> Path:
        """Create a test PDF file"""
        # For testing, we'll create a simple text file that mimics a PDF
        # In a real scenario, you'd use a PDF library to create actual PDFs
        test_file = Path(self.temp_dir) / "test_document.pdf"
        test_file.write_text(content)
        return test_file
    
    def create_test_txt(self, content: str = "Test text content") -> Path:
        """Create a test text file"""
        test_file = Path(self.temp_dir) / "test_document.txt"
        test_file.write_text(content)
        return test_file
    
    @patch('app.services.vector_service.embedding_service')
    def test_complete_document_processing_pipeline(self, mock_embedding_service, db_session: Session):
        """Test the complete document processing pipeline from upload to completion"""
        # Mock embedding service
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_service.store_embeddings.return_value = True
        
        # Create test document content
        test_content = """
        This is a test document for CSRD compliance.
        It contains information about environmental sustainability reporting.
        Companies must disclose their environmental impact according to ESRS standards.
        This includes data on climate change, pollution, water usage, and biodiversity.
        The document should be processed into chunks for vector search.
        """
        
        test_file = self.create_test_txt(test_content)
        
        # Step 1: Upload document
        document_service = DocumentService(db_session)
        
        # Mock file upload
        from fastapi import UploadFile
        from io import BytesIO
        
        file_content = test_content.encode()
        upload_file = UploadFile(
            filename="test_document.txt",
            file=BytesIO(file_content),
            size=len(file_content)
        )
        
        with patch('app.services.document_service.Path.exists', return_value=True):
            with patch('app.services.document_service.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = len(file_content)
                
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.write = Mock()
                    
                    # Upload document
                    document_response = await document_service.upload_document(
                        upload_file, 
                        schema_type="EU_ESRS_CSRD"
                    )
        
        assert document_response.filename == "test_document.txt"
        assert document_response.processing_status == ProcessingStatus.PENDING
        
        # Step 2: Process document synchronously (simulating async task completion)
        text_service = TextProcessingService(db_session)
        
        # Mock file reading for text extraction
        with patch('app.services.text_processing_service.open', create=True) as mock_file_open:
            mock_file_open.return_value.__enter__.return_value.read.return_value = test_content
            
            # Process document text
            chunks = await text_service.process_document_text(
                document_id=document_response.id,
                chunk_size=200,
                chunk_overlap=50,
                generate_embeddings=True
            )
        
        # Verify chunks were created
        assert len(chunks) > 0
        assert all(chunk.document_id == document_response.id for chunk in chunks)
        assert all(len(chunk.content) > 0 for chunk in chunks)
        
        # Step 3: Verify document status was updated
        updated_document = document_service.get_document_by_id(document_response.id)
        assert updated_document.processing_status == ProcessingStatus.COMPLETED
        
        # Step 4: Verify chunks are stored in database
        db_chunks = (
            db_session.query(TextChunk)
            .filter(TextChunk.document_id == document_response.id)
            .order_by(TextChunk.chunk_index)
            .all()
        )
        
        assert len(db_chunks) == len(chunks)
        for i, chunk in enumerate(db_chunks):
            assert chunk.chunk_index == i
            assert chunk.content is not None
            assert len(chunk.content) > 0
        
        # Step 5: Verify embeddings were generated (mocked)
        mock_embedding_service.store_embeddings.assert_called_once()
        stored_chunks = mock_embedding_service.store_embeddings.call_args[0][0]
        assert len(stored_chunks) == len(chunks)
        
        # Step 6: Test search functionality would work
        # (This would be tested separately in search service tests)
        
        print(f"✅ Successfully processed document with {len(chunks)} chunks")
    
    @patch('app.tasks.document_processing.process_document_async.delay')
    def test_async_document_processing_workflow(self, mock_delay, db_session: Session):
        """Test the async document processing workflow via API"""
        # Create a document in the database
        document = Document(
            filename="async_test.pdf",
            file_path="/tmp/async_test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.PENDING
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "test-task-123"
        mock_delay.return_value = mock_task
        
        # Start async processing via API
        response = self.client.post(
            f"/api/async/process/{document.id}",
            json={
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "generate_embeddings": True,
                "classify_schema": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["document_id"] == document.id
        assert data["task_type"] == "document_processing"
        
        # Verify task was called with correct parameters
        mock_delay.assert_called_once_with(
            document_id=document.id,
            chunk_size=1000,
            chunk_overlap=200,
            generate_embeddings=True,
            classify_schema=True
        )
    
    @patch('app.tasks.document_processing.batch_process_documents.delay')
    def test_batch_processing_workflow(self, mock_delay, db_session: Session):
        """Test batch processing workflow via API"""
        # Create multiple documents
        documents = []
        for i in range(3):
            document = Document(
                filename=f"batch_test_{i}.pdf",
                file_path=f"/tmp/batch_test_{i}.pdf",
                file_size=1024 * (i + 1),
                document_type=DocumentType.PDF,
                processing_status=ProcessingStatus.PENDING
            )
            db_session.add(document)
            documents.append(document)
        
        db_session.commit()
        for doc in documents:
            db_session.refresh(doc)
        
        document_ids = [doc.id for doc in documents]
        
        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "batch-task-456"
        mock_delay.return_value = mock_task
        
        # Start batch processing via API
        response = self.client.post(
            "/api/async/batch-process",
            json={
                "document_ids": document_ids,
                "chunk_size": 800,
                "generate_embeddings": True,
                "classify_schema": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "batch-task-456"
        assert data["task_type"] == "batch_processing"
        
        # Verify task was called with correct parameters
        mock_delay.assert_called_once_with(
            document_ids=document_ids,
            chunk_size=800,
            chunk_overlap=None,
            generate_embeddings=True,
            classify_schema=False
        )
    
    @patch('app.services.async_document_service.AsyncResult')
    def test_task_status_monitoring(self, mock_async_result):
        """Test task status monitoring via API"""
        # Mock task in progress
        mock_result = Mock()
        mock_result.status = "PROGRESS"
        mock_result.ready.return_value = False
        mock_result.info = {
            "current": 60,
            "total": 100,
            "status": "Generating embeddings"
        }
        mock_async_result.return_value = mock_result
        
        # Get task status
        response = self.client.get("/api/async/task/test-task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "PROGRESS"
        assert data["ready"] is False
        assert data["progress"]["current"] == 60
        assert data["progress"]["status"] == "Generating embeddings"
    
    @patch('app.services.async_document_service.AsyncResult')
    def test_task_completion_monitoring(self, mock_async_result):
        """Test monitoring completed task via API"""
        # Mock completed task
        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {
            "document_id": "test-doc-id",
            "status": "completed",
            "total_chunks": 8,
            "embeddings_generated": 8
        }
        mock_async_result.return_value = mock_result
        
        # Get task status
        response = self.client.get("/api/async/task/completed-task-789")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["ready"] is True
        assert data["successful"] is True
        assert data["result"]["total_chunks"] == 8
        assert data["progress"]["current"] == 100
    
    def test_processing_statistics_api(self, db_session: Session):
        """Test processing statistics API endpoint"""
        # Create documents with different statuses
        statuses = [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.PROCESSING]
        for i, status in enumerate(statuses):
            document = Document(
                filename=f"stats_test_{i}.pdf",
                file_path=f"/tmp/stats_test_{i}.pdf",
                file_size=1024,
                document_type=DocumentType.PDF,
                processing_status=status
            )
            db_session.add(document)
        
        db_session.commit()
        
        # Mock queue status
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.get_processing_queue_status') as mock_queue:
            mock_queue.return_value = {
                "queue_status": "healthy",
                "task_counts": {"active": 1, "scheduled": 0},
                "workers_online": 1,
                "timestamp": "2023-01-01T00:00:00"
            }
            
            # Get processing statistics
            response = self.client.get("/api/async/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_documents"] == 3
            assert data["status_counts"]["completed"] == 1
            assert data["status_counts"]["failed"] == 1
            assert data["status_counts"]["processing"] == 1
            assert data["success_rate"] == pytest.approx(33.33, rel=1e-2)
    
    def test_health_check_api(self):
        """Test health check API endpoint"""
        with patch('app.services.async_document_service.AsyncDocumentProcessingService.get_processing_queue_status') as mock_queue:
            mock_queue.return_value = {
                "queue_status": "healthy",
                "workers_online": 2,
                "timestamp": "2023-01-01T00:00:00"
            }
            
            response = self.client.get("/api/async/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"
            assert data["queue"] == "healthy"
            assert data["workers"] == 2
    
    def test_error_handling_invalid_document(self):
        """Test error handling for invalid document ID"""
        response = self.client.post(
            "/api/async/process/invalid-document-id",
            json={"generate_embeddings": True}
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_error_handling_invalid_batch(self):
        """Test error handling for invalid batch request"""
        response = self.client.post(
            "/api/async/batch-process",
            json={
                "document_ids": [],  # Empty list
                "generate_embeddings": True
            }
        )
        
        assert response.status_code == 400
        assert "No document IDs provided" in response.json()["detail"]
    
    @patch('app.core.celery_app.celery_app.control.revoke')
    def test_task_cancellation(self, mock_revoke):
        """Test task cancellation via API"""
        response = self.client.delete("/api/async/task/test-task-to-cancel")
        
        assert response.status_code == 200
        assert "cancelled successfully" in response.json()["message"]
        mock_revoke.assert_called_once_with("test-task-to-cancel", terminate=True)
    
    def test_processing_request_validation(self):
        """Test request validation for processing parameters"""
        # Test invalid chunk size
        response = self.client.post(
            "/api/async/process/some-doc-id",
            json={
                "chunk_size": 50,  # Too small
                "generate_embeddings": True
            }
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test invalid chunk overlap
        response = self.client.post(
            "/api/async/process/some-doc-id",
            json={
                "chunk_overlap": -10,  # Negative
                "generate_embeddings": True
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestDocumentProcessingErrorScenarios:
    """Test error scenarios in document processing"""
    
    def test_processing_with_corrupted_file(self, db_session: Session):
        """Test processing a document with corrupted file"""
        # Create document with non-existent file path
        document = Document(
            filename="corrupted.pdf",
            file_path="/non/existent/path.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.PENDING
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        text_service = TextProcessingService(db_session)
        
        # Attempt to process document
        with pytest.raises(Exception):  # Should raise TextExtractionError
            text_service.extract_text_from_document(document)
    
    def test_processing_with_empty_content(self, db_session: Session):
        """Test processing a document with empty content"""
        document = Document(
            filename="empty.txt",
            file_path="/tmp/empty.txt",
            file_size=0,
            document_type=DocumentType.TXT,
            processing_status=ProcessingStatus.PENDING
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        text_service = TextProcessingService(db_session)
        
        # Mock empty file
        with patch('app.services.text_processing_service.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = ""
            
            with pytest.raises(Exception):  # Should raise TextExtractionError
                text_service.extract_text_from_document(document)
    
    @patch('app.services.vector_service.embedding_service')
    def test_processing_with_embedding_failure(self, mock_embedding_service, db_session: Session):
        """Test processing when embedding generation fails"""
        # Mock embedding service to fail
        mock_embedding_service.generate_embedding.side_effect = Exception("Embedding failed")
        
        document = Document(
            filename="embedding_fail.txt",
            file_path="/tmp/embedding_fail.txt",
            file_size=100,
            document_type=DocumentType.TXT,
            processing_status=ProcessingStatus.PENDING
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        text_service = TextProcessingService(db_session)
        
        # Mock file content
        test_content = "This is test content for embedding failure test."
        with patch('app.services.text_processing_service.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = test_content
            
            # Process document - should complete but without embeddings
            chunks = await text_service.process_document_text(
                document_id=document.id,
                generate_embeddings=True
            )
            
            # Should still create chunks even if embedding fails
            assert len(chunks) > 0
            
            # Document should still be marked as completed
            db_session.refresh(document)
            assert document.processing_status == ProcessingStatus.COMPLETED
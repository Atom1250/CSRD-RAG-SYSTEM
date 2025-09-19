"""
Tests for Celery tasks
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.models.database import Document, DocumentType, ProcessingStatus, TextChunk
from app.tasks.document_processing import (
    process_document_async,
    batch_process_documents,
    regenerate_document_embeddings,
    cleanup_failed_processing
)


class TestDocumentProcessingTasks:
    """Test cases for document processing Celery tasks"""
    
    @patch('app.tasks.document_processing.get_db_session')
    @patch('app.tasks.document_processing.TextProcessingService')
    @patch('app.tasks.document_processing.SchemaService')
    def test_process_document_async_success(self, mock_schema_service, mock_text_service, mock_get_db):
        """Test successful document processing task"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock document
        mock_document = Mock()
        mock_document.id = "test-doc-id"
        mock_document.processing_status = ProcessingStatus.PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document
        
        # Mock text processing service
        mock_text_instance = Mock()
        mock_text_service.return_value = mock_text_instance
        mock_text_instance.extract_text_from_document.return_value = "Sample text content"
        mock_text_instance.preprocess_text.return_value = "Processed text content"
        mock_text_instance.chunk_text.return_value = ["Chunk 1", "Chunk 2", "Chunk 3"]
        
        # Mock schema service
        mock_schema_instance = Mock()
        mock_schema_service.return_value = mock_schema_instance
        mock_schema_instance.classify_document.return_value = ["element1", "element2"]
        
        # Mock TextChunk creation
        with patch('app.tasks.document_processing.TextChunk') as mock_text_chunk:
            mock_chunk_instances = []
            for i in range(3):
                mock_chunk = Mock()
                mock_chunk.id = f"chunk-{i}"
                mock_chunk.created_at = Mock()
                mock_chunk.created_at.isoformat.return_value = "2023-01-01T00:00:00"
                mock_chunk_instances.append(mock_chunk)
            
            mock_text_chunk.side_effect = mock_chunk_instances
            
            # Mock embedding service
            with patch('app.services.vector_service.embedding_service') as mock_embedding_service:
                mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
                
                # Create mock task
                mock_task = Mock()
                mock_task.update_state = Mock()
                
                # Execute task
                result = process_document_async(
                    mock_task,
                    document_id="test-doc-id",
                    chunk_size=1000,
                    generate_embeddings=True,
                    classify_schema=True
                )
                
                # Verify results
                assert result["document_id"] == "test-doc-id"
                assert result["status"] == "completed"
                assert result["total_chunks"] == 3
                assert result["embeddings_generated"] == 3
                assert result["schema_elements_found"] == 2
                
                # Verify document status was updated
                assert mock_document.processing_status == ProcessingStatus.COMPLETED
                
                # Verify task progress updates
                assert mock_task.update_state.call_count >= 5
    
    @patch('app.tasks.document_processing.get_db_session')
    def test_process_document_async_document_not_found(self, mock_get_db):
        """Test processing task with non-existent document"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute task and expect exception
        with pytest.raises(ValueError, match="Document not found"):
            process_document_async(
                mock_task,
                document_id="non-existent-id"
            )
    
    @patch('app.tasks.document_processing.get_db_session')
    @patch('app.tasks.document_processing.TextProcessingService')
    def test_process_document_async_text_extraction_failure(self, mock_text_service, mock_get_db):
        """Test processing task with text extraction failure"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_document = Mock()
        mock_document.id = "test-doc-id"
        mock_document.processing_status = ProcessingStatus.PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document
        
        # Mock text processing service to raise exception
        mock_text_instance = Mock()
        mock_text_service.return_value = mock_text_instance
        mock_text_instance.extract_text_from_document.side_effect = Exception("Text extraction failed")
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute task and expect exception
        with pytest.raises(Exception, match="Text extraction failed"):
            process_document_async(
                mock_task,
                document_id="test-doc-id"
            )
        
        # Verify document status was set to failed
        assert mock_document.processing_status == ProcessingStatus.FAILED
    
    @patch('app.tasks.document_processing.process_document_async.apply')
    def test_batch_process_documents_success(self, mock_apply):
        """Test successful batch processing task"""
        # Mock individual task results
        mock_results = []
        for i in range(3):
            mock_result = Mock()
            mock_result.get.return_value = {
                "document_id": f"doc-{i}",
                "status": "completed",
                "total_chunks": 5
            }
            mock_results.append(mock_result)
        
        mock_apply.side_effect = mock_results
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute batch task
        result = batch_process_documents(
            mock_task,
            document_ids=["doc-0", "doc-1", "doc-2"],
            chunk_size=1000,
            generate_embeddings=True
        )
        
        # Verify results
        assert result["status"] == "completed"
        assert result["total_documents"] == 3
        assert len(result["processed_documents"]) == 3
        assert len(result["failed_documents"]) == 0
        assert result["success_rate"] == 100.0
        
        # Verify individual tasks were called
        assert mock_apply.call_count == 3
    
    @patch('app.tasks.document_processing.process_document_async.apply')
    def test_batch_process_documents_partial_failure(self, mock_apply):
        """Test batch processing with some failures"""
        # Mock mixed results
        mock_results = []
        
        # First document succeeds
        mock_result_1 = Mock()
        mock_result_1.get.return_value = {"document_id": "doc-0", "status": "completed", "total_chunks": 5}
        mock_results.append(mock_result_1)
        
        # Second document fails
        mock_result_2 = Mock()
        mock_result_2.get.side_effect = Exception("Processing failed")
        mock_results.append(mock_result_2)
        
        # Third document succeeds
        mock_result_3 = Mock()
        mock_result_3.get.return_value = {"document_id": "doc-2", "status": "completed", "total_chunks": 3}
        mock_results.append(mock_result_3)
        
        mock_apply.side_effect = mock_results
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute batch task
        result = batch_process_documents(
            mock_task,
            document_ids=["doc-0", "doc-1", "doc-2"]
        )
        
        # Verify results
        assert result["status"] == "completed"
        assert result["total_documents"] == 3
        assert len(result["processed_documents"]) == 2
        assert len(result["failed_documents"]) == 1
        assert result["success_rate"] == pytest.approx(66.67, rel=1e-2)
        
        # Check failed document details
        failed_doc = result["failed_documents"][0]
        assert failed_doc["document_id"] == "doc-1"
        assert failed_doc["status"] == "failed"
        assert "Processing failed" in failed_doc["error"]
    
    def test_batch_process_documents_empty_list(self):
        """Test batch processing with empty document list"""
        mock_task = Mock()
        
        result = batch_process_documents(mock_task, document_ids=[])
        
        assert result["status"] == "completed"
        assert result["processed_documents"] == []
        assert result["failed_documents"] == []
    
    @patch('app.tasks.document_processing.get_db_session')
    @patch('app.tasks.document_processing.TextProcessingService')
    def test_regenerate_document_embeddings_success(self, mock_text_service, mock_get_db):
        """Test successful embedding regeneration task"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_text_instance = Mock()
        mock_text_service.return_value = mock_text_instance
        
        # Mock async method
        async def mock_regenerate_embeddings(doc_id):
            return True
        
        mock_text_instance.regenerate_embeddings = mock_regenerate_embeddings
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute task
        result = regenerate_document_embeddings(
            mock_task,
            document_id="test-doc-id"
        )
        
        # Verify results
        assert result["document_id"] == "test-doc-id"
        assert result["status"] == "completed"
        assert result["embeddings_regenerated"] is True
        
        # Verify progress updates
        assert mock_task.update_state.call_count >= 2
    
    @patch('app.tasks.document_processing.get_db_session')
    @patch('app.tasks.document_processing.TextProcessingService')
    def test_regenerate_document_embeddings_failure(self, mock_text_service, mock_get_db):
        """Test embedding regeneration task failure"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_text_instance = Mock()
        mock_text_service.return_value = mock_text_instance
        
        # Mock async method to raise exception
        async def mock_regenerate_embeddings(doc_id):
            raise Exception("Regeneration failed")
        
        mock_text_instance.regenerate_embeddings = mock_regenerate_embeddings
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute task and expect exception
        with pytest.raises(Exception, match="Regeneration failed"):
            regenerate_document_embeddings(
                mock_task,
                document_id="test-doc-id"
            )
        
        # Verify failure state was set
        mock_task.update_state.assert_called_with(
            state="FAILURE",
            meta={"error": "Regeneration failed", "document_id": "test-doc-id"}
        )
    
    @patch('app.tasks.document_processing.get_db_session')
    def test_cleanup_failed_processing_success(self, mock_get_db):
        """Test successful cleanup of stuck processing documents"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock stuck documents
        mock_stuck_docs = []
        for i in range(2):
            mock_doc = Mock()
            mock_doc.processing_status = ProcessingStatus.PROCESSING
            mock_stuck_docs.append(mock_doc)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_stuck_docs
        
        mock_task = Mock()
        
        # Execute cleanup task
        result = cleanup_failed_processing(mock_task, max_age_hours=24)
        
        # Verify results
        assert result["status"] == "completed"
        assert result["cleaned_documents"] == 2
        assert "cutoff_time" in result
        
        # Verify documents were marked as failed
        for doc in mock_stuck_docs:
            assert doc.processing_status == ProcessingStatus.FAILED
        
        # Verify database commit was called
        mock_db.commit.assert_called_once()
    
    @patch('app.tasks.document_processing.get_db_session')
    def test_cleanup_failed_processing_no_stuck_documents(self, mock_get_db):
        """Test cleanup when no stuck documents exist"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        mock_task = Mock()
        
        # Execute cleanup task
        result = cleanup_failed_processing(mock_task, max_age_hours=48)
        
        # Verify results
        assert result["status"] == "completed"
        assert result["cleaned_documents"] == 0
    
    @patch('app.tasks.document_processing.get_db_session')
    def test_cleanup_failed_processing_database_error(self, mock_get_db):
        """Test cleanup task with database error"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")
        
        mock_task = Mock()
        
        # Execute cleanup task and expect exception
        with pytest.raises(Exception, match="Database error"):
            cleanup_failed_processing(mock_task, max_age_hours=24)


class TestCeleryTaskIntegration:
    """Integration tests for Celery tasks with real database"""
    
    def test_task_registration(self):
        """Test that tasks are properly registered with Celery"""
        from app.core.celery_app import celery_app
        
        registered_tasks = celery_app.tasks.keys()
        
        assert "process_document_async" in registered_tasks
        assert "batch_process_documents" in registered_tasks
        assert "regenerate_document_embeddings" in registered_tasks
        assert "cleanup_failed_processing" in registered_tasks
    
    def test_task_routing_configuration(self):
        """Test that task routing is properly configured"""
        from app.core.celery_app import celery_app
        
        # Check that document processing tasks are routed to the correct queue
        task_routes = celery_app.conf.task_routes
        
        assert "app.tasks.document_processing.*" in task_routes
        assert task_routes["app.tasks.document_processing.*"]["queue"] == "document_processing"
    
    def test_celery_configuration(self):
        """Test Celery configuration settings"""
        from app.core.celery_app import celery_app
        
        # Check important configuration settings
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.task_track_started is True
        
        # Check time limits
        assert celery_app.conf.task_time_limit == 30 * 60  # 30 minutes
        assert celery_app.conf.task_soft_time_limit == 25 * 60  # 25 minutes
#!/usr/bin/env python3
"""
Demo script for async document processing functionality
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.async_document_service import AsyncDocumentProcessingService
from app.models.database import Document, DocumentType, ProcessingStatus


def demo_async_service():
    """Demonstrate AsyncDocumentProcessingService functionality"""
    print("🚀 CSRD RAG System - Async Document Processing Demo")
    print("=" * 60)
    
    # Mock database session
    mock_db = Mock()
    
    # Create service instance
    service = AsyncDocumentProcessingService(mock_db)
    print("✅ AsyncDocumentProcessingService initialized")
    
    # Demo 1: Mock document processing task
    print("\n📄 Demo 1: Document Processing Task")
    print("-" * 40)
    
    # Mock document
    mock_document = Mock()
    mock_document.id = "demo-doc-123"
    mock_document.processing_status = ProcessingStatus.PENDING
    mock_db.query.return_value.filter.return_value.first.return_value = mock_document
    
    # Mock Celery task
    mock_task = Mock()
    mock_task.id = "task-abc-123"
    
    # Mock the delay method
    from unittest.mock import patch
    with patch('app.tasks.document_processing.process_document_async.delay', return_value=mock_task):
            try:
                result = service.start_document_processing(
                    document_id="demo-doc-123",
                    chunk_size=1000,
                    generate_embeddings=True,
                    classify_schema=True
                )
                
                print(f"   Task ID: {result.task_id}")
                print(f"   Document ID: {result.document_id}")
                print(f"   Task Type: {result.task_type}")
                print("   ✅ Document processing task started successfully")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    # Demo 2: Task status monitoring
    print("\n📊 Demo 2: Task Status Monitoring")
    print("-" * 40)
    
    with patch('app.services.async_document_service.AsyncResult') as mock_result_class:
        mock_result = Mock()
        mock_result.status = "PROGRESS"
        mock_result.ready.return_value = False
        mock_result.info = {
            "current": 75,
            "total": 100,
            "status": "Generating embeddings"
        }
        mock_result_class.return_value = mock_result
        
        status = service.get_task_status("demo-task-456")
        
        print(f"   Task ID: {status['task_id']}")
        print(f"   Status: {status['status']}")
        print(f"   Progress: {status['progress']['current']}/{status['progress']['total']}")
        print(f"   Current Step: {status['progress']['status']}")
        print("   ✅ Task status retrieved successfully")
    
    # Demo 3: Batch processing
    print("\n📚 Demo 3: Batch Processing")
    print("-" * 40)
    
    # Mock multiple documents
    mock_docs = []
    for i in range(3):
        doc = Mock()
        doc.id = f"batch-doc-{i}"
        mock_docs.append(doc)
    
    mock_db.query.return_value.filter.return_value.all.return_value = mock_docs
    
    with patch('app.tasks.document_processing.batch_process_documents.delay') as mock_batch_delay:
        mock_batch_task = Mock()
        mock_batch_task.id = "batch-task-789"
        mock_batch_delay.return_value = mock_batch_task
        
        try:
            result = service.start_batch_processing(
                document_ids=["batch-doc-0", "batch-doc-1", "batch-doc-2"],
                chunk_size=800,
                generate_embeddings=True
            )
            
            print(f"   Batch Task ID: {result.task_id}")
            print(f"   Task Type: {result.task_type}")
            print("   ✅ Batch processing started successfully")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Demo 4: Queue status
    print("\n🔄 Demo 4: Processing Queue Status")
    print("-" * 40)
    
    with patch('app.core.celery_app.celery_app.control.inspect') as mock_inspect:
        mock_inspect_instance = Mock()
        mock_inspect.return_value = mock_inspect_instance
        
        # Mock queue data
        mock_inspect_instance.active.return_value = {
            "worker1": [
                {"name": "process_document_async", "id": "task1"},
                {"name": "batch_process_documents", "id": "task2"}
            ]
        }
        mock_inspect_instance.scheduled.return_value = {"worker1": []}
        mock_inspect_instance.reserved.return_value = {"worker1": []}
        
        queue_status = service.get_processing_queue_status()
        
        print(f"   Queue Status: {queue_status['queue_status']}")
        print(f"   Active Tasks: {queue_status['task_counts']['active']}")
        print(f"   Workers Online: {queue_status['workers_online']}")
        print("   ✅ Queue status retrieved successfully")
    
    # Demo 5: Processing statistics
    print("\n📈 Demo 5: Processing Statistics")
    print("-" * 40)
    
    # Mock document counts
    mock_db.query.return_value.count.return_value = 100
    mock_db.query.return_value.filter.return_value.count.side_effect = [80, 15, 3, 2]  # completed, failed, processing, pending
    
    with patch.object(service, 'get_processing_queue_status') as mock_queue_status:
        mock_queue_status.return_value = {
            "queue_status": "healthy",
            "task_counts": {"active": 2},
            "workers_online": 1,
            "timestamp": "2023-01-01T00:00:00"
        }
        
        stats = service.get_processing_statistics()
        
        print(f"   Total Documents: {stats['total_documents']}")
        print(f"   Success Rate: {stats['success_rate']}%")
        print(f"   Status Breakdown:")
        for status, count in stats['status_counts'].items():
            print(f"     - {status.title()}: {count}")
        print("   ✅ Processing statistics retrieved successfully")
    
    print("\n🎉 Demo completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start Redis server: redis-server")
    print("2. Start Celery worker: python celery_worker.py worker --loglevel=info")
    print("3. Start FastAPI server: python main.py")
    print("4. Test API endpoints at http://localhost:8000/docs")


if __name__ == "__main__":
    demo_async_service()
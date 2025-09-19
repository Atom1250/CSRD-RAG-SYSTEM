"""
Celery tasks for asynchronous document processing
"""
import logging
from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.database import Document, ProcessingStatus
from app.services.text_processing_service import TextProcessingService
from app.services.schema_service import SchemaService

logger = logging.getLogger(__name__)

# Create database engine and session factory for tasks
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get database session for tasks"""
    return SessionLocal()


@celery_app.task(bind=True, name="process_document_async")
def process_document_async(
    self, 
    document_id: str, 
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    generate_embeddings: bool = True,
    classify_schema: bool = True
) -> Dict[str, Any]:
    """
    Asynchronously process a document through the complete pipeline
    
    Args:
        document_id: Document ID to process
        chunk_size: Optional chunk size override
        chunk_overlap: Optional chunk overlap override
        generate_embeddings: Whether to generate embeddings
        classify_schema: Whether to classify against schema
        
    Returns:
        Dict containing processing results and statistics
    """
    db = get_db_session()
    
    try:
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting document processing"}
        )
        
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        # Update document status to processing
        document.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        logger.info(f"Starting async processing for document {document_id}")
        
        # Initialize services
        text_service = TextProcessingService(db)
        schema_service = SchemaService(db) if classify_schema else None
        
        # Step 1: Extract and preprocess text (20% progress)
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Extracting text from document"}
        )
        
        raw_text = text_service.extract_text_from_document(document)
        processed_text = text_service.preprocess_text(raw_text)
        
        logger.info(f"Extracted {len(processed_text)} characters from document {document_id}")
        
        # Step 2: Chunk text (40% progress)
        self.update_state(
            state="PROGRESS",
            meta={"current": 40, "total": 100, "status": "Chunking document text"}
        )
        
        chunks = text_service.chunk_text(processed_text, chunk_size, chunk_overlap)
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        
        # Step 3: Create text chunk records (60% progress)
        self.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Creating text chunk records"}
        )
        
        created_chunks = []
        chunks_for_embedding = []
        
        for i, chunk_content in enumerate(chunks):
            from app.models.database import TextChunk
            
            db_chunk = TextChunk(
                document_id=document_id,
                content=chunk_content,
                chunk_index=i
            )
            
            db.add(db_chunk)
            db.flush()  # Get the ID
            
            created_chunks.append({
                "id": db_chunk.id,
                "chunk_index": i,
                "content_length": len(chunk_content)
            })
            
            # Prepare for embedding generation
            if generate_embeddings:
                chunks_for_embedding.append({
                    "id": db_chunk.id,
                    "document_id": document_id,
                    "content": chunk_content,
                    "chunk_index": i,
                    "schema_elements": [],
                    "created_at": db_chunk.created_at.isoformat() if db_chunk.created_at else ""
                })
        
        # Step 4: Generate embeddings (80% progress)
        if generate_embeddings and chunks_for_embedding:
            self.update_state(
                state="PROGRESS",
                meta={"current": 80, "total": 100, "status": "Generating embeddings"}
            )
            
            try:
                # Import here to avoid circular imports
                from app.services.vector_service import embedding_service
                
                # Generate embeddings synchronously in Celery task
                embedding_success = True
                for chunk_data in chunks_for_embedding:
                    try:
                        embedding = embedding_service.generate_embedding(chunk_data["content"])
                        chunk_data["embedding_vector"] = embedding
                    except Exception as e:
                        logger.error(f"Failed to generate embedding for chunk {chunk_data['id']}: {str(e)}")
                        embedding_success = False
                
                # Store embeddings in vector database
                if embedding_success:
                    # Use synchronous method for Celery task
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        embedding_success = loop.run_until_complete(
                            embedding_service.store_embeddings(chunks_for_embedding)
                        )
                    finally:
                        loop.close()
                
                if embedding_success:
                    # Update database with embedding vectors
                    for chunk_data in chunks_for_embedding:
                        if "embedding_vector" in chunk_data:
                            from app.models.database import TextChunk
                            db_chunk = db.query(TextChunk).filter(TextChunk.id == chunk_data["id"]).first()
                            if db_chunk:
                                db_chunk.embedding_vector = chunk_data["embedding_vector"]
                    
                    logger.info(f"Generated embeddings for {len(chunks_for_embedding)} chunks")
                else:
                    logger.warning(f"Failed to generate embeddings for document {document_id}")
                    
            except Exception as e:
                logger.error(f"Embedding generation failed for document {document_id}: {str(e)}")
                # Don't fail the entire process if embedding generation fails
        
        # Step 5: Schema classification (90% progress)
        schema_classification_results = []
        if classify_schema and schema_service:
            self.update_state(
                state="PROGRESS",
                meta={"current": 90, "total": 100, "status": "Classifying against schema"}
            )
            
            try:
                classification_result = schema_service.classify_document(document)
                if classification_result:
                    schema_classification_results = classification_result
                    logger.info(f"Classified document {document_id} against schema")
                else:
                    logger.warning(f"Schema classification failed for document {document_id}")
                    
            except Exception as e:
                logger.error(f"Schema classification failed for document {document_id}: {str(e)}")
                # Don't fail the entire process if schema classification fails
        
        # Step 6: Finalize processing (100% progress)
        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Finalizing processing"}
        )
        
        # Update document status to completed
        document.processing_status = ProcessingStatus.COMPLETED
        db.commit()
        
        # Prepare results
        processing_results = {
            "document_id": document_id,
            "status": "completed",
            "total_chunks": len(created_chunks),
            "total_characters": len(processed_text),
            "average_chunk_size": len(processed_text) / len(created_chunks) if created_chunks else 0,
            "embeddings_generated": len(chunks_for_embedding) if generate_embeddings else 0,
            "schema_elements_found": len(schema_classification_results),
            "processing_time_seconds": None,  # Will be calculated by Celery
            "chunks": created_chunks[:10],  # Return first 10 chunks for preview
            "schema_classification": schema_classification_results[:5] if schema_classification_results else []
        }
        
        logger.info(f"Successfully completed async processing for document {document_id}")
        return processing_results
        
    except Exception as e:
        # Update document status to failed
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = ProcessingStatus.FAILED
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update document status: {str(db_error)}")
        
        logger.error(f"Async document processing failed for {document_id}: {str(e)}")
        
        # Update task state to failure
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "document_id": document_id}
        )
        
        raise e
        
    finally:
        db.close()


@celery_app.task(bind=True, name="batch_process_documents")
def batch_process_documents(
    self,
    document_ids: list,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    generate_embeddings: bool = True,
    classify_schema: bool = True
) -> Dict[str, Any]:
    """
    Process multiple documents in batch
    
    Args:
        document_ids: List of document IDs to process
        chunk_size: Optional chunk size override
        chunk_overlap: Optional chunk overlap override
        generate_embeddings: Whether to generate embeddings
        classify_schema: Whether to classify against schema
        
    Returns:
        Dict containing batch processing results
    """
    if not document_ids:
        return {"status": "completed", "processed_documents": [], "failed_documents": []}
    
    total_documents = len(document_ids)
    processed_documents = []
    failed_documents = []
    
    for i, document_id in enumerate(document_ids):
        try:
            # Update progress
            progress = int((i / total_documents) * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": progress,
                    "total": 100,
                    "status": f"Processing document {i+1} of {total_documents}",
                    "current_document": document_id
                }
            )
            
            # Process individual document
            result = process_document_async.apply(
                args=[document_id, chunk_size, chunk_overlap, generate_embeddings, classify_schema]
            ).get()
            
            processed_documents.append({
                "document_id": document_id,
                "status": "completed",
                "chunks_created": result.get("total_chunks", 0)
            })
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id} in batch: {str(e)}")
            failed_documents.append({
                "document_id": document_id,
                "status": "failed",
                "error": str(e)
            })
    
    # Final results
    batch_results = {
        "status": "completed",
        "total_documents": total_documents,
        "processed_documents": processed_documents,
        "failed_documents": failed_documents,
        "success_rate": len(processed_documents) / total_documents * 100 if total_documents > 0 else 0
    }
    
    logger.info(f"Batch processing completed: {len(processed_documents)} successful, {len(failed_documents)} failed")
    return batch_results


@celery_app.task(bind=True, name="regenerate_document_embeddings")
def regenerate_document_embeddings(self, document_id: str) -> Dict[str, Any]:
    """
    Regenerate embeddings for all chunks of a document
    
    Args:
        document_id: Document ID
        
    Returns:
        Dict containing regeneration results
    """
    db = get_db_session()
    
    try:
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting embedding regeneration"}
        )
        
        # Initialize text processing service
        text_service = TextProcessingService(db)
        
        # Regenerate embeddings
        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Regenerating embeddings"}
        )
        
        # Use synchronous method for Celery task
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(text_service.regenerate_embeddings(document_id))
        finally:
            loop.close()
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Embedding regeneration completed"}
        )
        
        result = {
            "document_id": document_id,
            "status": "completed" if success else "failed",
            "embeddings_regenerated": success
        }
        
        logger.info(f"Embedding regeneration {'successful' if success else 'failed'} for document {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"Embedding regeneration failed for document {document_id}: {str(e)}")
        
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "document_id": document_id}
        )
        
        raise e
        
    finally:
        db.close()


@celery_app.task(bind=True, name="cleanup_failed_processing")
def cleanup_failed_processing(self, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up documents that have been stuck in processing state
    
    Args:
        max_age_hours: Maximum age in hours for stuck processing documents
        
    Returns:
        Dict containing cleanup results
    """
    db = get_db_session()
    
    try:
        from datetime import datetime, timedelta
        
        # Find documents stuck in processing state
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        stuck_documents = (
            db.query(Document)
            .filter(
                Document.processing_status == ProcessingStatus.PROCESSING,
                Document.upload_date < cutoff_time
            )
            .all()
        )
        
        cleaned_count = 0
        for document in stuck_documents:
            document.processing_status = ProcessingStatus.FAILED
            cleaned_count += 1
        
        db.commit()
        
        result = {
            "status": "completed",
            "cleaned_documents": cleaned_count,
            "cutoff_time": cutoff_time.isoformat()
        }
        
        logger.info(f"Cleaned up {cleaned_count} stuck processing documents")
        return result
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise e
        
    finally:
        db.close()
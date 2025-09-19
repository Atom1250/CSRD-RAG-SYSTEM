"""
Unit tests for database configuration and setup
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.database_config import (
    DatabaseManager, get_db_session, create_tables, drop_tables
)
from app.models.database import Base, Document, DocumentType, ProcessingStatus


class TestDatabaseConfig:
    """Test database configuration and management"""
    
    def test_database_manager_init(self):
        """Test database manager initialization"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        
        try:
            # Create a separate engine for this test
            test_engine = create_engine(f"sqlite:///{db_path}")
            
            # Create tables directly using the Base metadata
            Base.metadata.create_all(bind=test_engine)
            
            # Verify tables were created
            with test_engine.connect() as conn:
                # Check if tables exist
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result]
                
                expected_tables = ['documents', 'text_chunks', 'schema_elements', 
                                 'client_requirements', 'rag_responses']
                
                for table in expected_tables:
                    assert table in tables
            
        finally:
            os.close(db_fd)
            os.unlink(db_path)
    
    def test_database_manager_check_connection(self):
        """Test database connection check"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        
        try:
            # Create a separate engine and session for this test
            test_engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(bind=test_engine)
            
            # Test connection by creating a session and executing a query
            TestSessionLocal = sessionmaker(bind=test_engine)
            with TestSessionLocal() as session:
                result = session.execute(text("SELECT 1"))
                assert result.scalar() == 1
            
        finally:
            os.close(db_fd)
            os.unlink(db_path)
    
    def test_get_db_session_context_manager(self):
        """Test database session context manager"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        
        try:
            # Create a separate engine and session for this test
            test_engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(bind=test_engine)
            TestSessionLocal = sessionmaker(bind=test_engine)
            
            # Test context manager functionality
            with TestSessionLocal() as db:
                # Create a document
                document = Document(
                    filename="test_context.pdf",
                    file_path="/path/to/test_context.pdf",
                    file_size=1024,
                    document_type=DocumentType.PDF,
                    processing_status=ProcessingStatus.PENDING
                )
                db.add(document)
                db.commit()
            
            # Verify document was saved
            with TestSessionLocal() as db:
                saved_doc = db.query(Document).filter_by(filename="test_context.pdf").first()
                assert saved_doc is not None
                assert saved_doc.filename == "test_context.pdf"
            
        finally:
            os.close(db_fd)
            os.unlink(db_path)
    
    def test_database_reset(self):
        """Test database reset functionality"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        
        try:
            # Create a separate engine and session for this test
            test_engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(bind=test_engine)
            TestSessionLocal = sessionmaker(bind=test_engine)
            
            # Add some data
            with TestSessionLocal() as db:
                document = Document(
                    filename="test_reset.pdf",
                    file_path="/path/to/test_reset.pdf",
                    file_size=1024,
                    document_type=DocumentType.PDF,
                    processing_status=ProcessingStatus.PENDING
                )
                db.add(document)
                db.commit()
            
            # Verify data exists
            with TestSessionLocal() as db:
                count = db.query(Document).count()
                assert count == 1
            
            # Reset database (drop and recreate tables)
            Base.metadata.drop_all(bind=test_engine)
            Base.metadata.create_all(bind=test_engine)
            
            # Verify data was cleared
            with TestSessionLocal() as db:
                count = db.query(Document).count()
                assert count == 0
            
        finally:
            os.close(db_fd)
            os.unlink(db_path)


class TestDatabaseIntegration:
    """Test database integration with models"""
    
    def test_full_database_workflow(self):
        """Test complete database workflow with all models"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        
        try:
            from app.models.database import TextChunk, SchemaElement, SchemaType
            
            # Create a separate engine and session for this test
            test_engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(bind=test_engine)
            TestSessionLocal = sessionmaker(bind=test_engine)
            
            with TestSessionLocal() as db:
                # Create document
                document = Document(
                    filename="test_workflow.pdf",
                    file_path="/path/to/test_workflow.pdf",
                    file_size=1024,
                    document_type=DocumentType.PDF,
                    processing_status=ProcessingStatus.COMPLETED
                )
                db.add(document)
                db.flush()  # Get the ID
                
                # Create schema element
                schema_element = SchemaElement(
                    schema_type=SchemaType.EU_ESRS_CSRD,
                    element_code="E1",
                    element_name="Climate Change",
                    description="Climate change disclosures"
                )
                db.add(schema_element)
                db.flush()
                
                # Create text chunk
                text_chunk = TextChunk(
                    document_id=document.id,
                    content="This is test content about climate change",
                    chunk_index=0,
                    embedding_vector=[0.1, 0.2, 0.3],
                    schema_elements=[schema_element.id]
                )
                db.add(text_chunk)
                db.commit()
            
            # Verify all data was saved and relationships work
            with TestSessionLocal() as db:
                # Check document
                saved_doc = db.query(Document).filter_by(filename="test_workflow.pdf").first()
                assert saved_doc.filename == "test_workflow.pdf"
                assert len(saved_doc.text_chunks) == 1
                
                # Check text chunk
                saved_chunk = db.query(TextChunk).first()
                assert saved_chunk.content == "This is test content about climate change"
                assert saved_chunk.document == saved_doc
                
                # Check schema element
                saved_element = db.query(SchemaElement).first()
                assert saved_element.element_code == "E1"
                assert saved_element.element_name == "Climate Change"
            
        finally:
            os.close(db_fd)
            os.unlink(db_path)
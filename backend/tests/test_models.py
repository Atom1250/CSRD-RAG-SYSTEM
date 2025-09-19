"""
Unit tests for database models and schemas
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from app.models.database import (
    Base, Document, TextChunk, SchemaElement, ClientRequirements, RAGResponse,
    DocumentType, SchemaType, ProcessingStatus
)
from app.models.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    TextChunkCreate, TextChunkResponse,
    SchemaElementCreate, SchemaElementUpdate, SchemaElementResponse,
    ClientRequirementsCreate, ClientRequirementsUpdate, ClientRequirementsResponse,
    RAGResponseCreate, RAGResponseResponse,
    DocumentFilters, SearchResult, SchemaMapping, ProcessedRequirement
)


@pytest.fixture
def db_session():
    """Create a test database session"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Create engine with SQLite in-memory database
    engine = create_engine(
        f"sqlite:///{db_path}",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    os.close(db_fd)
    os.unlink(db_path)


class TestDocumentModel:
    """Test Document database model"""
    
    def test_create_document(self, db_session):
        """Test creating a document"""
        document = Document(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            schema_type=SchemaType.EU_ESRS_CSRD,
            processing_status=ProcessingStatus.PENDING,
            document_metadata={"author": "Test Author"}
        )
        
        db_session.add(document)
        db_session.commit()
        
        # Verify document was created
        saved_doc = db_session.query(Document).filter_by(filename="test.pdf").first()
        assert saved_doc is not None
        assert saved_doc.filename == "test.pdf"
        assert saved_doc.file_size == 1024
        assert saved_doc.document_type == DocumentType.PDF
        assert saved_doc.schema_type == SchemaType.EU_ESRS_CSRD
        assert saved_doc.processing_status == ProcessingStatus.PENDING
        assert saved_doc.document_metadata["author"] == "Test Author"
        assert saved_doc.upload_date is not None
        assert saved_doc.id is not None
    
    def test_document_relationships(self, db_session):
        """Test document relationships with text chunks"""
        # Create document
        document = Document(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.COMPLETED
        )
        db_session.add(document)
        db_session.commit()
        
        # Create text chunks
        chunk1 = TextChunk(
            document_id=document.id,
            content="First chunk content",
            chunk_index=0,
            embedding_vector=[0.1, 0.2, 0.3]
        )
        chunk2 = TextChunk(
            document_id=document.id,
            content="Second chunk content",
            chunk_index=1,
            embedding_vector=[0.4, 0.5, 0.6]
        )
        
        db_session.add_all([chunk1, chunk2])
        db_session.commit()
        
        # Verify relationships
        saved_doc = db_session.query(Document).filter_by(filename="test.pdf").first()
        assert len(saved_doc.text_chunks) == 2
        assert saved_doc.text_chunks[0].content == "First chunk content"
        assert saved_doc.text_chunks[1].content == "Second chunk content"


class TestTextChunkModel:
    """Test TextChunk database model"""
    
    def test_create_text_chunk(self, db_session):
        """Test creating a text chunk"""
        # First create a document
        document = Document(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.COMPLETED
        )
        db_session.add(document)
        db_session.commit()
        
        # Create text chunk
        chunk = TextChunk(
            document_id=document.id,
            content="This is a test chunk content",
            chunk_index=0,
            embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            schema_elements=["E1", "E2"]
        )
        
        db_session.add(chunk)
        db_session.commit()
        
        # Verify chunk was created
        saved_chunk = db_session.query(TextChunk).filter_by(chunk_index=0).first()
        assert saved_chunk is not None
        assert saved_chunk.content == "This is a test chunk content"
        assert saved_chunk.chunk_index == 0
        assert saved_chunk.embedding_vector == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert saved_chunk.schema_elements == ["E1", "E2"]
        assert saved_chunk.document_id == document.id
        assert saved_chunk.created_at is not None


class TestSchemaElementModel:
    """Test SchemaElement database model"""
    
    def test_create_schema_element(self, db_session):
        """Test creating a schema element"""
        element = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change related disclosures",
            requirements=["Disclose GHG emissions", "Report climate risks"]
        )
        
        db_session.add(element)
        db_session.commit()
        
        # Verify element was created
        saved_element = db_session.query(SchemaElement).filter_by(element_code="E1").first()
        assert saved_element is not None
        assert saved_element.schema_type == SchemaType.EU_ESRS_CSRD
        assert saved_element.element_code == "E1"
        assert saved_element.element_name == "Climate Change"
        assert saved_element.description == "Climate change related disclosures"
        assert saved_element.requirements == ["Disclose GHG emissions", "Report climate risks"]
        assert saved_element.created_at is not None
        assert saved_element.updated_at is not None
    
    def test_schema_element_hierarchy(self, db_session):
        """Test hierarchical schema elements"""
        # Create parent element
        parent = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E",
            element_name="Environmental",
            description="Environmental disclosures"
        )
        db_session.add(parent)
        db_session.commit()
        
        # Create child element
        child = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change related disclosures",
            parent_element_id=parent.id
        )
        db_session.add(child)
        db_session.commit()
        
        # Verify hierarchy
        saved_parent = db_session.query(SchemaElement).filter_by(element_code="E").first()
        saved_child = db_session.query(SchemaElement).filter_by(element_code="E1").first()
        
        assert saved_child.parent_element_id == saved_parent.id
        assert saved_child.parent == saved_parent
        assert saved_child in saved_parent.children


class TestClientRequirementsModel:
    """Test ClientRequirements database model"""
    
    def test_create_client_requirements(self, db_session):
        """Test creating client requirements"""
        schema_mappings = [
            {"requirement_id": "req1", "schema_element_id": "E1", "confidence_score": 0.9}
        ]
        processed_requirements = [
            {
                "requirement_id": "req1",
                "requirement_text": "Report GHG emissions",
                "mapped_elements": ["E1"],
                "priority": "high"
            }
        ]
        
        requirements = ClientRequirements(
            client_name="Test Client",
            requirements_text="Please provide GHG emissions data",
            schema_mappings=schema_mappings,
            processed_requirements=processed_requirements
        )
        
        db_session.add(requirements)
        db_session.commit()
        
        # Verify requirements were created
        saved_req = db_session.query(ClientRequirements).filter_by(client_name="Test Client").first()
        assert saved_req is not None
        assert saved_req.client_name == "Test Client"
        assert saved_req.requirements_text == "Please provide GHG emissions data"
        assert saved_req.schema_mappings == schema_mappings
        assert saved_req.processed_requirements == processed_requirements
        assert saved_req.upload_date is not None


class TestRAGResponseModel:
    """Test RAGResponse database model"""
    
    def test_create_rag_response(self, db_session):
        """Test creating a RAG response"""
        response = RAGResponse(
            query="What are the GHG emission requirements?",
            response_text="Companies must disclose Scope 1, 2, and 3 emissions...",
            confidence_score=0.85,
            source_chunks=["chunk1", "chunk2"],
            model_used="gpt-4"
        )
        
        db_session.add(response)
        db_session.commit()
        
        # Verify response was created
        saved_response = db_session.query(RAGResponse).filter_by(model_used="gpt-4").first()
        assert saved_response is not None
        assert saved_response.query == "What are the GHG emission requirements?"
        assert "Companies must disclose" in saved_response.response_text
        assert saved_response.confidence_score == 0.85
        assert saved_response.source_chunks == ["chunk1", "chunk2"]
        assert saved_response.model_used == "gpt-4"
        assert saved_response.generation_timestamp is not None


class TestPydanticSchemas:
    """Test Pydantic schemas for validation and serialization"""
    
    def test_document_create_schema(self):
        """Test DocumentCreate schema validation"""
        # Valid document
        doc_data = {
            "filename": "test.pdf",
            "document_type": "pdf",
            "file_size": 1024,
            "file_path": "/path/to/test.pdf",
            "schema_type": "EU_ESRS_CSRD",
            "document_metadata": {"author": "Test"}
        }
        
        doc = DocumentCreate(**doc_data)
        assert doc.filename == "test.pdf"
        assert doc.document_type == DocumentType.PDF
        assert doc.file_size == 1024
        assert doc.schema_type == SchemaType.EU_ESRS_CSRD
        
        # Test validation errors
        with pytest.raises(ValueError):
            DocumentCreate(filename="", document_type="pdf", file_size=1024, file_path="/path")
        
        with pytest.raises(ValueError):
            DocumentCreate(filename="test.pdf", document_type="pdf", file_size=0, file_path="/path")
    
    def test_text_chunk_create_schema(self):
        """Test TextChunkCreate schema validation"""
        chunk_data = {
            "document_id": "doc123",
            "content": "This is test content",
            "chunk_index": 0,
            "embedding_vector": [0.1, 0.2, 0.3],
            "schema_elements": ["E1", "E2"]
        }
        
        chunk = TextChunkCreate(**chunk_data)
        assert chunk.document_id == "doc123"
        assert chunk.content == "This is test content"
        assert chunk.chunk_index == 0
        assert chunk.embedding_vector == [0.1, 0.2, 0.3]
        
        # Test validation errors
        with pytest.raises(ValueError):
            TextChunkCreate(document_id="doc123", content="", chunk_index=0)
    
    def test_schema_element_create_schema(self):
        """Test SchemaElementCreate schema validation"""
        element_data = {
            "schema_type": "EU_ESRS_CSRD",
            "element_code": "e1",
            "element_name": "Climate Change",
            "description": "Climate disclosures",
            "requirements": ["Disclose emissions"]
        }
        
        element = SchemaElementCreate(**element_data)
        assert element.schema_type == SchemaType.EU_ESRS_CSRD
        assert element.element_code == "E1"  # Should be uppercase
        assert element.element_name == "Climate Change"
        
        # Test validation errors
        with pytest.raises(ValueError):
            SchemaElementCreate(schema_type="EU_ESRS_CSRD", element_code="", element_name="Test")
    
    def test_client_requirements_create_schema(self):
        """Test ClientRequirementsCreate schema validation"""
        req_data = {
            "client_name": "Test Client",
            "requirements_text": "Need GHG data",
            "schema_mappings": [
                {"requirement_id": "req1", "schema_element_id": "E1", "confidence_score": 0.9}
            ]
        }
        
        requirements = ClientRequirementsCreate(**req_data)
        assert requirements.client_name == "Test Client"
        assert requirements.requirements_text == "Need GHG data"
        assert len(requirements.schema_mappings) == 1
        
        # Test validation errors
        with pytest.raises(ValueError):
            ClientRequirementsCreate(client_name="", requirements_text="Test")
    
    def test_rag_response_create_schema(self):
        """Test RAGResponseCreate schema validation"""
        response_data = {
            "query": "What are emissions requirements?",
            "response_text": "Companies must report...",
            "model_used": "gpt-4",
            "confidence_score": 0.85,
            "source_chunks": ["chunk1", "chunk2"]
        }
        
        response = RAGResponseCreate(**response_data)
        assert response.query == "What are emissions requirements?"
        assert response.response_text == "Companies must report..."
        assert response.model_used == "gpt-4"
        assert response.confidence_score == 0.85
        
        # Test validation errors
        with pytest.raises(ValueError):
            RAGResponseCreate(query="", response_text="Test", model_used="gpt-4")
    
    def test_document_filters_schema(self):
        """Test DocumentFilters schema"""
        filters = DocumentFilters(
            document_type="pdf",
            schema_type="EU_ESRS_CSRD",
            processing_status="completed",
            filename_contains="test"
        )
        
        assert filters.document_type == DocumentType.PDF
        assert filters.schema_type == SchemaType.EU_ESRS_CSRD
        assert filters.processing_status == ProcessingStatus.COMPLETED
        assert filters.filename_contains == "test"
    
    def test_search_result_schema(self):
        """Test SearchResult schema"""
        result = SearchResult(
            chunk_id="chunk123",
            document_id="doc123",
            content="Test content",
            relevance_score=0.85,
            document_filename="test.pdf",
            schema_elements=["E1", "E2"]
        )
        
        assert result.chunk_id == "chunk123"
        assert result.document_id == "doc123"
        assert result.content == "Test content"
        assert result.relevance_score == 0.85
        assert result.document_filename == "test.pdf"
        assert result.schema_elements == ["E1", "E2"]
    
    def test_schema_mapping_schema(self):
        """Test SchemaMapping schema"""
        mapping = SchemaMapping(
            requirement_id="req1",
            schema_element_id="E1",
            confidence_score=0.9
        )
        
        assert mapping.requirement_id == "req1"
        assert mapping.schema_element_id == "E1"
        assert mapping.confidence_score == 0.9
        
        # Test confidence score validation
        with pytest.raises(ValueError):
            SchemaMapping(requirement_id="req1", schema_element_id="E1", confidence_score=1.5)
    
    def test_processed_requirement_schema(self):
        """Test ProcessedRequirement schema"""
        processed = ProcessedRequirement(
            requirement_id="req1",
            requirement_text="Report emissions",
            mapped_elements=["E1", "E2"],
            priority="high"
        )
        
        assert processed.requirement_id == "req1"
        assert processed.requirement_text == "Report emissions"
        assert processed.mapped_elements == ["E1", "E2"]
        assert processed.priority == "high"


class TestDatabaseOperations:
    """Test database operations and constraints"""
    
    def test_cascade_delete(self, db_session):
        """Test cascade delete of text chunks when document is deleted"""
        # Create document with text chunks
        document = Document(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.COMPLETED
        )
        db_session.add(document)
        db_session.commit()
        
        chunk = TextChunk(
            document_id=document.id,
            content="Test content",
            chunk_index=0
        )
        db_session.add(chunk)
        db_session.commit()
        
        # Verify chunk exists
        assert db_session.query(TextChunk).count() == 1
        
        # Delete document
        db_session.delete(document)
        db_session.commit()
        
        # Verify chunk was also deleted (cascade)
        assert db_session.query(TextChunk).count() == 0
    
    def test_foreign_key_constraint(self, db_session):
        """Test foreign key constraints"""
        # Note: SQLite doesn't enforce foreign key constraints by default
        # This test verifies the relationship works when valid data is provided
        
        # Create a valid document first
        document = Document(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.COMPLETED
        )
        db_session.add(document)
        db_session.commit()
        
        # Create text chunk with valid document_id
        chunk = TextChunk(
            document_id=document.id,
            content="Test content",
            chunk_index=0
        )
        db_session.add(chunk)
        db_session.commit()
        
        # Verify the relationship works
        saved_chunk = db_session.query(TextChunk).first()
        assert saved_chunk.document_id == document.id
        assert saved_chunk.document == document
    
    def test_enum_constraints(self, db_session):
        """Test enum field constraints"""
        # Valid enum values should work
        document = Document(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            schema_type=SchemaType.EU_ESRS_CSRD,
            processing_status=ProcessingStatus.PENDING
        )
        db_session.add(document)
        db_session.commit()
        
        # Verify document was created successfully
        saved_doc = db_session.query(Document).first()
        assert saved_doc.document_type == DocumentType.PDF
        assert saved_doc.schema_type == SchemaType.EU_ESRS_CSRD
        assert saved_doc.processing_status == ProcessingStatus.PENDING
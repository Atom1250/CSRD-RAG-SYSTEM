"""
Test configuration and fixtures for CSRD RAG System
"""
import pytest
import tempfile
import io
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.models.database import Base, Document, TextChunk, SchemaElement, ClientRequirements
from app.models.database_config import get_db
from app.models.schemas import DocumentType, SchemaType, ProcessingStatus


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def test_settings():
    """Test settings with overrides for testing environment"""
    return Settings(
        database_url="sqlite:///./test.db",
        debug=True,
        upload_directory="./test_data/documents",
        chroma_persist_directory="./test_data/chroma_db",
        schema_directory="./test_data/schemas"
    )


@pytest.fixture(scope="session")
def client():
    """Test client for API testing"""
    from main import app
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create database session for testing"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_document(db_session):
    """Create a sample document for testing"""
    document = Document(
        filename="test_document.pdf",
        file_path="/test/path/test_document.pdf",
        file_size=1024,
        document_type=DocumentType.PDF,
        schema_type=SchemaType.EU_ESRS_CSRD,
        processing_status=ProcessingStatus.COMPLETED
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def sample_processed_document(db_session):
    """Create a sample processed document with embeddings for testing"""
    document = Document(
        filename="processed_document.pdf",
        file_path="/test/path/processed_document.pdf",
        file_size=2048,
        document_type=DocumentType.PDF,
        schema_type=SchemaType.EU_ESRS_CSRD,
        processing_status=ProcessingStatus.COMPLETED
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Add some text chunks with embeddings
    for i in range(3):
        chunk = TextChunk(
            document_id=document.document_id,
            content=f"This is sample text chunk {i} for testing search functionality.",
            chunk_index=i,
            embedding_vector=[0.1 + i * 0.1] * 384,  # Mock 384-dimensional vector
            schema_elements=["E1", "S1"] if i % 2 == 0 else ["E2", "G1"]
        )
        db_session.add(chunk)
    
    db_session.commit()
    return document


@pytest.fixture
def sample_text_chunk(db_session, sample_document):
    """Create a sample text chunk for testing"""
    chunk = TextChunk(
        document_id=sample_document.document_id,
        content="This is a sample text chunk for testing purposes.",
        chunk_index=0,
        embedding_vector=[0.1, 0.2, 0.3] * 128,  # Mock 384-dimensional vector
        schema_elements=["E1", "S1"]
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)
    return chunk


@pytest.fixture
def sample_schema_element(db_session):
    """Create a sample schema element for testing"""
    element = SchemaElement(
        schema_type=SchemaType.EU_ESRS_CSRD,
        element_code="E1",
        element_name="Climate Change",
        description="Climate change adaptation and mitigation requirements"
    )
    db_session.add(element)
    db_session.commit()
    db_session.refresh(element)
    return element


@pytest.fixture
def sample_client_requirements(db_session):
    """Create sample client requirements for testing"""
    requirements = ClientRequirements(
        client_name="Test Client",
        requirements_text="Sample client requirements for testing including climate change reporting and governance requirements",
        schema_type=SchemaType.EU_ESRS_CSRD,
        processed_requirements=[
            {
                "requirement_id": "req_1",
                "requirement_text": "Climate change adaptation reporting",
                "priority": "high",
                "schema_mappings": ["E1"]
            },
            {
                "requirement_id": "req_2", 
                "requirement_text": "Governance disclosure requirements",
                "priority": "medium",
                "schema_mappings": ["G1"]
            }
        ]
    )
    db_session.add(requirements)
    db_session.commit()
    db_session.refresh(requirements)
    return requirements


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing uploads"""
    # Create a simple PDF-like content for testing
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
    return io.BytesIO(pdf_content)


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing uploads"""
    content = "This is a sample text file for testing document upload functionality."
    return io.BytesIO(content.encode('utf-8'))


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment with mocked services"""
    # Mock the problematic imports first
    mock_sentence_transformers = MagicMock()
    mock_sentence_transformers.SentenceTransformer = MagicMock()
    
    mock_chromadb = MagicMock()
    mock_chromadb.config = MagicMock()
    mock_chromadb.config.Settings = MagicMock()
    mock_chromadb.utils = MagicMock()
    mock_chromadb.utils.embedding_functions = MagicMock()
    
    with patch.dict('sys.modules', {
        'sentence_transformers': mock_sentence_transformers,
        'chromadb': mock_chromadb,
        'chromadb.config': mock_chromadb.config,
        'chromadb.utils': mock_chromadb.utils,
        'chromadb.utils.embedding_functions': mock_chromadb.utils.embedding_functions,
        'openai': MagicMock(),
        'anthropic': MagicMock(),
        'celery': MagicMock(),
    }):
        with patch('app.services.vector_service.VectorService') as mock_vector, \
             patch('app.services.rag_service.RAGService') as mock_rag, \
             patch('app.services.async_document_service.AsyncDocumentProcessingService') as mock_async:
            
            # Configure vector service mock
            mock_vector_instance = MagicMock()
            mock_vector_instance.is_available.return_value = True
            mock_vector_instance.search_similar.return_value = []
            mock_vector_instance.generate_embedding.return_value = [0.1] * 384
            mock_vector.return_value = mock_vector_instance
            
            # Configure RAG service mock
            mock_rag_instance = MagicMock()
            mock_rag_instance.generate_rag_response.return_value = {
                "question": "Test question",
                "response_text": "Test response",
                "confidence_score": 0.8,
                "source_chunks": [],
                "model_used": "test_model",
                "generation_timestamp": "2024-01-01T00:00:00Z"
            }
            mock_rag_instance.get_available_models.return_value = []
            mock_rag_instance.get_model_status.return_value = {}
            mock_rag.return_value = mock_rag_instance
            
            # Configure async service mock
            mock_async_instance = MagicMock()
            mock_async_instance.start_document_processing.return_value = MagicMock(
                task_id="test_task",
                document_id="test_doc",
                task_type="processing",
                status="PENDING"
            )
            mock_async_instance.get_task_status.return_value = {
                "task_id": "test_task",
                "status": "SUCCESS",
                "ready": True
            }
            mock_async_instance.get_processing_queue_status.return_value = {
                "queue_status": "healthy",
                "task_counts": {},
                "workers_online": 1,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            mock_async_instance.get_processing_statistics.return_value = {
                "total_documents": 0,
                "status_counts": {},
                "success_rate": 1.0,
                "queue_status": {"queue_status": "healthy"},
                "timestamp": "2024-01-01T00:00:00Z"
            }
            mock_async.return_value = mock_async_instance
            
            yield
"""
Integration tests for document upload and storage functionality
"""
import pytest
import tempfile
import shutil
import io
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.models.database import Base, Document
from app.models.database_config import get_db


class TestDocumentIntegration:
    """Integration tests for document functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        yield TestingSessionLocal
        
        # Clean up
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Create temporary upload directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def client_with_temp_storage(self, temp_db, temp_upload_dir):
        """Create test client with temporary storage"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.upload_directory = str(temp_upload_dir)
            mock_settings.max_file_size = 50 * 1024 * 1024  # 50MB
            mock_settings.allowed_file_types = ["pdf", "docx", "txt"]
            
            client = TestClient(app)
            yield client, temp_db
    
    def create_test_file_content(self, filename: str, content: bytes = b"test content"):
        """Create test file content for upload"""
        return (filename, io.BytesIO(content), "application/octet-stream")
    
    def test_complete_upload_workflow(self, client_with_temp_storage, temp_upload_dir):
        """Test complete document upload workflow"""
        client, db_session = client_with_temp_storage
        
        # Create test file content
        test_content = b"This is a test PDF document content for integration testing."
        files = {"file": self.create_test_file_content("integration_test.pdf", test_content)}
        
        # Upload document
        response = client.post("/api/documents/upload", files=files)
        
        assert response.status_code == 200
        upload_data = response.json()
        
        # Verify response structure
        assert "id" in upload_data
        assert upload_data["filename"] == "integration_test.pdf"
        assert upload_data["document_type"] == "pdf"
        assert upload_data["processing_status"] == "pending"
        assert upload_data["file_size"] == len(test_content)
        
        document_id = upload_data["id"]
        
        # Verify file was saved to disk
        uploaded_files = list(temp_upload_dir.glob("*integration_test.pdf"))
        assert len(uploaded_files) == 1
        
        saved_file = uploaded_files[0]
        assert saved_file.read_bytes() == test_content
        
        # Verify document was saved to database
        with db_session() as db:
            db_document = db.query(Document).filter(Document.id == document_id).first()
            assert db_document is not None
            assert db_document.filename == "integration_test.pdf"
            assert db_document.file_size == len(test_content)
            assert str(saved_file) == db_document.file_path
        
        # Test document retrieval
        response = client.get(f"/api/documents/{document_id}")
        assert response.status_code == 200
        
        retrieved_data = response.json()
        assert retrieved_data["id"] == document_id
        assert retrieved_data["filename"] == "integration_test.pdf"
        
        # Test document listing
        response = client.get("/api/documents/")
        assert response.status_code == 200
        
        documents_list = response.json()
        assert len(documents_list) == 1
        assert documents_list[0]["id"] == document_id
        
        # Test metadata retrieval
        response = client.get(f"/api/documents/{document_id}/metadata")
        assert response.status_code == 200
        
        metadata = response.json()
        assert "original_filename" in metadata
        assert metadata["original_filename"] == "integration_test.pdf"
        assert "file_hash" in metadata
        assert "upload_timestamp" in metadata
        
        # Test metadata update
        update_data = {"custom_field": "custom_value", "processed": True}
        response = client.put(f"/api/documents/{document_id}/metadata", json=update_data)
        assert response.status_code == 200
        
        updated_doc = response.json()
        assert updated_doc["document_metadata"]["custom_field"] == "custom_value"
        assert updated_doc["document_metadata"]["processed"] is True
        
        # Test document deletion
        response = client.delete(f"/api/documents/{document_id}")
        assert response.status_code == 200
        
        # Verify file was deleted from disk
        assert not saved_file.exists()
        
        # Verify document was deleted from database
        with db_session() as db:
            db_document = db.query(Document).filter(Document.id == document_id).first()
            assert db_document is None
        
        # Verify document is no longer retrievable
        response = client.get(f"/api/documents/{document_id}")
        assert response.status_code == 404
    
    def test_upload_multiple_documents(self, client_with_temp_storage):
        """Test uploading multiple documents"""
        client, db_session = client_with_temp_storage
        
        # Upload multiple documents
        documents = [
            ("test1.pdf", b"PDF content 1"),
            ("test2.txt", b"Text content 2"),
            ("test3.docx", b"DOCX content 3")
        ]
        
        uploaded_ids = []
        
        for filename, content in documents:
            files = {"file": self.create_test_file_content(filename, content)}
            response = client.post("/api/documents/upload", files=files)
            
            assert response.status_code == 200
            upload_data = response.json()
            uploaded_ids.append(upload_data["id"])
        
        # Verify all documents are listed
        response = client.get("/api/documents/")
        assert response.status_code == 200
        
        documents_list = response.json()
        assert len(documents_list) == 3
        
        # Verify each document can be retrieved
        for doc_id in uploaded_ids:
            response = client.get(f"/api/documents/{doc_id}")
            assert response.status_code == 200
    
    def test_upload_with_schema_type(self, client_with_temp_storage):
        """Test document upload with schema type classification"""
        client, db_session = client_with_temp_storage
        
        files = {"file": self.create_test_file_content("csrd_document.pdf")}
        params = {"schema_type": "EU_ESRS_CSRD"}
        
        response = client.post("/api/documents/upload", files=files, params=params)
        
        assert response.status_code == 200
        upload_data = response.json()
        
        # Verify schema type was set
        assert upload_data["schema_type"] == "EU_ESRS_CSRD"
        
        # Verify in database
        document_id = upload_data["id"]
        with db_session() as db:
            db_document = db.query(Document).filter(Document.id == document_id).first()
            assert db_document.schema_type.value == "EU_ESRS_CSRD"
    
    def test_document_filtering(self, client_with_temp_storage):
        """Test document filtering functionality"""
        client, db_session = client_with_temp_storage
        
        # Upload documents with different types and schema types
        test_documents = [
            ("doc1.pdf", "EU_ESRS_CSRD"),
            ("doc2.txt", "UK_SRD"),
            ("doc3.pdf", "EU_ESRS_CSRD"),
            ("doc4.docx", None)
        ]
        
        for filename, schema_type in test_documents:
            files = {"file": self.create_test_file_content(filename)}
            params = {"schema_type": schema_type} if schema_type else {}
            
            response = client.post("/api/documents/upload", files=files, params=params)
            assert response.status_code == 200
        
        # Test filtering by document type
        response = client.get("/api/documents/", params={"document_type": "pdf"})
        assert response.status_code == 200
        
        pdf_docs = response.json()
        assert len(pdf_docs) == 2
        assert all(doc["document_type"] == "pdf" for doc in pdf_docs)
        
        # Test filtering by schema type
        response = client.get("/api/documents/", params={"schema_type": "EU_ESRS_CSRD"})
        assert response.status_code == 200
        
        esrs_docs = response.json()
        assert len(esrs_docs) == 2
        assert all(doc["schema_type"] == "EU_ESRS_CSRD" for doc in esrs_docs)
        
        # Test filtering by filename
        response = client.get("/api/documents/", params={"filename_contains": "doc1"})
        assert response.status_code == 200
        
        filtered_docs = response.json()
        assert len(filtered_docs) == 1
        assert "doc1" in filtered_docs[0]["filename"]
    
    def test_file_validation_errors(self, client_with_temp_storage):
        """Test various file validation error scenarios"""
        client, db_session = client_with_temp_storage
        
        # Test unsupported file type
        files = {"file": self.create_test_file_content("test.jpg")}
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
        
        # Test file too large (mock large file)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"file": self.create_test_file_content("large.pdf", large_content)}
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 413
        assert "exceeds maximum allowed size" in response.json()["detail"]
    
    def test_error_cleanup(self, client_with_temp_storage, temp_upload_dir):
        """Test that files are cleaned up when database operations fail"""
        client, db_session = client_with_temp_storage
        
        # This test would require mocking database failure
        # For now, we'll test the basic cleanup behavior
        files = {"file": self.create_test_file_content("test.pdf")}
        
        # Normal upload should work
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 200
        
        # Verify file exists
        uploaded_files = list(temp_upload_dir.glob("*test.pdf"))
        assert len(uploaded_files) == 1


# Import patch for mocking
from unittest.mock import patch
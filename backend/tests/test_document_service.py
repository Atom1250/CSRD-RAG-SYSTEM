"""
Tests for document service functionality
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.services.document_service import DocumentService
from app.models.database import Document, DocumentType, ProcessingStatus
from app.models.schemas import DocumentFilters


class TestDocumentService:
    """Test cases for DocumentService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Create temporary upload directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def document_service(self, mock_db, temp_upload_dir):
        """Create document service with mocked dependencies"""
        with patch('app.services.document_service.settings') as mock_settings:
            mock_settings.upload_directory = str(temp_upload_dir)
            mock_settings.max_file_size = 50 * 1024 * 1024  # 50MB
            mock_settings.allowed_file_types = ["pdf", "docx", "txt"]
            service = DocumentService(mock_db)
            return service
    
    def create_mock_upload_file(self, filename: str, content: bytes = b"test content", content_type: str = "text/plain"):
        """Create mock UploadFile for testing"""
        async def async_read():
            return content
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.size = len(content)
        mock_file.read = async_read
        return mock_file
    
    def test_validate_file_success_pdf(self, document_service):
        """Test successful PDF file validation"""
        mock_file = self.create_mock_upload_file("test.pdf", content_type="application/pdf")
        
        result = document_service.validate_file(mock_file)
        
        assert result == DocumentType.PDF
    
    def test_validate_file_success_docx(self, document_service):
        """Test successful DOCX file validation"""
        mock_file = self.create_mock_upload_file("test.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        result = document_service.validate_file(mock_file)
        
        assert result == DocumentType.DOCX
    
    def test_validate_file_success_txt(self, document_service):
        """Test successful TXT file validation"""
        mock_file = self.create_mock_upload_file("test.txt", content_type="text/plain")
        
        result = document_service.validate_file(mock_file)
        
        assert result == DocumentType.TXT
    
    def test_validate_file_no_filename(self, document_service):
        """Test validation failure when filename is missing"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        
        with pytest.raises(HTTPException) as exc_info:
            document_service.validate_file(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Filename is required" in str(exc_info.value.detail)
    
    def test_validate_file_unsupported_type(self, document_service):
        """Test validation failure for unsupported file type"""
        mock_file = self.create_mock_upload_file("test.jpg")
        
        with pytest.raises(HTTPException) as exc_info:
            document_service.validate_file(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "not supported" in str(exc_info.value.detail)
    
    def test_validate_file_size_too_large(self, document_service):
        """Test validation failure for file size too large"""
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        mock_file = self.create_mock_upload_file("test.pdf", content=large_content)
        
        with pytest.raises(HTTPException) as exc_info:
            document_service.validate_file(mock_file)
        
        assert exc_info.value.status_code == 413
        assert "exceeds maximum allowed size" in str(exc_info.value.detail)
    
    def test_extract_metadata(self, document_service, temp_upload_dir):
        """Test metadata extraction from file"""
        # Create test file
        test_file = temp_upload_dir / "test.txt"
        test_content = b"test content for metadata extraction"
        test_file.write_bytes(test_content)
        
        mock_file = self.create_mock_upload_file("original_test.txt")
        
        metadata = document_service.extract_metadata(mock_file, test_file)
        
        assert metadata["original_filename"] == "original_test.txt"
        assert metadata["content_type"] == "text/plain"
        assert "upload_timestamp" in metadata
        assert metadata["file_size_bytes"] == len(test_content)
        assert "file_hash" in metadata
        assert "created_at" in metadata
        assert "modified_at" in metadata
    
    def test_generate_unique_filename(self, document_service):
        """Test unique filename generation"""
        import time
        original = "test_document.pdf"
        
        filename1 = document_service._generate_unique_filename(original)
        time.sleep(1)  # Ensure different timestamp
        filename2 = document_service._generate_unique_filename(original)
        
        assert filename1 != filename2
        assert filename1.endswith("_test_document.pdf")
        assert filename2.endswith("_test_document.pdf")
    
    def test_calculate_file_hash(self, document_service, temp_upload_dir):
        """Test file hash calculation"""
        test_file = temp_upload_dir / "test.txt"
        test_content = b"test content for hash calculation"
        test_file.write_bytes(test_content)
        
        hash1 = document_service._calculate_file_hash(test_file)
        hash2 = document_service._calculate_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest length
    
    @pytest.mark.asyncio
    async def test_upload_document_success(self, document_service, mock_db):
        """Test successful document upload"""
        mock_file = self.create_mock_upload_file("test.pdf", b"PDF content")
        mock_document = Mock()
        mock_document.id = "test-id"
        mock_document.filename = "test.pdf"
        mock_document.file_size = 11
        mock_document.document_type = DocumentType.PDF
        mock_document.processing_status = ProcessingStatus.PENDING
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch('app.services.document_service.DocumentResponse') as mock_response:
            mock_response.model_validate.return_value = mock_document
            
            result = await document_service.upload_document(mock_file)
            
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            assert result == mock_document
    
    @pytest.mark.asyncio
    async def test_upload_document_file_too_large_after_upload(self, document_service, mock_db):
        """Test upload failure when file size exceeds limit after upload"""
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        mock_file = self.create_mock_upload_file("test.pdf", large_content)
        
        with pytest.raises(HTTPException) as exc_info:
            await document_service.upload_document(mock_file)
        
        assert exc_info.value.status_code == 413
    
    def test_get_documents_no_filters(self, document_service, mock_db):
        """Test getting documents without filters"""
        mock_documents = [Mock(), Mock()]
        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = mock_documents
        mock_db.query.return_value = mock_query
        
        with patch('app.services.document_service.DocumentResponse') as mock_response:
            mock_response.model_validate.side_effect = lambda x: x
            
            result = document_service.get_documents()
            
            assert len(result) == 2
            mock_db.query.assert_called_once_with(Document)
    
    def test_get_documents_with_filters(self, document_service, mock_db):
        """Test getting documents with filters applied"""
        filters = DocumentFilters(
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.COMPLETED,
            filename_contains="test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        document_service.get_documents(filters)
        
        # Verify filters were applied (3 filter calls)
        assert mock_query.filter.call_count == 3
    
    def test_get_document_by_id_found(self, document_service, mock_db):
        """Test getting document by ID when found"""
        mock_document = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_document
        mock_db.query.return_value = mock_query
        
        with patch('app.services.document_service.DocumentResponse') as mock_response:
            mock_response.model_validate.return_value = mock_document
            
            result = document_service.get_document_by_id("test-id")
            
            assert result == mock_document
    
    def test_get_document_by_id_not_found(self, document_service, mock_db):
        """Test getting document by ID when not found"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = document_service.get_document_by_id("nonexistent-id")
        
        assert result is None
    
    def test_delete_document_success(self, document_service, mock_db, temp_upload_dir):
        """Test successful document deletion"""
        # Create test file
        test_file = temp_upload_dir / "test.txt"
        test_file.write_text("test content")
        
        mock_document = Mock()
        mock_document.file_path = str(test_file)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_document
        mock_db.query.return_value = mock_query
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        result = document_service.delete_document("test-id")
        
        assert result is True
        assert not test_file.exists()
        mock_db.delete.assert_called_once_with(mock_document)
        mock_db.commit.assert_called_once()
    
    def test_delete_document_not_found(self, document_service, mock_db):
        """Test document deletion when document not found"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = document_service.delete_document("nonexistent-id")
        
        assert result is False
    
    def test_update_document_metadata_success(self, document_service, mock_db):
        """Test successful metadata update"""
        mock_document = Mock()
        mock_document.document_metadata = {"existing": "data"}
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_document
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch('app.services.document_service.DocumentResponse') as mock_response:
            mock_response.model_validate.return_value = mock_document
            
            update_data = {"new_field": "new_value"}
            result = document_service.update_document_metadata("test-id", update_data)
            
            assert result == mock_document
            assert mock_document.document_metadata["new_field"] == "new_value"
            assert mock_document.document_metadata["existing"] == "data"
    
    def test_update_document_metadata_not_found(self, document_service, mock_db):
        """Test metadata update when document not found"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = document_service.update_document_metadata("nonexistent-id", {"test": "data"})
        
        assert result is None
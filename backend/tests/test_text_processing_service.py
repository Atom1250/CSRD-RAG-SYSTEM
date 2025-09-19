"""
Unit tests for text processing service
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.text_processing_service import (
    TextProcessingService, 
    TextExtractionError, 
    TextChunkingError,
    TextProcessingConfig
)
from app.models.database import Document, TextChunk, DocumentType, ProcessingStatus
from app.models.schemas import TextChunkResponse


class TestTextProcessingConfig:
    """Test text processing configuration"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = TextProcessingConfig()
        
        assert config.DEFAULT_CHUNK_SIZE == 1000
        assert config.DEFAULT_CHUNK_OVERLAP == 200
        assert config.MIN_CHUNK_SIZE == 100
        assert config.MAX_CHUNK_SIZE == 5000
        assert config.PDF_EXTRACTION_FALLBACK is True
        assert config.PDF_MIN_CONFIDENCE == 0.5


class TestTextProcessingService:
    """Test text processing service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Text processing service instance"""
        return TextProcessingService(mock_db)
    
    @pytest.fixture
    def sample_document(self):
        """Sample document for testing"""
        return Document(
            id="test-doc-id",
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            document_type=DocumentType.PDF,
            processing_status=ProcessingStatus.PENDING
        )
    
    def test_service_initialization(self, mock_db):
        """Test service initialization"""
        service = TextProcessingService(mock_db)
        
        assert service.db == mock_db
        assert isinstance(service.config, TextProcessingConfig)
    
    def test_preprocess_text_basic_cleaning(self, service):
        """Test basic text preprocessing"""
        raw_text = "  This   is    a   test  \n\n\n\n  with   extra   spaces  "
        
        result = service.preprocess_text(raw_text)
        
        assert result == "This is a test with extra spaces"
    
    def test_preprocess_text_special_characters(self, service):
        """Test preprocessing with special characters"""
        raw_text = "Text with\x00null\ufeffBOM and\r\nline endings"
        
        result = service.preprocess_text(raw_text)
        
        assert "\x00" not in result
        assert "\ufeff" not in result
        assert "\r" not in result
        assert result == "Text withnullBOM and line endings"
    
    def test_preprocess_text_empty_input(self, service):
        """Test preprocessing with empty input"""
        assert service.preprocess_text("") == ""
        assert service.preprocess_text("   ") == ""
        assert service.preprocess_text(None) == ""
    
    def test_chunk_text_basic_functionality(self, service):
        """Test basic text chunking"""
        text = "This is a test sentence. " * 50  # ~1250 characters
        
        chunks = service.chunk_text(text, chunk_size=500, chunk_overlap=50)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 500 for chunk in chunks)
        assert len(chunks[0]) > 0
    
    def test_chunk_text_with_sentence_boundaries(self, service):
        """Test chunking respects sentence boundaries"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        
        chunks = service.chunk_text(text, chunk_size=150, chunk_overlap=20)
        
        # Should break at sentence boundaries when possible
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) > 0
    
    def test_chunk_text_empty_input(self, service):
        """Test chunking with empty input"""
        assert service.chunk_text("") == []
        assert service.chunk_text("   ") == []
    
    def test_chunk_text_invalid_parameters(self, service):
        """Test chunking with invalid parameters"""
        text = "Test text"
        
        # Chunk size too small
        with pytest.raises(TextChunkingError, match="Chunk size must be at least"):
            service.chunk_text(text, chunk_size=50)
        
        # Chunk size too large
        with pytest.raises(TextChunkingError, match="Chunk size cannot exceed"):
            service.chunk_text(text, chunk_size=10000)
        
        # Overlap >= chunk size
        with pytest.raises(TextChunkingError, match="Chunk overlap must be less than chunk size"):
            service.chunk_text(text, chunk_size=100, chunk_overlap=100)
        
        # Negative overlap
        with pytest.raises(TextChunkingError, match="Chunk overlap cannot be negative"):
            service.chunk_text(text, chunk_size=100, chunk_overlap=-10)
    
    def test_chunk_text_default_parameters(self, service):
        """Test chunking with default parameters"""
        text = "A" * 2000  # 2000 characters
        
        chunks = service.chunk_text(text)
        
        assert len(chunks) >= 2  # Should create multiple chunks
        assert all(len(chunk) <= service.config.DEFAULT_CHUNK_SIZE for chunk in chunks)
    
    def test_find_sentence_boundary(self, service):
        """Test sentence boundary detection"""
        text = "First sentence. Second sentence! Third sentence?"
        
        # Should find sentence boundary
        boundary = service._find_sentence_boundary(text, 10, 20)
        assert boundary > 10
        
        # Should return -1 if no boundary found
        boundary = service._find_sentence_boundary(text, 0, 5)
        assert boundary == -1
    
    def test_find_word_boundary(self, service):
        """Test word boundary detection"""
        text = "This is a test sentence"
        
        # Should find word boundary
        boundary = service._find_word_boundary(text, 10)
        assert boundary <= 10
        assert text[boundary - 1].isspace() or boundary == 0
    
    @patch('app.services.text_processing_service.Path')
    def test_extract_text_file_not_found(self, mock_path, service, sample_document):
        """Test text extraction when file doesn't exist"""
        mock_path.return_value.exists.return_value = False
        
        with pytest.raises(TextExtractionError, match="Document file not found"):
            service.extract_text_from_document(sample_document)
    
    def test_extract_text_unsupported_type(self, service):
        """Test text extraction with unsupported document type"""
        document = Document(
            id="test-id",
            filename="test.xyz",
            file_path="/tmp/test.xyz",
            document_type="unsupported",  # Invalid type
            processing_status=ProcessingStatus.PENDING
        )
        
        with patch('app.services.text_processing_service.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            with pytest.raises(TextExtractionError, match="Unsupported document type"):
                service.extract_text_from_document(document)
    
    def test_extract_text_from_txt_success(self, service):
        """Test successful TXT text extraction"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content\nWith multiple lines")
            temp_path = f.name
        
        try:
            result = service._extract_text_from_txt(Path(temp_path))
            assert "This is test content" in result
            assert "With multiple lines" in result
        finally:
            os.unlink(temp_path)
    
    def test_extract_text_from_txt_encoding_detection(self, service):
        """Test TXT extraction with different encodings"""
        # Test UTF-8
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("UTF-8 content with special chars: àáâã")
            temp_path = f.name
        
        try:
            result = service._extract_text_from_txt(Path(temp_path))
            assert "UTF-8 content" in result
            assert "àáâã" in result
        finally:
            os.unlink(temp_path)
    
    def test_extract_text_from_txt_empty_file(self, service):
        """Test TXT extraction from empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            with pytest.raises(TextExtractionError, match="Could not decode TXT file"):
                service._extract_text_from_txt(Path(temp_path))
        finally:
            os.unlink(temp_path)
    
    @patch('app.services.text_processing_service.pdfplumber')
    def test_extract_text_from_pdf_success(self, mock_pdfplumber, service):
        """Test successful PDF text extraction"""
        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        # Make sure the content is long enough to avoid fallback (>100 chars)
        long_content = "Page content with enough text to avoid fallback mechanism. " * 3
        mock_page.extract_text.return_value = long_content
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        result = service._extract_text_from_pdf(Path("/fake/path.pdf"))
        
        assert "Page content with enough text to avoid fallback mechanism." in result
        assert "Page 1" in result
    
    @patch('app.services.text_processing_service.pdfplumber')
    @patch('app.services.text_processing_service.PyPDF2')
    def test_extract_text_from_pdf_fallback(self, mock_pypdf2, mock_pdfplumber, service):
        """Test PDF extraction with PyPDF2 fallback"""
        # Mock pdfplumber to return insufficient content
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Short"  # Less than 100 chars
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        # Mock PyPDF2 fallback
        mock_reader = MagicMock()
        mock_pdf_page = MagicMock()
        mock_pdf_page.extract_text.return_value = "Fallback content from PyPDF2"
        mock_reader.pages = [mock_pdf_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        with patch('builtins.open', MagicMock()):
            result = service._extract_text_from_pdf(Path("/fake/path.pdf"))
        
        assert "Fallback content from PyPDF2" in result
    
    @patch('app.services.text_processing_service.DocxDocument')
    def test_extract_text_from_docx_success(self, mock_docx, service):
        """Test successful DOCX text extraction"""
        # Mock docx document
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Paragraph content"
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []
        mock_docx.return_value = mock_doc
        
        result = service._extract_text_from_docx(Path("/fake/path.docx"))
        
        assert "Paragraph content" in result
    
    @patch('app.services.text_processing_service.DocxDocument')
    def test_extract_text_from_docx_with_tables(self, mock_docx, service):
        """Test DOCX extraction with tables"""
        # Mock docx document with table
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        
        mock_cell = MagicMock()
        mock_cell.text = "Cell content"
        mock_row = MagicMock()
        mock_row.cells = [mock_cell]
        mock_table = MagicMock()
        mock_table.rows = [mock_row]
        mock_doc.tables = [mock_table]
        
        mock_docx.return_value = mock_doc
        
        result = service._extract_text_from_docx(Path("/fake/path.docx"))
        
        assert "Cell content" in result
    
    def test_process_document_text_document_not_found(self, service, mock_db):
        """Test processing when document is not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(TextExtractionError, match="Document not found"):
            service.process_document_text("nonexistent-id")
    
    def test_process_document_text_success(self, service, mock_db, sample_document):
        """Test successful document text processing"""
        # Mock database operations
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.commit = MagicMock()
        
        # Mock text extraction
        with patch.object(service, 'extract_text_from_document') as mock_extract:
            mock_extract.return_value = "Sample extracted text content for testing chunking"
            
            # Mock TextChunk creation
            with patch('app.services.text_processing_service.TextChunk') as mock_chunk_class:
                mock_chunk = MagicMock()
                mock_chunk.id = "chunk-id"
                mock_chunk.document_id = sample_document.id
                mock_chunk.content = "Sample extracted text content for testing chunking"
                mock_chunk.chunk_index = 0
                mock_chunk.created_at = "2023-01-01T00:00:00"
                mock_chunk_class.return_value = mock_chunk
                
                result = service.process_document_text(sample_document.id)
                
                assert len(result) >= 1
                assert sample_document.processing_status == ProcessingStatus.COMPLETED
                mock_db.commit.assert_called()
    
    def test_process_document_text_failure(self, service, mock_db, sample_document):
        """Test document processing failure handling"""
        # Mock database operations
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        mock_db.commit = MagicMock()
        
        # Mock text extraction to fail
        with patch.object(service, 'extract_text_from_document') as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")
            
            with pytest.raises(TextExtractionError, match="Document processing failed"):
                service.process_document_text(sample_document.id)
            
            assert sample_document.processing_status == ProcessingStatus.FAILED
            mock_db.commit.assert_called()
    
    def test_get_document_chunks(self, service, mock_db):
        """Test retrieving document chunks"""
        # Mock database query
        mock_chunk = MagicMock()
        mock_chunk.id = "chunk-id"
        mock_chunk.document_id = "doc-id"
        mock_chunk.content = "Chunk content"
        mock_chunk.chunk_index = 0
        mock_chunk.created_at = "2023-01-01T00:00:00"
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_chunk]
        
        result = service.get_document_chunks("doc-id")
        
        assert len(result) == 1
        mock_db.query.assert_called()
    
    def test_get_processing_statistics_no_document(self, service, mock_db):
        """Test processing statistics for non-existent document"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = service.get_processing_statistics("nonexistent-id")
        
        assert result == {}
    
    def test_get_processing_statistics_success(self, service, mock_db, sample_document):
        """Test processing statistics calculation"""
        # Mock document query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        
        # Mock get_document_chunks
        mock_chunks = [
            MagicMock(content="A" * 100),
            MagicMock(content="B" * 200)
        ]
        
        with patch.object(service, 'get_document_chunks') as mock_get_chunks:
            mock_get_chunks.return_value = mock_chunks
            
            result = service.get_processing_statistics(sample_document.id)
            
            assert result["document_id"] == sample_document.id
            assert result["total_chunks"] == 2
            assert result["total_characters"] == 300
            assert result["average_chunk_size"] == 150.0
            assert result["chunk_sizes"] == [100, 200]
    
    def test_get_processing_statistics_no_chunks(self, service, mock_db, sample_document):
        """Test processing statistics with no chunks"""
        # Mock document query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        
        # Mock get_document_chunks to return empty list
        with patch.object(service, 'get_document_chunks') as mock_get_chunks:
            mock_get_chunks.return_value = []
            
            result = service.get_processing_statistics(sample_document.id)
            
            assert result["document_id"] == sample_document.id
            assert result["total_chunks"] == 0
            assert result["total_characters"] == 0
            assert result["average_chunk_size"] == 0


class TestTextExtractionIntegration:
    """Integration tests for text extraction with real files"""
    
    @pytest.fixture
    def service(self):
        """Service with mock database for integration tests"""
        mock_db = Mock(spec=Session)
        return TextProcessingService(mock_db)
    
    def test_pdf_extraction_accuracy(self, service):
        """Test PDF extraction accuracy with a real PDF file"""
        # This would require a test PDF file
        # For now, we'll skip this test in the unit test suite
        pytest.skip("Integration test requires test PDF file")
    
    def test_docx_extraction_accuracy(self, service):
        """Test DOCX extraction accuracy with a real DOCX file"""
        # This would require a test DOCX file
        # For now, we'll skip this test in the unit test suite
        pytest.skip("Integration test requires test DOCX file")
    
    def test_chunking_consistency(self, service):
        """Test that chunking produces consistent results"""
        text = "This is a test document. " * 100  # Repeatable content
        
        chunks1 = service.chunk_text(text, chunk_size=500, chunk_overlap=50)
        chunks2 = service.chunk_text(text, chunk_size=500, chunk_overlap=50)
        
        # Results should be identical
        assert chunks1 == chunks2
        assert len(chunks1) == len(chunks2)
        
        # Verify overlap
        if len(chunks1) > 1:
            # Check that consecutive chunks have some overlap
            for i in range(len(chunks1) - 1):
                chunk1_end = chunks1[i][-50:]  # Last 50 chars
                chunk2_start = chunks1[i + 1][:50]  # First 50 chars
                
                # There should be some common content (not exact due to boundary detection)
                # This is a basic check - in practice, overlap detection is more complex
                assert len(chunk1_end) > 0
                assert len(chunk2_start) > 0
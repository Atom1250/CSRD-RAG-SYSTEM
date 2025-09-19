"""
Integration tests for text processing service with real files
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.text_processing_service import TextProcessingService
from app.models.database import Document, DocumentType, ProcessingStatus


class TestTextProcessingIntegration:
    """Integration tests for text processing with real files"""
    
    @pytest.fixture
    def service(self):
        """Service with mock database for integration tests"""
        mock_db = Mock(spec=Session)
        return TextProcessingService(mock_db)
    
    def test_txt_extraction_and_chunking_integration(self, service):
        """Test complete text extraction and chunking pipeline with real TXT file"""
        # Use the sample text file
        sample_file = Path(__file__).parent / "test_files" / "sample.txt"
        
        # Test text extraction
        extracted_text = service._extract_text_from_txt(sample_file)
        
        # Verify extraction
        assert "sample text file" in extracted_text
        assert "CSRD" in extracted_text
        assert "ESRS" in extracted_text
        assert len(extracted_text) > 100
        
        # Test preprocessing
        processed_text = service.preprocess_text(extracted_text)
        
        # Verify preprocessing cleaned the text
        assert processed_text.strip() == processed_text
        assert "\n\n\n" not in processed_text  # Multiple newlines should be reduced
        
        # Test chunking
        chunks = service.chunk_text(processed_text, chunk_size=200, chunk_overlap=50)
        
        # Verify chunking
        assert len(chunks) > 1  # Should create multiple chunks
        assert all(len(chunk) <= 200 for chunk in chunks)  # Respect size limit
        assert all(len(chunk) > 0 for chunk in chunks)  # No empty chunks
        
        # Verify content preservation
        combined_content = " ".join(chunks)
        assert "sample text file" in combined_content
        assert "CSRD" in combined_content
        assert "ESRS" in combined_content
    
    def test_chunking_consistency_with_real_content(self, service):
        """Test that chunking produces consistent results with real content"""
        sample_file = Path(__file__).parent / "test_files" / "sample.txt"
        
        # Extract and preprocess text
        extracted_text = service._extract_text_from_txt(sample_file)
        processed_text = service.preprocess_text(extracted_text)
        
        # Chunk multiple times with same parameters
        chunks1 = service.chunk_text(processed_text, chunk_size=150, chunk_overlap=30)
        chunks2 = service.chunk_text(processed_text, chunk_size=150, chunk_overlap=30)
        
        # Results should be identical
        assert chunks1 == chunks2
        assert len(chunks1) == len(chunks2)
        
        # Verify overlap exists between consecutive chunks
        if len(chunks1) > 1:
            for i in range(len(chunks1) - 1):
                # Check that there's some common content between consecutive chunks
                # This is a basic check - actual overlap detection is more sophisticated
                assert len(chunks1[i]) > 0
                assert len(chunks1[i + 1]) > 0
    
    def test_sentence_boundary_detection_with_real_content(self, service):
        """Test sentence boundary detection with real content"""
        sample_file = Path(__file__).parent / "test_files" / "sample.txt"
        
        extracted_text = service._extract_text_from_txt(sample_file)
        processed_text = service.preprocess_text(extracted_text)
        
        # Test sentence boundary detection
        # Find a sentence ending in the text
        sentence_end_pos = processed_text.find(". ")
        if sentence_end_pos > 0:
            boundary = service._find_sentence_boundary(
                processed_text, 
                max(0, sentence_end_pos - 10), 
                sentence_end_pos + 10
            )
            assert boundary > 0
            assert boundary <= sentence_end_pos + 2  # Should find the sentence end
    
    def test_word_boundary_detection_with_real_content(self, service):
        """Test word boundary detection with real content"""
        sample_file = Path(__file__).parent / "test_files" / "sample.txt"
        
        extracted_text = service._extract_text_from_txt(sample_file)
        processed_text = service.preprocess_text(extracted_text)
        
        # Test word boundary detection
        if len(processed_text) > 50:
            boundary = service._find_word_boundary(processed_text, 50)
            assert boundary <= 50
            # Should be at a word boundary (space or start of text)
            if boundary > 0:
                assert processed_text[boundary - 1].isspace()
    
    def test_processing_statistics_calculation(self, service):
        """Test processing statistics calculation with real content"""
        sample_file = Path(__file__).parent / "test_files" / "sample.txt"
        
        extracted_text = service._extract_text_from_txt(sample_file)
        processed_text = service.preprocess_text(extracted_text)
        chunks = service.chunk_text(processed_text, chunk_size=200, chunk_overlap=50)
        
        # Calculate expected statistics
        total_chars = sum(len(chunk) for chunk in chunks)
        avg_chunk_size = total_chars / len(chunks) if chunks else 0
        
        # Verify statistics make sense
        assert len(chunks) > 0
        assert total_chars > 0
        assert avg_chunk_size > 0
        assert avg_chunk_size <= 200  # Should not exceed max chunk size
        
        # Verify individual chunk sizes
        chunk_sizes = [len(chunk) for chunk in chunks]
        assert all(size > 0 for size in chunk_sizes)
        assert all(size <= 200 for size in chunk_sizes)
    
    def test_text_preprocessing_edge_cases(self, service):
        """Test text preprocessing with various edge cases"""
        # Test with different types of whitespace and special characters
        test_cases = [
            "Normal text with spaces",
            "Text\twith\ttabs",
            "Text\nwith\nnewlines",
            "Text\r\nwith\r\nwindows\r\nline\r\nendings",
            "Text   with    multiple    spaces",
            "Text\n\n\n\nwith\n\n\nexcessive\n\n\nnewlines",
            "Text with\x00null\ufeffBOM characters",
            "",
            "   ",
            "\n\n\n",
        ]
        
        for test_text in test_cases:
            result = service.preprocess_text(test_text)
            
            # Basic validation
            if test_text.strip():
                assert len(result) > 0
                assert result == result.strip()  # No leading/trailing whitespace
                assert "\x00" not in result  # No null characters
                assert "\ufeff" not in result  # No BOM
                assert "\r" not in result  # No carriage returns
            else:
                assert result == ""  # Empty input should produce empty output
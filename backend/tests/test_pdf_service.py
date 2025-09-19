"""
Tests for PDF generation service
"""
import pytest
from datetime import datetime
from pathlib import Path

from app.services.pdf_service import (
    PDFService, PDFStyle, Citation,
    create_pdf_from_report, validate_pdf_output
)


class TestPDFService:
    """Test cases for PDF generation service"""
    
    @pytest.fixture
    def pdf_service(self):
        """Create PDF service instance"""
        return PDFService()
    
    @pytest.fixture
    def sample_report_content(self):
        """Create sample report content for testing"""
        return {
            "title": "Test Sustainability Report",
            "client_name": "Test Client Corp",
            "generation_date": "2024-01-15T10:30:00",
            "template_type": "eu_esrs_standard",
            "schema_type": "eu_esrs_csrd",
            "executive_summary": "This report provides comprehensive analysis of sustainability compliance.",
            "sections": [
                {
                    "id": "executive_summary",
                    "title": "Executive Summary",
                    "content": "This is a comprehensive executive summary of the sustainability report.",
                    "subsections": [],
                    "metadata": {"required": True},
                    "sources": ["Document 1", "Document 2"]
                }
            ],
            "metadata": {
                "requirements_id": "test_req_123",
                "ai_model_used": "openai_gpt35",
                "generation_timestamp": "2024-01-15T10:30:00"
            }
        }
    
    def test_pdf_service_initialization(self, pdf_service):
        """Test PDF service initialization"""
        assert pdf_service is not None
        assert isinstance(pdf_service.style, PDFStyle)
        assert pdf_service.citations == []
        assert pdf_service.citation_counter == 0
    
    def test_generate_pdf_basic(self, pdf_service, sample_report_content):
        """Test basic PDF generation"""
        pdf_bytes = pdf_service.generate_pdf(sample_report_content)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100  # Should have some content
        assert pdf_bytes.startswith(b'%PDF-')  # Valid PDF header
    
    def test_validate_pdf_quality_valid(self, pdf_service, sample_report_content):
        """Test PDF quality validation with valid PDF"""
        pdf_bytes = pdf_service.generate_pdf(sample_report_content)
        validation_results = pdf_service.validate_pdf_quality(pdf_bytes)
        
        assert validation_results["is_valid_pdf"] is True
        assert validation_results["file_size_bytes"] == len(pdf_bytes)
        assert validation_results["quality_score"] > 0.0
        assert validation_results["estimated_pages"] > 0
    
    def test_validate_pdf_quality_invalid(self, pdf_service):
        """Test PDF quality validation with invalid data"""
        invalid_pdf = b"This is not a PDF file"
        validation_results = pdf_service.validate_pdf_quality(invalid_pdf)
        
        assert validation_results["is_valid_pdf"] is False
        assert validation_results["quality_score"] == 0.0
        assert "Invalid PDF format" in validation_results["issues"]
    
    def test_citation_formatting(self):
        """Test citation formatting"""
        citation = Citation(
            id="test_1",
            title="Test Document",
            source="Test Source",
            page=123,
            url="https://example.com",
            access_date=datetime(2024, 1, 15)
        )
        
        formatted = citation.format_citation()
        
        assert "Test Document" in formatted
        assert "Test Source" in formatted
        assert "p. 123" in formatted
        assert "https://example.com" in formatted
        assert "2024-01-15" in formatted
    
    def test_markdown_processing(self, pdf_service):
        """Test markdown text processing"""
        markdown_text = """
        # Main Title
        ## Subtitle
        
        This is **bold text** and *italic text*.
        
        - List item 1
        - List item 2
        """
        
        processed = pdf_service._process_markdown_to_html(markdown_text)
        
        # Check conversions
        assert '<h1>Main Title</h1>' in processed
        assert '<h2>Subtitle</h2>' in processed
        assert '<strong>bold text</strong>' in processed
        assert '<em>italic text</em>' in processed
        assert '<li>List item 1</li>' in processed
    
    def test_html_generation(self, pdf_service, sample_report_content):
        """Test HTML report generation"""
        html_content = pdf_service._generate_html_report(sample_report_content)
        
        assert isinstance(html_content, str)
        assert len(html_content) > 1000
        assert "<!DOCTYPE html>" in html_content
        assert "Test Sustainability Report" in html_content
        assert "Test Client Corp" in html_content
    
    def test_citation_processing(self, pdf_service, sample_report_content):
        """Test citation creation and management"""
        # Generate PDF to trigger citation processing
        pdf_service.generate_pdf(sample_report_content)
        
        # Check citations were created
        assert len(pdf_service.citations) > 0
        assert pdf_service.citation_counter > 0
        
        # Check citation format
        citation = pdf_service.citations[0]
        assert isinstance(citation, Citation)
        assert citation.id.startswith('ref_')
        assert citation.source is not None


class TestPDFUtilityFunctions:
    """Test utility functions for PDF generation"""
    
    @pytest.fixture
    def sample_report_content(self):
        """Create sample report content for testing"""
        return {
            "title": "Test Report",
            "client_name": "Test Client",
            "generation_date": "2024-01-15T10:30:00",
            "template_type": "standard",
            "schema_type": "unknown",
            "executive_summary": "Test summary",
            "sections": [],
            "metadata": {}
        }
    
    def test_create_pdf_from_report(self, sample_report_content):
        """Test convenience function for PDF creation"""
        pdf_bytes = create_pdf_from_report(sample_report_content)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes.startswith(b'%PDF-')
    
    def test_validate_pdf_output(self, sample_report_content):
        """Test convenience function for PDF validation"""
        pdf_bytes = create_pdf_from_report(sample_report_content)
        validation_results = validate_pdf_output(pdf_bytes)
        
        assert "is_valid_pdf" in validation_results
        assert "quality_score" in validation_results
        assert validation_results["is_valid_pdf"] is True
    
    def test_create_pdf_with_output_path(self, sample_report_content, tmp_path):
        """Test PDF creation with file output"""
        output_file = tmp_path / "test_report.pdf"
        
        pdf_bytes = create_pdf_from_report(sample_report_content, str(output_file))
        
        # Check file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 100
        
        # Check returned bytes match file content
        with open(output_file, 'rb') as f:
            file_content = f.read()
        assert pdf_bytes == file_content
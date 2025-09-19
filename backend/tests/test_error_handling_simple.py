"""
Simple tests for error handling functionality without complex dependencies
"""
import pytest
from fastapi import HTTPException, status

from app.middleware.error_middleware import (
    ErrorDetail,
    DocumentProcessingError,
    VectorDatabaseError,
    AIModelError,
    SchemaValidationError,
    RemoteDirectoryError,
    create_error_response
)
from app.utils.validation import (
    validate_text,
    validate_email,
    validate_url,
    validate_path,
    validate_schema_type,
    validate_query,
    TextValidationConfig,
    format_file_size
)


class TestErrorDetail:
    """Test ErrorDetail class"""
    
    def test_error_detail_creation(self):
        """Test creating error detail"""
        error = ErrorDetail(
            error_type="TestError",
            status_code=400,
            message="Test message",
            details={"key": "value"},
            path="/test",
            method="GET",
            request_id="123"
        )
        
        assert error.error_type == "TestError"
        assert error.status_code == 400
        assert error.message == "Test message"
        assert error.details == {"key": "value"}
        assert error.path == "/test"
        assert error.method == "GET"
        assert error.request_id == "123"
        assert error.timestamp is not None
    
    def test_error_detail_to_dict(self):
        """Test converting error detail to dictionary"""
        error = ErrorDetail(
            error_type="TestError",
            status_code=400,
            message="Test message"
        )
        
        result = error.to_dict()
        
        assert result["type"] == "TestError"
        assert result["status_code"] == 400
        assert result["message"] == "Test message"
        assert "timestamp" in result


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_document_processing_error(self):
        """Test DocumentProcessingError"""
        error = DocumentProcessingError("Processing failed")
        assert str(error) == "Processing failed"
    
    def test_vector_database_error(self):
        """Test VectorDatabaseError"""
        error = VectorDatabaseError("Vector DB connection failed")
        assert str(error) == "Vector DB connection failed"
    
    def test_ai_model_error(self):
        """Test AIModelError"""
        error = AIModelError("Model unavailable")
        assert str(error) == "Model unavailable"
    
    def test_schema_validation_error(self):
        """Test SchemaValidationError"""
        error = SchemaValidationError("Invalid schema")
        assert str(error) == "Invalid schema"
    
    def test_remote_directory_error(self):
        """Test RemoteDirectoryError"""
        error = RemoteDirectoryError("Directory not accessible")
        assert str(error) == "Directory not accessible"


class TestTextValidation:
    """Test text validation functionality"""
    
    def test_validate_text_normal(self):
        """Test validating normal text"""
        result = validate_text("Hello world")
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_text_too_short(self):
        """Test validating text that's too short"""
        config = TextValidationConfig(min_length=10)
        result = validate_text("Hi", config)
        
        assert result.is_valid is False
        assert any("Minimum length" in error for error in result.errors)
    
    def test_validate_text_too_long(self):
        """Test validating text that's too long"""
        config = TextValidationConfig(max_length=5)
        result = validate_text("Hello world", config)
        
        assert result.is_valid is False
        assert any("Maximum length" in error for error in result.errors)
    
    def test_validate_text_required_empty(self):
        """Test validating empty required text"""
        config = TextValidationConfig(required=True)
        result = validate_text("", config)
        
        assert result.is_valid is False
        assert any("required" in error for error in result.errors)
    
    def test_validate_text_pattern_match(self):
        """Test validating text against pattern"""
        config = TextValidationConfig(pattern=r"^[a-z]+\d+$")
        result = validate_text("abc123", config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_text_pattern_no_match(self):
        """Test validating text that doesn't match pattern"""
        config = TextValidationConfig(
            pattern=r"^[a-z]+\d+$",
            pattern_message="Must be lowercase letters followed by numbers"
        )
        result = validate_text("ABC123", config)
        
        assert result.is_valid is False
        assert any("lowercase letters" in error for error in result.errors)


class TestSpecificValidators:
    """Test specific validation functions"""
    
    def test_validate_email_valid(self):
        """Test validating valid email addresses"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            result = validate_email(email)
            assert result.is_valid is True, f"Email {email} should be valid"
    
    def test_validate_email_invalid(self):
        """Test validating invalid email addresses"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com"
        ]
        
        for email in invalid_emails:
            result = validate_email(email)
            assert result.is_valid is False, f"Email {email} should be invalid"
    
    def test_validate_url_valid(self):
        """Test validating valid URLs"""
        valid_urls = [
            "http://example.com",
            "https://www.example.com",
            "https://example.com/path?query=value#fragment"
        ]
        
        for url in valid_urls:
            result = validate_url(url, required=True)
            assert result.is_valid is True, f"URL {url} should be valid"
    
    def test_validate_path_valid(self):
        """Test validating valid paths"""
        valid_paths = [
            "/home/user/documents",
            "./relative/path"
        ]
        
        for path in valid_paths:
            result = validate_path(path)
            assert result.is_valid is True, f"Path {path} should be valid"
    
    def test_validate_path_security_issue(self):
        """Test validating path with security issues"""
        result = validate_path("/home/../etc/passwd")
        
        assert result.is_valid is False
        assert any("security" in error for error in result.errors)
    
    def test_validate_schema_type_valid(self):
        """Test validating valid schema types"""
        valid_types = ["EU_ESRS_CSRD", "UK_SRD", "OTHER"]
        
        for schema_type in valid_types:
            result = validate_schema_type(schema_type)
            assert result.is_valid is True, f"Schema type {schema_type} should be valid"
    
    def test_validate_schema_type_invalid(self):
        """Test validating invalid schema type"""
        result = validate_schema_type("INVALID_TYPE")
        
        assert result.is_valid is False
        assert any("Invalid schema type" in error for error in result.errors)
    
    def test_validate_query_valid(self):
        """Test validating valid query"""
        result = validate_query("What are the CSRD requirements?")
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_query_too_short(self):
        """Test validating query that's too short"""
        result = validate_query("Hi")
        
        assert result.is_valid is False
        assert any("Minimum length" in error for error in result.errors)


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_format_file_size(self):
        """Test file size formatting"""
        assert format_file_size(0) == "0 Bytes"
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(1024 * 1024) == "1.00 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
        assert format_file_size(1536) == "1.50 KB"
    
    def test_create_error_response(self):
        """Test creating error response"""
        response = create_error_response(
            status_code=400,
            message="Test error",
            error_type="TestError"
        )
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "Test error" in content
        assert "TestError" in content
"""
Tests for configuration management
"""
import pytest
from app.core.config import Settings


def test_default_settings():
    """Test default settings initialization"""
    settings = Settings()
    
    assert settings.app_name == "CSRD RAG System"
    assert settings.app_version == "1.0.0"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.chunk_size == 1000
    assert settings.chunk_overlap == 200
    assert "pdf" in settings.allowed_file_types
    assert "docx" in settings.allowed_file_types
    assert "txt" in settings.allowed_file_types


def test_settings_validation():
    """Test settings validation"""
    settings = Settings(
        max_file_size=1024,
        chunk_size=500
    )
    
    assert settings.max_file_size == 1024
    assert settings.chunk_size == 500


def test_supported_schemas():
    """Test supported schema configuration"""
    settings = Settings()
    
    assert "EU_ESRS_CSRD" in settings.supported_schemas
    assert "UK_SRD" in settings.supported_schemas
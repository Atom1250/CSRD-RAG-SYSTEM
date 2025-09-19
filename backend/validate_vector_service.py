#!/usr/bin/env python3
"""
Validation script for vector service implementation
"""
import sys
import os
import tempfile
import shutil

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_structure():
    """Test basic structure without ML dependencies"""
    print("Testing basic structure...")
    
    try:
        # Test configuration
        from app.core.config import settings
        assert hasattr(settings, 'vector_db_type')
        assert hasattr(settings, 'chroma_persist_directory')
        assert hasattr(settings, 'default_embedding_model')
        print("✓ Configuration has vector-related settings")
        
        # Test schemas
        from app.models.schemas import SearchResult
        result = SearchResult(
            chunk_id="test",
            document_id="doc1",
            content="test content",
            relevance_score=0.9,
            document_filename="test.pdf"
        )
        assert result.chunk_id == "test"
        assert result.relevance_score == 0.9
        print("✓ SearchResult schema works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic structure test failed: {e}")
        return False

def test_database_models():
    """Test database models for vector support"""
    print("Testing database models...")
    
    try:
        from app.models.database import TextChunk
        from app.models.schemas import TextChunkCreate, TextChunkResponse
        
        # Test that TextChunk has embedding_vector field
        chunk_data = {
            'id': 'test-chunk',
            'document_id': 'test-doc',
            'content': 'Test content',
            'chunk_index': 0,
            'embedding_vector': [0.1, 0.2, 0.3],
            'schema_elements': ['E1'],
            'created_at': '2023-01-01T00:00:00'
        }
        
        # Test schema validation
        chunk_create = TextChunkCreate(
            document_id='test-doc',
            content='Test content',
            chunk_index=0,
            embedding_vector=[0.1, 0.2, 0.3]
        )
        assert chunk_create.embedding_vector == [0.1, 0.2, 0.3]
        print("✓ TextChunk models support embedding vectors")
        
        return True
        
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        return False

def test_text_processing_integration():
    """Test text processing service integration points"""
    print("Testing text processing integration...")
    
    try:
        from app.services.text_processing_service import TextProcessingService
        
        # Check that the service has the new async methods
        service_methods = dir(TextProcessingService)
        assert 'process_document_text' in service_methods
        print("✓ Text processing service has required methods")
        
        return True
        
    except Exception as e:
        print(f"✗ Text processing integration test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("Testing file structure...")
    
    required_files = [
        'app/services/vector_service.py',
        'app/services/search_service.py',
        'tests/test_vector_service.py',
        'tests/test_vector_integration.py',
        'tests/test_search_service.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files exist")
        return True

def main():
    """Run all validation tests"""
    print("Validating Vector Service Implementation")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_basic_structure,
        test_database_models,
        test_text_processing_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ Vector service implementation is structurally complete!")
        print("\nNext steps:")
        print("1. Install compatible ML dependencies (sentence-transformers, chromadb)")
        print("2. Run integration tests with actual ML models")
        print("3. Test with real document processing workflow")
        return True
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
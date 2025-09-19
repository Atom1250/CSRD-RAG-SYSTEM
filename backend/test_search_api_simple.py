#!/usr/bin/env python3
"""
Simple API test for search endpoints
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app


def test_search_endpoints():
    """Test search API endpoints"""
    print("Testing Search API Endpoints")
    print("=" * 40)
    
    client = TestClient(app)
    
    # Test health endpoint
    print("Testing search health endpoint...")
    response = client.get("/api/search/health")
    assert response.status_code == 200
    health = response.json()
    assert "status" in health
    print(f"✓ Health check: {health['status']}")
    
    # Test statistics endpoint
    print("Testing search statistics endpoint...")
    response = client.get("/api/search/statistics")
    assert response.status_code == 200
    stats = response.json()
    assert "total_documents" in stats
    assert "vector_service_available" in stats
    print(f"✓ Statistics: {stats['total_documents']} documents, vector service: {stats['vector_service_available']}")
    
    # Test suggestions endpoint
    print("Testing search suggestions endpoint...")
    response = client.get("/api/search/suggestions", params={"partial_query": "climate"})
    assert response.status_code == 200
    suggestions = response.json()
    assert "suggestions" in suggestions
    assert "query" in suggestions
    print(f"✓ Suggestions for 'climate': {len(suggestions['suggestions'])} found")
    
    # Test search endpoint with GET (should return empty due to no vector service)
    print("Testing search GET endpoint...")
    response = client.get("/api/search/", params={"query": "climate change"})
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    print(f"✓ Search GET: {len(results)} results (expected 0 due to no vector service)")
    
    # Test search endpoint with POST
    print("Testing search POST endpoint...")
    search_data = {
        "query": "sustainability reporting",
        "top_k": 5,
        "min_relevance_score": 0.5
    }
    response = client.post("/api/search/", json=search_data)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    print(f"✓ Search POST: {len(results)} results (expected 0 due to no vector service)")
    
    # Test embedding generation endpoint
    print("Testing embedding generation endpoint...")
    response = client.post("/api/search/embedding/generate", params={"query": "test query"})
    # This should fail gracefully due to no vector service
    assert response.status_code == 500
    error = response.json()
    assert "detail" in error
    print("✓ Embedding generation: Properly handles vector service unavailable")
    
    # Test performance metrics endpoint
    print("Testing performance metrics endpoint...")
    response = client.get("/api/search/performance", params={"query": "test query"})
    # Should return error due to no vector service
    assert response.status_code == 500
    error = response.json()
    assert "detail" in error
    print("✓ Performance metrics: Properly handles vector service unavailable")
    
    # Test schema search endpoint
    print("Testing schema search endpoint...")
    schema_data = {
        "schema_elements": ["E1", "E1-1"],
        "top_k": 10
    }
    response = client.post("/api/search/schema", json=schema_data)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    print(f"✓ Schema search: {len(results)} results")
    
    # Test similar chunks endpoint
    print("Testing similar chunks endpoint...")
    similar_data = {
        "chunk_id": "test_chunk_id",
        "top_k": 5
    }
    response = client.post("/api/search/similar", json=similar_data)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    print(f"✓ Similar chunks: {len(results)} results")
    
    print("\n" + "=" * 40)
    print("🎉 All search API tests passed!")
    print("\nAPI Endpoints implemented:")
    print("✓ GET  /api/search/health - Health check")
    print("✓ GET  /api/search/statistics - Search statistics")
    print("✓ GET  /api/search/suggestions - Search suggestions")
    print("✓ GET  /api/search/ - Simple search")
    print("✓ POST /api/search/ - Advanced search with filters")
    print("✓ POST /api/search/embedding - Search with custom embedding")
    print("✓ POST /api/search/schema - Search by schema elements")
    print("✓ POST /api/search/similar - Find similar chunks")
    print("✓ POST /api/search/embedding/generate - Generate embeddings")
    print("✓ GET  /api/search/performance - Performance metrics")
    
    return True


def test_search_validation():
    """Test API parameter validation"""
    print("\nTesting API parameter validation...")
    
    client = TestClient(app)
    
    # Test invalid query length
    response = client.get("/api/search/", params={"query": ""})
    assert response.status_code == 422
    print("✓ Empty query validation")
    
    # Test invalid top_k
    response = client.get("/api/search/", params={"query": "test", "top_k": 0})
    assert response.status_code == 422
    print("✓ Invalid top_k validation")
    
    # Test invalid relevance score
    response = client.get("/api/search/", params={"query": "test", "min_relevance_score": 1.5})
    assert response.status_code == 422
    print("✓ Invalid relevance score validation")
    
    # Test invalid suggestions query
    response = client.get("/api/search/suggestions", params={"partial_query": "a"})
    assert response.status_code == 422
    print("✓ Short suggestions query validation")
    
    print("✓ All validation tests passed")


def main():
    """Run all API tests"""
    try:
        test_search_endpoints()
        test_search_validation()
        return True
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
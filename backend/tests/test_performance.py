"""
Performance tests for caching and optimization features
"""
import pytest
import time
import asyncio
from unittest.mock import Mock, patch
from typing import List

from app.services.cache_service import CacheService
from app.services.performance_service import PerformanceMonitor, performance_timer, async_performance_timer
from app.services.vector_service import EmbeddingService
from app.services.search_service import SearchService
from app.services.rag_service import RAGService


class TestCacheService:
    """Test cache service functionality"""
    
    def test_cache_basic_operations(self):
        """Test basic cache set/get operations"""
        cache = CacheService()
        
        # Test string data
        assert cache.set("test_key", "test_value", ttl=60)
        assert cache.get("test_key") == "test_value"
        
        # Test dict data
        test_dict = {"key": "value", "number": 42}
        assert cache.set("test_dict", test_dict, ttl=60)
        retrieved = cache.get("test_dict")
        assert retrieved == test_dict
        
        # Test list data
        test_list = [1, 2, 3, "test"]
        assert cache.set("test_list", test_list, ttl=60)
        assert cache.get("test_list") == test_list
    
    def test_cache_embedding_operations(self):
        """Test embedding-specific cache operations"""
        cache = CacheService()
        
        text = "This is a test sentence for embedding"
        model = "test-model"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Cache embedding
        assert cache.cache_embedding(text, model, embedding)
        
        # Retrieve embedding
        retrieved = cache.get_cached_embedding(text, model)
        assert retrieved == embedding
        
        # Test non-existent embedding
        assert cache.get_cached_embedding("non-existent", model) is None
    
    def test_cache_search_results(self):
        """Test search result caching"""
        cache = CacheService()
        
        query = "test query"
        filters = {"document_type": "pdf"}
        results = [
            {"chunk_id": "1", "content": "test content 1", "relevance_score": 0.9},
            {"chunk_id": "2", "content": "test content 2", "relevance_score": 0.8}
        ]
        
        # Cache search results
        assert cache.cache_search_results(query, filters, results)
        
        # Retrieve search results
        retrieved = cache.get_cached_search_results(query, filters)
        assert retrieved == results
        
        # Test with different filters
        different_filters = {"document_type": "docx"}
        assert cache.get_cached_search_results(query, different_filters) is None
    
    def test_cache_rag_response(self):
        """Test RAG response caching"""
        cache = CacheService()
        
        query = "What is CSRD?"
        model = "gpt-4"
        context_hash = "abc123"
        response = {
            "query": query,
            "response_text": "CSRD stands for Corporate Sustainability Reporting Directive",
            "confidence_score": 0.95,
            "model_used": model
        }
        
        # Cache RAG response
        assert cache.cache_rag_response(query, model, context_hash, response)
        
        # Retrieve RAG response
        retrieved = cache.get_cached_rag_response(query, model, context_hash)
        assert retrieved == response
    
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration"""
        cache = CacheService()
        
        # Set with very short TTL
        cache.set("short_ttl", "value", ttl=1)
        assert cache.get("short_ttl") == "value"
        
        # Wait for expiration
        time.sleep(2)
        assert cache.get("short_ttl") is None
    
    def test_cache_pattern_clearing(self):
        """Test clearing cache by pattern"""
        cache = CacheService()
        
        # Set multiple keys
        cache.set("test:1", "value1")
        cache.set("test:2", "value2")
        cache.set("other:1", "value3")
        
        # Clear test pattern
        cleared = cache.clear_pattern("test:*")
        assert cleared >= 2
        
        # Check remaining keys
        assert cache.get("test:1") is None
        assert cache.get("test:2") is None
        assert cache.get("other:1") == "value3"


class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization"""
        monitor = PerformanceMonitor()
        assert monitor.start_time > 0
        assert monitor.request_count == 0
        assert monitor.error_count == 0
    
    def test_request_recording(self):
        """Test request performance recording"""
        monitor = PerformanceMonitor()
        
        # Record successful request
        monitor.record_request("test_endpoint", "GET", 0.5, 200)
        assert monitor.request_count == 1
        assert monitor.error_count == 0
        
        # Record error request
        monitor.record_request("test_endpoint", "POST", 1.0, 500)
        assert monitor.request_count == 2
        assert monitor.error_count == 1
    
    def test_operation_recording(self):
        """Test operation performance recording"""
        monitor = PerformanceMonitor()
        
        # Record successful operation
        monitor.record_operation("test_operation", 0.3, True)
        
        # Record failed operation
        monitor.record_operation("test_operation", 0.8, False)
    
    def test_system_metrics(self):
        """Test system metrics collection"""
        monitor = PerformanceMonitor()
        metrics = monitor.get_system_metrics()
        
        assert "timestamp" in metrics
        assert "uptime_seconds" in metrics
        assert "cpu_percent" in metrics
        assert "memory_total_gb" in metrics
        assert "memory_used_gb" in metrics
        assert "memory_percent" in metrics
        assert "request_count" in metrics
        assert "error_count" in metrics
        assert "error_rate" in metrics
    
    def test_performance_timer_decorator(self):
        """Test performance timer decorator"""
        
        @performance_timer("test_function")
        def test_function():
            time.sleep(0.1)
            return "result"
        
        result = test_function()
        assert result == "result"
    
    @pytest.mark.asyncio
    async def test_async_performance_timer_decorator(self):
        """Test async performance timer decorator"""
        
        @async_performance_timer("test_async_function")
        async def test_async_function():
            await asyncio.sleep(0.1)
            return "async_result"
        
        result = await test_async_function()
        assert result == "async_result"
    
    def test_measure_operation_context_manager(self):
        """Test operation measurement context manager"""
        monitor = PerformanceMonitor()
        
        with monitor.measure_operation("test_context"):
            time.sleep(0.05)
    
    @pytest.mark.asyncio
    async def test_measure_async_operation_context_manager(self):
        """Test async operation measurement context manager"""
        monitor = PerformanceMonitor()
        
        async with monitor.measure_async_operation("test_async_context"):
            await asyncio.sleep(0.05)


class TestPerformanceIntegration:
    """Test performance features integration with services"""
    
    @pytest.mark.asyncio
    async def test_vector_service_caching(self):
        """Test vector service embedding caching"""
        # Mock the sentence transformer model
        with patch('app.services.vector_service.SentenceTransformer') as mock_transformer:
            mock_model = Mock()
            mock_model.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_transformer.return_value = mock_model
            
            # Create embedding service
            embedding_service = EmbeddingService()
            
            # Generate embedding (should call model)
            text = "test embedding text"
            embedding1 = embedding_service.generate_embedding(text)
            assert mock_model.encode.call_count == 1
            
            # Generate same embedding again (should use cache)
            embedding2 = embedding_service.generate_embedding(text)
            assert mock_model.encode.call_count == 1  # Should not increase
            assert embedding1 == embedding2
    
    @pytest.mark.asyncio
    async def test_search_service_caching(self, test_db):
        """Test search service result caching"""
        # Mock vector service
        with patch('app.services.search_service.embedding_service') as mock_embedding:
            mock_embedding.search_similar_chunks.return_value = []
            
            search_service = SearchService(test_db)
            
            # First search
            results1 = await search_service.search_documents("test query")
            
            # Second search with same query (should use cache)
            results2 = await search_service.search_documents("test query")
            
            assert results1 == results2
    
    def test_database_connection_pooling(self):
        """Test database connection pool configuration"""
        from app.services.performance_service import db_pool
        
        config = db_pool.get_engine_config()
        assert config["pool_size"] == 20
        assert config["max_overflow"] == 30
        assert config["pool_timeout"] == 30
        assert config["pool_recycle"] == 3600
        assert config["pool_pre_ping"] is True


class TestPerformanceBenchmarks:
    """Performance benchmark tests to establish baseline metrics"""
    
    def test_cache_performance_benchmark(self):
        """Benchmark cache operations"""
        cache = CacheService()
        
        # Benchmark cache set operations
        start_time = time.time()
        for i in range(1000):
            cache.set(f"benchmark_key_{i}", f"value_{i}")
        set_duration = time.time() - start_time
        
        # Benchmark cache get operations
        start_time = time.time()
        for i in range(1000):
            cache.get(f"benchmark_key_{i}")
        get_duration = time.time() - start_time
        
        # Assert performance thresholds
        assert set_duration < 5.0, f"Cache set operations too slow: {set_duration:.3f}s"
        assert get_duration < 2.0, f"Cache get operations too slow: {get_duration:.3f}s"
        
        print(f"Cache benchmark - Set: {set_duration:.3f}s, Get: {get_duration:.3f}s")
    
    @pytest.mark.asyncio
    async def test_embedding_generation_benchmark(self):
        """Benchmark embedding generation performance"""
        with patch('app.services.vector_service.SentenceTransformer') as mock_transformer:
            mock_model = Mock()
            mock_model.encode.return_value = [0.1] * 384  # Typical embedding size
            mock_transformer.return_value = mock_model
            
            embedding_service = EmbeddingService()
            
            # Benchmark single embedding generation
            start_time = time.time()
            for i in range(100):
                embedding_service.generate_embedding(f"test text {i}")
            single_duration = time.time() - start_time
            
            # Benchmark batch embedding generation
            texts = [f"batch text {i}" for i in range(100)]
            start_time = time.time()
            embedding_service.generate_embeddings(texts)
            batch_duration = time.time() - start_time
            
            print(f"Embedding benchmark - Single: {single_duration:.3f}s, Batch: {batch_duration:.3f}s")
            
            # Batch should be significantly faster than individual calls
            assert batch_duration < single_duration * 0.5, "Batch processing not optimized"
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring"""
        monitor = PerformanceMonitor()
        
        # Get initial memory usage
        initial_metrics = monitor.get_system_metrics()
        initial_memory = initial_metrics.get("process_memory_mb", 0)
        
        # Create some data to increase memory usage
        large_data = ["x" * 1000 for _ in range(10000)]  # ~10MB of data
        
        # Get memory usage after allocation
        final_metrics = monitor.get_system_metrics()
        final_memory = final_metrics.get("process_memory_mb", 0)
        
        # Memory should have increased
        memory_increase = final_memory - initial_memory
        assert memory_increase > 0, "Memory monitoring not working"
        
        print(f"Memory increase: {memory_increase:.2f}MB")
        
        # Clean up
        del large_data


@pytest.fixture
def test_db():
    """Mock database session for testing"""
    from unittest.mock import Mock
    db = Mock()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    return db
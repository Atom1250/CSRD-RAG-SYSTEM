#!/usr/bin/env python3
"""
Simple performance test script for caching and optimization features
"""
import asyncio
import time
import requests
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_ITERATIONS = 10


def test_cache_service():
    """Test cache service functionality"""
    print("Testing Cache Service...")
    
    from app.services.cache_service import cache_service
    
    # Test basic operations
    test_key = "test_performance_key"
    test_value = {"data": "test_value", "timestamp": time.time()}
    
    # Test set operation
    start_time = time.time()
    success = cache_service.set(test_key, test_value, ttl=300)
    set_duration = time.time() - start_time
    
    print(f"  Cache SET: {success} in {set_duration:.4f}s")
    
    # Test get operation
    start_time = time.time()
    retrieved_value = cache_service.get(test_key)
    get_duration = time.time() - start_time
    
    print(f"  Cache GET: {retrieved_value == test_value} in {get_duration:.4f}s")
    
    # Test embedding cache
    text = "This is a test sentence for embedding caching"
    model = "test-model"
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    start_time = time.time()
    cache_service.cache_embedding(text, model, embedding)
    cache_duration = time.time() - start_time
    
    start_time = time.time()
    cached_embedding = cache_service.get_cached_embedding(text, model)
    retrieve_duration = time.time() - start_time
    
    print(f"  Embedding cache: {cached_embedding == embedding} in {cache_duration:.4f}s / {retrieve_duration:.4f}s")
    
    # Clean up
    cache_service.delete(test_key)
    
    return True


def test_performance_monitoring():
    """Test performance monitoring functionality"""
    print("Testing Performance Monitoring...")
    
    from app.services.performance_service import performance_monitor
    
    # Test system metrics
    start_time = time.time()
    metrics = performance_monitor.get_system_metrics()
    metrics_duration = time.time() - start_time
    
    print(f"  System metrics collected in {metrics_duration:.4f}s")
    print(f"  CPU: {metrics.get('cpu_percent', 0):.1f}%")
    print(f"  Memory: {metrics.get('memory_percent', 0):.1f}%")
    print(f"  Uptime: {metrics.get('uptime_seconds', 0):.1f}s")
    
    # Test operation recording
    start_time = time.time()
    performance_monitor.record_operation("test_operation", 0.1, True)
    record_duration = time.time() - start_time
    
    print(f"  Operation recorded in {record_duration:.4f}s")
    
    return True


def test_api_performance():
    """Test API performance with caching"""
    print("Testing API Performance...")
    
    try:
        # Test health endpoint
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        health_duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"  Health check: OK in {health_duration:.4f}s")
        else:
            print(f"  Health check: FAILED ({response.status_code})")
            return False
        
        # Test metrics endpoint
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/v1/metrics/health", timeout=10)
        metrics_duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"  Metrics endpoint: OK in {metrics_duration:.4f}s")
            metrics_data = response.json()
            print(f"  System status: {metrics_data.get('status', 'unknown')}")
        else:
            print(f"  Metrics endpoint: FAILED ({response.status_code})")
        
        # Test performance summary
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/v1/metrics/performance", timeout=10)
        perf_duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"  Performance summary: OK in {perf_duration:.4f}s")
            perf_data = response.json()
            print(f"  Overall status: {perf_data.get('overall_status', 'unknown')}")
        else:
            print(f"  Performance summary: FAILED ({response.status_code})")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  API test failed: {e}")
        return False


def test_caching_effectiveness():
    """Test caching effectiveness with repeated requests"""
    print("Testing Caching Effectiveness...")
    
    try:
        # Make the same request multiple times to test caching
        test_endpoint = f"{BASE_URL}/api/v1/metrics/system"
        
        # First request (should be slower - no cache)
        start_time = time.time()
        response1 = requests.get(test_endpoint, timeout=10)
        first_duration = time.time() - start_time
        
        if response1.status_code != 200:
            print(f"  First request failed: {response1.status_code}")
            return False
        
        # Second request (should be faster - cached)
        start_time = time.time()
        response2 = requests.get(test_endpoint, timeout=10)
        second_duration = time.time() - start_time
        
        if response2.status_code != 200:
            print(f"  Second request failed: {response2.status_code}")
            return False
        
        print(f"  First request: {first_duration:.4f}s")
        print(f"  Second request: {second_duration:.4f}s")
        
        # Check if caching improved performance
        if second_duration < first_duration * 0.8:
            print(f"  Caching effective: {((first_duration - second_duration) / first_duration * 100):.1f}% improvement")
        else:
            print(f"  Caching may not be effective or requests are already fast")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  Caching test failed: {e}")
        return False


def benchmark_performance():
    """Run performance benchmarks"""
    print("Running Performance Benchmarks...")
    
    # Benchmark cache operations
    from app.services.cache_service import cache_service
    
    # Benchmark multiple cache operations
    start_time = time.time()
    for i in range(100):
        cache_service.set(f"benchmark_{i}", f"value_{i}", ttl=60)
    bulk_set_duration = time.time() - start_time
    
    start_time = time.time()
    for i in range(100):
        cache_service.get(f"benchmark_{i}")
    bulk_get_duration = time.time() - start_time
    
    print(f"  Bulk cache operations (100 items):")
    print(f"    SET: {bulk_set_duration:.4f}s ({100/bulk_set_duration:.0f} ops/sec)")
    print(f"    GET: {bulk_get_duration:.4f}s ({100/bulk_get_duration:.0f} ops/sec)")
    
    # Clean up
    cache_service.clear_pattern("benchmark_*")
    
    return True


def main():
    """Run all performance tests"""
    print("=" * 60)
    print("CSRD RAG System - Performance Test Suite")
    print("=" * 60)
    
    tests = [
        ("Cache Service", test_cache_service),
        ("Performance Monitoring", test_performance_monitoring),
        ("API Performance", test_api_performance),
        ("Caching Effectiveness", test_caching_effectiveness),
        ("Performance Benchmarks", benchmark_performance),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        try:
            start_time = time.time()
            success = test_func()
            duration = time.time() - start_time
            
            results[test_name] = {
                "success": success,
                "duration": duration
            }
            
            status = "PASS" if success else "FAIL"
            print(f"  Result: {status} (took {duration:.3f}s)")
            
        except Exception as e:
            results[test_name] = {
                "success": False,
                "duration": 0,
                "error": str(e)
            }
            print(f"  Result: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(tests)
    passed_tests = sum(1 for result in results.values() if result["success"])
    
    for test_name, result in results.items():
        status = "PASS" if result["success"] else "FAIL"
        duration = result["duration"]
        error = result.get("error", "")
        
        print(f"{test_name:25} | {status:4} | {duration:6.3f}s | {error}")
    
    print("-" * 60)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All performance tests passed!")
        return 0
    else:
        print("❌ Some performance tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
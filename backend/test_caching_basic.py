#!/usr/bin/env python3
"""
Basic caching functionality test without external dependencies
"""
import sys
import os
import time

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_cache_service_basic():
    """Test basic cache service functionality"""
    print("Testing Cache Service (basic functionality)...")
    
    try:
        from app.services.cache_service import CacheService
        
        # Create cache service instance
        cache = CacheService()
        
        # Test basic operations even if Redis is not available
        print("  Cache service initialized")
        
        # Test health check
        health = cache.health_check()
        print(f"  Cache health: {health.get('status', 'unknown')}")
        
        # Test key generation
        key = cache._generate_key("test", "identifier")
        print(f"  Key generation: {key is not None}")
        
        # Test serialization
        test_data = {"key": "value", "number": 42}
        serialized = cache._serialize_data(test_data)
        deserialized = cache._deserialize_data(serialized)
        print(f"  Serialization: {deserialized == test_data}")
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def test_performance_monitor_basic():
    """Test basic performance monitoring functionality"""
    print("Testing Performance Monitor (basic functionality)...")
    
    try:
        from app.services.performance_service import PerformanceMonitor
        
        # Create performance monitor
        monitor = PerformanceMonitor()
        print("  Performance monitor initialized")
        
        # Test request recording
        monitor.record_request("test_endpoint", "GET", 0.1, 200)
        print(f"  Request recorded: count={monitor.request_count}")
        
        # Test operation recording
        monitor.record_operation("test_operation", 0.05, True)
        print("  Operation recorded")
        
        # Test system metrics (should work even without psutil)
        metrics = monitor.get_system_metrics()
        print(f"  System metrics: {len(metrics)} fields")
        print(f"  Uptime: {metrics.get('uptime_seconds', 0):.2f}s")
        print(f"  PSUTIL available: {metrics.get('psutil_available', False)}")
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def test_performance_decorators():
    """Test performance timing decorators"""
    print("Testing Performance Decorators...")
    
    try:
        from app.services.performance_service import performance_timer
        
        @performance_timer("test_function")
        def test_function():
            time.sleep(0.01)  # Small delay
            return "success"
        
        result = test_function()
        print(f"  Decorator test: {result == 'success'}")
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def test_database_pool_config():
    """Test database connection pool configuration"""
    print("Testing Database Pool Configuration...")
    
    try:
        from app.services.performance_service import DatabaseConnectionPool
        
        pool = DatabaseConnectionPool()
        engine_config = pool.get_engine_config()
        session_config = pool.get_session_config()
        
        print(f"  Pool size: {engine_config.get('pool_size', 0)}")
        print(f"  Max overflow: {engine_config.get('max_overflow', 0)}")
        print(f"  Pool timeout: {engine_config.get('pool_timeout', 0)}")
        print(f"  Session autoflush: {session_config.get('autoflush', False)}")
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def test_query_optimizer():
    """Test query optimization utilities"""
    print("Testing Query Optimizer...")
    
    try:
        from app.services.performance_service import QueryOptimizer
        
        # Test pagination
        pagination = QueryOptimizer.get_pagination_params(page=2, size=50)
        print(f"  Pagination: limit={pagination['limit']}, offset={pagination['offset']}")
        
        # Test optimization hints
        hints = QueryOptimizer.get_search_optimization_hints()
        print(f"  Optimization hints: {len(hints)} settings")
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    """Run all basic tests"""
    print("=" * 60)
    print("CSRD RAG System - Basic Caching & Performance Tests")
    print("=" * 60)
    
    tests = [
        ("Cache Service Basic", test_cache_service_basic),
        ("Performance Monitor Basic", test_performance_monitor_basic),
        ("Performance Decorators", test_performance_decorators),
        ("Database Pool Config", test_database_pool_config),
        ("Query Optimizer", test_query_optimizer),
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
        print("🎉 All basic tests passed!")
        return 0
    else:
        print("❌ Some basic tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
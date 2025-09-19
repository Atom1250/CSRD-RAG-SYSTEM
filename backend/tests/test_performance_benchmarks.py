"""
Performance Benchmarking Tests for CSRD RAG System

This module contains performance tests that measure and validate system performance
against defined benchmarks for document processing and query response times.
"""

import pytest
import time
import asyncio
import tempfile
import os
import statistics
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from tests.conftest import test_db, client
except ImportError:
    # For validation purposes when test modules aren't available
    pass


class TestDocumentProcessingPerformance:
    """Test document processing performance benchmarks"""
    
    def setup_method(self):
        """Set up performance test data"""
        self.performance_targets = {
            "small_document_processing": 10.0,  # seconds
            "medium_document_processing": 30.0,  # seconds
            "large_document_processing": 60.0,  # seconds
            "concurrent_processing": 45.0,  # seconds for 5 documents
        }
        
        self.test_documents = {
            "small": "A" * 1000 + " sustainability reporting content with ESRS E1 requirements",
            "medium": "B" * 10000 + " detailed sustainability reporting with multiple ESRS standards",
            "large": "C" * 50000 + " comprehensive sustainability report with full ESRS compliance data"
        }
    
    @pytest.mark.asyncio
    async def test_small_document_processing_performance(self, client: TestClient, test_db: Session):
        """Test processing performance for small documents (< 5KB)"""
        
        start_time = time.time()
        
        # Upload small document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(self.test_documents["small"])
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("small_perf_test.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
                doc_id = response.json()["id"]
            
            os.unlink(f.name)
        
        # Wait for processing completion
        max_retries = 100
        for _ in range(max_retries):
            response = client.get(f"/api/documents/{doc_id}")
            if response.json()["processing_status"] == "completed":
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Document processing did not complete in time")
        
        processing_time = time.time() - start_time
        target_time = self.performance_targets["small_document_processing"]
        
        assert processing_time <= target_time, \
            f"Small document processing too slow: {processing_time:.2f}s > {target_time}s"
        
        print(f"Small document processing time: {processing_time:.2f}s (target: {target_time}s)")
    
    @pytest.mark.asyncio
    async def test_medium_document_processing_performance(self, client: TestClient, test_db: Session):
        """Test processing performance for medium documents (5-50KB)"""
        
        start_time = time.time()
        
        # Upload medium document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(self.test_documents["medium"])
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("medium_perf_test.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
                doc_id = response.json()["id"]
            
            os.unlink(f.name)
        
        # Wait for processing completion
        max_retries = 300
        for _ in range(max_retries):
            response = client.get(f"/api/documents/{doc_id}")
            if response.json()["processing_status"] == "completed":
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail("Document processing did not complete in time")
        
        processing_time = time.time() - start_time
        target_time = self.performance_targets["medium_document_processing"]
        
        assert processing_time <= target_time, \
            f"Medium document processing too slow: {processing_time:.2f}s > {target_time}s"
        
        print(f"Medium document processing time: {processing_time:.2f}s (target: {target_time}s)")
    
    @pytest.mark.asyncio
    async def test_concurrent_document_processing_performance(self, client: TestClient, test_db: Session):
        """Test performance under concurrent document processing load"""
        
        start_time = time.time()
        
        # Upload 5 documents concurrently
        doc_ids = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Document {i}: " + self.test_documents["small"])
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (f"concurrent_perf_{i}.txt", upload_file, "text/plain")},
                        data={"schema_type": "EU_ESRS_CSRD"}
                    )
                    assert response.status_code == 200
                    doc_ids.append(response.json()["id"])
                
                os.unlink(f.name)
        
        # Wait for all documents to complete processing
        completed_docs = set()
        max_retries = 450
        for _ in range(max_retries):
            for doc_id in doc_ids:
                if doc_id not in completed_docs:
                    response = client.get(f"/api/documents/{doc_id}")
                    if response.json()["processing_status"] == "completed":
                        completed_docs.add(doc_id)
            
            if len(completed_docs) == len(doc_ids):
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail(f"Concurrent processing did not complete: {len(completed_docs)}/{len(doc_ids)}")
        
        processing_time = time.time() - start_time
        target_time = self.performance_targets["concurrent_processing"]
        
        assert processing_time <= target_time, \
            f"Concurrent processing too slow: {processing_time:.2f}s > {target_time}s"
        
        print(f"Concurrent processing time: {processing_time:.2f}s (target: {target_time}s)")


class TestQueryResponsePerformance:
    """Test query and search response performance benchmarks"""
    
    def setup_method(self):
        """Set up query performance test data"""
        self.performance_targets = {
            "search_query_response": 2.0,  # seconds
            "rag_query_response": 5.0,  # seconds
            "batch_search_queries": 10.0,  # seconds for 10 queries
        }
        
        self.test_queries = [
            "ESRS E1 greenhouse gas emissions requirements",
            "UK SRD environmental disclosure standards",
            "Carbon footprint reporting methodology",
            "Scope 3 emissions calculation guidelines",
            "Sustainability reporting compliance framework"
        ]
    
    @pytest.mark.asyncio
    async def test_search_query_performance(self, client: TestClient, test_db: Session):
        """Test search query response time performance"""
        
        # First ensure we have some documents to search
        await self._setup_test_documents(client)
        
        response_times = []
        
        for query in self.test_queries[:3]:  # Test first 3 queries
            start_time = time.time()
            
            response = client.post(
                "/api/search",
                json={"query": query, "top_k": 10}
            )
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
            assert response_time <= self.performance_targets["search_query_response"], \
                f"Search query too slow: {response_time:.2f}s > {self.performance_targets['search_query_response']}s"
        
        avg_response_time = statistics.mean(response_times)
        print(f"Average search response time: {avg_response_time:.2f}s (target: {self.performance_targets['search_query_response']}s)")
    
    @pytest.mark.asyncio
    async def test_rag_query_performance(self, client: TestClient, test_db: Session):
        """Test RAG query response time performance"""
        
        # Ensure we have documents for RAG context
        await self._setup_test_documents(client)
        
        response_times = []
        
        for query in self.test_queries[:2]:  # Test first 2 queries for RAG
            start_time = time.time()
            
            response = client.post(
                "/api/rag/query",
                json={
                    "question": f"What are the requirements for {query}?",
                    "model": "gpt-4"
                }
            )
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
            assert response_time <= self.performance_targets["rag_query_response"], \
                f"RAG query too slow: {response_time:.2f}s > {self.performance_targets['rag_query_response']}s"
        
        avg_response_time = statistics.mean(response_times)
        print(f"Average RAG response time: {avg_response_time:.2f}s (target: {self.performance_targets['rag_query_response']}s)")
    
    @pytest.mark.asyncio
    async def test_batch_query_performance(self, client: TestClient, test_db: Session):
        """Test performance under batch query load"""
        
        await self._setup_test_documents(client)
        
        start_time = time.time()
        
        # Execute multiple search queries in sequence
        for query in self.test_queries:
            response = client.post(
                "/api/search",
                json={"query": query, "top_k": 5}
            )
            assert response.status_code == 200
        
        batch_time = time.time() - start_time
        target_time = self.performance_targets["batch_search_queries"]
        
        assert batch_time <= target_time, \
            f"Batch queries too slow: {batch_time:.2f}s > {target_time}s"
        
        print(f"Batch query time: {batch_time:.2f}s (target: {target_time}s)")
    
    async def _setup_test_documents(self, client: TestClient):
        """Helper method to set up test documents for query performance tests"""
        
        test_content = """
        ESRS E1 Climate Change Standard requires comprehensive greenhouse gas emissions disclosure.
        Companies must report scope 1, scope 2, and scope 3 emissions following GHG Protocol.
        UK SRD environmental standards mandate carbon footprint reporting and reduction targets.
        Sustainability reporting frameworks ensure compliance with regulatory requirements.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("query_perf_test.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
            
            os.unlink(f.name)
        
        # Wait for processing
        await asyncio.sleep(3)


class TestSystemResourcePerformance:
    """Test system resource usage and performance under load"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, client: TestClient, test_db: Session):
        """Test memory usage remains stable under processing load"""
        
        # This test would ideally use memory profiling tools
        # For now, we'll test that the system continues to respond under load
        
        # Upload multiple documents to create memory pressure
        doc_ids = []
        for i in range(10):
            large_content = f"Document {i}: " + "X" * 5000 + " sustainability content"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(large_content)
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (f"memory_test_{i}.txt", upload_file, "text/plain")},
                        data={"schema_type": "EU_ESRS_CSRD"}
                    )
                    assert response.status_code == 200
                    doc_ids.append(response.json()["id"])
                
                os.unlink(f.name)
        
        # Perform multiple operations to test system stability
        for _ in range(5):
            # Test search still works
            search_response = client.post(
                "/api/search",
                json={"query": "sustainability", "top_k": 5}
            )
            assert search_response.status_code == 200
            
            # Test document listing still works
            list_response = client.get("/api/documents")
            assert list_response.status_code == 200
            
            await asyncio.sleep(0.5)
        
        print("System remained stable under memory load test")
    
    @pytest.mark.asyncio
    async def test_api_response_consistency(self, client: TestClient, test_db: Session):
        """Test API response times remain consistent over multiple calls"""
        
        # Setup test document
        test_content = "ESRS sustainability reporting requirements for performance testing"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("consistency_test.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
            
            os.unlink(f.name)
        
        await asyncio.sleep(2)  # Wait for processing
        
        # Test multiple identical API calls
        response_times = []
        for _ in range(10):
            start_time = time.time()
            
            response = client.post(
                "/api/search",
                json={"query": "ESRS requirements", "top_k": 5}
            )
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Check response time consistency (standard deviation should be low)
        avg_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        # Standard deviation should be less than 50% of average time
        assert std_dev <= avg_time * 0.5, \
            f"Response times too inconsistent: std_dev={std_dev:.3f}, avg={avg_time:.3f}"
        
        print(f"API response consistency: avg={avg_time:.3f}s, std_dev={std_dev:.3f}s")
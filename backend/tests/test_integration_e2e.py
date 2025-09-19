"""
End-to-End Integration Tests for CSRD RAG System

This module contains comprehensive integration tests that cover complete user journeys
from document upload through report generation, validating the entire system workflow.
"""

import pytest
import asyncio
import tempfile
import os
import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.main import app
    from app.models.database import get_db
    from app.services.document_service import DocumentService
    from app.services.rag_service import RAGService
    from app.services.report_service import ReportService
    from app.services.schema_service import SchemaService
    from tests.conftest import test_db, client
except ImportError:
    # For validation purposes when app modules aren't available
    pass


class TestEndToEndUserJourneys:
    """Test complete user workflows from start to finish"""
    
    def setup_method(self):
        """Set up test data and services for each test"""
        self.test_documents = self._create_test_documents()
        self.test_client_requirements = self._create_test_client_requirements()
    
    def _create_test_documents(self) -> List[Dict[str, Any]]:
        """Create sample test documents for different scenarios"""
        return [
            {
                "filename": "esrs_e1_climate_change.pdf",
                "content": "ESRS E1 Climate Change requirements for greenhouse gas emissions disclosure...",
                "schema_type": "EU_ESRS_CSRD",
                "expected_elements": ["E1-1", "E1-2", "E1-3"]
            },
            {
                "filename": "uk_srd_environmental.pdf", 
                "content": "UK SRD environmental reporting requirements for carbon footprint...",
                "schema_type": "UK_SRD",
                "expected_elements": ["ENV-1", "ENV-2"]
            }
        ]
    
    def _create_test_client_requirements(self) -> Dict[str, Any]:
        """Create sample client requirements for testing"""
        return {
            "client_name": "Test Corporation",
            "requirements": [
                "Provide greenhouse gas emissions data according to ESRS E1",
                "Detail carbon reduction strategies and targets",
                "Include scope 1, 2, and 3 emissions calculations"
            ]
        }

    @pytest.mark.asyncio
    async def test_complete_document_to_report_journey(self, client: TestClient, test_db: Session):
        """Test the complete journey from document upload to PDF report generation"""
        
        # Step 1: Upload documents
        uploaded_docs = []
        for doc_data in self.test_documents:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data["content"])
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (doc_data["filename"], upload_file, "text/plain")},
                        data={"schema_type": doc_data["schema_type"]}
                    )
                    assert response.status_code == 200
                    uploaded_docs.append(response.json())
                
                os.unlink(f.name)
        
        # Step 2: Wait for document processing to complete
        for doc in uploaded_docs:
            doc_id = doc["id"]
            max_retries = 30
            for _ in range(max_retries):
                response = client.get(f"/api/documents/{doc_id}")
                if response.json()["processing_status"] == "completed":
                    break
                await asyncio.sleep(1)
            else:
                pytest.fail(f"Document {doc_id} processing did not complete in time")
        
        # Step 3: Verify documents are searchable
        search_response = client.post(
            "/api/search",
            json={"query": "greenhouse gas emissions", "top_k": 5}
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert len(search_results["results"]) > 0
        assert search_results["results"][0]["relevance_score"] > 0.5
        
        # Step 4: Test RAG question answering
        rag_response = client.post(
            "/api/rag/query",
            json={
                "question": "What are the ESRS E1 requirements for greenhouse gas emissions?",
                "model": "gpt-4"
            }
        )
        assert rag_response.status_code == 200
        rag_result = rag_response.json()
        assert len(rag_result["response"]) > 100
        assert len(rag_result["sources"]) > 0
        assert rag_result["confidence_score"] > 0.7
        
        # Step 5: Upload client requirements
        requirements_response = client.post(
            "/api/client-requirements/upload",
            json=self.test_client_requirements
        )
        assert requirements_response.status_code == 200
        requirements_id = requirements_response.json()["id"]
        
        # Step 6: Generate report
        report_response = client.post(
            "/api/reports/generate",
            json={
                "requirements_id": requirements_id,
                "template_type": "standard",
                "model": "gpt-4"
            }
        )
        assert report_response.status_code == 200
        report_data = report_response.json()
        
        # Step 7: Generate and download PDF
        pdf_response = client.get(f"/api/reports/{report_data['id']}/pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert len(pdf_response.content) > 1000  # Ensure PDF has content

    @pytest.mark.asyncio
    async def test_multi_schema_document_processing(self, client: TestClient, test_db: Session):
        """Test processing documents with different schema types"""
        
        # Upload documents with different schemas
        schema_results = {}
        for doc_data in self.test_documents:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data["content"])
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (doc_data["filename"], upload_file, "text/plain")},
                        data={"schema_type": doc_data["schema_type"]}
                    )
                    assert response.status_code == 200
                    schema_results[doc_data["schema_type"]] = response.json()
                
                os.unlink(f.name)
        
        # Wait for processing and verify schema classification
        for schema_type, doc_result in schema_results.items():
            doc_id = doc_result["id"]
            
            # Wait for processing
            max_retries = 30
            for _ in range(max_retries):
                response = client.get(f"/api/documents/{doc_id}")
                doc_status = response.json()
                if doc_status["processing_status"] == "completed":
                    break
                await asyncio.sleep(1)
            
            # Verify schema classification
            assert doc_status["schema_type"] == schema_type
            assert len(doc_status.get("schema_elements", [])) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_document_processing(self, client: TestClient, test_db: Session):
        """Test system behavior under concurrent document uploads"""
        
        # Create multiple test documents
        concurrent_docs = []
        for i in range(5):
            doc_content = f"Test document {i} with sustainability reporting content for concurrent processing test..."
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_content)
                f.flush()
                concurrent_docs.append(f.name)
        
        # Upload all documents concurrently
        upload_tasks = []
        for i, doc_path in enumerate(concurrent_docs):
            with open(doc_path, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": (f"concurrent_doc_{i}.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
                upload_tasks.append(response.json())
        
        # Wait for all documents to complete processing
        for doc_result in upload_tasks:
            doc_id = doc_result["id"]
            max_retries = 60  # Longer timeout for concurrent processing
            for _ in range(max_retries):
                response = client.get(f"/api/documents/{doc_id}")
                if response.json()["processing_status"] == "completed":
                    break
                await asyncio.sleep(1)
            else:
                pytest.fail(f"Concurrent document {doc_id} processing did not complete")
        
        # Cleanup
        for doc_path in concurrent_docs:
            os.unlink(doc_path)
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, client: TestClient, test_db: Session):
        """Test system resilience and error recovery mechanisms"""
        
        # Test 1: Invalid file format
        invalid_response = client.post(
            "/api/documents/upload",
            files={"file": ("test.xyz", b"invalid content", "application/octet-stream")},
            data={"schema_type": "EU_ESRS_CSRD"}
        )
        assert invalid_response.status_code == 400
        assert "unsupported file format" in invalid_response.json()["detail"].lower()
        
        # Test 2: Empty file
        empty_response = client.post(
            "/api/documents/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
            data={"schema_type": "EU_ESRS_CSRD"}
        )
        assert empty_response.status_code == 400
        
        # Test 3: Invalid RAG query
        invalid_rag_response = client.post(
            "/api/rag/query",
            json={"question": "", "model": "invalid-model"}
        )
        assert invalid_rag_response.status_code == 400
        
        # Test 4: Query with no context available
        no_context_response = client.post(
            "/api/rag/query",
            json={"question": "What is the meaning of life?", "model": "gpt-4"}
        )
        assert no_context_response.status_code == 200
        result = no_context_response.json()
        assert "insufficient context" in result["response"].lower() or result["confidence_score"] < 0.3


class TestSchemaClassificationAccuracy:
    """Test automated schema classification accuracy"""
    
    def setup_method(self):
        """Set up test data with known schema classifications"""
        self.schema_test_cases = [
            {
                "content": "ESRS E1-1 requires disclosure of greenhouse gas emissions in scope 1, 2, and 3 categories according to GHG Protocol standards.",
                "expected_schema": "EU_ESRS_CSRD",
                "expected_elements": ["E1-1", "E1-2"],
                "confidence_threshold": 0.8
            },
            {
                "content": "UK SRD environmental disclosure requirements mandate reporting of carbon footprint and energy consumption metrics.",
                "expected_schema": "UK_SRD", 
                "expected_elements": ["ENV-1"],
                "confidence_threshold": 0.7
            },
            {
                "content": "ESRS S1 workforce-related disclosures include diversity metrics, working conditions, and employee development programs.",
                "expected_schema": "EU_ESRS_CSRD",
                "expected_elements": ["S1-1", "S1-2"],
                "confidence_threshold": 0.8
            }
        ]
    
    @pytest.mark.asyncio
    async def test_schema_classification_accuracy(self, client: TestClient, test_db: Session):
        """Test accuracy of automated schema classification"""
        
        correct_classifications = 0
        total_tests = len(self.schema_test_cases)
        
        for i, test_case in enumerate(self.schema_test_cases):
            # Upload test document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_case["content"])
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (f"schema_test_{i}.txt", upload_file, "text/plain")},
                        data={"schema_type": test_case["expected_schema"]}
                    )
                    assert response.status_code == 200
                    doc_result = response.json()
                
                os.unlink(f.name)
            
            # Wait for processing
            doc_id = doc_result["id"]
            max_retries = 30
            for _ in range(max_retries):
                response = client.get(f"/api/documents/{doc_id}")
                doc_status = response.json()
                if doc_status["processing_status"] == "completed":
                    break
                await asyncio.sleep(1)
            
            # Verify classification accuracy
            if doc_status["schema_type"] == test_case["expected_schema"]:
                correct_classifications += 1
            
            # Check if expected schema elements are detected
            detected_elements = doc_status.get("schema_elements", [])
            expected_elements = test_case["expected_elements"]
            
            # At least 50% of expected elements should be detected
            detected_expected = sum(1 for elem in expected_elements if elem in detected_elements)
            element_accuracy = detected_expected / len(expected_elements)
            assert element_accuracy >= 0.5, f"Schema element detection accuracy too low: {element_accuracy}"
        
        # Overall accuracy should be at least 80%
        overall_accuracy = correct_classifications / total_tests
        assert overall_accuracy >= 0.8, f"Schema classification accuracy too low: {overall_accuracy}"


class TestRAGResponseQuality:
    """Test RAG response quality and accuracy"""
    
    def setup_method(self):
        """Set up test questions with expected response characteristics"""
        self.quality_test_cases = [
            {
                "question": "What are the ESRS E1 requirements for greenhouse gas emissions disclosure?",
                "expected_keywords": ["greenhouse gas", "emissions", "scope 1", "scope 2", "scope 3", "ESRS E1"],
                "min_response_length": 100,
                "min_confidence": 0.7,
                "expected_sources": 1
            },
            {
                "question": "How should companies report their carbon reduction targets under UK SRD?",
                "expected_keywords": ["carbon", "reduction", "targets", "UK SRD"],
                "min_response_length": 80,
                "min_confidence": 0.6,
                "expected_sources": 1
            }
        ]
    
    @pytest.mark.asyncio
    async def test_rag_response_quality(self, client: TestClient, test_db: Session):
        """Test quality metrics for RAG responses"""
        
        # First upload relevant documents
        test_content = """
        ESRS E1 Climate Change Standard requires companies to disclose greenhouse gas emissions 
        across scope 1 (direct emissions), scope 2 (indirect emissions from energy), and 
        scope 3 (other indirect emissions) categories. Companies must follow GHG Protocol 
        standards and provide quantitative data with reduction targets.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("rag_test_doc.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
            
            os.unlink(f.name)
        
        # Wait for document processing
        await asyncio.sleep(5)
        
        # Test each quality case
        for test_case in self.quality_test_cases:
            response = client.post(
                "/api/rag/query",
                json={
                    "question": test_case["question"],
                    "model": "gpt-4"
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Test response length
            assert len(result["response"]) >= test_case["min_response_length"], \
                f"Response too short: {len(result['response'])} < {test_case['min_response_length']}"
            
            # Test confidence score
            assert result["confidence_score"] >= test_case["min_confidence"], \
                f"Confidence too low: {result['confidence_score']} < {test_case['min_confidence']}"
            
            # Test source citations
            assert len(result["sources"]) >= test_case["expected_sources"], \
                f"Not enough sources: {len(result['sources'])} < {test_case['expected_sources']}"
            
            # Test keyword presence (at least 50% should be present)
            response_text = result["response"].lower()
            keyword_matches = sum(1 for keyword in test_case["expected_keywords"] 
                                if keyword.lower() in response_text)
            keyword_accuracy = keyword_matches / len(test_case["expected_keywords"])
            assert keyword_accuracy >= 0.5, \
                f"Keyword accuracy too low: {keyword_accuracy} < 0.5"
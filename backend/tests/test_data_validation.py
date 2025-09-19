"""
Data Validation Tests for Schema Compliance and Document Integrity

This module contains tests that validate data integrity, schema compliance,
and document processing accuracy throughout the CSRD RAG system.
"""

import pytest
import json
import tempfile
import os
import asyncio
from typing import List, Dict, Any, Optional
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.services.schema_service import SchemaService
    from app.services.document_service import DocumentService
    from app.models.schemas import Document, TextChunk, SchemaElement
    from tests.conftest import test_db, client
except ImportError:
    # For validation purposes when app modules aren't available
    pass


class TestSchemaCompliance:
    """Test compliance with EU ESRS/CSRD and UK SRD schema definitions"""
    
    def setup_method(self):
        """Set up schema validation test data"""
        self.eu_esrs_test_cases = [
            {
                "content": "ESRS E1-1 Transition plan for climate change mitigation requires disclosure of GHG emission reduction targets",
                "expected_elements": ["E1-1"],
                "schema_type": "EU_ESRS_CSRD"
            },
            {
                "content": "ESRS E1-2 Policies related to climate change mitigation and adaptation must be disclosed with implementation details",
                "expected_elements": ["E1-2"],
                "schema_type": "EU_ESRS_CSRD"
            },
            {
                "content": "ESRS S1-1 Policies related to own workforce including diversity, inclusion, and working conditions",
                "expected_elements": ["S1-1"],
                "schema_type": "EU_ESRS_CSRD"
            },
            {
                "content": "ESRS G1-1 Business model and strategy disclosure requirements for governance reporting",
                "expected_elements": ["G1-1"],
                "schema_type": "EU_ESRS_CSRD"
            }
        ]
        
        self.uk_srd_test_cases = [
            {
                "content": "UK SRD environmental disclosure requirements for carbon emissions and energy consumption reporting",
                "expected_elements": ["ENV-1"],
                "schema_type": "UK_SRD"
            },
            {
                "content": "UK SRD social impact reporting including employee welfare and community engagement metrics",
                "expected_elements": ["SOC-1"],
                "schema_type": "UK_SRD"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_eu_esrs_schema_compliance(self, client: TestClient, test_db: Session):
        """Test compliance with EU ESRS/CSRD schema elements"""
        
        for test_case in self.eu_esrs_test_cases:
            # Upload document with specific ESRS content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_case["content"])
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (f"esrs_test.txt", upload_file, "text/plain")},
                        data={"schema_type": test_case["schema_type"]}
                    )
                    assert response.status_code == 200
                    doc_id = response.json()["id"]
                
                os.unlink(f.name)
            
            # Wait for processing and validate schema compliance
            max_retries = 30
            for _ in range(max_retries):
                response = client.get(f"/api/documents/{doc_id}")
                doc_data = response.json()
                if doc_data["processing_status"] == "completed":
                    break
                await asyncio.sleep(1)
            
            # Validate schema elements are correctly identified
            detected_elements = doc_data.get("schema_elements", [])
            expected_elements = test_case["expected_elements"]
            
            # Check if at least one expected element is detected
            found_expected = any(elem in detected_elements for elem in expected_elements)
            assert found_expected, f"Expected elements {expected_elements} not found in {detected_elements}"
            
            # Validate schema type is correctly assigned
            assert doc_data["schema_type"] == test_case["schema_type"]
    
    @pytest.mark.asyncio
    async def test_uk_srd_schema_compliance(self, client: TestClient, test_db: Session):
        """Test compliance with UK SRD schema elements"""
        
        for test_case in self.uk_srd_test_cases:
            # Upload document with UK SRD content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_case["content"])
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (f"uk_srd_test.txt", upload_file, "text/plain")},
                        data={"schema_type": test_case["schema_type"]}
                    )
                    assert response.status_code == 200
                    doc_id = response.json()["id"]
                
                os.unlink(f.name)
            
            # Wait for processing and validate schema compliance
            max_retries = 30
            for _ in range(max_retries):
                response = client.get(f"/api/documents/{doc_id}")
                doc_data = response.json()
                if doc_data["processing_status"] == "completed":
                    break
                await asyncio.sleep(1)
            
            # Validate schema compliance
            assert doc_data["schema_type"] == test_case["schema_type"]
            detected_elements = doc_data.get("schema_elements", [])
            assert len(detected_elements) > 0, "No schema elements detected"
    
    def test_schema_definition_integrity(self, client: TestClient, test_db: Session):
        """Test integrity of loaded schema definitions"""
        
        # Test EU ESRS schema loading
        eu_response = client.get("/api/schemas/EU_ESRS_CSRD")
        assert eu_response.status_code == 200
        eu_schema = eu_response.json()
        
        # Validate required ESRS elements are present
        required_esrs_elements = ["E1", "E2", "E3", "E4", "E5", "S1", "S2", "S3", "S4", "G1"]
        schema_elements = [elem["element_code"] for elem in eu_schema.get("elements", [])]
        
        for required_elem in required_esrs_elements:
            found = any(required_elem in elem for elem in schema_elements)
            assert found, f"Required ESRS element {required_elem} not found in schema"
        
        # Test UK SRD schema loading
        uk_response = client.get("/api/schemas/UK_SRD")
        assert uk_response.status_code == 200
        uk_schema = uk_response.json()
        
        # Validate UK SRD has required categories
        uk_elements = [elem["element_code"] for elem in uk_schema.get("elements", [])]
        assert len(uk_elements) > 0, "UK SRD schema has no elements"
    
    def test_schema_element_relationships(self, client: TestClient, test_db: Session):
        """Test schema element parent-child relationships are valid"""
        
        # Get EU ESRS schema
        response = client.get("/api/schemas/EU_ESRS_CSRD")
        assert response.status_code == 200
        schema = response.json()
        
        elements = schema.get("elements", [])
        element_ids = {elem["id"] for elem in elements}
        
        # Validate parent-child relationships
        for element in elements:
            parent_id = element.get("parent_element_id")
            if parent_id:
                assert parent_id in element_ids, \
                    f"Element {element['id']} references non-existent parent {parent_id}"


class TestDocumentIntegrity:
    """Test document processing integrity and data consistency"""
    
    def setup_method(self):
        """Set up document integrity test data"""
        self.integrity_test_documents = [
            {
                "filename": "test_integrity_1.txt",
                "content": "This is a test document for integrity validation with ESRS E1 content about climate change.",
                "expected_chunks": 1,
                "min_content_length": 50
            },
            {
                "filename": "test_integrity_2.txt", 
                "content": "A" * 2000 + " Extended document content for chunking validation with multiple ESRS standards including E1, E2, and S1 requirements.",
                "expected_chunks": 2,
                "min_content_length": 2000
            }
        ]
    
    @pytest.mark.asyncio
    async def test_document_metadata_integrity(self, client: TestClient, test_db: Session):
        """Test document metadata is correctly stored and retrieved"""
        
        for doc_data in self.integrity_test_documents:
            # Upload document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data["content"])
                f.flush()
                file_size = os.path.getsize(f.name)
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (doc_data["filename"], upload_file, "text/plain")},
                        data={"schema_type": "EU_ESRS_CSRD"}
                    )
                    assert response.status_code == 200
                    doc_result = response.json()
                
                os.unlink(f.name)
            
            # Validate metadata integrity
            doc_id = doc_result["id"]
            response = client.get(f"/api/documents/{doc_id}")
            assert response.status_code == 200
            
            doc_metadata = response.json()
            assert doc_metadata["filename"] == doc_data["filename"]
            assert doc_metadata["file_size"] == file_size
            assert doc_metadata["schema_type"] == "EU_ESRS_CSRD"
            assert "upload_date" in doc_metadata
            assert "id" in doc_metadata
    
    @pytest.mark.asyncio
    async def test_text_extraction_integrity(self, client: TestClient, test_db: Session):
        """Test text extraction preserves content integrity"""
        
        original_content = "ESRS E1 Climate Change Standard requires comprehensive greenhouse gas emissions disclosure including scope 1, 2, and 3 emissions."
        
        # Upload document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(original_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("extraction_test.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
                doc_id = response.json()["id"]
            
            os.unlink(f.name)
        
        # Wait for processing
        max_retries = 30
        for _ in range(max_retries):
            response = client.get(f"/api/documents/{doc_id}")
            if response.json()["processing_status"] == "completed":
                break
            await asyncio.sleep(1)
        
        # Get document chunks to verify content integrity
        chunks_response = client.get(f"/api/documents/{doc_id}/chunks")
        assert chunks_response.status_code == 200
        chunks = chunks_response.json()
        
        # Reconstruct content from chunks
        reconstructed_content = " ".join([chunk["content"] for chunk in chunks])
        
        # Verify key terms are preserved
        key_terms = ["ESRS E1", "Climate Change", "greenhouse gas", "emissions", "scope 1", "scope 2", "scope 3"]
        for term in key_terms:
            assert term in reconstructed_content, f"Key term '{term}' lost during processing"
    
    @pytest.mark.asyncio
    async def test_chunking_integrity(self, client: TestClient, test_db: Session):
        """Test document chunking maintains content integrity"""
        
        for doc_data in self.integrity_test_documents:
            # Upload document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data["content"])
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (doc_data["filename"], upload_file, "text/plain")},
                        data={"schema_type": "EU_ESRS_CSRD"}
                    )
                    assert response.status_code == 200
                    doc_id = response.json()["id"]
                
                os.unlink(f.name)
            
            # Wait for processing
            max_retries = 30
            for _ in range(max_retries):
                response = client.get(f"/api/documents/{doc_id}")
                if response.json()["processing_status"] == "completed":
                    break
                await asyncio.sleep(1)
            
            # Validate chunking integrity
            chunks_response = client.get(f"/api/documents/{doc_id}/chunks")
            assert chunks_response.status_code == 200
            chunks = chunks_response.json()
            
            # Validate expected number of chunks
            assert len(chunks) >= doc_data["expected_chunks"], \
                f"Expected at least {doc_data['expected_chunks']} chunks, got {len(chunks)}"
            
            # Validate chunk content integrity
            total_chunk_length = sum(len(chunk["content"]) for chunk in chunks)
            assert total_chunk_length >= doc_data["min_content_length"], \
                f"Total chunk content too short: {total_chunk_length} < {doc_data['min_content_length']}"
            
            # Validate chunk ordering
            for i, chunk in enumerate(chunks):
                assert chunk["chunk_index"] == i, f"Chunk index mismatch: expected {i}, got {chunk['chunk_index']}"
    
    @pytest.mark.asyncio
    async def test_embedding_generation_integrity(self, client: TestClient, test_db: Session):
        """Test vector embedding generation integrity"""
        
        test_content = "ESRS E1 requires disclosure of greenhouse gas emissions across all scopes with quantitative targets."
        
        # Upload document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("embedding_test.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
                doc_id = response.json()["id"]
            
            os.unlink(f.name)
        
        # Wait for processing
        max_retries = 30
        for _ in range(max_retries):
            response = client.get(f"/api/documents/{doc_id}")
            if response.json()["processing_status"] == "completed":
                break
            await asyncio.sleep(1)
        
        # Validate embeddings are generated
        chunks_response = client.get(f"/api/documents/{doc_id}/chunks")
        assert chunks_response.status_code == 200
        chunks = chunks_response.json()
        
        for chunk in chunks:
            # Validate embedding exists and has reasonable dimensions
            assert "embedding_vector" in chunk or "has_embedding" in chunk, \
                "Chunk missing embedding information"
            
            # If embedding vector is included, validate dimensions
            if "embedding_vector" in chunk and chunk["embedding_vector"]:
                embedding = chunk["embedding_vector"]
                assert isinstance(embedding, list), "Embedding should be a list"
                assert len(embedding) > 0, "Embedding vector should not be empty"
                assert all(isinstance(x, (int, float)) for x in embedding), \
                    "Embedding vector should contain only numbers"


class TestDataConsistency:
    """Test data consistency across system operations"""
    
    @pytest.mark.asyncio
    async def test_search_result_consistency(self, client: TestClient, test_db: Session):
        """Test search results are consistent and reference valid documents"""
        
        # Upload test document
        test_content = "ESRS E1 Climate Change Standard comprehensive requirements for sustainability reporting."
        
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
                doc_id = response.json()["id"]
            
            os.unlink(f.name)
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Perform search
        search_response = client.post(
            "/api/search",
            json={"query": "ESRS E1 Climate Change", "top_k": 10}
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        
        # Validate search result consistency
        for result in search_results["results"]:
            # Validate result structure
            assert "document_id" in result
            assert "chunk_id" in result
            assert "content" in result
            assert "relevance_score" in result
            
            # Validate referenced document exists
            doc_response = client.get(f"/api/documents/{result['document_id']}")
            assert doc_response.status_code == 200
            
            # Validate relevance score is reasonable
            assert 0 <= result["relevance_score"] <= 1, \
                f"Invalid relevance score: {result['relevance_score']}"
    
    @pytest.mark.asyncio
    async def test_rag_source_consistency(self, client: TestClient, test_db: Session):
        """Test RAG responses reference valid and consistent sources"""
        
        # Upload test document
        test_content = "ESRS E1-1 Transition plan for climate change mitigation requires detailed disclosure of greenhouse gas emission reduction targets and implementation strategies."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("rag_consistency_test.txt", upload_file, "text/plain")},
                    data={"schema_type": "EU_ESRS_CSRD"}
                )
                assert response.status_code == 200
            
            os.unlink(f.name)
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Perform RAG query
        rag_response = client.post(
            "/api/rag/query",
            json={
                "question": "What are the ESRS E1-1 requirements for transition plans?",
                "model": "gpt-4"
            }
        )
        assert rag_response.status_code == 200
        rag_result = rag_response.json()
        
        # Validate source consistency
        sources = rag_result.get("sources", [])
        for source in sources:
            # Validate source structure
            assert "document_id" in source
            assert "chunk_id" in source
            assert "content" in source
            
            # Validate referenced document exists
            doc_response = client.get(f"/api/documents/{source['document_id']}")
            assert doc_response.status_code == 200
            
            # Validate source content is not empty
            assert len(source["content"].strip()) > 0, "Source content should not be empty"
    
    def test_database_referential_integrity(self, client: TestClient, test_db: Session):
        """Test database referential integrity constraints"""
        
        # Get all documents
        docs_response = client.get("/api/documents")
        assert docs_response.status_code == 200
        documents = docs_response.json()
        
        for doc in documents:
            doc_id = doc["id"]
            
            # Validate document chunks reference valid document
            chunks_response = client.get(f"/api/documents/{doc_id}/chunks")
            if chunks_response.status_code == 200:
                chunks = chunks_response.json()
                for chunk in chunks:
                    assert chunk["document_id"] == doc_id, \
                        f"Chunk references wrong document: {chunk['document_id']} != {doc_id}"
        
        print(f"Validated referential integrity for {len(documents)} documents")
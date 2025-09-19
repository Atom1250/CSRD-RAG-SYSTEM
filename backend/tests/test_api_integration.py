"""
Comprehensive API integration tests for all endpoints
"""
import pytest
import json
import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.models.schemas import SchemaType, DocumentType, ProcessingStatus


class TestSystemEndpoints:
    """Test system-level endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
        assert "api_prefix" in data
        assert data["api_prefix"] == "/api"
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "app_name" in data
        assert "version" in data
        assert "services" in data
        assert isinstance(data["services"], dict)
    
    def test_api_info_endpoint(self, client):
        """Test API info endpoint"""
        response = client.get("/api")
        assert response.status_code == 200
        
        data = response.json()
        assert "api_name" in data
        assert "endpoints" in data
        assert "documentation" in data
        assert isinstance(data["endpoints"], dict)
    
    def test_api_status_endpoint(self, client):
        """Test API status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_status" in data
        assert "endpoints" in data
        assert isinstance(data["endpoints"], dict)


class TestDocumentEndpoints:
    """Test document management endpoints"""
    
    def test_upload_document_success(self, client, sample_pdf_file):
        """Test successful document upload"""
        files = {"file": ("test.pdf", sample_pdf_file, "application/pdf")}
        data = {"schema_type": SchemaType.EU_ESRS_CSRD.value}
        
        response = client.post("/api/documents/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert "document_id" in result
        assert result["filename"] == "test.pdf"
        assert result["document_type"] == DocumentType.PDF.value
    
    def test_upload_document_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        files = {"file": ("test.exe", b"invalid content", "application/octet-stream")}
        
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 400
    
    def test_upload_document_empty_file(self, client):
        """Test upload with empty file"""
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 400
    
    def test_get_documents_list(self, client, sample_document):
        """Test getting documents list"""
        response = client.get("/api/documents/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_documents_with_filters(self, client, sample_document):
        """Test getting documents with filters"""
        params = {
            "document_type": DocumentType.PDF.value,
            "schema_type": SchemaType.EU_ESRS_CSRD.value,
            "processing_status": ProcessingStatus.COMPLETED.value
        }
        
        response = client.get("/api/documents/", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_document_by_id(self, client, sample_document):
        """Test getting specific document by ID"""
        response = client.get(f"/api/documents/{sample_document.document_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["document_id"] == sample_document.document_id
    
    def test_get_document_not_found(self, client):
        """Test getting non-existent document"""
        response = client.get("/api/documents/nonexistent-id")
        assert response.status_code == 404
    
    def test_delete_document(self, client, sample_document):
        """Test deleting document"""
        response = client.delete(f"/api/documents/{sample_document.document_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["document_id"] == sample_document.document_id
    
    def test_get_document_metadata(self, client, sample_document):
        """Test getting document metadata"""
        response = client.get(f"/api/documents/{sample_document.document_id}/metadata")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_update_document_metadata(self, client, sample_document):
        """Test updating document metadata"""
        metadata_update = {"custom_field": "test_value", "priority": "high"}
        
        response = client.put(
            f"/api/documents/{sample_document.document_id}/metadata",
            json=metadata_update
        )
        assert response.status_code == 200


class TestSearchEndpoints:
    """Test search functionality endpoints"""
    
    def test_search_documents_post(self, client, sample_processed_document):
        """Test POST search endpoint"""
        search_request = {
            "query": "sustainability reporting requirements",
            "top_k": 5,
            "min_relevance_score": 0.3,
            "enable_reranking": True
        }
        
        response = client.post("/api/search/", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_documents_get(self, client, sample_processed_document):
        """Test GET search endpoint"""
        params = {
            "query": "climate change adaptation",
            "top_k": 10,
            "min_relevance_score": 0.2
        }
        
        response = client.get("/api/search/", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_with_filters(self, client, sample_processed_document):
        """Test search with document filters"""
        search_request = {
            "query": "environmental standards",
            "top_k": 5,
            "document_type": DocumentType.PDF.value,
            "schema_type": SchemaType.EU_ESRS_CSRD.value
        }
        
        response = client.post("/api/search/", json=search_request)
        assert response.status_code == 200
    
    def test_search_with_embedding(self, client, sample_processed_document):
        """Test search with pre-computed embedding"""
        embedding_request = {
            "query_embedding": [0.1] * 384,  # Mock embedding vector
            "top_k": 5,
            "min_relevance_score": 0.3
        }
        
        response = client.post("/api/search/embedding", json=embedding_request)
        assert response.status_code == 200
    
    def test_search_by_schema_elements(self, client, sample_processed_document):
        """Test search by schema elements"""
        schema_request = {
            "schema_elements": ["E1", "E2", "S1"],
            "top_k": 10,
            "schema_type": SchemaType.EU_ESRS_CSRD.value
        }
        
        response = client.post("/api/search/schema", json=schema_request)
        assert response.status_code == 200
    
    def test_find_similar_chunks(self, client, sample_text_chunk):
        """Test finding similar chunks"""
        similar_request = {
            "chunk_id": sample_text_chunk.chunk_id,
            "top_k": 5,
            "exclude_same_document": True
        }
        
        response = client.post("/api/search/similar", json=similar_request)
        assert response.status_code == 200
    
    def test_get_search_suggestions(self, client):
        """Test search suggestions"""
        params = {"partial_query": "climat", "max_suggestions": 5}
        
        response = client.get("/api/search/suggestions", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        assert "query" in data
    
    def test_generate_query_embedding(self, client):
        """Test query embedding generation"""
        params = {"query": "environmental sustainability requirements"}
        
        response = client.post("/api/search/embedding/generate", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_search_performance_metrics(self, client, sample_processed_document):
        """Test search performance metrics"""
        params = {"query": "governance requirements", "top_k": 5}
        
        response = client.get("/api/search/performance", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "total_time_ms" in data
        assert "results_count" in data
    
    def test_search_statistics(self, client):
        """Test search statistics"""
        response = client.get("/api/search/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "embedding_coverage" in data
    
    def test_search_health_check(self, client):
        """Test search health check"""
        response = client.get("/api/search/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "vector_service_available" in data


class TestRAGEndpoints:
    """Test RAG functionality endpoints"""
    
    def test_generate_rag_response(self, client, sample_processed_document):
        """Test RAG response generation"""
        rag_request = {
            "question": "What are the key requirements for climate change reporting?",
            "max_context_chunks": 5,
            "min_relevance_score": 0.3,
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = client.post("/api/rag/query", json=rag_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "question" in data
        assert "response_text" in data
        assert "source_chunks" in data
    
    def test_batch_rag_responses(self, client, sample_processed_document):
        """Test batch RAG response generation"""
        batch_request = {
            "questions": [
                "What are greenhouse gas emission requirements?",
                "How should biodiversity impacts be reported?",
                "What are the governance disclosure requirements?"
            ],
            "max_concurrent": 2
        }
        
        response = client.post("/api/rag/batch-query", json=batch_request)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
    
    def test_get_available_models(self, client):
        """Test getting available AI models"""
        response = client.get("/api/rag/models")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_model_status(self, client):
        """Test getting model status"""
        response = client.get("/api/rag/models/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        assert "default_model" in data
        assert "available_count" in data
    
    def test_validate_response_quality(self, client):
        """Test response quality validation"""
        validation_request = {
            "response_id": "test-response-123",
            "expected_topics": ["climate", "emissions", "reporting"]
        }
        
        response = client.post("/api/rag/validate-quality", json=validation_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response_id" in data
        assert "quality_score" in data
        assert "metrics" in data
    
    def test_rag_health_check(self, client):
        """Test RAG health check"""
        response = client.get("/api/rag/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "available_models" in data
    
    def test_example_sustainability_question(self, client, sample_processed_document):
        """Test example sustainability question"""
        response = client.post("/api/rag/examples/sustainability-question")
        assert response.status_code == 200
        
        data = response.json()
        assert "example_question" in data
        assert "response" in data
    
    def test_example_batch_questions(self, client, sample_processed_document):
        """Test example batch questions"""
        response = client.post("/api/rag/examples/batch-questions")
        assert response.status_code == 200
        
        data = response.json()
        assert "example_questions" in data
        assert "responses" in data


class TestReportEndpoints:
    """Test report generation endpoints"""
    
    def test_get_available_templates(self, client):
        """Test getting available report templates"""
        response = client.get("/api/reports/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_template_details(self, client):
        """Test getting template details"""
        response = client.get("/api/reports/templates/eu_esrs_standard")
        assert response.status_code == 200
        
        data = response.json()
        assert "type" in data
        assert "config" in data
    
    def test_generate_report(self, client, sample_client_requirements):
        """Test report generation"""
        params = {
            "requirements_id": sample_client_requirements.requirements_id,
            "template_type": "eu_esrs_standard",
            "ai_model": "openai_gpt35",
            "report_format": "structured_text"
        }
        
        response = client.post("/api/reports/generate", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "report_content" in data
        assert "metadata" in data
    
    def test_generate_report_async(self, client, sample_client_requirements):
        """Test async report generation"""
        params = {
            "requirements_id": sample_client_requirements.requirements_id,
            "template_type": "eu_esrs_standard"
        }
        
        response = client.post("/api/reports/generate-async", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
    
    def test_get_available_formats(self, client):
        """Test getting available report formats"""
        response = client.get("/api/reports/formats")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        for format_info in data:
            assert "value" in format_info
            assert "name" in format_info
    
    def test_get_available_ai_models(self, client):
        """Test getting available AI models for reports"""
        response = client.get("/api/reports/ai-models")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_preview_report_structure(self, client, sample_client_requirements):
        """Test report structure preview"""
        params = {
            "requirements_id": sample_client_requirements.requirements_id,
            "template_type": "eu_esrs_standard"
        }
        
        response = client.get(f"/api/reports/preview/{sample_client_requirements.requirements_id}", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "client_name" in data
        assert "sections" in data
    
    def test_validate_requirements_for_report(self, client, sample_client_requirements):
        """Test requirements validation for report"""
        params = {"template_type": "eu_esrs_standard"}
        
        response = client.post(
            f"/api/reports/validate-requirements/{sample_client_requirements.requirements_id}",
            params=params
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "validation_status" in data
        assert "coverage_percentage" in data
    
    def test_generate_pdf_report(self, client, sample_client_requirements):
        """Test PDF report generation"""
        params = {
            "requirements_id": sample_client_requirements.requirements_id,
            "download": False
        }
        
        response = client.post("/api/reports/generate-pdf", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "pdf_generated" in data
        assert "pdf_size_bytes" in data
    
    def test_generate_complete_report(self, client, sample_client_requirements):
        """Test complete report generation"""
        params = {
            "requirements_id": sample_client_requirements.requirements_id,
            "include_pdf": True
        }
        
        response = client.post("/api/reports/generate-complete", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "report_content" in data
        assert "pdf_generated" in data


class TestClientRequirementsEndpoints:
    """Test client requirements endpoints"""
    
    def test_upload_client_requirements(self, client):
        """Test uploading client requirements file"""
        file_content = """
        1. Climate change adaptation reporting requirements
        2. Greenhouse gas emission disclosure standards
        3. Biodiversity impact assessment procedures
        """
        
        files = {"file": ("requirements.txt", file_content.encode(), "text/plain")}
        data = {
            "client_name": "Test Client",
            "schema_type": SchemaType.EU_ESRS_CSRD.value
        }
        
        response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert "requirements_id" in result
        assert result["client_name"] == "Test Client"
    
    def test_create_client_requirements(self, client):
        """Test creating client requirements programmatically"""
        requirements_data = {
            "client_name": "API Test Client",
            "requirements_text": "Test requirements for API integration",
            "schema_type": SchemaType.EU_ESRS_CSRD.value
        }
        
        response = client.post("/api/client-requirements/", json=requirements_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["client_name"] == "API Test Client"
    
    def test_list_client_requirements(self, client, sample_client_requirements):
        """Test listing client requirements"""
        response = client.get("/api/client-requirements/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_client_requirements(self, client, sample_client_requirements):
        """Test getting specific client requirements"""
        response = client.get(f"/api/client-requirements/{sample_client_requirements.requirements_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["requirements_id"] == sample_client_requirements.requirements_id
    
    def test_perform_gap_analysis(self, client, sample_client_requirements):
        """Test gap analysis"""
        response = client.get(f"/api/client-requirements/{sample_client_requirements.requirements_id}/gap-analysis")
        assert response.status_code == 200
        
        data = response.json()
        assert "coverage_percentage" in data
        assert "gaps" in data
    
    def test_update_requirements_mapping(self, client, sample_client_requirements):
        """Test updating requirements mapping"""
        mappings = [
            {
                "requirement_id": "req_1",
                "schema_element_id": "E1",
                "confidence_score": 0.8,
                "mapping_type": "direct"
            }
        ]
        
        response = client.put(
            f"/api/client-requirements/{sample_client_requirements.requirements_id}/mappings",
            json=mappings
        )
        assert response.status_code == 200
    
    def test_delete_client_requirements(self, client, sample_client_requirements):
        """Test deleting client requirements"""
        response = client.delete(f"/api/client-requirements/{sample_client_requirements.requirements_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_analyze_requirements_text(self, client, sample_client_requirements):
        """Test analyzing requirements against different schema"""
        response = client.post(
            f"/api/client-requirements/{sample_client_requirements.requirements_id}/analyze",
            params={"schema_type": SchemaType.UK_SRD.value}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "schema_mappings" in data
        assert "processed_requirements" in data


class TestSchemaEndpoints:
    """Test schema management endpoints"""
    
    def test_initialize_schemas(self, client):
        """Test schema initialization"""
        response = client.post("/api/schemas/initialize")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_schema_elements(self, client):
        """Test getting schema elements"""
        response = client.get(f"/api/schemas/elements/{SchemaType.EU_ESRS_CSRD.value}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_classify_document(self, client, sample_document):
        """Test document classification"""
        response = client.post(f"/api/schemas/classify/document/{sample_document.document_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "classified_chunks" in data
    
    def test_update_document_schema(self, client, sample_document):
        """Test updating document schema"""
        response = client.put(
            f"/api/schemas/document/{sample_document.document_id}/schema/{SchemaType.UK_SRD.value}"
        )
        assert response.status_code == 200
    
    def test_get_unclassified_documents(self, client):
        """Test getting unclassified documents"""
        response = client.get("/api/schemas/unclassified")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_map_client_requirements(self, client):
        """Test mapping client requirements to schema"""
        requirements_text = "Climate change adaptation and mitigation requirements"
        
        response = client.post(
            f"/api/schemas/map-requirements/{SchemaType.EU_ESRS_CSRD.value}",
            params={"requirements_text": requirements_text}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "mappings" in data
    
    def test_get_schema_types(self, client):
        """Test getting schema types"""
        response = client.get("/api/schemas/types")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert SchemaType.EU_ESRS_CSRD.value in data
    
    def test_get_schema_statistics(self, client):
        """Test getting schema statistics"""
        response = client.get(f"/api/schemas/stats/{SchemaType.EU_ESRS_CSRD.value}")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_elements" in data
        assert "classification_rate_percent" in data


class TestAsyncProcessingEndpoints:
    """Test async processing endpoints"""
    
    def test_start_document_processing(self, client, sample_document):
        """Test starting document processing"""
        processing_request = {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "generate_embeddings": True,
            "classify_schema": True
        }
        
        response = client.post(
            f"/api/async/process/{sample_document.document_id}",
            json=processing_request
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
    
    def test_start_batch_processing(self, client, sample_document):
        """Test starting batch processing"""
        batch_request = {
            "document_ids": [sample_document.document_id],
            "generate_embeddings": True
        }
        
        response = client.post("/api/async/batch-process", json=batch_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
    
    def test_regenerate_embeddings(self, client, sample_document):
        """Test regenerating embeddings"""
        response = client.post(f"/api/async/regenerate-embeddings/{sample_document.document_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
    
    def test_get_task_status(self, client):
        """Test getting task status"""
        task_id = "test-task-123"
        
        response = client.get(f"/api/async/task/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
    
    def test_cancel_task(self, client):
        """Test canceling task"""
        task_id = "test-task-123"
        
        response = client.delete(f"/api/async/task/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_get_queue_status(self, client):
        """Test getting queue status"""
        response = client.get("/api/async/queue/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "queue_status" in data
        assert "task_counts" in data
    
    def test_get_processing_statistics(self, client):
        """Test getting processing statistics"""
        response = client.get("/api/async/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_documents" in data
        assert "status_counts" in data
    
    def test_cleanup_stuck_processing(self, client):
        """Test cleanup stuck processing"""
        response = client.post("/api/async/cleanup", params={"max_age_hours": 24})
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
    
    def test_get_document_processing_history(self, client, sample_document):
        """Test getting document processing history"""
        response = client.get(f"/api/async/history/{sample_document.document_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "document_id" in data
        assert "history" in data
    
    def test_async_health_check(self, client):
        """Test async processing health check"""
        response = client.get("/api/async/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data


class TestErrorHandling:
    """Test error handling across all endpoints"""
    
    def test_validation_error_handling(self, client):
        """Test request validation error handling"""
        # Send invalid data to trigger validation error
        invalid_data = {"invalid_field": "invalid_value"}
        
        response = client.post("/api/documents/upload", json=invalid_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "ValidationError"
    
    def test_not_found_error_handling(self, client):
        """Test 404 error handling"""
        response = client.get("/api/documents/nonexistent-id")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 404
    
    def test_method_not_allowed_error(self, client):
        """Test method not allowed error"""
        response = client.patch("/api/documents/")  # PATCH not supported
        assert response.status_code == 405
    
    def test_large_request_handling(self, client):
        """Test handling of large requests"""
        # Create a very large request body
        large_data = {"query": "x" * 10000}  # Very long query
        
        response = client.post("/api/search/", json=large_data)
        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 413, 422]


class TestCORSAndSecurity:
    """Test CORS and security features"""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/documents/")
        assert response.status_code == 200
        
        # Check for CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
    
    def test_process_time_header(self, client):
        """Test process time header is added"""
        response = client.get("/")
        assert response.status_code == 200
        
        headers = response.headers
        assert "x-process-time" in headers
        
        # Verify it's a valid float
        process_time = float(headers["x-process-time"])
        assert process_time >= 0


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_spec_available(self, client):
        """Test OpenAPI specification is available"""
        response = client.get("/openapi.json")
        # Should be available in debug mode
        assert response.status_code in [200, 404]  # 404 if disabled in production
        
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data
            assert "info" in data
            assert "paths" in data
    
    def test_swagger_ui_available(self, client):
        """Test Swagger UI is available"""
        response = client.get("/docs")
        # Should be available in debug mode
        assert response.status_code in [200, 404]  # 404 if disabled in production
    
    def test_redoc_available(self, client):
        """Test ReDoc is available"""
        response = client.get("/redoc")
        # Should be available in debug mode
        assert response.status_code in [200, 404]  # 404 if disabled in production
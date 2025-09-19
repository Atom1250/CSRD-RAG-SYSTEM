# CSRD RAG System API Documentation

## Overview

The CSRD RAG System provides a comprehensive REST API for managing sustainability reporting documents, performing semantic search, and generating AI-powered reports. This documentation covers all available endpoints, request/response formats, and usage examples.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

Currently, the API does not require authentication. In production deployments, consider implementing API key authentication or OAuth2.

## API Endpoints

### Health Check

#### GET /health
Check the health status of the application and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "vector_db": "healthy",
    "celery": "healthy"
  },
  "version": "1.0.0"
}
```

### Document Management

#### POST /api/documents/upload
Upload a new document for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Document file (PDF, DOCX, TXT)
  - `schema_type`: Schema type ("eu_esrs_csrd" or "uk_srd")
  - `metadata`: Optional JSON metadata

**Example:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@document.pdf" \
  -F "schema_type=eu_esrs_csrd" \
  -F "metadata={\"category\": \"environmental\"}"
```

**Response:**
```json
{
  "id": "doc_123456",
  "filename": "document.pdf",
  "file_size": 1024000,
  "schema_type": "eu_esrs_csrd",
  "processing_status": "queued",
  "upload_date": "2024-01-15T10:30:00Z",
  "metadata": {
    "category": "environmental"
  }
}
```

#### GET /api/documents
List all uploaded documents with optional filtering.

**Query Parameters:**
- `schema_type`: Filter by schema type
- `status`: Filter by processing status
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Example:**
```bash
curl "http://localhost:8000/api/documents?schema_type=eu_esrs_csrd&limit=10"
```

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_123456",
      "filename": "document.pdf",
      "file_size": 1024000,
      "schema_type": "eu_esrs_csrd",
      "processing_status": "completed",
      "upload_date": "2024-01-15T10:30:00Z",
      "chunk_count": 45,
      "schema_elements": ["E1", "E2", "G1"]
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### GET /api/documents/{document_id}
Get details of a specific document.

**Response:**
```json
{
  "id": "doc_123456",
  "filename": "document.pdf",
  "file_size": 1024000,
  "schema_type": "eu_esrs_csrd",
  "processing_status": "completed",
  "upload_date": "2024-01-15T10:30:00Z",
  "processing_completed_at": "2024-01-15T10:35:00Z",
  "chunk_count": 45,
  "schema_elements": ["E1", "E2", "G1"],
  "metadata": {
    "category": "environmental"
  }
}
```

#### DELETE /api/documents/{document_id}
Delete a document and all associated data.

**Response:**
```json
{
  "message": "Document deleted successfully",
  "document_id": "doc_123456"
}
```

### Search

#### POST /api/search
Perform semantic search across all documents.

**Request:**
```json
{
  "query": "carbon emissions reporting requirements",
  "schema_type": "eu_esrs_csrd",
  "limit": 10,
  "min_relevance_score": 0.7
}
```

**Response:**
```json
{
  "query": "carbon emissions reporting requirements",
  "results": [
    {
      "chunk_id": "chunk_789",
      "document_id": "doc_123456",
      "document_name": "ESRS_E1_Climate_Change.pdf",
      "content": "Organizations shall report their Scope 1, 2, and 3 greenhouse gas emissions...",
      "relevance_score": 0.92,
      "schema_elements": ["E1"],
      "page_number": 15
    }
  ],
  "total_results": 1,
  "processing_time_ms": 245
}
```

### RAG (Question Answering)

#### POST /api/rag/query
Ask questions and get AI-generated answers based on document content.

**Request:**
```json
{
  "question": "What are the mandatory disclosure requirements for Scope 3 emissions under ESRS E1?",
  "schema_type": "eu_esrs_csrd",
  "model": "gpt-4",
  "max_context_chunks": 10,
  "temperature": 0.1
}
```

**Response:**
```json
{
  "question": "What are the mandatory disclosure requirements for Scope 3 emissions under ESRS E1?",
  "answer": "Under ESRS E1, organizations are required to disclose Scope 3 emissions when they represent more than 40% of total GHG emissions. The disclosure must include...",
  "confidence_score": 0.89,
  "model_used": "gpt-4",
  "sources": [
    {
      "document_name": "ESRS_E1_Climate_Change.pdf",
      "page_number": 15,
      "relevance_score": 0.92,
      "excerpt": "Organizations shall report their Scope 1, 2, and 3 greenhouse gas emissions..."
    }
  ],
  "processing_time_ms": 3420,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/rag/models
Get list of available AI models.

**Response:**
```json
{
  "models": [
    {
      "name": "gpt-4",
      "provider": "openai",
      "description": "Most capable model for complex reasoning",
      "max_tokens": 8192,
      "cost_per_1k_tokens": 0.03
    },
    {
      "name": "claude-3-sonnet",
      "provider": "anthropic",
      "description": "Balanced performance and speed",
      "max_tokens": 4096,
      "cost_per_1k_tokens": 0.015
    }
  ]
}
```

### Client Requirements

#### POST /api/client-requirements/upload
Upload client-specific reporting requirements.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Requirements file (PDF, DOCX, TXT)
  - `client_name`: Client identifier
  - `schema_type`: Target schema type

**Response:**
```json
{
  "id": "req_789012",
  "client_name": "Acme Corp",
  "filename": "acme_requirements.pdf",
  "schema_type": "eu_esrs_csrd",
  "processing_status": "queued",
  "upload_date": "2024-01-15T10:30:00Z"
}
```

#### GET /api/client-requirements/{requirement_id}
Get processed client requirements with schema mappings.

**Response:**
```json
{
  "id": "req_789012",
  "client_name": "Acme Corp",
  "filename": "acme_requirements.pdf",
  "schema_type": "eu_esrs_csrd",
  "processing_status": "completed",
  "requirements": [
    {
      "requirement_text": "Report on carbon footprint reduction initiatives",
      "mapped_schema_elements": ["E1.1", "E1.2"],
      "confidence_score": 0.85
    }
  ],
  "gap_analysis": {
    "covered_elements": ["E1.1", "E1.2"],
    "missing_elements": ["E1.3"],
    "coverage_percentage": 67
  }
}
```

### Report Generation

#### POST /api/reports/generate
Generate a comprehensive report based on client requirements.

**Request:**
```json
{
  "client_requirements_id": "req_789012",
  "template_type": "standard",
  "model": "gpt-4",
  "include_citations": true,
  "output_format": "pdf"
}
```

**Response:**
```json
{
  "report_id": "rpt_345678",
  "status": "generating",
  "estimated_completion": "2024-01-15T10:45:00Z",
  "progress_url": "/api/reports/rpt_345678/status"
}
```

#### GET /api/reports/{report_id}/status
Check report generation status.

**Response:**
```json
{
  "report_id": "rpt_345678",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:42:00Z",
  "download_url": "/api/reports/rpt_345678/download",
  "page_count": 25,
  "section_count": 8
}
```

#### GET /api/reports/{report_id}/download
Download the generated report.

**Response:**
- Content-Type: `application/pdf`
- Binary PDF content

### Schema Management

#### GET /api/schemas
List available reporting schemas.

**Response:**
```json
{
  "schemas": [
    {
      "type": "eu_esrs_csrd",
      "name": "EU European Sustainability Reporting Standards (CSRD)",
      "version": "1.0",
      "elements_count": 82,
      "last_updated": "2024-01-01T00:00:00Z"
    },
    {
      "type": "uk_srd",
      "name": "UK Sustainability Reporting Directive",
      "version": "1.0",
      "elements_count": 45,
      "last_updated": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /api/schemas/{schema_type}/elements
Get detailed schema elements.

**Response:**
```json
{
  "schema_type": "eu_esrs_csrd",
  "elements": [
    {
      "code": "E1",
      "name": "Climate Change",
      "description": "Climate-related disclosures including GHG emissions",
      "sub_elements": [
        {
          "code": "E1.1",
          "name": "Transition plan for climate change mitigation",
          "requirements": [
            "Describe the transition plan",
            "Include quantitative targets"
          ]
        }
      ]
    }
  ]
}
```

### Remote Directory Management

#### POST /api/remote-directories
Configure a remote directory for automatic document synchronization.

**Request:**
```json
{
  "name": "SharePoint Documents",
  "path": "/mnt/sharepoint/sustainability",
  "sync_interval": 3600,
  "schema_type": "eu_esrs_csrd",
  "enabled": true
}
```

**Response:**
```json
{
  "id": "remote_123",
  "name": "SharePoint Documents",
  "path": "/mnt/sharepoint/sustainability",
  "sync_interval": 3600,
  "schema_type": "eu_esrs_csrd",
  "enabled": true,
  "last_sync": null,
  "document_count": 0
}
```

#### POST /api/remote-directories/{directory_id}/sync
Trigger manual synchronization of a remote directory.

**Response:**
```json
{
  "sync_id": "sync_456",
  "status": "started",
  "directory_id": "remote_123",
  "started_at": "2024-01-15T10:30:00Z"
}
```

### Metrics and Monitoring

#### GET /api/metrics
Get system performance metrics.

**Response:**
```json
{
  "system": {
    "uptime_seconds": 86400,
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 67.8,
    "disk_usage_percent": 23.1
  },
  "application": {
    "total_documents": 150,
    "total_chunks": 6750,
    "total_queries": 1250,
    "avg_query_time_ms": 245,
    "total_reports_generated": 45
  },
  "services": {
    "database_connections": 12,
    "redis_memory_mb": 128,
    "celery_active_tasks": 3,
    "vector_db_collections": 2
  }
}
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid file format. Supported formats: PDF, DOCX, TXT",
    "details": {
      "field": "file",
      "received_format": "xlsx"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid request parameters
- `FILE_TOO_LARGE`: Uploaded file exceeds size limit
- `PROCESSING_FAILED`: Document processing failed
- `MODEL_UNAVAILABLE`: AI model is not available
- `INSUFFICIENT_CONTEXT`: Not enough relevant documents found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Rate Limits

- General API: 100 requests per minute per IP
- Upload endpoints: 10 requests per minute per IP
- RAG queries: 20 requests per minute per IP

## SDKs and Examples

### Python SDK Example

```python
import requests

class CSRDClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_document(self, file_path, schema_type="eu_esrs_csrd"):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/documents/upload",
                files={'file': f},
                data={'schema_type': schema_type}
            )
        return response.json()
    
    def ask_question(self, question, model="gpt-4"):
        response = requests.post(
            f"{self.base_url}/api/rag/query",
            json={
                'question': question,
                'model': model
            }
        )
        return response.json()

# Usage
client = CSRDClient()
doc = client.upload_document("sustainability_report.pdf")
answer = client.ask_question("What are the Scope 3 emission requirements?")
```

### JavaScript/Node.js Example

```javascript
class CSRDClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async uploadDocument(file, schemaType = 'eu_esrs_csrd') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('schema_type', schemaType);
        
        const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
            method: 'POST',
            body: formData
        });
        
        return response.json();
    }
    
    async askQuestion(question, model = 'gpt-4') {
        const response = await fetch(`${this.baseUrl}/api/rag/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question,
                model
            })
        });
        
        return response.json();
    }
}

// Usage
const client = new CSRDClient();
const doc = await client.uploadDocument(fileInput.files[0]);
const answer = await client.askQuestion('What are the Scope 3 emission requirements?');
```

## Interactive API Documentation

The system provides interactive API documentation using Swagger UI:

- **URL**: `http://localhost:8000/docs`
- **Features**: 
  - Try out endpoints directly
  - View request/response schemas
  - Download OpenAPI specification

## Support and Troubleshooting

For API support and troubleshooting:

1. Check the interactive documentation at `/docs`
2. Review error messages and codes
3. Check system health at `/health`
4. Monitor logs for detailed error information
5. Refer to the user guide for common usage patterns
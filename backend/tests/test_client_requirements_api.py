"""
Tests for Client Requirements API endpoints
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from io import BytesIO

from app.models.database import ClientRequirements, SchemaElement
from app.models.schemas import SchemaType


class TestClientRequirementsAPI:
    """Test cases for Client Requirements API endpoints"""
    
    def test_upload_client_requirements_json(self, client: TestClient, db_session: Session):
        """Test uploading JSON requirements file"""
        requirements_data = {
            "requirements": [
                "Report on greenhouse gas emissions",
                "Disclose water usage metrics"
            ]
        }
        
        json_content = json.dumps(requirements_data)
        
        files = {
            "file": ("requirements.json", BytesIO(json_content.encode()), "application/json")
        }
        data = {
            "client_name": "Test Client Corp",
            "schema_type": "EU_ESRS_CSRD"
        }
        
        response = client.post("/api/client-requirements/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["client_name"] == "Test Client Corp"
        assert result["requirements_text"] == json_content
        assert result["id"] is not None
        assert result["processed_requirements"] is not None
    
    def test_upload_client_requirements_text(self, client: TestClient, db_session: Session):
        """Test uploading text requirements file"""
        text_content = """
        1. Report on carbon emissions (Scope 1, 2, 3)
        2. Disclose water usage and conservation efforts
        3. Provide waste management information
        """
        
        files = {
            "file": ("requirements.txt", BytesIO(text_content.encode()), "text/plain")
        }
        data = {
            "client_name": "Test Client",
            "schema_type": "UK_SRD"
        }
        
        response = client.post("/api/client-requirements/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["client_name"] == "Test Client"
        assert result["requirements_text"] == text_content
        assert len(result["processed_requirements"]) == 3
    
    def test_upload_invalid_file_type(self, client: TestClient, db_session: Session):
        """Test uploading unsupported file type"""
        files = {
            "file": ("requirements.pdf", BytesIO(b"fake pdf content"), "application/pdf")
        }
        data = {
            "client_name": "Test Client",
            "schema_type": "EU_ESRS_CSRD"
        }
        
        response = client.post("/api/client-requirements/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_upload_empty_file(self, client: TestClient, db_session: Session):
        """Test uploading empty file"""
        files = {
            "file": ("empty.txt", BytesIO(b""), "text/plain")
        }
        data = {
            "client_name": "Test Client",
            "schema_type": "EU_ESRS_CSRD"
        }
        
        response = client.post("/api/client-requirements/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]
    
    def test_create_client_requirements(self, client: TestClient, db_session: Session):
        """Test creating client requirements via JSON API"""
        requirements_data = {
            "client_name": "API Test Client",
            "requirements_text": "Report on environmental impact and social responsibility",
            "schema_mappings": [],
            "processed_requirements": []
        }
        
        response = client.post("/api/client-requirements/", json=requirements_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["client_name"] == "API Test Client"
        assert result["requirements_text"] == "Report on environmental impact and social responsibility"
        assert result["id"] is not None
    
    def test_list_client_requirements(self, client: TestClient, db_session: Session):
        """Test listing client requirements"""
        # Create test requirements
        req1 = ClientRequirements(
            client_name="Client A",
            requirements_text="Requirements for Client A"
        )
        req2 = ClientRequirements(
            client_name="Client B Corp",
            requirements_text="Requirements for Client B"
        )
        
        db_session.add_all([req1, req2])
        db_session.commit()
        
        # Test listing all
        response = client.get("/api/client-requirements/")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 2
        
        # Test filtering by client name
        response = client.get("/api/client-requirements/?client_name=Client A")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["client_name"] == "Client A"
    
    def test_get_client_requirements(self, client: TestClient, db_session: Session):
        """Test getting specific client requirements"""
        # Create test requirements
        req = ClientRequirements(
            client_name="Test Client",
            requirements_text="Test requirements text"
        )
        db_session.add(req)
        db_session.commit()
        
        # Get requirements
        response = client.get(f"/api/client-requirements/{req.id}")
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == req.id
        assert result["client_name"] == "Test Client"
    
    def test_get_nonexistent_requirements(self, client: TestClient, db_session: Session):
        """Test getting non-existent requirements"""
        response = client.get("/api/client-requirements/nonexistent_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_gap_analysis(self, client: TestClient, db_session: Session, sample_requirements_with_coverage):
        """Test gap analysis endpoint"""
        req_id = sample_requirements_with_coverage
        
        response = client.get(f"/api/client-requirements/{req_id}/gap-analysis")
        assert response.status_code == 200
        
        result = response.json()
        assert result["requirements_id"] == req_id
        assert "total_requirements" in result
        assert "coverage_percentage" in result
        assert "available_documents" in result
        assert "gaps" in result
        assert "recommendations" in result
    
    def test_gap_analysis_nonexistent_requirements(self, client: TestClient, db_session: Session):
        """Test gap analysis for non-existent requirements"""
        response = client.get("/api/client-requirements/nonexistent_id/gap-analysis")
        assert response.status_code == 404
    
    def test_update_requirements_mapping(self, client: TestClient, db_session: Session):
        """Test updating requirements mapping"""
        # Create test requirements
        req = ClientRequirements(
            client_name="Test Client",
            requirements_text="Test requirements",
            processed_requirements=[{
                "requirement_id": "req_1",
                "requirement_text": "Test requirement",
                "mapped_elements": ["old_elem"],
                "priority": "medium"
            }]
        )
        db_session.add(req)
        db_session.commit()
        
        # Update mappings
        new_mappings = [{
            "requirement_id": "req_1",
            "schema_element_id": "new_elem_1",
            "confidence_score": 0.95
        }]
        
        response = client.put(f"/api/client-requirements/{req.id}/mappings", json=new_mappings)
        assert response.status_code == 200
        
        result = response.json()
        assert len(result["schema_mappings"]) == 1
        assert result["schema_mappings"][0]["schema_element_id"] == "new_elem_1"
    
    def test_delete_client_requirements(self, client: TestClient, db_session: Session):
        """Test deleting client requirements"""
        # Create test requirements
        req = ClientRequirements(
            client_name="Test Client",
            requirements_text="Test requirements"
        )
        db_session.add(req)
        db_session.commit()
        req_id = req.id
        
        # Delete requirements
        response = client.delete(f"/api/client-requirements/{req_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion
        response = client.get(f"/api/client-requirements/{req_id}")
        assert response.status_code == 404
    
    def test_delete_nonexistent_requirements(self, client: TestClient, db_session: Session):
        """Test deleting non-existent requirements"""
        response = client.delete("/api/client-requirements/nonexistent_id")
        assert response.status_code == 404
    
    def test_analyze_requirements_text(self, client: TestClient, db_session: Session, sample_schema_elements):
        """Test re-analyzing requirements against different schema"""
        # Create test requirements
        req = ClientRequirements(
            client_name="Test Client",
            requirements_text="1. Report on carbon emissions\n2. Disclose water usage"
        )
        db_session.add(req)
        db_session.commit()
        
        # Analyze against schema
        response = client.post(f"/api/client-requirements/{req.id}/analyze?schema_type=EU_ESRS_CSRD")
        assert response.status_code == 200
        
        result = response.json()
        assert result["requirements_id"] == req.id
        assert result["schema_type"] == "EU_ESRS_CSRD"
        assert "parsed_requirements" in result
        assert "schema_mappings" in result
        assert "processed_requirements" in result
    
    def test_analyze_nonexistent_requirements(self, client: TestClient, db_session: Session):
        """Test analyzing non-existent requirements"""
        response = client.post("/api/client-requirements/nonexistent_id/analyze?schema_type=EU_ESRS_CSRD")
        assert response.status_code == 404


@pytest.fixture
def sample_requirements_with_coverage(db_session: Session):
    """Create sample requirements with some document coverage for testing"""
    from app.models.database import Document, TextChunk
    from app.models.schemas import DocumentType, ProcessingStatus
    
    # Create schema elements
    schema_elem = SchemaElement(
        schema_type=SchemaType.EU_ESRS_CSRD,
        element_code="E1",
        element_name="Climate Change",
        description="Climate change related disclosures"
    )
    db_session.add(schema_elem)
    db_session.commit()
    
    # Create document and chunk
    document = Document(
        filename="test_doc.pdf",
        file_path="/test/path/test_doc.pdf",
        file_size=1024,
        document_type=DocumentType.PDF,
        schema_type=SchemaType.EU_ESRS_CSRD,
        processing_status=ProcessingStatus.COMPLETED
    )
    db_session.add(document)
    db_session.commit()
    
    chunk = TextChunk(
        document_id=document.id,
        content="Climate change emissions reporting requirements",
        chunk_index=0,
        schema_elements=[schema_elem.id]
    )
    db_session.add(chunk)
    db_session.commit()
    
    # Create client requirements
    req = ClientRequirements(
        client_name="Test Client",
        requirements_text="Report on climate change impacts",
        schema_mappings=[{
            "requirement_id": "req_1",
            "schema_element_id": schema_elem.id,
            "confidence_score": 0.9
        }],
        processed_requirements=[{
            "requirement_id": "req_1",
            "requirement_text": "Report on climate change impacts",
            "mapped_elements": [schema_elem.id],
            "priority": "high"
        }]
    )
    db_session.add(req)
    db_session.commit()
    
    return req.id


@pytest.fixture
def sample_schema_elements(db_session: Session):
    """Create sample schema elements for testing"""
    elements = [
        SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change related disclosures including greenhouse gas emissions"
        ),
        SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E3",
            element_name="Water Resources",
            description="Water usage, conservation and management"
        )
    ]
    
    db_session.add_all(elements)
    db_session.commit()
    return elements
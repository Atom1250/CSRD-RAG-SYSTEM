"""
Tests for Report API endpoints
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.report_service import (
    ReportService, ReportTemplate, ReportFormat, ReportContent, ReportSection
)
from app.services.rag_service import AIModelType
from app.models.schemas import ClientRequirementsResponse, SchemaType


class TestReportAPI:
    """Test cases for Report API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_report_service(self):
        """Mock report service"""
        return Mock(spec=ReportService)
    
    def test_get_available_templates(self, client):
        """Test GET /api/reports/templates endpoint"""
        with patch('app.api.reports.ReportService') as mock_service_class:
            mock_service = Mock()
            mock_service.template_manager.get_available_templates.return_value = [
                {
                    "type": "eu_esrs_standard",
                    "name": "EU ESRS/CSRD Standard Report",
                    "description": "Standard report template for EU ESRS/CSRD compliance"
                },
                {
                    "type": "uk_srd_standard",
                    "name": "UK SRD Standard Report",
                    "description": "Standard report template for UK SRD compliance"
                }
            ]
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/reports/templates")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["type"] == "eu_esrs_standard"
            assert data[1]["type"] == "uk_srd_standard"
    
    def test_get_template_details(self, client):
        """Test GET /api/reports/templates/{template_type} endpoint"""
        with patch('app.api.reports.ReportService') as mock_service_class:
            mock_service = Mock()
            mock_service.template_manager.get_template.return_value = {
                "name": "EU ESRS/CSRD Standard Report",
                "description": "Standard template",
                "sections": [
                    {"id": "executive_summary", "title": "Executive Summary", "required": True}
                ]
            }
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/reports/templates/eu_esrs_standard")
            
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "eu_esrs_standard"
            assert "config" in data
            assert data["config"]["name"] == "EU ESRS/CSRD Standard Report"
    
    def test_get_template_details_not_found(self, client):
        """Test GET /api/reports/templates/{template_type} with invalid template"""
        response = client.get("/api/reports/templates/invalid_template")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @patch('app.api.reports.ReportService')
    def test_generate_report_success(self, mock_service_class, client):
        """Test POST /api/reports/generate endpoint success"""
        # Mock report content
        mock_report_content = ReportContent(
            title="Test Report",
            client_name="Test Client",
            generation_date=datetime.utcnow(),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=[
                ReportSection(
                    id="section_1",
                    title="Test Section",
                    content="Test content",
                    subsections=[],
                    metadata={},
                    sources=[]
                )
            ],
            executive_summary="Test summary",
            metadata={}
        )
        
        # Mock service
        mock_service = Mock()
        mock_service.generate_report = AsyncMock(return_value=mock_report_content)
        mock_service.format_report.return_value = "Formatted report content"
        mock_service.get_report_metadata.return_value = {
            "title": "Test Report",
            "client_name": "Test Client",
            "statistics": {"total_sections": 1}
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/reports/generate",
            params={
                "requirements_id": "test_req_1",
                "template_type": "eu_esrs_standard",
                "ai_model": "openai_gpt35",
                "report_format": "structured_text"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "report_content" in data
        assert "metadata" in data
        assert "raw_content" in data
        assert data["report_content"] == "Formatted report content"
    
    def test_generate_report_invalid_template(self, client):
        """Test POST /api/reports/generate with invalid template"""
        response = client.post(
            "/api/reports/generate",
            params={
                "requirements_id": "test_req_1",
                "template_type": "invalid_template"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid template type" in data["detail"]
    
    def test_generate_report_invalid_ai_model(self, client):
        """Test POST /api/reports/generate with invalid AI model"""
        response = client.post(
            "/api/reports/generate",
            params={
                "requirements_id": "test_req_1",
                "ai_model": "invalid_model"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid AI model" in data["detail"]
    
    def test_generate_report_invalid_format(self, client):
        """Test POST /api/reports/generate with invalid format"""
        response = client.post(
            "/api/reports/generate",
            params={
                "requirements_id": "test_req_1",
                "report_format": "invalid_format"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid report format" in data["detail"]
    
    def test_generate_report_async(self, client):
        """Test POST /api/reports/generate-async endpoint"""
        response = client.post(
            "/api/reports/generate-async",
            params={
                "requirements_id": "test_req_1",
                "template_type": "eu_esrs_standard"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "started"
    
    def test_get_available_formats(self, client):
        """Test GET /api/reports/formats endpoint"""
        response = client.get("/api/reports/formats")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # structured_text, markdown, html
        
        # Check format structure
        for fmt in data:
            assert "value" in fmt
            assert "name" in fmt
            assert "description" in fmt
    
    @patch('app.api.reports.ReportService')
    def test_get_available_ai_models(self, mock_service_class, client):
        """Test GET /api/reports/ai-models endpoint"""
        mock_service = Mock()
        mock_service.rag_service.get_available_models.return_value = [
            {
                "type": "openai_gpt4",
                "provider": "OpenAI",
                "model": "gpt-4",
                "available": True
            },
            {
                "type": "openai_gpt35",
                "provider": "OpenAI", 
                "model": "gpt-3.5-turbo",
                "available": True
            }
        ]
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/reports/ai-models")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["type"] == "openai_gpt4"
    
    @patch('app.api.reports.ReportService')
    def test_preview_report_structure(self, mock_service_class, client):
        """Test GET /api/reports/preview/{requirements_id} endpoint"""
        # Mock client requirements
        mock_requirements = ClientRequirementsResponse(
            id="test_req_1",
            client_name="Test Client",
            requirements_text="Test requirements",
            upload_date=datetime.utcnow(),
            processed_requirements=[
                {
                    "requirement_id": "req_1",
                    "requirement_text": "Test requirement text",
                    "priority": "high"
                }
            ]
        )
        
        # Mock template config
        mock_template_config = {
            "name": "EU ESRS/CSRD Standard Report",
            "sections": [
                {
                    "id": "executive_summary",
                    "title": "Executive Summary",
                    "required": True,
                    "description": "High-level overview",
                    "subsections": []
                },
                {
                    "id": "environmental_standards",
                    "title": "Environmental Standards",
                    "required": False,
                    "description": "Environmental reporting",
                    "subsections": [
                        {"id": "e1_climate", "title": "E1 - Climate Change"}
                    ]
                }
            ]
        }
        
        # Mock service
        mock_service = Mock()
        mock_service.client_requirements_service.get_client_requirements.return_value = mock_requirements
        mock_service.template_manager.get_template.return_value = mock_template_config
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/reports/preview/test_req_1?template_type=eu_esrs_standard")
        
        assert response.status_code == 200
        data = response.json()
        assert data["client_name"] == "Test Client"
        assert data["template_type"] == "eu_esrs_standard"
        assert "sections" in data
        assert len(data["sections"]) == 2
        assert data["sections"][0]["id"] == "executive_summary"
        assert len(data["sections"][1]["subsections"]) == 1
        assert "relevant_requirements" in data
    
    def test_preview_report_structure_not_found(self, client):
        """Test GET /api/reports/preview/{requirements_id} with invalid ID"""
        with patch('app.api.reports.ReportService') as mock_service_class:
            mock_service = Mock()
            mock_service.client_requirements_service.get_client_requirements.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/reports/preview/invalid_req_id")
            
            assert response.status_code == 404
    
    @patch('app.api.reports.ReportService')
    def test_validate_requirements_for_report(self, mock_service_class, client):
        """Test POST /api/reports/validate-requirements/{requirements_id} endpoint"""
        # Mock client requirements
        mock_requirements = ClientRequirementsResponse(
            id="test_req_1",
            client_name="Test Client",
            requirements_text="Test requirements",
            upload_date=datetime.utcnow()
        )
        
        # Mock gap analysis
        mock_gap_analysis = {
            "requirements_id": "test_req_1",
            "client_name": "Test Client",
            "total_requirements": 5,
            "covered_requirements": 4,
            "coverage_percentage": 80.0,
            "available_documents": [
                {"id": "doc_1", "filename": "test.pdf"}
            ],
            "gaps": {
                "uncovered_requirements": [
                    {"id": "req_5", "text": "Uncovered requirement", "priority": "low"}
                ]
            }
        }
        
        # Mock service
        mock_service = Mock()
        mock_service.client_requirements_service.get_client_requirements.return_value = mock_requirements
        mock_service.client_requirements_service.perform_gap_analysis.return_value = mock_gap_analysis
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/reports/validate-requirements/test_req_1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["requirements_id"] == "test_req_1"
        assert data["coverage_percentage"] == 80.0
        assert data["validation_status"] == "excellent"  # 80% coverage
        assert "recommendations" in data
        assert "gap_analysis" in data
    
    @patch('app.api.reports.ReportService')
    def test_validate_requirements_poor_coverage(self, mock_service_class, client):
        """Test validation with poor coverage"""
        # Mock client requirements
        mock_requirements = ClientRequirementsResponse(
            id="test_req_1",
            client_name="Test Client",
            requirements_text="Test requirements",
            upload_date=datetime.utcnow()
        )
        
        # Mock gap analysis with poor coverage
        mock_gap_analysis = {
            "requirements_id": "test_req_1",
            "client_name": "Test Client",
            "total_requirements": 10,
            "covered_requirements": 2,
            "coverage_percentage": 20.0,
            "gaps": {
                "uncovered_requirements": [
                    {"id": "req_1", "text": "High priority requirement", "priority": "high"},
                    {"id": "req_2", "text": "Another requirement", "priority": "medium"}
                ]
            }
        }
        
        # Mock service
        mock_service = Mock()
        mock_service.client_requirements_service.get_client_requirements.return_value = mock_requirements
        mock_service.client_requirements_service.perform_gap_analysis.return_value = mock_gap_analysis
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/reports/validate-requirements/test_req_1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["validation_status"] == "poor"  # 20% coverage
        assert len(data["warnings"]) > 0
        assert any("Low coverage" in warning for warning in data["warnings"])
    
    def test_validate_requirements_not_found(self, client):
        """Test validation with invalid requirements ID"""
        with patch('app.api.reports.ReportService') as mock_service_class:
            mock_service = Mock()
            mock_service.client_requirements_service.get_client_requirements.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/reports/validate-requirements/invalid_req_id")
            
            assert response.status_code == 404


class TestReportAPIErrorHandling:
    """Test error handling in Report API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('app.api.reports.ReportService')
    def test_generate_report_service_error(self, mock_service_class, client):
        """Test report generation with service error"""
        mock_service = Mock()
        mock_service.generate_report = AsyncMock(side_effect=Exception("Service error"))
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/reports/generate",
            params={"requirements_id": "test_req_1"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Service error" in data["detail"]
    
    @patch('app.api.reports.ReportService')
    def test_get_templates_service_error(self, mock_service_class, client):
        """Test get templates with service error"""
        mock_service = Mock()
        mock_service.template_manager.get_available_templates.side_effect = Exception("Template error")
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/reports/templates")
        
        assert response.status_code == 500
        data = response.json()
        assert "Template error" in data["detail"]
    
    @patch('app.api.reports.ReportService')
    def test_preview_report_service_error(self, mock_service_class, client):
        """Test preview report with service error"""
        mock_service = Mock()
        mock_service.client_requirements_service.get_client_requirements.side_effect = Exception("Preview error")
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/reports/preview/test_req_1")
        
        assert response.status_code == 500
        data = response.json()
        assert "Preview error" in data["detail"]


class TestReportAPIValidation:
    """Test input validation in Report API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_generate_report_missing_requirements_id(self, client):
        """Test report generation without requirements ID"""
        response = client.post("/api/reports/generate")
        
        assert response.status_code == 422  # Validation error
    
    def test_preview_report_invalid_template_type(self, client):
        """Test preview with invalid template type"""
        response = client.get("/api/reports/preview/test_req_1?template_type=invalid_template")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid template type" in data["detail"]
    
    def test_generate_report_async_validation(self, client):
        """Test async generation parameter validation"""
        # Test with all invalid parameters
        response = client.post(
            "/api/reports/generate-async",
            params={
                "requirements_id": "test_req_1",
                "template_type": "invalid_template",
                "ai_model": "invalid_model",
                "report_format": "invalid_format"
            }
        )
        
        assert response.status_code == 400
        # Should fail on first invalid parameter (template_type)
        data = response.json()
        assert "Invalid template type" in data["detail"]


@pytest.mark.asyncio
class TestReportAPIIntegration:
    """Integration tests for Report API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @patch('app.api.reports.ReportService')
    def test_full_report_generation_workflow(self, mock_service_class, client):
        """Test complete workflow from validation to generation"""
        # Mock client requirements
        mock_requirements = ClientRequirementsResponse(
            id="workflow_req_1",
            client_name="Workflow Test Client",
            requirements_text="Complete workflow test requirements",
            upload_date=datetime.utcnow(),
            processed_requirements=[
                {
                    "requirement_id": "req_1",
                    "requirement_text": "Climate reporting requirement",
                    "priority": "high"
                }
            ]
        )
        
        # Mock gap analysis
        mock_gap_analysis = {
            "requirements_id": "workflow_req_1",
            "coverage_percentage": 85.0,
            "gaps": {"uncovered_requirements": []}
        }
        
        # Mock report content
        mock_report_content = ReportContent(
            title="Workflow Test Report",
            client_name="Workflow Test Client",
            generation_date=datetime.utcnow(),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=[],
            executive_summary="Workflow test summary",
            metadata={}
        )
        
        # Mock service
        mock_service = Mock()
        mock_service.client_requirements_service.get_client_requirements.return_value = mock_requirements
        mock_service.client_requirements_service.perform_gap_analysis.return_value = mock_gap_analysis
        mock_service.template_manager.get_template.return_value = {
            "name": "EU ESRS Standard",
            "sections": [{"id": "test", "title": "Test"}]
        }
        mock_service.generate_report = AsyncMock(return_value=mock_report_content)
        mock_service.format_report.return_value = "Formatted workflow report"
        mock_service.get_report_metadata.return_value = {"title": "Workflow Test Report"}
        mock_service_class.return_value = mock_service
        
        # Step 1: Validate requirements
        validation_response = client.post("/api/reports/validate-requirements/workflow_req_1")
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data["validation_status"] == "excellent"
        
        # Step 2: Preview report structure
        preview_response = client.get("/api/reports/preview/workflow_req_1")
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert preview_data["client_name"] == "Workflow Test Client"
        
        # Step 3: Generate report
        generation_response = client.post(
            "/api/reports/generate",
            params={"requirements_id": "workflow_req_1"}
        )
        assert generation_response.status_code == 200
        generation_data = generation_response.json()
        assert "report_content" in generation_data
        assert generation_data["report_content"] == "Formatted workflow report"
    
    def test_error_propagation_in_workflow(self, client):
        """Test that errors are properly propagated through the workflow"""
        # Test with non-existent requirements ID
        validation_response = client.post("/api/reports/validate-requirements/nonexistent_req")
        preview_response = client.get("/api/reports/preview/nonexistent_req")
        generation_response = client.post(
            "/api/reports/generate",
            params={"requirements_id": "nonexistent_req"}
        )
        
        # All should return appropriate error codes
        assert validation_response.status_code in [404, 500]
        assert preview_response.status_code in [404, 500]
        assert generation_response.status_code in [404, 500]
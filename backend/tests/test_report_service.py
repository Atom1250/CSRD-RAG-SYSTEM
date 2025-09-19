"""
Tests for Report Service
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.report_service import (
    ReportService, ReportTemplateManager, ReportTemplate, 
    ReportFormat, ReportSection, ReportContent
)
from app.services.rag_service import AIModelType
from app.models.schemas import (
    ClientRequirementsResponse, SchemaMapping, ProcessedRequirement, SchemaType
)


class TestReportTemplateManager:
    """Test cases for ReportTemplateManager"""
    
    def test_load_default_templates(self):
        """Test loading of default templates"""
        manager = ReportTemplateManager()
        
        # Check that all expected templates are loaded
        assert ReportTemplate.EU_ESRS_STANDARD in manager.templates
        assert ReportTemplate.UK_SRD_STANDARD in manager.templates
        assert ReportTemplate.GAP_ANALYSIS in manager.templates
        
        # Check EU ESRS template structure
        eu_template = manager.templates[ReportTemplate.EU_ESRS_STANDARD]
        assert eu_template["name"] == "EU ESRS/CSRD Standard Report"
        assert "sections" in eu_template
        assert len(eu_template["sections"]) > 0
        
        # Check required sections exist
        section_ids = [section["id"] for section in eu_template["sections"]]
        assert "executive_summary" in section_ids
        assert "general_requirements" in section_ids
        assert "environmental_standards" in section_ids
    
    def test_get_template(self):
        """Test getting template by type"""
        manager = ReportTemplateManager()
        
        # Test valid template
        template = manager.get_template(ReportTemplate.EU_ESRS_STANDARD)
        assert template is not None
        assert "name" in template
        assert "sections" in template
        
        # Test invalid template (should return empty dict)
        invalid_template = manager.get_template("invalid_template")
        assert invalid_template == {}
    
    def test_get_available_templates(self):
        """Test getting list of available templates"""
        manager = ReportTemplateManager()
        
        templates = manager.get_available_templates()
        assert isinstance(templates, list)
        assert len(templates) >= 3  # At least EU, UK, and Gap Analysis
        
        # Check template structure
        for template in templates:
            assert "type" in template
            assert "name" in template
            assert "description" in template
    
    def test_add_custom_template(self):
        """Test adding custom template"""
        manager = ReportTemplateManager()
        
        custom_config = {
            "name": "Custom Test Template",
            "description": "Test template",
            "sections": [
                {"id": "test_section", "title": "Test Section", "required": True}
            ]
        }
        
        result = manager.add_custom_template("custom_test", custom_config)
        assert result is True
        
        # Verify template was added
        custom_template = manager.get_template(ReportTemplate.CUSTOM_TEMPLATE)
        assert custom_template == custom_config


class TestReportService:
    """Test cases for ReportService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_client_requirements(self):
        """Mock client requirements"""
        return ClientRequirementsResponse(
            id="test_req_1",
            client_name="Test Client",
            requirements_text="Test requirements text",
            upload_date=datetime.utcnow(),
            schema_mappings=[
                SchemaMapping(
                    requirement_id="req_1",
                    schema_element_id="EU_ESRS_E1_1",
                    confidence_score=0.8
                )
            ],
            processed_requirements=[
                ProcessedRequirement(
                    requirement_id="req_1",
                    requirement_text="Climate change reporting requirements",
                    mapped_elements=["EU_ESRS_E1_1"],
                    priority="high"
                )
            ]
        )
    
    @pytest.fixture
    def report_service(self, mock_db_session):
        """Create ReportService instance with mocked dependencies"""
        with patch('app.services.report_service.ClientRequirementsService'), \
             patch('app.services.report_service.RAGService'):
            service = ReportService(mock_db_session)
            return service
    
    def test_determine_schema_type(self, report_service, mock_client_requirements):
        """Test schema type determination"""
        # Test EU schema detection
        schema_type = report_service._determine_schema_type(
            mock_client_requirements, ReportTemplate.EU_ESRS_STANDARD
        )
        assert schema_type == SchemaType.EU_ESRS_CSRD
        
        # Test UK template default
        schema_type = report_service._determine_schema_type(
            mock_client_requirements, ReportTemplate.UK_SRD_STANDARD
        )
        assert schema_type == SchemaType.UK_SRD
    
    def test_find_relevant_requirements(self, report_service, mock_client_requirements):
        """Test finding relevant requirements for sections"""
        # Test climate section
        relevant_reqs = report_service._find_relevant_requirements(
            "e1_climate", mock_client_requirements
        )
        assert len(relevant_reqs) > 0
        
        # Test executive summary section
        relevant_reqs = report_service._find_relevant_requirements(
            "executive_summary", mock_client_requirements
        )
        # Should include high priority requirements when no specific matches
        assert len(relevant_reqs) > 0
    
    def test_generate_section_questions(self, report_service):
        """Test generation of section questions"""
        section_config = {
            "id": "e1_climate",
            "title": "Climate Change",
            "description": "Climate change reporting requirements"
        }
        
        relevant_requirements = [
            {
                "requirement_id": "req_1",
                "requirement_text": "Report greenhouse gas emissions",
                "priority": "high"
            }
        ]
        
        questions = report_service._generate_section_questions(
            section_config, relevant_requirements
        )
        
        assert len(questions) > 0
        assert any("Climate Change" in question for question in questions)
        assert any("greenhouse gas emissions" in question for question in questions)
    
    def test_structure_section_content(self, report_service):
        """Test structuring of section content"""
        section_title = "Climate Change"
        content_parts = [
            "Organizations must report their greenhouse gas emissions.",
            "Scope 1, 2, and 3 emissions should be included."
        ]
        relevant_requirements = [
            {
                "requirement_id": "req_1",
                "requirement_text": "Report GHG emissions",
                "priority": "high"
            }
        ]
        
        structured_content = report_service._structure_section_content(
            section_title, content_parts, relevant_requirements
        )
        
        assert "## Climate Change" in structured_content
        assert "### Relevant Requirements" in structured_content
        assert "### Analysis and Guidance" in structured_content
        assert "greenhouse gas emissions" in structured_content
    
    @pytest.mark.asyncio
    async def test_generate_executive_summary(self, report_service):
        """Test executive summary generation"""
        mock_client_requirements = ClientRequirementsResponse(
            id="test_req_1",
            client_name="Test Client",
            requirements_text="Test requirements",
            upload_date=datetime.utcnow()
        )
        
        sections = [
            ReportSection(
                id="section_1",
                title="Test Section",
                content="This is test content for the section.",
                subsections=[],
                metadata={},
                sources=[]
            )
        ]
        
        # Mock RAG service response
        mock_rag_response = Mock()
        mock_rag_response.response_text = "This is a test executive summary."
        mock_rag_response.confidence_score = 0.8
        
        report_service.rag_service.generate_rag_response = AsyncMock(return_value=mock_rag_response)
        
        summary = await report_service._generate_executive_summary(
            mock_client_requirements, sections, AIModelType.OPENAI_GPT35
        )
        
        assert "This is a test executive summary." in summary
    
    @pytest.mark.asyncio
    async def test_generate_executive_summary_fallback(self, report_service):
        """Test executive summary generation with fallback"""
        mock_client_requirements = ClientRequirementsResponse(
            id="test_req_1",
            client_name="Test Client",
            requirements_text="Test requirements",
            upload_date=datetime.utcnow()
        )
        
        sections = [
            ReportSection(
                id="section_1",
                title="Test Section",
                content="Test content",
                subsections=[],
                metadata={},
                sources=[]
            )
        ]
        
        # Mock RAG service to fail
        report_service.rag_service.generate_rag_response = AsyncMock(side_effect=Exception("RAG failed"))
        
        summary = await report_service._generate_executive_summary(
            mock_client_requirements, sections, AIModelType.OPENAI_GPT35
        )
        
        assert "Test Client" in summary
        assert "Executive Summary" in summary
    
    @pytest.mark.asyncio
    async def test_generate_report_full_flow(self, report_service, mock_client_requirements):
        """Test full report generation flow"""
        # Mock dependencies
        report_service.client_requirements_service.get_client_requirements = Mock(
            return_value=mock_client_requirements
        )
        
        # Mock RAG responses
        mock_rag_response = Mock()
        mock_rag_response.response_text = "Test RAG response content"
        mock_rag_response.confidence_score = 0.7
        mock_rag_response.source_chunks = ["chunk_1", "chunk_2"]
        
        report_service.rag_service.generate_rag_response = AsyncMock(return_value=mock_rag_response)
        
        # Generate report
        report_content = await report_service.generate_report(
            requirements_id="test_req_1",
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            ai_model=AIModelType.OPENAI_GPT35,
            report_format=ReportFormat.STRUCTURED_TEXT
        )
        
        # Verify report structure
        assert isinstance(report_content, ReportContent)
        assert report_content.client_name == "Test Client"
        assert report_content.template_type == ReportTemplate.EU_ESRS_STANDARD
        assert report_content.schema_type == SchemaType.EU_ESRS_CSRD
        assert len(report_content.sections) > 0
        assert report_content.executive_summary is not None
    
    def test_format_report_markdown(self, report_service):
        """Test Markdown report formatting"""
        report_content = ReportContent(
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
                    sources=["source_1"]
                )
            ],
            executive_summary="Test executive summary",
            metadata={}
        )
        
        formatted = report_service.format_report(report_content, ReportFormat.MARKDOWN)
        
        assert "# Test Report" in formatted
        assert "**Client:** Test Client" in formatted
        assert "## Test Section" in formatted
        assert "Test content" in formatted
        assert "**Sources:**" in formatted
    
    def test_format_report_html(self, report_service):
        """Test HTML report formatting"""
        report_content = ReportContent(
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
            executive_summary="Test executive summary",
            metadata={}
        )
        
        formatted = report_service.format_report(report_content, ReportFormat.HTML)
        
        assert "<!DOCTYPE html>" in formatted
        assert "<h1>Test Report</h1>" in formatted
        assert "<strong>Client:</strong> Test Client" in formatted
        assert "Test content" in formatted
    
    def test_format_report_structured_text(self, report_service):
        """Test structured text report formatting"""
        report_content = ReportContent(
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
            executive_summary="Test executive summary",
            metadata={}
        )
        
        formatted = report_service.format_report(report_content, ReportFormat.STRUCTURED_TEXT)
        
        assert "SUSTAINABILITY REPORT: Test Report" in formatted
        assert "Client: Test Client" in formatted
        assert "1. TEST SECTION" in formatted
        assert "Test content" in formatted
    
    def test_get_report_metadata(self, report_service):
        """Test report metadata extraction"""
        report_content = ReportContent(
            title="Test Report",
            client_name="Test Client",
            generation_date=datetime.utcnow(),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=[
                ReportSection(
                    id="section_1",
                    title="Test Section",
                    content="Test content with some length to test statistics",
                    subsections=[
                        ReportSection(
                            id="subsection_1",
                            title="Test Subsection",
                            content="Subsection content",
                            subsections=[],
                            metadata={},
                            sources=["source_1", "source_2"]
                        )
                    ],
                    metadata={},
                    sources=["source_3"]
                )
            ],
            executive_summary="Test executive summary",
            metadata={"test_key": "test_value"}
        )
        
        metadata = report_service.get_report_metadata(report_content)
        
        assert metadata["title"] == "Test Report"
        assert metadata["client_name"] == "Test Client"
        assert metadata["template_type"] == "eu_esrs_standard"
        assert metadata["schema_type"] == "EU_ESRS_CSRD"
        
        stats = metadata["statistics"]
        assert stats["total_sections"] == 1
        assert stats["total_subsections"] == 1
        assert stats["total_sources"] == 3
        assert stats["total_content_length"] > 0
        assert stats["estimated_reading_time_minutes"] >= 1
    
    @patch('builtins.open')
    @patch('pathlib.Path.mkdir')
    def test_save_report(self, mock_mkdir, mock_open, report_service):
        """Test saving report to file"""
        report_content = ReportContent(
            title="Test Report",
            client_name="Test Client",
            generation_date=datetime.utcnow(),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=[],
            executive_summary="Test summary",
            metadata={}
        )
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = report_service.save_report(
            report_content, 
            "/test/path/report.md", 
            ReportFormat.MARKDOWN
        )
        
        assert result is True
        mock_mkdir.assert_called_once()
        mock_open.assert_called_once()
        mock_file.write.assert_called_once()


class TestReportSection:
    """Test cases for ReportSection data class"""
    
    def test_report_section_creation(self):
        """Test ReportSection creation and to_dict method"""
        subsection = ReportSection(
            id="sub_1",
            title="Subsection",
            content="Sub content",
            subsections=[],
            metadata={"type": "subsection"},
            sources=["source_1"]
        )
        
        section = ReportSection(
            id="section_1",
            title="Main Section",
            content="Main content",
            subsections=[subsection],
            metadata={"type": "main"},
            sources=["source_2", "source_3"]
        )
        
        section_dict = section.to_dict()
        
        assert section_dict["id"] == "section_1"
        assert section_dict["title"] == "Main Section"
        assert section_dict["content"] == "Main content"
        assert len(section_dict["subsections"]) == 1
        assert section_dict["subsections"][0]["id"] == "sub_1"
        assert len(section_dict["sources"]) == 2


class TestReportContent:
    """Test cases for ReportContent data class"""
    
    def test_report_content_creation(self):
        """Test ReportContent creation and to_dict method"""
        section = ReportSection(
            id="section_1",
            title="Test Section",
            content="Test content",
            subsections=[],
            metadata={},
            sources=[]
        )
        
        report_content = ReportContent(
            title="Test Report",
            client_name="Test Client",
            generation_date=datetime(2024, 1, 1, 12, 0, 0),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=[section],
            executive_summary="Test summary",
            metadata={"version": "1.0"}
        )
        
        content_dict = report_content.to_dict()
        
        assert content_dict["title"] == "Test Report"
        assert content_dict["client_name"] == "Test Client"
        assert content_dict["generation_date"] == "2024-01-01T12:00:00"
        assert content_dict["template_type"] == "eu_esrs_standard"
        assert content_dict["schema_type"] == "EU_ESRS_CSRD"
        assert len(content_dict["sections"]) == 1
        assert content_dict["executive_summary"] == "Test summary"
        assert content_dict["metadata"]["version"] == "1.0"


@pytest.mark.asyncio
class TestReportServiceIntegration:
    """Integration tests for ReportService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for integration tests"""
        return Mock(spec=Session)
    
    @pytest.mark.asyncio
    async def test_report_generation_consistency(self, mock_db_session):
        """Test that report generation produces consistent results"""
        with patch('app.services.report_service.ClientRequirementsService'), \
             patch('app.services.report_service.RAGService'):
            
            service = ReportService(mock_db_session)
            
            # Mock client requirements
            mock_requirements = ClientRequirementsResponse(
                id="test_req_1",
                client_name="Consistency Test Client",
                requirements_text="Test requirements for consistency",
                upload_date=datetime.utcnow(),
                processed_requirements=[
                    ProcessedRequirement(
                        requirement_id="req_1",
                        requirement_text="Climate reporting requirement",
                        mapped_elements=["EU_ESRS_E1_1"],
                        priority="high"
                    )
                ]
            )
            
            service.client_requirements_service.get_client_requirements = Mock(
                return_value=mock_requirements
            )
            
            # Mock consistent RAG responses
            mock_rag_response = Mock()
            mock_rag_response.response_text = "Consistent RAG response for testing"
            mock_rag_response.confidence_score = 0.8
            mock_rag_response.source_chunks = ["chunk_1"]
            
            service.rag_service.generate_rag_response = AsyncMock(return_value=mock_rag_response)
            
            # Generate multiple reports with same parameters
            report1 = await service.generate_report(
                requirements_id="test_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            report2 = await service.generate_report(
                requirements_id="test_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Verify consistency (structure should be the same)
            assert report1.client_name == report2.client_name
            assert report1.template_type == report2.template_type
            assert report1.schema_type == report2.schema_type
            assert len(report1.sections) == len(report2.sections)
            
            # Section titles should be consistent
            for i, (section1, section2) in enumerate(zip(report1.sections, report2.sections)):
                assert section1.title == section2.title
                assert section1.id == section2.id
    
    @pytest.mark.asyncio
    async def test_template_population_accuracy(self, mock_db_session):
        """Test that templates are populated accurately based on requirements"""
        with patch('app.services.report_service.ClientRequirementsService'), \
             patch('app.services.report_service.RAGService'):
            
            service = ReportService(mock_db_session)
            
            # Create requirements with specific climate focus
            climate_requirements = ClientRequirementsResponse(
                id="climate_req_1",
                client_name="Climate Focused Client",
                requirements_text="Climate change and carbon emissions reporting",
                upload_date=datetime.utcnow(),
                processed_requirements=[
                    ProcessedRequirement(
                        requirement_id="climate_req_1",
                        requirement_text="Report greenhouse gas emissions across all scopes",
                        mapped_elements=["EU_ESRS_E1_1", "EU_ESRS_E1_2"],
                        priority="high"
                    ),
                    ProcessedRequirement(
                        requirement_id="climate_req_2",
                        requirement_text="Disclose climate transition plan",
                        mapped_elements=["EU_ESRS_E1_3"],
                        priority="medium"
                    )
                ]
            )
            
            service.client_requirements_service.get_client_requirements = Mock(
                return_value=climate_requirements
            )
            
            # Mock RAG responses that should be climate-focused
            def mock_rag_response_generator(question, **kwargs):
                mock_response = Mock()
                if "climate" in question.lower() or "e1" in question.lower():
                    mock_response.response_text = f"Climate-specific response for: {question[:50]}..."
                    mock_response.confidence_score = 0.9
                else:
                    mock_response.response_text = f"General response for: {question[:50]}..."
                    mock_response.confidence_score = 0.5
                mock_response.source_chunks = ["climate_chunk_1"]
                return mock_response
            
            service.rag_service.generate_rag_response = AsyncMock(side_effect=mock_rag_response_generator)
            
            # Generate report
            report = await service.generate_report(
                requirements_id="climate_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Verify climate-focused content appears in relevant sections
            climate_section = None
            for section in report.sections:
                if "climate" in section.title.lower() or section.id == "e1_climate":
                    climate_section = section
                    break
            
            # Should have climate-related content
            if climate_section:
                assert "climate" in climate_section.content.lower() or "greenhouse gas" in climate_section.content.lower()
            
            # Executive summary should mention climate
            assert "climate" in report.executive_summary.lower() or "Climate Focused Client" in report.executive_summary
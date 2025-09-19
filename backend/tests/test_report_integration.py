"""
Integration tests for Report Generation System
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.report_service import (
    ReportService, ReportTemplate, ReportFormat, ReportTemplateManager
)
from app.services.client_requirements_service import ClientRequirementsService
from app.services.rag_service import RAGService, AIModelType
from app.models.schemas import (
    ClientRequirementsResponse, SchemaMapping, ProcessedRequirement, 
    SchemaType, RAGResponseResponse
)


@pytest.mark.asyncio
class TestReportGenerationIntegration:
    """Integration tests for complete report generation workflow"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_client_requirements(self):
        """Sample client requirements for testing"""
        return ClientRequirementsResponse(
            id="integration_req_1",
            client_name="Integration Test Corporation",
            requirements_text="""
            Our organization needs to comply with EU CSRD requirements for the following areas:
            1. Climate change reporting including Scope 1, 2, and 3 emissions
            2. Water usage and conservation measures
            3. Biodiversity impact assessment
            4. Workforce diversity and inclusion metrics
            5. Supply chain sustainability practices
            """,
            upload_date=datetime.utcnow(),
            schema_mappings=[
                SchemaMapping(
                    requirement_id="req_1",
                    schema_element_id="EU_ESRS_E1_1",
                    confidence_score=0.9
                ),
                SchemaMapping(
                    requirement_id="req_2", 
                    schema_element_id="EU_ESRS_E3_1",
                    confidence_score=0.8
                ),
                SchemaMapping(
                    requirement_id="req_3",
                    schema_element_id="EU_ESRS_E4_1", 
                    confidence_score=0.7
                ),
                SchemaMapping(
                    requirement_id="req_4",
                    schema_element_id="EU_ESRS_S1_1",
                    confidence_score=0.8
                ),
                SchemaMapping(
                    requirement_id="req_5",
                    schema_element_id="EU_ESRS_S2_1",
                    confidence_score=0.6
                )
            ],
            processed_requirements=[
                ProcessedRequirement(
                    requirement_id="req_1",
                    requirement_text="Climate change reporting including Scope 1, 2, and 3 emissions",
                    mapped_elements=["EU_ESRS_E1_1"],
                    priority="high"
                ),
                ProcessedRequirement(
                    requirement_id="req_2",
                    requirement_text="Water usage and conservation measures",
                    mapped_elements=["EU_ESRS_E3_1"],
                    priority="medium"
                ),
                ProcessedRequirement(
                    requirement_id="req_3",
                    requirement_text="Biodiversity impact assessment",
                    mapped_elements=["EU_ESRS_E4_1"],
                    priority="medium"
                ),
                ProcessedRequirement(
                    requirement_id="req_4",
                    requirement_text="Workforce diversity and inclusion metrics",
                    mapped_elements=["EU_ESRS_S1_1"],
                    priority="high"
                ),
                ProcessedRequirement(
                    requirement_id="req_5",
                    requirement_text="Supply chain sustainability practices",
                    mapped_elements=["EU_ESRS_S2_1"],
                    priority="low"
                )
            ]
        )
    
    @pytest.fixture
    def mock_rag_responses(self):
        """Mock RAG responses for different question types"""
        def create_rag_response(question: str) -> RAGResponseResponse:
            """Create contextual RAG response based on question content"""
            response_id = f"rag_{hash(question) % 10000}"
            
            if "climate" in question.lower() or "emission" in question.lower():
                return RAGResponseResponse(
                    id=response_id,
                    query=question,
                    response_text="""
                    Organizations must report greenhouse gas emissions across all three scopes according to ESRS E1. 
                    Scope 1 emissions include direct emissions from owned or controlled sources. 
                    Scope 2 emissions are indirect emissions from purchased energy. 
                    Scope 3 emissions cover all other indirect emissions in the value chain.
                    Companies should establish science-based targets and develop transition plans.
                    """,
                    model_used="openai_gpt35",
                    confidence_score=0.9,
                    source_chunks=["climate_chunk_1", "climate_chunk_2"],
                    generation_timestamp=datetime.utcnow()
                )
            elif "water" in question.lower():
                return RAGResponseResponse(
                    id=response_id,
                    query=question,
                    response_text="""
                    Water management under ESRS E3 requires disclosure of water consumption, 
                    water sources, and water-related risks. Organizations should report on 
                    water efficiency measures, recycling initiatives, and impacts on water-stressed areas.
                    """,
                    model_used="openai_gpt35",
                    confidence_score=0.8,
                    source_chunks=["water_chunk_1"],
                    generation_timestamp=datetime.utcnow()
                )
            elif "biodiversity" in question.lower():
                return RAGResponseResponse(
                    id=response_id,
                    query=question,
                    response_text="""
                    Biodiversity reporting under ESRS E4 covers impacts on ecosystems and species.
                    Organizations should assess their dependencies on biodiversity and ecosystem services,
                    identify material impacts, and report on conservation measures.
                    """,
                    model_used="openai_gpt35",
                    confidence_score=0.7,
                    source_chunks=["biodiversity_chunk_1"],
                    generation_timestamp=datetime.utcnow()
                )
            elif "workforce" in question.lower() or "diversity" in question.lower():
                return RAGResponseResponse(
                    id=response_id,
                    query=question,
                    response_text="""
                    Workforce reporting under ESRS S1 includes diversity metrics, working conditions,
                    and employee rights. Organizations should disclose gender pay gaps, 
                    diversity statistics, health and safety metrics, and training programs.
                    """,
                    model_used="openai_gpt35",
                    confidence_score=0.8,
                    source_chunks=["workforce_chunk_1"],
                    generation_timestamp=datetime.utcnow()
                )
            elif "supply chain" in question.lower():
                return RAGResponseResponse(
                    id=response_id,
                    query=question,
                    response_text="""
                    Supply chain sustainability under ESRS S2 covers workers in the value chain.
                    Organizations should assess and report on working conditions, human rights,
                    and sustainability practices throughout their supply chain.
                    """,
                    model_used="openai_gpt35",
                    confidence_score=0.6,
                    source_chunks=["supply_chain_chunk_1"],
                    generation_timestamp=datetime.utcnow()
                )
            else:
                return RAGResponseResponse(
                    id=response_id,
                    query=question,
                    response_text=f"""
                    This is a general response for the question: {question[:100]}...
                    Organizations should follow applicable ESRS standards and ensure comprehensive disclosure.
                    """,
                    model_used="openai_gpt35",
                    confidence_score=0.5,
                    source_chunks=["general_chunk_1"],
                    generation_timestamp=datetime.utcnow()
                )
        
        return create_rag_response
    
    @pytest.mark.asyncio
    async def test_complete_report_generation_workflow(
        self, 
        mock_db_session, 
        sample_client_requirements, 
        mock_rag_responses
    ):
        """Test complete report generation from requirements to formatted output"""
        
        # Setup mocked services
        with patch('app.services.report_service.ClientRequirementsService') as mock_client_service_class, \
             patch('app.services.report_service.RAGService') as mock_rag_service_class:
            
            # Mock client requirements service
            mock_client_service = Mock()
            mock_client_service.get_client_requirements.return_value = sample_client_requirements
            mock_client_service_class.return_value = mock_client_service
            
            # Mock RAG service
            mock_rag_service = Mock()
            mock_rag_service.generate_rag_response = AsyncMock(side_effect=mock_rag_responses)
            mock_rag_service_class.return_value = mock_rag_service
            
            # Create report service
            report_service = ReportService(mock_db_session)
            
            # Generate report
            report_content = await report_service.generate_report(
                requirements_id="integration_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35,
                report_format=ReportFormat.STRUCTURED_TEXT
            )
            
            # Verify report structure
            assert report_content.client_name == "Integration Test Corporation"
            assert report_content.template_type == ReportTemplate.EU_ESRS_STANDARD
            assert report_content.schema_type == SchemaType.EU_ESRS_CSRD
            assert len(report_content.sections) > 0
            
            # Verify executive summary exists
            assert report_content.executive_summary is not None
            assert len(report_content.executive_summary) > 0
            
            # Verify sections contain relevant content
            section_titles = [section.title for section in report_content.sections]
            assert any("Environmental" in title for title in section_titles)
            assert any("Social" in title for title in section_titles)
            
            # Check that climate section has climate-related content
            climate_section = None
            for section in report_content.sections:
                if "climate" in section.title.lower() or any("climate" in sub.title.lower() for sub in section.subsections):
                    climate_section = section
                    break
                for subsection in section.subsections:
                    if "climate" in subsection.title.lower():
                        climate_section = subsection
                        break
            
            if climate_section:
                assert "emission" in climate_section.content.lower() or "greenhouse gas" in climate_section.content.lower()
    
    @pytest.mark.asyncio
    async def test_report_generation_with_different_templates(
        self, 
        mock_db_session, 
        sample_client_requirements, 
        mock_rag_responses
    ):
        """Test report generation with different template types"""
        
        with patch('app.services.report_service.ClientRequirementsService') as mock_client_service_class, \
             patch('app.services.report_service.RAGService') as mock_rag_service_class:
            
            # Setup mocks
            mock_client_service = Mock()
            mock_client_service.get_client_requirements.return_value = sample_client_requirements
            mock_client_service_class.return_value = mock_client_service
            
            mock_rag_service = Mock()
            mock_rag_service.generate_rag_response = AsyncMock(side_effect=mock_rag_responses)
            mock_rag_service_class.return_value = mock_rag_service
            
            report_service = ReportService(mock_db_session)
            
            # Test EU ESRS template
            eu_report = await report_service.generate_report(
                requirements_id="integration_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Test UK SRD template
            uk_report = await report_service.generate_report(
                requirements_id="integration_req_1",
                template_type=ReportTemplate.UK_SRD_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Test Gap Analysis template
            gap_report = await report_service.generate_report(
                requirements_id="integration_req_1",
                template_type=ReportTemplate.GAP_ANALYSIS,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Verify different templates produce different structures
            assert eu_report.template_type != uk_report.template_type
            assert uk_report.template_type != gap_report.template_type
            
            # Verify all reports have content
            assert len(eu_report.sections) > 0
            assert len(uk_report.sections) > 0
            assert len(gap_report.sections) > 0
            
            # Verify template-specific sections
            eu_section_titles = [s.title for s in eu_report.sections]
            uk_section_titles = [s.title for s in uk_report.sections]
            gap_section_titles = [s.title for s in gap_report.sections]
            
            # EU report should have environmental/social sections
            assert any("Environmental" in title or "Social" in title for title in eu_section_titles)
            
            # UK report should have mandatory/voluntary disclosure sections
            assert any("Mandatory" in title or "Compliance" in title for title in uk_section_titles)
            
            # Gap report should have gap analysis sections
            assert any("Gap" in title or "Coverage" in title for title in gap_section_titles)
    
    @pytest.mark.asyncio
    async def test_report_formatting_consistency(
        self, 
        mock_db_session, 
        sample_client_requirements, 
        mock_rag_responses
    ):
        """Test that different output formats maintain content consistency"""
        
        with patch('app.services.report_service.ClientRequirementsService') as mock_client_service_class, \
             patch('app.services.report_service.RAGService') as mock_rag_service_class:
            
            # Setup mocks
            mock_client_service = Mock()
            mock_client_service.get_client_requirements.return_value = sample_client_requirements
            mock_client_service_class.return_value = mock_client_service
            
            mock_rag_service = Mock()
            mock_rag_service.generate_rag_response = AsyncMock(side_effect=mock_rag_responses)
            mock_rag_service_class.return_value = mock_rag_service
            
            report_service = ReportService(mock_db_session)
            
            # Generate report content
            report_content = await report_service.generate_report(
                requirements_id="integration_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Format in different formats
            markdown_output = report_service.format_report(report_content, ReportFormat.MARKDOWN)
            html_output = report_service.format_report(report_content, ReportFormat.HTML)
            text_output = report_service.format_report(report_content, ReportFormat.STRUCTURED_TEXT)
            
            # Verify all formats contain core content
            client_name = "Integration Test Corporation"
            
            assert client_name in markdown_output
            assert client_name in html_output
            assert client_name in text_output
            
            # Verify format-specific elements
            assert "# " in markdown_output  # Markdown headers
            assert "<!DOCTYPE html>" in html_output  # HTML structure
            assert "=" in text_output  # Text formatting
            
            # Verify section content is preserved across formats
            first_section_title = report_content.sections[0].title if report_content.sections else "Test"
            
            assert first_section_title in markdown_output
            assert first_section_title in html_output
            assert first_section_title.upper() in text_output  # Text format uses uppercase
    
    @pytest.mark.asyncio
    async def test_report_generation_error_handling(
        self, 
        mock_db_session, 
        sample_client_requirements
    ):
        """Test error handling during report generation"""
        
        with patch('app.services.report_service.ClientRequirementsService') as mock_client_service_class, \
             patch('app.services.report_service.RAGService') as mock_rag_service_class:
            
            # Setup mocks
            mock_client_service = Mock()
            mock_client_service.get_client_requirements.return_value = sample_client_requirements
            mock_client_service_class.return_value = mock_client_service
            
            # Mock RAG service to fail
            mock_rag_service = Mock()
            mock_rag_service.generate_rag_response = AsyncMock(side_effect=Exception("RAG service failed"))
            mock_rag_service_class.return_value = mock_rag_service
            
            report_service = ReportService(mock_db_session)
            
            # Generate report (should handle RAG failures gracefully)
            report_content = await report_service.generate_report(
                requirements_id="integration_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Report should still be generated with fallback content
            assert report_content is not None
            assert report_content.client_name == "Integration Test Corporation"
            assert len(report_content.sections) > 0
            
            # Sections should have fallback content
            for section in report_content.sections:
                assert section.content is not None
                assert len(section.content) > 0
    
    @pytest.mark.asyncio
    async def test_report_metadata_accuracy(
        self, 
        mock_db_session, 
        sample_client_requirements, 
        mock_rag_responses
    ):
        """Test that report metadata accurately reflects content"""
        
        with patch('app.services.report_service.ClientRequirementsService') as mock_client_service_class, \
             patch('app.services.report_service.RAGService') as mock_rag_service_class:
            
            # Setup mocks
            mock_client_service = Mock()
            mock_client_service.get_client_requirements.return_value = sample_client_requirements
            mock_client_service_class.return_value = mock_client_service
            
            mock_rag_service = Mock()
            mock_rag_service.generate_rag_response = AsyncMock(side_effect=mock_rag_responses)
            mock_rag_service_class.return_value = mock_rag_service
            
            report_service = ReportService(mock_db_session)
            
            # Generate report
            report_content = await report_service.generate_report(
                requirements_id="integration_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            # Get metadata
            metadata = report_service.get_report_metadata(report_content)
            
            # Verify metadata accuracy
            assert metadata["client_name"] == "Integration Test Corporation"
            assert metadata["template_type"] == "eu_esrs_standard"
            assert metadata["schema_type"] == "EU_ESRS_CSRD"
            
            # Verify statistics
            stats = metadata["statistics"]
            assert stats["total_sections"] == len(report_content.sections)
            
            # Calculate expected subsections
            expected_subsections = sum(len(section.subsections) for section in report_content.sections)
            assert stats["total_subsections"] == expected_subsections
            
            # Calculate expected sources
            expected_sources = sum(len(section.sources) for section in report_content.sections)
            for section in report_content.sections:
                expected_sources += sum(len(sub.sources) for sub in section.subsections)
            assert stats["total_sources"] == expected_sources
            
            # Verify content length calculation
            expected_length = len(report_content.executive_summary)
            for section in report_content.sections:
                expected_length += len(section.content)
                for subsection in section.subsections:
                    expected_length += len(subsection.content)
            assert stats["total_content_length"] == expected_length
    
    def test_template_manager_integration(self):
        """Test template manager integration with report service"""
        
        template_manager = ReportTemplateManager()
        
        # Test all default templates are loadable
        for template_type in ReportTemplate:
            template_config = template_manager.get_template(template_type)
            
            if template_type != ReportTemplate.CUSTOM_TEMPLATE:  # Custom template may be empty
                assert template_config is not None
                assert "name" in template_config
                assert "sections" in template_config
                
                # Verify section structure
                for section in template_config["sections"]:
                    assert "id" in section
                    assert "title" in section
                    assert "required" in section
        
        # Test available templates list
        available_templates = template_manager.get_available_templates()
        assert len(available_templates) >= 3  # At least EU, UK, Gap Analysis
        
        for template in available_templates:
            assert "type" in template
            assert "name" in template
            assert "description" in template
    
    @pytest.mark.asyncio
    async def test_performance_with_large_requirements(
        self, 
        mock_db_session, 
        mock_rag_responses
    ):
        """Test report generation performance with large number of requirements"""
        
        # Create large requirements set
        large_requirements = ClientRequirementsResponse(
            id="large_req_1",
            client_name="Large Corporation",
            requirements_text="Large set of requirements for performance testing",
            upload_date=datetime.utcnow(),
            processed_requirements=[
                ProcessedRequirement(
                    requirement_id=f"req_{i}",
                    requirement_text=f"Requirement {i} for performance testing with detailed description",
                    mapped_elements=[f"EU_ESRS_E{(i % 5) + 1}_{(i % 3) + 1}"],
                    priority="medium"
                )
                for i in range(50)  # 50 requirements
            ]
        )
        
        with patch('app.services.report_service.ClientRequirementsService') as mock_client_service_class, \
             patch('app.services.report_service.RAGService') as mock_rag_service_class:
            
            # Setup mocks
            mock_client_service = Mock()
            mock_client_service.get_client_requirements.return_value = large_requirements
            mock_client_service_class.return_value = mock_client_service
            
            mock_rag_service = Mock()
            mock_rag_service.generate_rag_response = AsyncMock(side_effect=mock_rag_responses)
            mock_rag_service_class.return_value = mock_rag_service
            
            report_service = ReportService(mock_db_session)
            
            # Measure generation time
            start_time = datetime.utcnow()
            
            report_content = await report_service.generate_report(
                requirements_id="large_req_1",
                template_type=ReportTemplate.EU_ESRS_STANDARD,
                ai_model=AIModelType.OPENAI_GPT35
            )
            
            end_time = datetime.utcnow()
            generation_time = (end_time - start_time).total_seconds()
            
            # Verify report was generated successfully
            assert report_content is not None
            assert report_content.client_name == "Large Corporation"
            assert len(report_content.sections) > 0
            
            # Performance should be reasonable (adjust threshold as needed)
            assert generation_time < 60  # Should complete within 60 seconds
            
            # Verify content quality isn't degraded
            assert len(report_content.executive_summary) > 0
            for section in report_content.sections:
                assert len(section.content) > 0
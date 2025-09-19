#!/usr/bin/env python3
"""
Simple test script for Report Generation functionality
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.report_service import (
    ReportService, ReportTemplateManager, ReportTemplate, ReportFormat
)
from app.services.rag_service import AIModelType
from app.models.schemas import (
    ClientRequirementsResponse, SchemaMapping, ProcessedRequirement, SchemaType
)
from unittest.mock import Mock, AsyncMock


def test_template_manager():
    """Test ReportTemplateManager functionality"""
    print("Testing ReportTemplateManager...")
    
    manager = ReportTemplateManager()
    
    # Test getting available templates
    templates = manager.get_available_templates()
    print(f"Available templates: {len(templates)}")
    for template in templates:
        print(f"  - {template['type']}: {template['name']}")
    
    # Test getting specific template
    eu_template = manager.get_template(ReportTemplate.EU_ESRS_STANDARD)
    print(f"EU ESRS template sections: {len(eu_template.get('sections', []))}")
    
    uk_template = manager.get_template(ReportTemplate.UK_SRD_STANDARD)
    print(f"UK SRD template sections: {len(uk_template.get('sections', []))}")
    
    print("✓ ReportTemplateManager tests passed\n")


def create_sample_requirements():
    """Create sample client requirements for testing"""
    return ClientRequirementsResponse(
        id="test_req_1",
        client_name="Test Corporation",
        requirements_text="""
        Our organization needs to report on:
        1. Climate change and carbon emissions
        2. Water usage and conservation
        3. Workforce diversity metrics
        4. Supply chain sustainability
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
            )
        ],
        processed_requirements=[
            {
                "requirement_id": "req_1",
                "requirement_text": "Climate change and carbon emissions reporting",
                "mapped_elements": ["EU_ESRS_E1_1"],
                "priority": "high"
            },
            {
                "requirement_id": "req_2",
                "requirement_text": "Water usage and conservation measures",
                "mapped_elements": ["EU_ESRS_E3_1"],
                "priority": "medium"
            }
        ]
    )


def create_mock_rag_response(question: str):
    """Create mock RAG response based on question"""
    from app.models.schemas import RAGResponseResponse
    
    if "climate" in question.lower():
        content = "Organizations must report greenhouse gas emissions across Scope 1, 2, and 3 according to ESRS E1 standards."
    elif "water" in question.lower():
        content = "Water management requires disclosure of consumption, sources, and conservation measures under ESRS E3."
    elif "workforce" in question.lower():
        content = "Workforce reporting includes diversity metrics, working conditions, and employee rights under ESRS S1."
    else:
        content = f"General sustainability guidance for: {question[:50]}..."
    
    return RAGResponseResponse(
        id=f"mock_rag_{hash(question) % 1000}",
        query=question,
        response_text=content,
        model_used="mock_model",
        confidence_score=0.8,
        source_chunks=["mock_chunk_1"],
        generation_timestamp=datetime.utcnow()
    )


async def test_report_service():
    """Test ReportService functionality"""
    print("Testing ReportService...")
    
    # Create mock database session
    mock_db = Mock()
    
    # Create report service with mocked dependencies
    from unittest.mock import patch
    
    with patch('app.services.report_service.ClientRequirementsService') as mock_client_service_class, \
         patch('app.services.report_service.RAGService') as mock_rag_service_class:
        
        # Setup mock client requirements service
        mock_client_service = Mock()
        mock_client_service.get_client_requirements.return_value = create_sample_requirements()
        mock_client_service_class.return_value = mock_client_service
        
        # Setup mock RAG service
        mock_rag_service = Mock()
        
        async def mock_rag_response_wrapper(question, **kwargs):
            return create_mock_rag_response(question)
        
        mock_rag_service.generate_rag_response = AsyncMock(side_effect=mock_rag_response_wrapper)
        mock_rag_service_class.return_value = mock_rag_service
        
        # Create report service
        report_service = ReportService(mock_db)
        
        print("Generating EU ESRS report...")
        eu_report = await report_service.generate_report(
            requirements_id="test_req_1",
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            ai_model=AIModelType.OPENAI_GPT35,
            report_format=ReportFormat.STRUCTURED_TEXT
        )
        
        print(f"✓ EU ESRS report generated:")
        print(f"  - Title: {eu_report.title}")
        print(f"  - Client: {eu_report.client_name}")
        print(f"  - Sections: {len(eu_report.sections)}")
        print(f"  - Executive summary length: {len(eu_report.executive_summary)}")
        
        print("\nGenerating UK SRD report...")
        uk_report = await report_service.generate_report(
            requirements_id="test_req_1",
            template_type=ReportTemplate.UK_SRD_STANDARD,
            ai_model=AIModelType.OPENAI_GPT35,
            report_format=ReportFormat.MARKDOWN
        )
        
        print(f"✓ UK SRD report generated:")
        print(f"  - Title: {uk_report.title}")
        print(f"  - Sections: {len(uk_report.sections)}")
        
        # Test report formatting
        print("\nTesting report formatting...")
        
        markdown_output = report_service.format_report(eu_report, ReportFormat.MARKDOWN)
        html_output = report_service.format_report(eu_report, ReportFormat.HTML)
        text_output = report_service.format_report(eu_report, ReportFormat.STRUCTURED_TEXT)
        
        print(f"✓ Markdown format: {len(markdown_output)} characters")
        print(f"✓ HTML format: {len(html_output)} characters")
        print(f"✓ Text format: {len(text_output)} characters")
        
        # Test metadata extraction
        metadata = report_service.get_report_metadata(eu_report)
        print(f"\n✓ Report metadata:")
        print(f"  - Total sections: {metadata['statistics']['total_sections']}")
        print(f"  - Total content length: {metadata['statistics']['total_content_length']}")
        print(f"  - Reading time: {metadata['statistics']['estimated_reading_time_minutes']} minutes")
        
        print("\n✓ ReportService tests passed\n")


def test_report_formatting():
    """Test report formatting functionality"""
    print("Testing report formatting...")
    
    from app.services.report_service import ReportContent, ReportSection
    from unittest.mock import patch
    
    # Create sample report content
    section = ReportSection(
        id="test_section",
        title="Test Section",
        content="This is test content for the section with **bold text** and regular text.",
        subsections=[],
        metadata={"test": True},
        sources=["source1.pdf", "source2.pdf"]
    )
    
    report_content = ReportContent(
        title="Test Report",
        client_name="Test Client",
        generation_date=datetime.utcnow(),
        template_type=ReportTemplate.EU_ESRS_STANDARD,
        schema_type=SchemaType.EU_ESRS_CSRD,
        sections=[section],
        executive_summary="This is a test executive summary.",
        metadata={"version": "1.0"}
    )
    
    # Create mock report service for formatting
    mock_db = Mock()
    
    with patch('app.services.report_service.ClientRequirementsService'), \
         patch('app.services.report_service.RAGService'):
        
        report_service = ReportService(mock_db)
        
        # Test different formats
        markdown = report_service.format_report(report_content, ReportFormat.MARKDOWN)
        html = report_service.format_report(report_content, ReportFormat.HTML)
        text = report_service.format_report(report_content, ReportFormat.STRUCTURED_TEXT)
        
        # Verify format-specific elements
        assert "# Test Report" in markdown
        assert "<!DOCTYPE html>" in html
        assert "SUSTAINABILITY REPORT" in text
        
        print("✓ Markdown formatting works")
        print("✓ HTML formatting works")
        print("✓ Text formatting works")
        
        # Test content preservation
        assert "Test Client" in markdown
        assert "Test Client" in html
        assert "Test Client" in text
        
        print("✓ Content preservation across formats works")
        
        print("✓ Report formatting tests passed\n")


def test_section_content_generation():
    """Test section content generation logic"""
    print("Testing section content generation...")
    
    from unittest.mock import patch
    mock_db = Mock()
    
    with patch('app.services.report_service.ClientRequirementsService'), \
         patch('app.services.report_service.RAGService'):
        
        report_service = ReportService(mock_db)
        
        # Test finding relevant requirements
        sample_requirements = create_sample_requirements()
        
        climate_reqs = report_service._find_relevant_requirements(
            "e1_climate", sample_requirements
        )
        print(f"✓ Found {len(climate_reqs)} climate-related requirements")
        
        water_reqs = report_service._find_relevant_requirements(
            "e3_water", sample_requirements
        )
        print(f"✓ Found {len(water_reqs)} water-related requirements")
        
        # Test question generation
        section_config = {
            "id": "e1_climate",
            "title": "Climate Change",
            "description": "Climate change reporting requirements"
        }
        
        questions = report_service._generate_section_questions(
            section_config, climate_reqs
        )
        print(f"✓ Generated {len(questions)} questions for climate section")
        
        # Test content structuring
        content_parts = [
            "Organizations must report greenhouse gas emissions.",
            "Scope 1, 2, and 3 emissions should be included."
        ]
        
        structured_content = report_service._structure_section_content(
            "Climate Change", content_parts, climate_reqs
        )
        
        assert "## Climate Change" in structured_content
        assert "### Relevant Requirements" in structured_content
        assert "### Analysis and Guidance" in structured_content
        
        print("✓ Content structuring works correctly")
        
        print("✓ Section content generation tests passed\n")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("REPORT GENERATION SYSTEM - SIMPLE TESTS")
    print("=" * 60)
    print()
    
    try:
        # Test template manager
        test_template_manager()
        
        # Test report service
        await test_report_service()
        
        # Test formatting
        test_report_formatting()
        
        # Test section generation
        test_section_content_generation()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
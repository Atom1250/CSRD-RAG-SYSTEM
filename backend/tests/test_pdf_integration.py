"""
Integration tests for PDF generation functionality
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.database import get_db
from app.models.schemas import SchemaType
from app.services.report_service import ReportContent, ReportSection, ReportTemplate
from app.services.pdf_service import PDFService


class TestPDFIntegration:
    """Integration tests for PDF generation with API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def sample_requirements_id(self):
        """Sample requirements ID for testing"""
        return "test_req_123"
    
    @pytest.fixture
    def mock_report_content(self):
        """Mock report content for testing"""
        sections = [
            ReportSection(
                id="executive_summary",
                title="Executive Summary",
                content="Comprehensive sustainability analysis for the organization.",
                subsections=[],
                metadata={"required": True},
                sources=["Regulatory Document 1", "Best Practices Guide"]
            ),
            ReportSection(
                id="environmental_standards",
                title="Environmental Standards",
                content="Environmental compliance assessment and recommendations.",
                subsections=[
                    ReportSection(
                        id="e1_climate",
                        title="E1 - Climate Change",
                        content="Climate change mitigation strategies and performance.",
                        subsections=[],
                        metadata={},
                        sources=["Climate Guidelines"]
                    )
                ],
                metadata={"required": True},
                sources=["Environmental Regulations"]
            )
        ]
        
        return ReportContent(
            title="Integration Test Sustainability Report",
            client_name="Test Integration Corp",
            generation_date=datetime(2024, 2, 20, 15, 45, 0),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=sections,
            executive_summary="This integration test report validates PDF generation capabilities.",
            metadata={
                "requirements_id": "test_req_123",
                "ai_model_used": "openai_gpt35",
                "generation_timestamp": "2024-02-20T15:45:00"
            }
        )
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_generate_pdf_report_endpoint(self, mock_report_service_class, mock_get_db, 
                                        client, mock_db_session, sample_requirements_id, 
                                        mock_report_content):
        """Test PDF generation endpoint"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_report_service = Mock()
        mock_report_service_class.return_value = mock_report_service
        
        # Mock PDF generation
        pdf_bytes = b"%PDF-1.4\nTest PDF content for integration testing"
        mock_report_service.generate_complete_report_with_pdf = AsyncMock(
            return_value=(mock_report_content, pdf_bytes)
        )
        mock_report_service.validate_pdf_quality.return_value = {
            "is_valid_pdf": True,
            "quality_score": 0.85,
            "file_size_bytes": len(pdf_bytes),
            "issues": []
        }
        
        # Make request
        response = client.post(
            f"/reports/generate-pdf?requirements_id={sample_requirements_id}&download=false"
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["pdf_generated"] is True
        assert data["pdf_size_bytes"] == len(pdf_bytes)
        assert "validation_results" in data
        assert data["validation_results"]["is_valid_pdf"] is True
        assert "report_metadata" in data
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_generate_pdf_report_download(self, mock_report_service_class, mock_get_db,
                                        client, mock_db_session, sample_requirements_id,
                                        mock_report_content):
        """Test PDF generation with download response"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_report_service = Mock()
        mock_report_service_class.return_value = mock_report_service
        
        # Mock PDF generation
        pdf_bytes = b"%PDF-1.4\nTest PDF content for download testing"
        mock_report_service.generate_complete_report_with_pdf = AsyncMock(
            return_value=(mock_report_content, pdf_bytes)
        )
        mock_report_service.validate_pdf_quality.return_value = {
            "is_valid_pdf": True,
            "quality_score": 0.90,
            "issues": []
        }
        
        # Make request with download=true
        response = client.post(
            f"/reports/generate-pdf?requirements_id={sample_requirements_id}&download=true"
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert response.content == pdf_bytes
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_generate_complete_report_with_pdf(self, mock_report_service_class, mock_get_db,
                                             client, mock_db_session, sample_requirements_id,
                                             mock_report_content):
        """Test complete report generation with PDF"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_report_service = Mock()
        mock_report_service_class.return_value = mock_report_service
        
        # Mock report generation
        pdf_bytes = b"%PDF-1.4\nComplete report PDF content"
        mock_report_service.generate_complete_report_with_pdf = AsyncMock(
            return_value=(mock_report_content, pdf_bytes)
        )
        mock_report_service.format_report.return_value = "Formatted report text content"
        mock_report_service.get_report_metadata.return_value = {
            "title": mock_report_content.title,
            "client_name": mock_report_content.client_name,
            "statistics": {"total_sections": 2}
        }
        mock_report_service.validate_pdf_quality.return_value = {
            "is_valid_pdf": True,
            "quality_score": 0.88,
            "file_size_bytes": len(pdf_bytes),
            "issues": []
        }
        
        # Make request
        response = client.post(
            f"/reports/generate-complete?requirements_id={sample_requirements_id}&include_pdf=true"
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "report_content" in data
        assert data["report_content"] == "Formatted report text content"
        assert data["pdf_generated"] is True
        assert data["pdf_size_bytes"] == len(pdf_bytes)
        assert "pdf_validation" in data
        assert "pdf_download_url" in data
        assert "metadata" in data
        assert "raw_content" in data
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_download_pdf_report_endpoint(self, mock_report_service_class, mock_get_db,
                                        client, mock_db_session, sample_requirements_id,
                                        mock_report_content):
        """Test PDF download endpoint"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_report_service = Mock()
        mock_report_service_class.return_value = mock_report_service
        
        # Mock PDF generation
        pdf_bytes = b"%PDF-1.4\nDownload test PDF content"
        mock_report_service.generate_complete_report_with_pdf = AsyncMock(
            return_value=(mock_report_content, pdf_bytes)
        )
        
        # Make request
        response = client.get(f"/reports/download-pdf/{sample_requirements_id}")
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "sustainability_report_" in response.headers["content-disposition"]
        assert response.content == pdf_bytes
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_validate_pdf_quality_endpoint(self, mock_report_service_class, mock_get_db,
                                         client, mock_db_session):
        """Test PDF quality validation endpoint"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_report_service = Mock()
        mock_report_service_class.return_value = mock_report_service
        
        # Mock validation results
        validation_results = {
            "is_valid_pdf": True,
            "quality_score": 0.92,
            "file_size_bytes": 15000,
            "estimated_pages": 5,
            "issues": []
        }
        mock_report_service.validate_pdf_quality.return_value = validation_results
        
        # Test PDF content
        test_pdf = b"%PDF-1.4\nTest PDF for validation"
        
        # Make request
        response = client.post("/reports/validate-pdf", content=test_pdf)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "validation_results" in data
        assert data["validation_results"] == validation_results
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_pdf_generation_error_handling(self, mock_report_service_class, mock_get_db,
                                         client, mock_db_session, sample_requirements_id):
        """Test PDF generation error handling"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_report_service = Mock()
        mock_report_service_class.return_value = mock_report_service
        
        # Mock PDF generation failure
        mock_report_service.generate_complete_report_with_pdf = AsyncMock(
            return_value=(None, None)
        )
        
        # Make request
        response = client.post(
            f"/reports/generate-pdf?requirements_id={sample_requirements_id}"
        )
        
        # Verify error response
        assert response.status_code == 500
        assert "Failed to generate PDF" in response.json()["detail"]
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_invalid_template_type_error(self, mock_report_service_class, mock_get_db,
                                       client, mock_db_session, sample_requirements_id):
        """Test error handling for invalid template type"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        
        # Make request with invalid template
        response = client.post(
            f"/reports/generate-pdf?requirements_id={sample_requirements_id}&template_type=invalid_template"
        )
        
        # Verify error response
        assert response.status_code == 400
        assert "Invalid template type" in response.json()["detail"]
    
    @patch('app.api.reports.get_db')
    @patch('app.services.report_service.ReportService')
    def test_invalid_ai_model_error(self, mock_report_service_class, mock_get_db,
                                  client, mock_db_session, sample_requirements_id):
        """Test error handling for invalid AI model"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        
        # Make request with invalid AI model
        response = client.post(
            f"/reports/generate-pdf?requirements_id={sample_requirements_id}&ai_model=invalid_model"
        )
        
        # Verify error response
        assert response.status_code == 400
        assert "Invalid AI model" in response.json()["detail"]


class TestPDFServiceIntegration:
    """Integration tests for PDF service with report service"""
    
    @pytest.fixture
    def pdf_service(self):
        """Create PDF service instance"""
        return PDFService()
    
    @pytest.fixture
    def comprehensive_report_content(self):
        """Create comprehensive report content for integration testing"""
        # Create nested subsections
        climate_subsections = [
            ReportSection(
                id="climate_mitigation",
                title="Climate Mitigation Strategies",
                content="Detailed analysis of climate mitigation approaches including carbon reduction targets and renewable energy adoption.",
                subsections=[],
                metadata={"category": "mitigation"},
                sources=["Carbon Management Guidelines", "Renewable Energy Standards"]
            ),
            ReportSection(
                id="climate_adaptation",
                title="Climate Adaptation Measures",
                content="Assessment of climate adaptation strategies and resilience planning.",
                subsections=[],
                metadata={"category": "adaptation"},
                sources=["Climate Resilience Framework"]
            )
        ]
        
        environmental_sections = [
            ReportSection(
                id="e1_climate",
                title="E1 - Climate Change",
                content="## Climate Change Performance\n\nComprehensive climate change analysis including:\n\n- **Scope 1 Emissions**: Direct emissions from operations\n- **Scope 2 Emissions**: Indirect emissions from energy\n- **Scope 3 Emissions**: Value chain emissions\n\n### Key Metrics\n\n1. Total CO2 equivalent emissions: 125,000 tonnes\n2. Emissions intensity: 2.5 tonnes CO2e per unit\n3. Renewable energy percentage: 45%",
                subsections=climate_subsections,
                metadata={"esrs_standard": "E1", "priority": "high"},
                sources=["GHG Protocol", "TCFD Guidelines", "EU Taxonomy Regulation"]
            ),
            ReportSection(
                id="e2_pollution",
                title="E2 - Pollution",
                content="### Pollution Prevention and Control\n\nAnalysis of pollution prevention measures:\n\n- Air quality management\n- Water pollution control\n- Waste management systems\n- Chemical safety protocols",
                subsections=[],
                metadata={"esrs_standard": "E2", "priority": "medium"},
                sources=["Environmental Protection Standards", "Waste Management Directive"]
            )
        ]
        
        social_sections = [
            ReportSection(
                id="s1_workforce",
                title="S1 - Own Workforce",
                content="## Workforce Management\n\n**Employee Statistics:**\n- Total employees: 2,500\n- Gender diversity: 48% female, 52% male\n- Training hours per employee: 40 hours annually\n\n**Key Initiatives:**\n1. Diversity and inclusion programs\n2. Professional development opportunities\n3. Health and safety protocols",
                subsections=[],
                metadata={"esrs_standard": "S1", "priority": "high"},
                sources=["HR Policy Manual", "Diversity Guidelines"]
            )
        ]
        
        main_sections = [
            ReportSection(
                id="executive_summary",
                title="Executive Summary",
                content="# Executive Summary\n\nThis comprehensive sustainability report demonstrates our organization's commitment to environmental, social, and governance excellence. The report covers all material ESRS topics and provides detailed analysis of our sustainability performance.\n\n## Key Highlights\n\n- **Environmental**: Achieved 25% reduction in carbon emissions\n- **Social**: Improved employee satisfaction by 15%\n- **Governance**: Enhanced board diversity and transparency\n\nThis report serves as a foundation for our continued sustainability journey and stakeholder engagement.",
                subsections=[],
                metadata={"required": True, "order": 1},
                sources=["Executive Board Minutes", "Sustainability Strategy Document"]
            ),
            ReportSection(
                id="environmental_standards",
                title="Environmental Standards (E1-E5)",
                content="## Environmental Performance Overview\n\nOur environmental strategy focuses on climate action, pollution prevention, and resource efficiency. This section provides detailed analysis of our performance against EU ESRS environmental standards.\n\n### Materiality Assessment\n\nBased on our materiality assessment, the following environmental topics are material to our business:\n\n1. **Climate Change (E1)** - High materiality\n2. **Pollution (E2)** - Medium materiality\n3. **Water Resources (E3)** - Low materiality\n4. **Biodiversity (E4)** - Low materiality\n5. **Circular Economy (E5)** - Medium materiality",
                subsections=environmental_sections,
                metadata={"required": True, "order": 2, "category": "environmental"},
                sources=["Environmental Management System", "Materiality Assessment Report"]
            ),
            ReportSection(
                id="social_standards",
                title="Social Standards (S1-S4)",
                content="## Social Impact and Responsibility\n\nOur social strategy encompasses workforce management, value chain responsibility, and community engagement. We are committed to creating positive social impact across all our operations.",
                subsections=social_sections,
                metadata={"required": True, "order": 3, "category": "social"},
                sources=["Social Impact Assessment", "Stakeholder Engagement Report"]
            ),
            ReportSection(
                id="governance_standards",
                title="Governance Standards (G1)",
                content="### Business Conduct and Ethics\n\n**Governance Framework:**\n\n- Board composition: 9 members (44% independent)\n- Audit committee: 3 independent members\n- Risk management: Comprehensive framework\n\n**Ethics and Compliance:**\n\n1. Code of conduct training: 100% completion\n2. Whistleblower system: Anonymous reporting\n3. Anti-corruption measures: Zero tolerance policy",
                subsections=[],
                metadata={"required": True, "order": 4, "category": "governance"},
                sources=["Corporate Governance Code", "Ethics Policy", "Risk Management Framework"]
            ),
            ReportSection(
                id="conclusions",
                title="Conclusions and Recommendations",
                content="## Key Conclusions\n\nBased on our comprehensive analysis, we have identified several key areas of strength and opportunities for improvement:\n\n### Strengths\n\n1. **Strong climate performance** with significant emissions reductions\n2. **Robust governance framework** with independent oversight\n3. **Engaged workforce** with high satisfaction scores\n\n### Areas for Improvement\n\n1. **Biodiversity impact** requires enhanced monitoring\n2. **Supply chain transparency** needs strengthening\n3. **Water management** efficiency can be improved\n\n## Strategic Recommendations\n\n### Short-term (1 year)\n\n- Implement enhanced biodiversity monitoring systems\n- Expand supplier sustainability assessments\n- Deploy water efficiency technologies\n\n### Medium-term (2-3 years)\n\n- Achieve carbon neutrality in direct operations\n- Establish circular economy initiatives\n- Enhance community engagement programs\n\n### Long-term (5+ years)\n\n- Reach net-zero emissions across value chain\n- Become a leader in sustainable innovation\n- Contribute to UN Sustainable Development Goals",
                subsections=[],
                metadata={"required": True, "order": 5},
                sources=["Strategic Planning Document", "Sustainability Roadmap", "Stakeholder Feedback"]
            )
        ]
        
        return ReportContent(
            title="Comprehensive Sustainability Report 2024 - EU ESRS Compliance Assessment",
            client_name="Global Sustainable Industries Ltd",
            generation_date=datetime(2024, 3, 20, 16, 30, 0),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=main_sections,
            executive_summary="This comprehensive sustainability report provides detailed analysis of our environmental, social, and governance performance in accordance with EU ESRS requirements. The report demonstrates our commitment to transparency, accountability, and continuous improvement in sustainability practices.",
            metadata={
                "requirements_id": "comprehensive_req_789",
                "ai_model_used": "openai_gpt4",
                "report_format": "structured_text",
                "generation_timestamp": "2024-03-20T16:30:00",
                "template_version": "2.0",
                "total_documents_analyzed": 45,
                "confidence_score": 0.91,
                "materiality_assessment_completed": True,
                "stakeholder_engagement_conducted": True,
                "external_assurance": "Limited assurance by third party"
            }
        )
    
    def test_comprehensive_pdf_generation(self, pdf_service, comprehensive_report_content):
        """Test comprehensive PDF generation with complex content structure"""
        pdf_bytes = pdf_service.generate_pdf(comprehensive_report_content)
        
        # Basic validation
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 20000  # Should be substantial due to comprehensive content
        assert pdf_bytes.startswith(b'%PDF-')
        
        # Quality validation
        validation_results = pdf_service.validate_pdf_quality(pdf_bytes)
        assert validation_results["is_valid_pdf"] is True
        assert validation_results["has_content"] is True
        assert validation_results["quality_score"] > 0.8
        assert validation_results["estimated_pages"] >= 5
        
        # Check comprehensive citation processing
        assert len(pdf_service.citations) >= 10  # Should have many citations
        assert pdf_service.citation_counter >= 10
    
    def test_pdf_content_structure_validation(self, pdf_service, comprehensive_report_content):
        """Test that PDF maintains proper content structure"""
        pdf_bytes = pdf_service.generate_pdf(comprehensive_report_content)
        
        # Convert to string for structure checking
        pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
        
        # Check for main structural elements
        assert "Comprehensive Sustainability Report 2024" in pdf_text
        assert "Global Sustainable Industries Ltd" in pdf_text
        assert "Table of Contents" in pdf_text
        assert "Executive Summary" in pdf_text
        assert "Environmental Standards" in pdf_text
        assert "Social Standards" in pdf_text
        assert "Governance Standards" in pdf_text
        assert "Conclusions and Recommendations" in pdf_text
        assert "Bibliography" in pdf_text
        
        # Check for subsection content
        assert "Climate Change" in pdf_text
        assert "Pollution" in pdf_text
        assert "Own Workforce" in pdf_text
        
        # Check for formatted content elements
        assert "Key Highlights" in pdf_text
        assert "Strategic Recommendations" in pdf_text
    
    def test_pdf_citation_accuracy(self, pdf_service, comprehensive_report_content):
        """Test accuracy of citation processing and bibliography generation"""
        pdf_bytes = pdf_service.generate_pdf(comprehensive_report_content)
        
        # Check citation processing
        citations = pdf_service.citations
        assert len(citations) > 0
        
        # Verify citation sources match report sources
        report_sources = set()
        for section in comprehensive_report_content.sections:
            report_sources.update(section.sources)
            for subsection in section.subsections:
                report_sources.update(subsection.sources)
                for subsubsection in subsection.subsections:
                    report_sources.update(subsubsection.sources)
        
        citation_sources = {citation.source for citation in citations}
        
        # Most report sources should appear in citations
        overlap = len(report_sources.intersection(citation_sources))
        assert overlap > 0  # Should have some overlap
    
    def test_pdf_performance_with_large_content(self, pdf_service):
        """Test PDF generation performance with very large content"""
        import time
        
        # Create large content sections
        large_content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 2000
        large_sections = []
        
        for i in range(10):  # Create 10 large sections
            large_sections.append(
                ReportSection(
                    id=f"large_section_{i}",
                    title=f"Large Section {i+1}",
                    content=large_content,
                    subsections=[],
                    metadata={},
                    sources=[f"Large Source {i+1}"]
                )
            )
        
        large_report = ReportContent(
            title="Performance Test Report",
            client_name="Performance Test Client",
            generation_date=datetime.now(),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=large_sections,
            executive_summary="Performance test executive summary",
            metadata={}
        )
        
        # Measure generation time
        start_time = time.time()
        pdf_bytes = pdf_service.generate_pdf(large_report)
        generation_time = time.time() - start_time
        
        # Validate results
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 50000  # Should be very large
        assert generation_time < 30  # Should complete within 30 seconds
        
        # Quality validation
        validation_results = pdf_service.validate_pdf_quality(pdf_bytes)
        assert validation_results["is_valid_pdf"] is True
    
    def test_pdf_error_recovery(self, pdf_service):
        """Test PDF generation error recovery and graceful degradation"""
        # Test with problematic content
        problematic_sections = [
            ReportSection(
                id="problematic_section",
                title="Section with Special Characters: àáâãäåæçèéêë",
                content="Content with special characters: ñóôõö÷øùúûüýþÿ and symbols: ©®™€£¥",
                subsections=[],
                metadata={},
                sources=["Source with special chars: àáâãäåæçèéêë"]
            )
        ]
        
        problematic_report = ReportContent(
            title="Problematic Report: Special Characters Test àáâãäåæçèéêë",
            client_name="Client with Special Name: Ñoël & Søren",
            generation_date=datetime.now(),
            template_type=ReportTemplate.EU_ESRS_STANDARD,
            schema_type=SchemaType.EU_ESRS_CSRD,
            sections=problematic_sections,
            executive_summary="Executive summary with special characters: àáâãäåæçèéêë",
            metadata={}
        )
        
        # Should handle special characters gracefully
        pdf_bytes = pdf_service.generate_pdf(problematic_report)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b'%PDF-')
        
        # Validation should still pass
        validation_results = pdf_service.validate_pdf_quality(pdf_bytes)
        assert validation_results["is_valid_pdf"] is True
    
    def test_concurrent_pdf_generation(self, comprehensive_report_content):
        """Test concurrent PDF generation with multiple service instances"""
        import threading
        import time
        
        results = []
        errors = []
        
        def generate_pdf_worker(worker_id):
            try:
                # Create separate service instance for each worker
                worker_pdf_service = PDFService()
                
                # Modify content slightly for each worker
                worker_content = comprehensive_report_content
                worker_content.title = f"Worker {worker_id} Report"
                worker_content.client_name = f"Client {worker_id}"
                
                pdf_bytes = worker_pdf_service.generate_pdf(worker_content)
                results.append({
                    'worker_id': worker_id,
                    'pdf_size': len(pdf_bytes),
                    'is_valid': pdf_bytes.startswith(b'%PDF-')
                })
            except Exception as e:
                errors.append({'worker_id': worker_id, 'error': str(e)})
        
        # Create and start multiple worker threads
        threads = []
        for i in range(3):  # Test with 3 concurrent workers
            thread = threading.Thread(target=generate_pdf_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        
        for result in results:
            assert result['is_valid'] is True
            assert result['pdf_size'] > 10000  # Should be substantial
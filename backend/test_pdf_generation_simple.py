#!/usr/bin/env python3
"""
Simple test script for PDF generation functionality
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_service import PDFService, create_pdf_from_report, validate_pdf_output
from app.services.report_service import ReportContent, ReportSection, ReportTemplate
from app.models.schemas import SchemaType


def create_sample_report():
    """Create a sample report for testing"""
    sections = [
        ReportSection(
            id="executive_summary",
            title="Executive Summary",
            content="""
            # Executive Summary
            
            This sustainability report provides a comprehensive analysis of our organization's 
            environmental, social, and governance performance. Key highlights include:
            
            - **25% reduction** in carbon emissions
            - **100% renewable** energy in main facilities  
            - **Zero workplace** accidents this year
            - **Enhanced board** diversity and transparency
            
            ## Strategic Priorities
            
            Our sustainability strategy focuses on three main areas:
            
            1. **Climate Action**: Achieving net-zero emissions by 2030
            2. **Social Impact**: Creating positive change in communities
            3. **Governance Excellence**: Maintaining highest ethical standards
            """,
            subsections=[],
            metadata={"required": True, "order": 1},
            sources=["Sustainability Strategy 2024", "Board Resolution 2024-03"]
        ),
        ReportSection(
            id="environmental_standards",
            title="Environmental Standards (E1-E5)",
            content="""
            ## Environmental Performance Overview
            
            Our environmental management system addresses all material environmental impacts:
            
            ### Climate Change (E1)
            - Scope 1 emissions: 15,000 tCO2e (↓20% vs 2023)
            - Scope 2 emissions: 8,500 tCO2e (↓30% vs 2023)  
            - Renewable energy: 85% of total consumption
            
            ### Pollution Prevention (E2)
            - Air quality: All facilities meet WHO standards
            - Water discharge: 100% compliance with regulations
            - Waste reduction: 40% decrease in landfill waste
            """,
            subsections=[
                ReportSection(
                    id="e1_climate",
                    title="E1 - Climate Change Details",
                    content="""
                    ### Climate Mitigation Strategies
                    
                    **Energy Efficiency Measures:**
                    - LED lighting conversion: 100% complete
                    - HVAC optimization: 15% energy savings
                    - Process improvements: 10% efficiency gains
                    
                    **Renewable Energy Transition:**
                    - Solar installations: 5 MW capacity added
                    - Wind power agreements: 20 MW contracted
                    - Energy storage: 2 MWh battery systems
                    """,
                    subsections=[],
                    metadata={"esrs_standard": "E1"},
                    sources=["Energy Management Report", "Carbon Footprint Assessment"]
                )
            ],
            metadata={"required": True, "category": "environmental"},
            sources=["Environmental Management System", "ESRS E1-E5 Guidelines"]
        ),
        ReportSection(
            id="social_standards",
            title="Social Standards (S1-S4)",
            content="""
            ## Social Impact and Workforce Management
            
            ### Own Workforce (S1)
            - Total employees: 2,847 (↑8% vs 2023)
            - Gender diversity: 52% female, 48% male
            - Training investment: €1.2M (42 hours per employee)
            - Employee satisfaction: 4.2/5.0 (↑0.3 vs 2023)
            
            ### Health and Safety
            - Zero fatalities and serious injuries
            - Lost time injury rate: 0.8 per 100,000 hours
            - Safety training completion: 100%
            """,
            subsections=[],
            metadata={"required": True, "category": "social"},
            sources=["HR Annual Report", "Health & Safety Statistics", "Employee Survey Results"]
        ),
        ReportSection(
            id="governance_standards", 
            title="Governance Standards (G1)",
            content="""
            ### Business Conduct and Ethics
            
            **Board Composition:**
            - Total directors: 9 (4 independent, 5 executive)
            - Gender diversity: 44% female representation
            - Average tenure: 4.2 years
            
            **Ethics and Compliance:**
            - Code of conduct training: 100% completion
            - Ethics hotline reports: 12 (all resolved)
            - Anti-corruption policy: Zero tolerance maintained
            
            **Risk Management:**
            - Enterprise risk framework: Fully implemented
            - Climate risk assessment: Completed annually
            - Cybersecurity incidents: Zero material breaches
            """,
            subsections=[],
            metadata={"required": True, "category": "governance"},
            sources=["Corporate Governance Report", "Ethics Committee Minutes", "Risk Assessment 2024"]
        ),
        ReportSection(
            id="conclusions",
            title="Conclusions and Next Steps",
            content="""
            ## Key Achievements
            
            This year marked significant progress in our sustainability journey:
            
            1. **Environmental Leadership**: Exceeded emission reduction targets
            2. **Social Excellence**: Improved employee engagement and safety
            3. **Governance Strength**: Enhanced transparency and accountability
            
            ## 2025 Priorities
            
            ### Environmental Goals
            - Achieve 100% renewable energy across all operations
            - Implement circular economy principles in manufacturing
            - Launch biodiversity conservation program
            
            ### Social Commitments  
            - Expand diversity and inclusion initiatives
            - Increase community investment by 25%
            - Enhance supply chain labor standards
            
            ### Governance Enhancements
            - Strengthen climate risk oversight
            - Implement AI ethics framework
            - Expand stakeholder engagement programs
            
            ## Stakeholder Engagement
            
            We remain committed to transparent dialogue with all stakeholders and 
            welcome feedback on our sustainability performance and future priorities.
            """,
            subsections=[],
            metadata={"required": True, "order": 5},
            sources=["Strategic Plan 2025", "Stakeholder Engagement Report"]
        )
    ]
    
    return ReportContent(
        title="Annual Sustainability Report 2024 - EU ESRS Compliance",
        client_name="Sustainable Manufacturing Corp",
        generation_date=datetime(2024, 3, 25, 14, 0, 0),
        template_type=ReportTemplate.EU_ESRS_STANDARD,
        schema_type=SchemaType.EU_ESRS_CSRD,
        sections=sections,
        executive_summary="""
        This annual sustainability report demonstrates our comprehensive approach to 
        environmental stewardship, social responsibility, and governance excellence. 
        Through measurable progress across all ESG dimensions, we continue to create 
        long-term value for stakeholders while contributing to a sustainable future.
        """,
        metadata={
            "requirements_id": "annual_report_2024",
            "ai_model_used": "openai_gpt4",
            "report_format": "structured_text",
            "generation_timestamp": "2024-03-25T14:00:00",
            "template_version": "2.1",
            "total_documents_analyzed": 32,
            "confidence_score": 0.94,
            "assurance_level": "Limited assurance",
            "reporting_period": "2024-01-01 to 2024-12-31"
        }
    )


def test_basic_pdf_generation():
    """Test basic PDF generation functionality"""
    print("🔧 Testing basic PDF generation...")
    
    try:
        # Create PDF service
        pdf_service = PDFService()
        print("✅ PDF service initialized successfully")
        
        # Create sample report
        report_content = create_sample_report()
        print("✅ Sample report content created")
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(report_content)
        print(f"✅ PDF generated successfully ({len(pdf_bytes):,} bytes)")
        
        # Validate PDF
        if pdf_bytes.startswith(b'%PDF-'):
            print("✅ PDF format validation passed")
        else:
            print("❌ PDF format validation failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Basic PDF generation failed: {str(e)}")
        return False


def test_pdf_quality_validation():
    """Test PDF quality validation"""
    print("\n🔍 Testing PDF quality validation...")
    
    try:
        # Create and generate PDF
        pdf_service = PDFService()
        report_content = create_sample_report()
        pdf_bytes = pdf_service.generate_pdf(report_content)
        
        # Validate quality
        validation_results = pdf_service.validate_pdf_quality(pdf_bytes)
        
        print(f"✅ PDF validation completed:")
        print(f"   - Valid PDF: {validation_results['is_valid_pdf']}")
        print(f"   - Has content: {validation_results['has_content']}")
        print(f"   - Quality score: {validation_results['quality_score']:.2f}")
        print(f"   - Estimated pages: {validation_results['estimated_pages']}")
        print(f"   - File size: {validation_results['file_size_bytes']:,} bytes")
        
        if validation_results['issues']:
            print(f"   - Issues found: {len(validation_results['issues'])}")
            for issue in validation_results['issues']:
                print(f"     • {issue}")
        else:
            print("   - No issues found")
        
        # Check quality threshold
        if validation_results['quality_score'] >= 0.7:
            print("✅ PDF quality validation passed")
            return True
        else:
            print("⚠️  PDF quality below threshold")
            return False
            
    except Exception as e:
        print(f"❌ PDF quality validation failed: {str(e)}")
        return False


def test_pdf_file_output():
    """Test PDF file output functionality"""
    print("\n💾 Testing PDF file output...")
    
    try:
        # Create output directory
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "test_sustainability_report.pdf"
        
        # Generate PDF with file output
        report_content = create_sample_report()
        pdf_bytes = create_pdf_from_report(report_content, str(output_file))
        
        # Check file was created
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ PDF file created: {output_file} ({file_size:,} bytes)")
            
            # Verify file content matches returned bytes
            with open(output_file, 'rb') as f:
                file_content = f.read()
            
            if file_content == pdf_bytes:
                print("✅ File content matches returned bytes")
                return True
            else:
                print("❌ File content mismatch")
                return False
        else:
            print("❌ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ PDF file output failed: {str(e)}")
        return False


def test_citation_processing():
    """Test citation processing and bibliography generation"""
    print("\n📚 Testing citation processing...")
    
    try:
        pdf_service = PDFService()
        report_content = create_sample_report()
        
        # Generate PDF to trigger citation processing
        pdf_bytes = pdf_service.generate_pdf(report_content)
        
        # Check citations were created
        citations_count = len(pdf_service.citations)
        print(f"✅ Citations processed: {citations_count} citations")
        
        if citations_count > 0:
            print("   Sample citations:")
            for i, citation in enumerate(pdf_service.citations[:3]):  # Show first 3
                print(f"   [{i+1}] {citation.source}")
            
            if citations_count > 3:
                print(f"   ... and {citations_count - 3} more")
                
            return True
        else:
            print("⚠️  No citations were processed")
            return False
            
    except Exception as e:
        print(f"❌ Citation processing failed: {str(e)}")
        return False


def test_convenience_functions():
    """Test convenience functions"""
    print("\n🛠️  Testing convenience functions...")
    
    try:
        report_content = create_sample_report()
        
        # Test create_pdf_from_report
        pdf_bytes = create_pdf_from_report(report_content)
        print(f"✅ create_pdf_from_report: {len(pdf_bytes):,} bytes")
        
        # Test validate_pdf_output
        validation_results = validate_pdf_output(pdf_bytes)
        print(f"✅ validate_pdf_output: Quality score {validation_results['quality_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions failed: {str(e)}")
        return False


def test_error_handling():
    """Test error handling scenarios"""
    print("\n🚨 Testing error handling...")
    
    try:
        pdf_service = PDFService()
        
        # Test invalid PDF validation
        invalid_pdf = b"This is not a PDF file"
        validation_results = pdf_service.validate_pdf_quality(invalid_pdf)
        
        if not validation_results['is_valid_pdf']:
            print("✅ Invalid PDF correctly identified")
        else:
            print("❌ Invalid PDF not detected")
            return False
        
        # Test small PDF validation
        small_pdf = b"%PDF-1.4\nsmall"
        validation_results = pdf_service.validate_pdf_quality(small_pdf)
        
        if "PDF file size too small" in validation_results.get('issues', []):
            print("✅ Small PDF size correctly flagged")
        else:
            print("⚠️  Small PDF size not flagged")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False


def main():
    """Run all PDF generation tests"""
    print("🚀 Starting PDF Generation Service Tests")
    print("=" * 50)
    
    tests = [
        ("Basic PDF Generation", test_basic_pdf_generation),
        ("PDF Quality Validation", test_pdf_quality_validation),
        ("PDF File Output", test_pdf_file_output),
        ("Citation Processing", test_citation_processing),
        ("Convenience Functions", test_convenience_functions),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All PDF generation tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
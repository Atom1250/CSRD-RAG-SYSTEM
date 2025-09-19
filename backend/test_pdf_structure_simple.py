#!/usr/bin/env python3
"""
Simple test script for PDF generation structure and functionality
Tests the PDF service without requiring external PDF libraries
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_service import PDFService, Citation, create_pdf_from_report, validate_pdf_output


def create_sample_report_dict():
    """Create a sample report dictionary for testing"""
    return {
        "title": "Test Sustainability Report 2024",
        "client_name": "Test Manufacturing Corp",
        "generation_date": "2024-03-25T14:00:00",
        "template_type": "eu_esrs_standard",
        "schema_type": "eu_esrs_csrd",
        "executive_summary": """
        This sustainability report demonstrates our comprehensive approach to 
        environmental stewardship, social responsibility, and governance excellence.
        
        **Key Achievements:**
        - 25% reduction in carbon emissions
        - 100% renewable energy adoption
        - Zero workplace accidents
        
        Our commitment to sustainability drives innovation and creates long-term value.
        """,
        "sections": [
            {
                "id": "environmental_standards",
                "title": "Environmental Standards (E1-E5)",
                "content": """
                ## Environmental Performance Overview
                
                Our environmental management system addresses all material impacts:
                
                ### Climate Change (E1)
                - **Scope 1 emissions**: 15,000 tCO2e (↓20% vs 2023)
                - **Scope 2 emissions**: 8,500 tCO2e (↓30% vs 2023)
                - **Renewable energy**: 85% of total consumption
                
                ### Key Initiatives
                1. Solar panel installations across all facilities
                2. Energy efficiency improvements in manufacturing
                3. Transition to electric vehicle fleet
                """,
                "subsections": [
                    {
                        "id": "e1_climate",
                        "title": "E1 - Climate Change Details",
                        "content": """
                        ### Climate Mitigation Strategies
                        
                        **Energy Efficiency Measures:**
                        - LED lighting conversion: 100% complete
                        - HVAC optimization: 15% energy savings
                        - Process improvements: 10% efficiency gains
                        
                        **Renewable Energy Transition:**
                        - Solar installations: 5 MW capacity added
                        - Wind power agreements: 20 MW contracted
                        """,
                        "subsections": [],
                        "metadata": {"esrs_standard": "E1"},
                        "sources": ["Energy Management Report", "Carbon Footprint Assessment"]
                    }
                ],
                "metadata": {"required": True, "category": "environmental"},
                "sources": ["Environmental Management System", "ESRS E1-E5 Guidelines"]
            },
            {
                "id": "social_standards",
                "title": "Social Standards (S1-S4)",
                "content": """
                ## Social Impact and Workforce Management
                
                ### Own Workforce (S1)
                - Total employees: 2,847 (↑8% vs 2023)
                - Gender diversity: 52% female, 48% male
                - Training investment: €1.2M (42 hours per employee)
                - Employee satisfaction: 4.2/5.0 (↑0.3 vs 2023)
                
                ### Health and Safety
                - **Zero fatalities** and serious injuries
                - Lost time injury rate: 0.8 per 100,000 hours
                - Safety training completion: 100%
                """,
                "subsections": [],
                "metadata": {"required": True, "category": "social"},
                "sources": ["HR Annual Report", "Health & Safety Statistics"]
            },
            {
                "id": "governance_standards",
                "title": "Governance Standards (G1)",
                "content": """
                ### Business Conduct and Ethics
                
                **Board Composition:**
                - Total directors: 9 (4 independent, 5 executive)
                - Gender diversity: 44% female representation
                - Average tenure: 4.2 years
                
                **Ethics and Compliance:**
                - Code of conduct training: 100% completion
                - Ethics hotline reports: 12 (all resolved)
                - Anti-corruption policy: Zero tolerance maintained
                """,
                "subsections": [],
                "metadata": {"required": True, "category": "governance"},
                "sources": ["Corporate Governance Report", "Ethics Committee Minutes"]
            }
        ],
        "metadata": {
            "requirements_id": "test_req_456",
            "ai_model_used": "openai_gpt4",
            "generation_timestamp": "2024-03-25T14:00:00",
            "confidence_score": 0.92
        }
    }


def test_pdf_service_initialization():
    """Test PDF service initialization"""
    print("🔧 Testing PDF service initialization...")
    
    try:
        pdf_service = PDFService()
        print(f"✅ PDF service initialized successfully")
        print(f"   - WeasyPrint available: {pdf_service.weasyprint_available}")
        print(f"   - ReportLab available: {pdf_service.reportlab_available}")
        print(f"   - Citations counter: {pdf_service.citation_counter}")
        return True
        
    except Exception as e:
        print(f"❌ PDF service initialization failed: {str(e)}")
        return False


def test_html_generation():
    """Test HTML report generation"""
    print("\n📄 Testing HTML report generation...")
    
    try:
        pdf_service = PDFService()
        report_dict = create_sample_report_dict()
        
        # Generate HTML content
        html_content = pdf_service._generate_html_report(report_dict)
        
        print(f"✅ HTML content generated ({len(html_content):,} characters)")
        
        # Check for key elements
        required_elements = [
            "<!DOCTYPE html>",
            "Sustainability Report",
            "Test Manufacturing Corp",
            "Table of Contents",
            "Executive Summary",
            "Environmental Standards",
            "Social Standards",
            "Governance Standards"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in html_content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"⚠️  Missing HTML elements: {missing_elements}")
            return False
        else:
            print("✅ All required HTML elements present")
            return True
            
    except Exception as e:
        print(f"❌ HTML generation failed: {str(e)}")
        return False


def test_markdown_processing():
    """Test markdown to HTML conversion"""
    print("\n🔄 Testing markdown processing...")
    
    try:
        pdf_service = PDFService()
        
        test_markdown = """
        # Main Title
        ## Subtitle
        ### Sub-subtitle
        
        This is **bold text** and *italic text*.
        
        - List item 1
        - List item 2
        
        1. Numbered item 1
        2. Numbered item 2
        
        Regular paragraph with some content.
        """
        
        html_result = pdf_service._process_markdown_to_html(test_markdown)
        
        print(f"✅ Markdown processed ({len(html_result)} characters)")
        
        # Check conversions
        expected_conversions = [
            "<h1>Main Title</h1>",
            "<h2>Subtitle</h2>",
            "<h3>Sub-subtitle</h3>",
            "<strong>bold text</strong>",
            "<em>italic text</em>",
            "<li>List item 1</li>",
            "<li>Numbered item 1</li>"
        ]
        
        missing_conversions = []
        for conversion in expected_conversions:
            if conversion not in html_result:
                missing_conversions.append(conversion)
        
        if missing_conversions:
            print(f"⚠️  Missing conversions: {missing_conversions}")
            return False
        else:
            print("✅ All markdown conversions successful")
            return True
            
    except Exception as e:
        print(f"❌ Markdown processing failed: {str(e)}")
        return False


def test_citation_processing():
    """Test citation processing"""
    print("\n📚 Testing citation processing...")
    
    try:
        pdf_service = PDFService()
        
        # Test citation creation
        citation = Citation(
            id="test_1",
            title="Test Document",
            source="Test Source",
            page=123,
            url="https://example.com",
            access_date=datetime(2024, 3, 25)
        )
        
        formatted = citation.format_citation()
        print(f"✅ Citation formatted: {formatted}")
        
        # Test source processing
        test_sources = ["Document 1", "Document 2", "Document 3"]
        processed_citations = pdf_service._process_section_sources(test_sources)
        
        print(f"✅ Processed {len(processed_citations)} citations")
        print(f"   - Citations counter: {pdf_service.citation_counter}")
        print(f"   - Citations stored: {len(pdf_service.citations)}")
        
        if len(processed_citations) == len(test_sources):
            print("✅ Citation processing successful")
            return True
        else:
            print("❌ Citation count mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Citation processing failed: {str(e)}")
        return False


def test_pdf_generation():
    """Test PDF generation (basic structure)"""
    print("\n🔧 Testing PDF generation...")
    
    try:
        pdf_service = PDFService()
        report_dict = create_sample_report_dict()
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(report_dict)
        
        print(f"✅ PDF generated ({len(pdf_bytes):,} bytes)")
        
        # Basic validation
        if pdf_bytes.startswith(b'%PDF-'):
            print("✅ PDF format validation passed")
        else:
            print("❌ PDF format validation failed")
            return False
        
        # Check citations were processed
        if len(pdf_service.citations) > 0:
            print(f"✅ Citations processed: {len(pdf_service.citations)} citations")
        else:
            print("⚠️  No citations were processed")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF generation failed: {str(e)}")
        return False


def test_pdf_validation():
    """Test PDF quality validation"""
    print("\n🔍 Testing PDF validation...")
    
    try:
        pdf_service = PDFService()
        report_dict = create_sample_report_dict()
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(report_dict)
        
        # Validate PDF
        validation_results = pdf_service.validate_pdf_quality(pdf_bytes)
        
        print(f"✅ PDF validation completed:")
        print(f"   - Valid PDF: {validation_results['is_valid_pdf']}")
        print(f"   - Has content: {validation_results['has_content']}")
        print(f"   - Quality score: {validation_results['quality_score']:.2f}")
        print(f"   - File size: {validation_results['file_size_bytes']:,} bytes")
        print(f"   - Estimated pages: {validation_results['estimated_pages']}")
        
        if validation_results['issues']:
            print(f"   - Issues: {len(validation_results['issues'])}")
            for issue in validation_results['issues']:
                print(f"     • {issue}")
        else:
            print("   - No issues found")
        
        if validation_results['is_valid_pdf']:
            print("✅ PDF validation passed")
            return True
        else:
            print("❌ PDF validation failed")
            return False
            
    except Exception as e:
        print(f"❌ PDF validation failed: {str(e)}")
        return False


def test_file_output():
    """Test PDF file output"""
    print("\n💾 Testing PDF file output...")
    
    try:
        # Create output directory
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "test_sustainability_report.pdf"
        
        # Generate PDF with file output
        report_dict = create_sample_report_dict()
        pdf_bytes = create_pdf_from_report(report_dict, str(output_file))
        
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


def test_convenience_functions():
    """Test convenience functions"""
    print("\n🛠️  Testing convenience functions...")
    
    try:
        report_dict = create_sample_report_dict()
        
        # Test create_pdf_from_report
        pdf_bytes = create_pdf_from_report(report_dict)
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
        
        # Test empty content
        empty_report = {
            "title": "Empty Report",
            "client_name": "Test Client",
            "generation_date": "2024-03-25T14:00:00",
            "template_type": "standard",
            "schema_type": "unknown",
            "executive_summary": "",
            "sections": [],
            "metadata": {}
        }
        
        pdf_bytes = pdf_service.generate_pdf(empty_report)
        if len(pdf_bytes) > 0:
            print("✅ Empty report handled gracefully")
        else:
            print("⚠️  Empty report produced no output")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False


def main():
    """Run all PDF structure tests"""
    print("🚀 Starting PDF Generation Structure Tests")
    print("=" * 60)
    
    tests = [
        ("PDF Service Initialization", test_pdf_service_initialization),
        ("HTML Generation", test_html_generation),
        ("Markdown Processing", test_markdown_processing),
        ("Citation Processing", test_citation_processing),
        ("PDF Generation", test_pdf_generation),
        ("PDF Validation", test_pdf_validation),
        ("File Output", test_file_output),
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
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All PDF structure tests passed!")
        print("\n📝 Notes:")
        print("- PDF generation works with fallback to simple PDF format")
        print("- Install WeasyPrint or ReportLab for enhanced PDF features")
        print("- HTML generation and structure validation successful")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
"""
Integration tests for Schema Service with real schema files
"""
import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.services.schema_service import SchemaService
from app.models.schemas import SchemaType
from app.models.database import SchemaElement


class TestSchemaIntegration:
    """Integration tests for schema loading and classification"""
    
    def test_schema_files_exist(self):
        """Test that schema definition files exist"""
        schema_path = Path(__file__).parent.parent / "data" / "schemas"
        
        eu_schema_file = schema_path / "eu_esrs_csrd.json"
        uk_schema_file = schema_path / "uk_srd.json"
        
        assert eu_schema_file.exists(), f"EU ESRS/CSRD schema file not found: {eu_schema_file}"
        assert uk_schema_file.exists(), f"UK SRD schema file not found: {uk_schema_file}"
    
    def test_schema_files_valid_json(self):
        """Test that schema files contain valid JSON"""
        import json
        
        schema_path = Path(__file__).parent.parent / "data" / "schemas"
        
        # Test EU schema file
        eu_schema_file = schema_path / "eu_esrs_csrd.json"
        with open(eu_schema_file, 'r') as f:
            eu_data = json.load(f)
        
        assert "schema_name" in eu_data
        assert "elements" in eu_data
        assert len(eu_data["elements"]) > 0
        
        # Test UK schema file
        uk_schema_file = schema_path / "uk_srd.json"
        with open(uk_schema_file, 'r') as f:
            uk_data = json.load(f)
        
        assert "schema_name" in uk_data
        assert "elements" in uk_data
        assert len(uk_data["elements"]) > 0
    
    def test_schema_elements_structure(self):
        """Test that schema elements have required structure"""
        import json
        
        schema_path = Path(__file__).parent.parent / "data" / "schemas"
        
        for schema_file in [schema_path / "eu_esrs_csrd.json", schema_path / "uk_srd.json"]:
            with open(schema_file, 'r') as f:
                schema_data = json.load(f)
            
            for element in schema_data["elements"]:
                # Required fields
                assert "code" in element, f"Element missing 'code': {element}"
                assert "name" in element, f"Element missing 'name': {element}"
                
                # Optional fields should be present but can be empty
                assert "description" in element or element.get("description") is not None
                assert "requirements" in element or element.get("requirements") is not None
                
                # Test child elements if present
                if "children" in element:
                    for child in element["children"]:
                        assert "code" in child, f"Child element missing 'code': {child}"
                        assert "name" in child, f"Child element missing 'name': {child}"
    
    def test_schema_classification_keywords(self):
        """Test that schema elements contain meaningful classification keywords"""
        import json
        
        schema_path = Path(__file__).parent.parent / "data" / "schemas"
        
        # Test EU ESRS schema has climate-related elements
        eu_schema_file = schema_path / "eu_esrs_csrd.json"
        with open(eu_schema_file, 'r') as f:
            eu_data = json.load(f)
        
        # Should have climate change element
        climate_elements = [
            elem for elem in eu_data["elements"] 
            if "climate" in elem["name"].lower() or "climate" in elem.get("description", "").lower()
        ]
        assert len(climate_elements) > 0, "EU ESRS schema should contain climate-related elements"
        
        # Test UK SRD schema has governance elements
        uk_schema_file = schema_path / "uk_srd.json"
        with open(uk_schema_file, 'r') as f:
            uk_data = json.load(f)
        
        governance_elements = [
            elem for elem in uk_data["elements"]
            if "governance" in elem["name"].lower() or "governance" in elem.get("description", "").lower()
        ]
        assert len(governance_elements) > 0, "UK SRD schema should contain governance-related elements"


@pytest.mark.integration
class TestSchemaServiceWithRealData:
    """Integration tests using real database and schema files"""
    
    def test_load_eu_schema_elements(self, db_session: Session):
        """Test loading EU ESRS/CSRD schema elements"""
        schema_service = SchemaService(db_session)
        
        try:
            elements = schema_service.load_schema_definitions(SchemaType.EU_ESRS_CSRD)
            
            # Should have loaded elements
            assert len(elements) > 0
            
            # Verify elements are in database
            db_elements = db_session.query(SchemaElement).filter(
                SchemaElement.schema_type == SchemaType.EU_ESRS_CSRD
            ).all()
            
            assert len(db_elements) > 0
            
            # Check for expected elements
            element_codes = [elem.element_code for elem in db_elements]
            assert "ESRS-E1" in element_codes, "Should contain climate change element"
            assert "ESRS-S1" in element_codes, "Should contain workforce element"
            
        except FileNotFoundError:
            pytest.skip("Schema files not available for integration test")
    
    def test_load_uk_schema_elements(self, db_session: Session):
        """Test loading UK SRD schema elements"""
        schema_service = SchemaService(db_session)
        
        try:
            elements = schema_service.load_schema_definitions(SchemaType.UK_SRD)
            
            # Should have loaded elements
            assert len(elements) > 0
            
            # Verify elements are in database
            db_elements = db_session.query(SchemaElement).filter(
                SchemaElement.schema_type == SchemaType.UK_SRD
            ).all()
            
            assert len(db_elements) > 0
            
            # Check for expected elements
            element_codes = [elem.element_code for elem in db_elements]
            assert any("governance" in code.lower() for code in element_codes), "Should contain governance elements"
            
        except FileNotFoundError:
            pytest.skip("Schema files not available for integration test")
    
    def test_document_classification_with_real_schemas(self, db_session: Session):
        """Test document classification using real schema data"""
        from app.models.database import Document, DocumentType
        
        schema_service = SchemaService(db_session)
        
        try:
            # Load schemas first
            schema_service.load_schema_definitions(SchemaType.EU_ESRS_CSRD)
            
            # Create a test document
            document = Document(
                filename="test_climate_report.pdf",
                file_path="/test/path",
                file_size=1000,
                document_type=DocumentType.PDF,
                schema_type=SchemaType.EU_ESRS_CSRD
            )
            db_session.add(document)
            db_session.commit()
            
            # Test classification with climate-related content
            climate_content = """
            This report covers our greenhouse gas emissions and climate change mitigation strategies.
            We have implemented a transition plan to reduce our carbon footprint and achieve net-zero emissions.
            Our Scope 1, 2, and 3 emissions are reported according to ESRS E1 requirements.
            """
            
            matched_elements = schema_service.classify_document(document, climate_content)
            
            # Should match climate-related elements
            assert len(matched_elements) > 0, "Should classify climate content to relevant schema elements"
            
            # Verify matched elements are climate-related
            matched_schema_elements = db_session.query(SchemaElement).filter(
                SchemaElement.id.in_(matched_elements)
            ).all()
            
            climate_matches = [
                elem for elem in matched_schema_elements
                if "climate" in elem.element_name.lower() or "e1" in elem.element_code.lower()
            ]
            
            assert len(climate_matches) > 0, "Should match to climate-related schema elements"
            
        except FileNotFoundError:
            pytest.skip("Schema files not available for integration test")
    
    def test_requirements_mapping_with_real_schemas(self, db_session: Session):
        """Test client requirements mapping using real schema data"""
        schema_service = SchemaService(db_session)
        
        try:
            # Load schemas first
            schema_service.load_schema_definitions(SchemaType.EU_ESRS_CSRD)
            
            # Test requirements mapping
            requirements_text = """
            Our client needs to report on their environmental impact, specifically:
            - Greenhouse gas emissions across all scopes
            - Climate change risks and opportunities
            - Transition planning for net-zero
            - Water usage and conservation efforts
            - Waste management and circular economy initiatives
            """
            
            mappings = schema_service.get_schema_mapping_for_requirements(
                requirements_text, SchemaType.EU_ESRS_CSRD
            )
            
            # Should find relevant mappings
            assert len(mappings) > 0, "Should find schema mappings for requirements"
            
            # Should have high-confidence mappings for climate and environmental topics
            high_confidence_mappings = [m for m in mappings if m['confidence_score'] > 0.3]
            assert len(high_confidence_mappings) > 0, "Should have high-confidence mappings"
            
            # Check for expected element types
            element_codes = [m['element_code'] for m in mappings]
            climate_codes = [code for code in element_codes if 'E1' in code or 'climate' in code.lower()]
            assert len(climate_codes) > 0, "Should map to climate-related elements"
            
        except FileNotFoundError:
            pytest.skip("Schema files not available for integration test")
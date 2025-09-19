"""
Simple test for client requirements functionality
"""
import json
from app.services.client_requirements_service import ClientRequirementsService
from app.models.schemas import SchemaType


def test_parse_requirements():
    """Test basic requirements parsing"""
    # Mock database session
    class MockDB:
        def __init__(self):
            pass
        
        def query(self, model):
            return MockQuery()
        
        def add(self, obj):
            pass
        
        def commit(self):
            pass
        
        def refresh(self, obj):
            obj.id = "test_id"
            obj.upload_date = "2024-01-01T00:00:00"
    
    class MockQuery:
        def filter(self, *args):
            return self
        
        def all(self):
            return []
    
    db_mock = MockDB()
    service = ClientRequirementsService(db_mock)
    
    # Test JSON parsing
    json_content = json.dumps({
        "requirements": [
            "Report on greenhouse gas emissions",
            "Disclose water usage metrics"
        ]
    })
    
    parsed = service._parse_json_requirements(json_content)
    print("JSON parsed requirements:", parsed)
    assert len(parsed) == 2
    assert parsed[0]['text'] == "Report on greenhouse gas emissions"
    
    # Test text parsing
    text_content = """
    1. Report on carbon emissions (Scope 1, 2, 3)
    2. Disclose water usage and conservation
    3. Provide waste management information
    """
    
    parsed_text = service._parse_text_requirements(text_content)
    print("Text parsed requirements:", parsed_text)
    assert len(parsed_text) == 3
    
    # Test bullet parsing
    bullet_content = """
    - Carbon emissions reporting
    - Energy efficiency metrics
    - Water usage disclosure
    """
    
    parsed_bullets = service._parse_text_requirements(bullet_content)
    print("Bullet parsed requirements:", parsed_bullets)
    assert len(parsed_bullets) == 3
    
    print("All parsing tests passed!")


if __name__ == "__main__":
    test_parse_requirements()
"""
Tests for Schema Service functionality
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.schema_service import SchemaService
from app.models.database import SchemaElement, Document, TextChunk
from app.models.schemas import SchemaType, DocumentType, ProcessingStatus


class TestSchemaService:
    """Test cases for SchemaService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def schema_service(self, mock_db_session):
        """Schema service instance with mocked dependencies"""
        with patch('app.services.schema_service.settings') as mock_settings:
            mock_settings.return_value = Mock()
            service = SchemaService(mock_db_session)
            return service
    
    @pytest.fixture
    def sample_schema_data(self):
        """Sample schema data for testing"""
        return {
            "schema_name": "Test Schema",
            "version": "1.0",
            "elements": [
                {
                    "code": "TEST-1",
                    "name": "Test Element 1",
                    "description": "Test description for element 1",
                    "requirements": ["Requirement 1", "Requirement 2"],
                    "children": [
                        {
                            "code": "TEST-1-1",
                            "name": "Test Sub Element 1",
                            "description": "Test sub element description",
                            "requirements": ["Sub requirement 1"]
                        }
                    ]
                },
                {
                    "code": "TEST-2",
                    "name": "Test Element 2",
                    "description": "Test description for element 2",
                    "requirements": ["Requirement 3"]
                }
            ]
        }
    
    @pytest.fixture
    def temp_schema_file(self, sample_schema_data):
        """Create temporary schema file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_schema_data, f)
            return Path(f.name)
    
    def test_load_schema_definitions_success(self, schema_service, mock_db_session, temp_schema_file):
        """Test successful loading of schema definitions"""
        # Mock the schema file path
        with patch.object(schema_service, '_get_schema_file_path', return_value=temp_schema_file):
            # Mock database operations
            mock_db_session.query.return_value.filter.return_value.delete.return_value = None
            mock_db_session.add = Mock()
            mock_db_session.flush = Mock()
            mock_db_session.commit = Mock()
            
            # Mock schema element creation
            mock_element = Mock(spec=SchemaElement)
            mock_element.id = "test-id"
            
            with patch.object(schema_service, '_create_schema_element', return_value=mock_element) as mock_create:
                elements = schema_service.load_schema_definitions(SchemaType.EU_ESRS_CSRD)
                
                # Verify schema elements were created
                assert len(elements) == 2  # Two top-level elements
                assert mock_create.call_count == 2
                mock_db_session.commit.assert_called_once()
        
        # Clean up
        temp_schema_file.unlink()
    
    def test_load_schema_definitions_file_not_found(self, schema_service):
        """Test loading schema definitions when file doesn't exist"""
        with patch.object(schema_service, '_get_schema_file_path', return_value=Path('/nonexistent/file.json')):
            with pytest.raises(FileNotFoundError):
                schema_service.load_schema_definitions(SchemaType.EU_ESRS_CSRD)
    
    def test_get_schema_file_path(self, schema_service):
        """Test getting schema file paths for different schema types"""
        eu_path = schema_service._get_schema_file_path(SchemaType.EU_ESRS_CSRD)
        uk_path = schema_service._get_schema_file_path(SchemaType.UK_SRD)
        
        assert eu_path.name == "eu_esrs_csrd.json"
        assert uk_path.name == "uk_srd.json"
        
        with pytest.raises(ValueError):
            schema_service._get_schema_file_path("INVALID_SCHEMA")
    
    def test_create_schema_element(self, schema_service, mock_db_session):
        """Test creating schema element from JSON data"""
        element_data = {
            "code": "TEST-1",
            "name": "Test Element",
            "description": "Test description",
            "requirements": ["Req 1", "Req 2"],
            "children": []
        }
        
        mock_element = Mock(spec=SchemaElement)
        mock_element.id = "test-id"
        
        with patch('app.services.schema_service.SchemaElement', return_value=mock_element):
            mock_db_session.add = Mock()
            mock_db_session.flush = Mock()
            
            element = schema_service._create_schema_element(element_data, SchemaType.EU_ESRS_CSRD)
            
            assert element == mock_element
            mock_db_session.add.assert_called_once_with(mock_element)
            mock_db_session.flush.assert_called_once()
    
    def test_get_schema_elements(self, schema_service, mock_db_session):
        """Test getting schema elements by type and parent"""
        mock_elements = [Mock(spec=SchemaElement), Mock(spec=SchemaElement)]
        mock_db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = mock_elements
        
        with patch('app.services.schema_service.SchemaElementResponse') as mock_response:
            mock_response.from_orm.return_value = Mock()
            
            elements = schema_service.get_schema_elements(SchemaType.EU_ESRS_CSRD)
            
            assert len(elements) == 2
            assert mock_response.from_orm.call_count == 2
    
    def test_classify_document_no_schema_type(self, schema_service):
        """Test document classification when document has no schema type"""
        document = Mock(spec=Document)
        document.schema_type = None
        
        result = schema_service.classify_document(document, "test content")
        
        assert result == []
    
    def test_classify_document_with_matches(self, schema_service, mock_db_session):
        """Test document classification with matching elements"""
        document = Mock(spec=Document)
        document.schema_type = SchemaType.EU_ESRS_CSRD
        
        mock_element1 = Mock(spec=SchemaElement)
        mock_element1.id = "element-1"
        mock_element1.element_name = "Climate Change"
        mock_element1.element_code = "E1"
        mock_element1.description = "Climate related disclosures"
        mock_element1.requirements = ["GHG emissions", "Transition plan"]
        
        mock_element2 = Mock(spec=SchemaElement)
        mock_element2.id = "element-2"
        mock_element2.element_name = "Biodiversity"
        mock_element2.element_code = "E4"
        mock_element2.description = "Biodiversity and ecosystems"
        mock_element2.requirements = ["Species protection"]
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_element1, mock_element2]
        
        with patch.object(schema_service, '_matches_schema_element') as mock_matches:
            mock_matches.side_effect = [True, False]  # First element matches, second doesn't
            
            result = schema_service.classify_document(document, "climate change emissions")
            
            assert result == ["element-1"]
            assert mock_matches.call_count == 2
    
    def test_matches_schema_element(self, schema_service):
        """Test schema element matching logic"""
        element = Mock(spec=SchemaElement)
        element.element_name = "Climate Change"
        element.element_code = "E1"
        element.description = "Climate related disclosures and reporting"
        element.requirements = ["GHG emissions reporting", "Transition planning"]
        
        # Test name match
        assert schema_service._matches_schema_element("climate change impacts", element) == True
        
        # Test code match
        assert schema_service._matches_schema_element("e1 reporting requirements", element) == True
        
        # Test description keyword match
        assert schema_service._matches_schema_element("climate related information", element) == True
        
        # Test requirements keyword match
        assert schema_service._matches_schema_element("ghg emissions data", element) == True
        
        # Test no match
        assert schema_service._matches_schema_element("biodiversity conservation", element) == False
    
    def test_classify_text_chunks(self, schema_service, mock_db_session):
        """Test classification of text chunks for a document"""
        document = Mock(spec=Document)
        document.id = "doc-1"
        document.schema_type = SchemaType.EU_ESRS_CSRD
        
        chunk1 = Mock(spec=TextChunk)
        chunk1.content = "Climate change emissions data"
        chunk2 = Mock(spec=TextChunk)
        chunk2.content = "Biodiversity conservation efforts"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = document
        mock_db_session.query.return_value.filter.return_value.all.return_value = [chunk1, chunk2]
        
        with patch.object(schema_service, 'classify_document') as mock_classify:
            mock_classify.side_effect = [["element-1"], ["element-2"]]
            
            result = schema_service.classify_text_chunks("doc-1")
            
            assert result == 2  # Both chunks classified
            assert chunk1.schema_elements == ["element-1"]
            assert chunk2.schema_elements == ["element-2"]
            mock_db_session.commit.assert_called_once()
    
    def test_get_schema_mapping_for_requirements(self, schema_service, mock_db_session):
        """Test mapping client requirements to schema elements"""
        mock_element1 = Mock(spec=SchemaElement)
        mock_element1.id = "element-1"
        mock_element1.element_code = "E1"
        mock_element1.element_name = "Climate Change"
        mock_element1.description = "Climate related reporting"
        mock_element1.requirements = ["GHG emissions"]
        
        mock_element2 = Mock(spec=SchemaElement)
        mock_element2.id = "element-2"
        mock_element2.element_code = "E2"
        mock_element2.element_name = "Pollution"
        mock_element2.description = "Pollution prevention"
        mock_element2.requirements = ["Air quality"]
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_element1, mock_element2]
        
        with patch.object(schema_service, '_calculate_mapping_confidence') as mock_confidence:
            mock_confidence.side_effect = [0.8, 0.2]  # First element high confidence, second low
            
            mappings = schema_service.get_schema_mapping_for_requirements(
                "We need climate change emissions reporting", SchemaType.EU_ESRS_CSRD
            )
            
            assert len(mappings) == 1  # Only high confidence mapping returned
            assert mappings[0]['schema_element_id'] == "element-1"
            assert mappings[0]['confidence_score'] == 0.8
    
    def test_calculate_mapping_confidence(self, schema_service):
        """Test confidence calculation for requirement mapping"""
        element = Mock(spec=SchemaElement)
        element.element_name = "Climate Change"
        element.element_code = "E1"
        element.description = "Climate related disclosures and reporting requirements"
        element.requirements = ["GHG emissions reporting", "Transition planning"]
        
        # High confidence - exact name match
        confidence = schema_service._calculate_mapping_confidence(
            "climate change reporting requirements", element
        )
        assert confidence >= 0.4
        
        # Medium confidence - code match
        confidence = schema_service._calculate_mapping_confidence(
            "e1 compliance requirements", element
        )
        assert confidence >= 0.3
        
        # Low confidence - partial keyword match
        confidence = schema_service._calculate_mapping_confidence(
            "environmental reporting standards", element
        )
        assert confidence < 0.3
    
    def test_update_document_schema_classification(self, schema_service, mock_db_session):
        """Test updating document schema classification"""
        document = Mock(spec=Document)
        document.id = "doc-1"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = document
        
        with patch.object(schema_service, 'classify_text_chunks', return_value=5) as mock_classify:
            result = schema_service.update_document_schema_classification("doc-1", SchemaType.EU_ESRS_CSRD)
            
            assert result == True
            assert document.schema_type == SchemaType.EU_ESRS_CSRD
            mock_classify.assert_called_once_with("doc-1")
            mock_db_session.commit.assert_called_once()
    
    def test_update_document_schema_classification_not_found(self, schema_service, mock_db_session):
        """Test updating schema classification for non-existent document"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = schema_service.update_document_schema_classification("nonexistent", SchemaType.EU_ESRS_CSRD)
        
        assert result == False
    
    def test_get_unclassified_documents(self, schema_service, mock_db_session):
        """Test getting unclassified documents"""
        mock_documents = [Mock(spec=Document), Mock(spec=Document)]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_documents
        
        result = schema_service.get_unclassified_documents()
        
        assert result == mock_documents
    
    def test_initialize_schemas(self, schema_service):
        """Test initializing all schemas"""
        with patch.object(schema_service, 'load_schema_definitions') as mock_load:
            mock_load.side_effect = [
                [Mock(), Mock(), Mock()],  # EU schema with 3 elements
                [Mock(), Mock()]           # UK schema with 2 elements
            ]
            
            results = schema_service.initialize_schemas()
            
            assert results[SchemaType.EU_ESRS_CSRD.value] == 3
            assert results[SchemaType.UK_SRD.value] == 2
            assert mock_load.call_count == 2
    
    def test_initialize_schemas_with_error(self, schema_service):
        """Test initializing schemas with file not found error"""
        with patch.object(schema_service, 'load_schema_definitions') as mock_load:
            mock_load.side_effect = [
                [Mock(), Mock()],  # EU schema succeeds
                FileNotFoundError("Schema file not found")  # UK schema fails
            ]
            
            results = schema_service.initialize_schemas()
            
            assert results[SchemaType.EU_ESRS_CSRD.value] == 2
            assert "Error:" in results[SchemaType.UK_SRD.value]


class TestSchemaServiceIntegration:
    """Integration tests for SchemaService with real database"""
    
    def test_full_schema_loading_workflow(self, db_session, temp_schema_file_with_data):
        """Test complete schema loading workflow with real database"""
        schema_service = SchemaService(db_session)
        
        # Mock the schema file path to use our test file
        with patch.object(schema_service, '_get_schema_file_path', return_value=temp_schema_file_with_data):
            elements = schema_service.load_schema_definitions(SchemaType.EU_ESRS_CSRD)
            
            # Verify elements were created in database
            assert len(elements) > 0
            
            # Verify we can retrieve them
            retrieved_elements = schema_service.get_schema_elements(SchemaType.EU_ESRS_CSRD)
            assert len(retrieved_elements) > 0
    
    @pytest.fixture
    def temp_schema_file_with_data(self):
        """Create temporary schema file with test data"""
        schema_data = {
            "schema_name": "Test Integration Schema",
            "version": "1.0",
            "elements": [
                {
                    "code": "INT-1",
                    "name": "Integration Test Element",
                    "description": "Test element for integration testing",
                    "requirements": ["Integration requirement 1"],
                    "children": [
                        {
                            "code": "INT-1-1",
                            "name": "Integration Sub Element",
                            "description": "Sub element for testing",
                            "requirements": ["Sub requirement"]
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_data, f)
            yield Path(f.name)
            Path(f.name).unlink()
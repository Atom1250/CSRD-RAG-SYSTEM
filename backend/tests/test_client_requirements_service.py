"""
Tests for Client Requirements Service
"""
import pytest
import json
from sqlalchemy.orm import Session

from app.services.client_requirements_service import ClientRequirementsService
from app.models.database import ClientRequirements, SchemaElement, Document, TextChunk
from app.models.schemas import SchemaType, ClientRequirementsCreate, SchemaMapping, ProcessedRequirement


class TestClientRequirementsService:
    """Test cases for ClientRequirementsService"""
    
    def test_parse_json_requirements(self, db_session: Session):
        """Test parsing JSON formatted requirements"""
        service = ClientRequirementsService(db_session)
        
        # Test structured JSON requirements
        json_content = json.dumps({
            "requirements": [
                {
                    "id": "req_1",
                    "text": "Report on greenhouse gas emissions",
                    "priority": "high",
                    "category": "environmental"
                },
                {
                    "id": "req_2", 
                    "text": "Disclose water usage metrics",
                    "priority": "medium"
                }
            ]
        })
        
        parsed = service._parse_json_requirements(json_content)
        
        assert len(parsed) == 2
        assert parsed[0]['id'] == 'req_1'
        assert parsed[0]['text'] == 'Report on greenhouse gas emissions'
        assert parsed[0]['priority'] == 'high'
        assert parsed[1]['id'] == 'req_2'
        assert parsed[1]['priority'] == 'medium'
    
    def test_parse_json_requirements_simple_list(self, db_session: Session):
        """Test parsing simple JSON list requirements"""
        service = ClientRequirementsService(db_session)
        
        json_content = json.dumps([
            "Report carbon footprint data",
            "Provide energy consumption metrics"
        ])
        
        parsed = service._parse_json_requirements(json_content)
        
        assert len(parsed) == 2
        assert parsed[0]['id'] == 'req_1'
        assert parsed[0]['text'] == 'Report carbon footprint data'
        assert parsed[1]['id'] == 'req_2'
        assert parsed[1]['text'] == 'Provide energy consumption metrics'
    
    def test_parse_text_requirements_numbered(self, db_session: Session):
        """Test parsing numbered text requirements"""
        service = ClientRequirementsService(db_session)
        
        text_content = """
        1. Report on Scope 1, 2, and 3 greenhouse gas emissions
        2. Disclose water usage and conservation efforts
        3. Provide information on waste management practices
        """
        
        parsed = service._parse_text_requirements(text_content)
        
        assert len(parsed) == 3
        assert parsed[0]['id'] == 'req_1'
        assert 'greenhouse gas emissions' in parsed[0]['text']
        assert parsed[1]['id'] == 'req_2'
        assert 'water usage' in parsed[1]['text']
        assert parsed[2]['id'] == 'req_3'
        assert 'waste management' in parsed[2]['text']
    
    def test_parse_text_requirements_bullets(self, db_session: Session):
        """Test parsing bullet point requirements"""
        service = ClientRequirementsService(db_session)
        
        text_content = """
        Environmental Requirements:
        - Carbon emissions reporting
        - Energy efficiency metrics
        • Water usage disclosure
        * Biodiversity impact assessment
        """
        
        parsed = service._parse_text_requirements(text_content)
        
        assert len(parsed) == 4
        assert any('carbon emissions' in req['text'].lower() for req in parsed)
        assert any('energy efficiency' in req['text'].lower() for req in parsed)
        assert any('water usage' in req['text'].lower() for req in parsed)
        assert any('biodiversity' in req['text'].lower() for req in parsed)
    
    def test_extract_priority(self, db_session: Session):
        """Test priority extraction from requirement text"""
        service = ClientRequirementsService(db_session)
        
        assert service._extract_priority("This is a critical requirement") == "high"
        assert service._extract_priority("Mandatory disclosure of emissions") == "high"
        assert service._extract_priority("Optional reporting on biodiversity") == "low"
        assert service._extract_priority("Nice to have water metrics") == "low"
        assert service._extract_priority("Standard reporting requirement") == "medium"
    
    def test_create_client_requirements(self, db_session: Session):
        """Test creating client requirements record"""
        service = ClientRequirementsService(db_session)
        
        requirements_data = ClientRequirementsCreate(
            client_name="Test Client Corp",
            requirements_text="Report on carbon emissions and water usage",
            schema_mappings=[
                SchemaMapping(
                    requirement_id="req_1",
                    schema_element_id="elem_1",
                    confidence_score=0.85
                )
            ],
            processed_requirements=[
                ProcessedRequirement(
                    requirement_id="req_1",
                    requirement_text="Report on carbon emissions",
                    mapped_elements=["elem_1"],
                    priority="high"
                )
            ]
        )
        
        result = service.create_client_requirements(requirements_data)
        
        assert result.client_name == "Test Client Corp"
        assert result.requirements_text == "Report on carbon emissions and water usage"
        assert len(result.schema_mappings) == 1
        assert len(result.processed_requirements) == 1
        assert result.id is not None
    
    def test_get_client_requirements(self, db_session: Session):
        """Test retrieving client requirements by ID"""
        service = ClientRequirementsService(db_session)
        
        # Create test requirements
        requirements_data = ClientRequirementsCreate(
            client_name="Test Client",
            requirements_text="Test requirements text"
        )
        created = service.create_client_requirements(requirements_data)
        
        # Retrieve requirements
        retrieved = service.get_client_requirements(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.client_name == "Test Client"
        assert retrieved.requirements_text == "Test requirements text"
    
    def test_list_client_requirements(self, db_session: Session):
        """Test listing client requirements with filtering"""
        service = ClientRequirementsService(db_session)
        
        # Create test requirements
        req1 = service.create_client_requirements(ClientRequirementsCreate(
            client_name="Client A",
            requirements_text="Requirements for Client A"
        ))
        
        req2 = service.create_client_requirements(ClientRequirementsCreate(
            client_name="Client B Corp",
            requirements_text="Requirements for Client B"
        ))
        
        # Test listing all
        all_reqs = service.list_client_requirements()
        assert len(all_reqs) >= 2
        
        # Test filtering by client name
        filtered_reqs = service.list_client_requirements(client_name="Client A")
        assert len(filtered_reqs) == 1
        assert filtered_reqs[0].client_name == "Client A"
    
    def test_process_requirements_file_json(self, db_session: Session, sample_schema_elements):
        """Test processing JSON requirements file"""
        service = ClientRequirementsService(db_session)
        
        json_content = json.dumps({
            "requirements": [
                "Report greenhouse gas emissions data",
                "Disclose energy consumption metrics"
            ]
        })
        
        result = service.process_requirements_file(
            file_content=json_content,
            filename="requirements.json",
            client_name="Test Client",
            schema_type=SchemaType.EU_ESRS_CSRD
        )
        
        assert result.client_name == "Test Client"
        assert result.requirements_text == json_content
        assert result.processed_requirements is not None
        assert len(result.processed_requirements) == 2
    
    def test_process_requirements_file_text(self, db_session: Session, sample_schema_elements):
        """Test processing text requirements file"""
        service = ClientRequirementsService(db_session)
        
        text_content = """
        1. Report on carbon emissions (Scope 1, 2, 3)
        2. Disclose water usage and conservation
        3. Provide waste management information
        """
        
        result = service.process_requirements_file(
            file_content=text_content,
            filename="requirements.txt",
            client_name="Test Client",
            schema_type=SchemaType.EU_ESRS_CSRD
        )
        
        assert result.client_name == "Test Client"
        assert result.requirements_text == text_content
        assert result.processed_requirements is not None
        assert len(result.processed_requirements) == 3
    
    def test_gap_analysis_with_coverage(self, db_session: Session, sample_documents_and_chunks):
        """Test gap analysis with some coverage"""
        service = ClientRequirementsService(db_session)
        
        # Create schema elements
        schema_elem1 = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change related disclosures"
        )
        schema_elem2 = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E3",
            element_name="Water Resources",
            description="Water usage and conservation"
        )
        db_session.add_all([schema_elem1, schema_elem2])
        db_session.commit()
        
        # Create client requirements with mappings
        requirements_data = ClientRequirementsCreate(
            client_name="Test Client",
            requirements_text="Report on climate and water",
            schema_mappings=[
                SchemaMapping(
                    requirement_id="req_1",
                    schema_element_id=schema_elem1.id,
                    confidence_score=0.9
                ),
                SchemaMapping(
                    requirement_id="req_2", 
                    schema_element_id=schema_elem2.id,
                    confidence_score=0.8
                )
            ],
            processed_requirements=[
                ProcessedRequirement(
                    requirement_id="req_1",
                    requirement_text="Report on climate change",
                    mapped_elements=[schema_elem1.id],
                    priority="high"
                ),
                ProcessedRequirement(
                    requirement_id="req_2",
                    requirement_text="Report on water usage",
                    mapped_elements=[schema_elem2.id],
                    priority="medium"
                )
            ]
        )
        
        client_req = service.create_client_requirements(requirements_data)
        
        # Create text chunk with schema element coverage
        document = sample_documents_and_chunks[0]
        chunk = TextChunk(
            document_id=document.id,
            content="Climate change emissions data and reporting",
            chunk_index=0,
            schema_elements=[schema_elem1.id]  # Only covers climate, not water
        )
        db_session.add(chunk)
        db_session.commit()
        
        # Perform gap analysis
        gap_analysis = service.perform_gap_analysis(client_req.id)
        
        assert gap_analysis['requirements_id'] == client_req.id
        assert gap_analysis['client_name'] == "Test Client"
        assert gap_analysis['total_requirements'] == 2
        assert gap_analysis['covered_requirements'] == 1  # Only climate covered
        assert gap_analysis['coverage_percentage'] == 50.0
        assert len(gap_analysis['available_documents']) >= 1
        assert len(gap_analysis['gaps']['uncovered_schema_elements']) == 1
        assert len(gap_analysis['gaps']['uncovered_requirements']) == 1
    
    def test_gap_analysis_no_coverage(self, db_session: Session):
        """Test gap analysis with no document coverage"""
        service = ClientRequirementsService(db_session)
        
        # Create client requirements without any matching documents
        requirements_data = ClientRequirementsCreate(
            client_name="Test Client",
            requirements_text="Report on biodiversity",
            processed_requirements=[
                ProcessedRequirement(
                    requirement_id="req_1",
                    requirement_text="Report on biodiversity impact",
                    mapped_elements=[],
                    priority="medium"
                )
            ]
        )
        
        client_req = service.create_client_requirements(requirements_data)
        
        # Perform gap analysis
        gap_analysis = service.perform_gap_analysis(client_req.id)
        
        assert gap_analysis['coverage_percentage'] == 0.0
        assert len(gap_analysis['available_documents']) == 0
        assert len(gap_analysis['gaps']['uncovered_requirements']) == 1
    
    def test_update_requirements_mapping(self, db_session: Session):
        """Test updating schema mappings for existing requirements"""
        service = ClientRequirementsService(db_session)
        
        # Create initial requirements
        requirements_data = ClientRequirementsCreate(
            client_name="Test Client",
            requirements_text="Test requirements",
            processed_requirements=[
                ProcessedRequirement(
                    requirement_id="req_1",
                    requirement_text="Test requirement",
                    mapped_elements=["old_elem_1"],
                    priority="medium"
                )
            ]
        )
        
        client_req = service.create_client_requirements(requirements_data)
        
        # Update mappings
        new_mappings = [
            SchemaMapping(
                requirement_id="req_1",
                schema_element_id="new_elem_1",
                confidence_score=0.95
            )
        ]
        
        updated = service.update_requirements_mapping(client_req.id, new_mappings)
        
        assert len(updated.schema_mappings) == 1
        assert updated.schema_mappings[0]['schema_element_id'] == "new_elem_1"
        assert updated.processed_requirements[0]['mapped_elements'] == ["new_elem_1"]
    
    def test_delete_client_requirements(self, db_session: Session):
        """Test deleting client requirements"""
        service = ClientRequirementsService(db_session)
        
        # Create requirements
        requirements_data = ClientRequirementsCreate(
            client_name="Test Client",
            requirements_text="Test requirements"
        )
        
        client_req = service.create_client_requirements(requirements_data)
        req_id = client_req.id
        
        # Delete requirements
        success = service.delete_client_requirements(req_id)
        assert success is True
        
        # Verify deletion
        retrieved = service.get_client_requirements(req_id)
        assert retrieved is None
        
        # Test deleting non-existent requirements
        success = service.delete_client_requirements("non_existent_id")
        assert success is False


@pytest.fixture
def sample_schema_elements(db_session: Session):
    """Create sample schema elements for testing"""
    elements = [
        SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change related disclosures including greenhouse gas emissions"
        ),
        SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E2",
            element_name="Pollution",
            description="Pollution prevention and control measures"
        ),
        SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E3",
            element_name="Water Resources",
            description="Water usage, conservation and management"
        )
    ]
    
    db_session.add_all(elements)
    db_session.commit()
    return elements


@pytest.fixture
def sample_documents_and_chunks(db_session: Session):
    """Create sample documents and text chunks for testing"""
    from app.models.schemas import DocumentType, ProcessingStatus
    
    document = Document(
        filename="test_document.pdf",
        file_path="/test/path/test_document.pdf",
        file_size=1024,
        document_type=DocumentType.PDF,
        schema_type=SchemaType.EU_ESRS_CSRD,
        processing_status=ProcessingStatus.COMPLETED
    )
    
    db_session.add(document)
    db_session.commit()
    
    return [document]
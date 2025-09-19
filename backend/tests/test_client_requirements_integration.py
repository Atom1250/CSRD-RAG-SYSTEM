"""
Integration tests for Client Requirements processing system
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from io import BytesIO

from app.models.database import SchemaElement, Document, TextChunk, ClientRequirements
from app.models.schemas import SchemaType, DocumentType, ProcessingStatus
from app.services.client_requirements_service import ClientRequirementsService


class TestClientRequirementsIntegration:
    """Integration tests for complete client requirements workflow"""
    
    def test_complete_requirements_processing_workflow(self, client: TestClient, db_session: Session):
        """Test complete workflow from upload to gap analysis"""
        
        # Step 1: Set up schema elements
        schema_elements = [
            SchemaElement(
                schema_type=SchemaType.EU_ESRS_CSRD,
                element_code="E1",
                element_name="Climate Change",
                description="Climate change mitigation and adaptation including greenhouse gas emissions"
            ),
            SchemaElement(
                schema_type=SchemaType.EU_ESRS_CSRD,
                element_code="E3",
                element_name="Water and Marine Resources",
                description="Water usage, conservation, and marine resource management"
            ),
            SchemaElement(
                schema_type=SchemaType.EU_ESRS_CSRD,
                element_code="S1",
                element_name="Own Workforce",
                description="Employment practices, working conditions, and employee rights"
            )
        ]
        db_session.add_all(schema_elements)
        db_session.commit()
        
        # Step 2: Set up documents with relevant content
        document1 = Document(
            filename="climate_guidance.pdf",
            file_path="/docs/climate_guidance.pdf",
            file_size=2048,
            document_type=DocumentType.PDF,
            schema_type=SchemaType.EU_ESRS_CSRD,
            processing_status=ProcessingStatus.COMPLETED
        )
        
        document2 = Document(
            filename="water_standards.pdf",
            file_path="/docs/water_standards.pdf",
            file_size=1536,
            document_type=DocumentType.PDF,
            schema_type=SchemaType.EU_ESRS_CSRD,
            processing_status=ProcessingStatus.COMPLETED
        )
        
        db_session.add_all([document1, document2])
        db_session.commit()
        
        # Step 3: Create text chunks with schema element mappings
        chunks = [
            TextChunk(
                document_id=document1.id,
                content="Organizations must report greenhouse gas emissions across Scope 1, 2, and 3 categories. Climate change mitigation strategies should be disclosed.",
                chunk_index=0,
                schema_elements=[schema_elements[0].id]  # Climate Change
            ),
            TextChunk(
                document_id=document1.id,
                content="Climate adaptation measures and resilience planning are required disclosures under ESRS E1.",
                chunk_index=1,
                schema_elements=[schema_elements[0].id]  # Climate Change
            ),
            TextChunk(
                document_id=document2.id,
                content="Water consumption, withdrawal, and discharge must be reported. Water conservation initiatives should be documented.",
                chunk_index=0,
                schema_elements=[schema_elements[1].id]  # Water Resources
            )
        ]
        db_session.add_all(chunks)
        db_session.commit()
        
        # Step 4: Upload client requirements
        requirements_content = json.dumps({
            "client": "Sustainable Corp Ltd",
            "requirements": [
                {
                    "id": "req_1",
                    "text": "Report comprehensive greenhouse gas emissions data including Scope 1, 2, and 3 emissions",
                    "priority": "high",
                    "category": "environmental"
                },
                {
                    "id": "req_2", 
                    "text": "Disclose water usage metrics and conservation efforts across all operations",
                    "priority": "high",
                    "category": "environmental"
                },
                {
                    "id": "req_3",
                    "text": "Provide information on employee diversity and inclusion programs",
                    "priority": "medium",
                    "category": "social"
                }
            ]
        })
        
        files = {
            "file": ("client_requirements.json", BytesIO(requirements_content.encode()), "application/json")
        }
        data = {
            "client_name": "Sustainable Corp Ltd",
            "schema_type": "EU_ESRS_CSRD"
        }
        
        upload_response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert upload_response.status_code == 200
        
        uploaded_req = upload_response.json()
        req_id = uploaded_req["id"]
        
        # Verify upload results
        assert uploaded_req["client_name"] == "Sustainable Corp Ltd"
        assert len(uploaded_req["processed_requirements"]) == 3
        assert uploaded_req["schema_mappings"] is not None
        
        # Step 5: Perform gap analysis
        gap_response = client.get(f"/api/client-requirements/{req_id}/gap-analysis")
        assert gap_response.status_code == 200
        
        gap_analysis = gap_response.json()
        
        # Verify gap analysis results
        assert gap_analysis["client_name"] == "Sustainable Corp Ltd"
        assert gap_analysis["total_requirements"] == 3
        
        # Should have partial coverage (climate and water covered, but not workforce)
        assert gap_analysis["coverage_percentage"] > 0
        assert gap_analysis["coverage_percentage"] < 100
        
        # Should have available documents
        assert len(gap_analysis["available_documents"]) >= 2
        
        # Should identify gaps for workforce requirements
        assert len(gap_analysis["gaps"]["uncovered_requirements"]) > 0
        
        # Should have recommendations
        assert len(gap_analysis["recommendations"]) > 0
        
        # Step 6: Test requirements retrieval
        get_response = client.get(f"/api/client-requirements/{req_id}")
        assert get_response.status_code == 200
        
        retrieved_req = get_response.json()
        assert retrieved_req["id"] == req_id
        assert retrieved_req["client_name"] == "Sustainable Corp Ltd"
    
    def test_requirements_mapping_accuracy(self, db_session: Session):
        """Test accuracy of requirements mapping to schema elements"""
        service = ClientRequirementsService(db_session)
        
        # Create specific schema elements
        climate_element = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change mitigation adaptation greenhouse gas emissions carbon footprint"
        )
        
        water_element = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E3", 
            element_name="Water Resources",
            description="Water consumption usage withdrawal discharge conservation management"
        )
        
        db_session.add_all([climate_element, water_element])
        db_session.commit()
        
        # Test climate-related requirement mapping
        climate_requirements = "Report on carbon emissions and greenhouse gas footprint"
        climate_mappings = service.schema_service.get_schema_mapping_for_requirements(
            climate_requirements, SchemaType.EU_ESRS_CSRD
        )
        
        # Should map to climate element with high confidence
        climate_mapping = next((m for m in climate_mappings if m['schema_element_id'] == climate_element.id), None)
        assert climate_mapping is not None
        assert climate_mapping['confidence_score'] > 0.5
        
        # Test water-related requirement mapping
        water_requirements = "Disclose water usage and conservation efforts"
        water_mappings = service.schema_service.get_schema_mapping_for_requirements(
            water_requirements, SchemaType.EU_ESRS_CSRD
        )
        
        # Should map to water element with high confidence
        water_mapping = next((m for m in water_mappings if m['schema_element_id'] == water_element.id), None)
        assert water_mapping is not None
        assert water_mapping['confidence_score'] > 0.5
        
        # Test unrelated requirement mapping
        unrelated_requirements = "Report on financial performance and revenue"
        unrelated_mappings = service.schema_service.get_schema_mapping_for_requirements(
            unrelated_requirements, SchemaType.EU_ESRS_CSRD
        )
        
        # Should have low or no confidence mappings
        for mapping in unrelated_mappings:
            assert mapping['confidence_score'] < 0.5
    
    def test_multi_format_requirements_processing(self, client: TestClient, db_session: Session):
        """Test processing requirements in different file formats"""
        
        # Create schema element for testing
        schema_element = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change and emissions reporting"
        )
        db_session.add(schema_element)
        db_session.commit()
        
        # Test JSON format
        json_content = json.dumps({
            "requirements": [
                "Report greenhouse gas emissions",
                "Disclose climate risks"
            ]
        })
        
        files = {"file": ("req.json", BytesIO(json_content.encode()), "application/json")}
        data = {"client_name": "JSON Client", "schema_type": "EU_ESRS_CSRD"}
        
        json_response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert json_response.status_code == 200
        json_result = json_response.json()
        assert len(json_result["processed_requirements"]) == 2
        
        # Test text format
        text_content = """
        1. Report on carbon emissions (mandatory)
        2. Disclose climate adaptation measures
        3. Provide energy consumption data
        """
        
        files = {"file": ("req.txt", BytesIO(text_content.encode()), "text/plain")}
        data = {"client_name": "Text Client", "schema_type": "EU_ESRS_CSRD"}
        
        text_response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert text_response.status_code == 200
        text_result = text_response.json()
        assert len(text_result["processed_requirements"]) == 3
        
        # Test markdown format
        md_content = """
        # Environmental Requirements
        
        - Carbon footprint reporting
        - Water usage disclosure
        - Waste management practices
        """
        
        files = {"file": ("req.md", BytesIO(md_content.encode()), "text/markdown")}
        data = {"client_name": "MD Client", "schema_type": "EU_ESRS_CSRD"}
        
        md_response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert md_response.status_code == 200
        md_result = md_response.json()
        assert len(md_result["processed_requirements"]) == 3
    
    def test_cross_schema_analysis(self, client: TestClient, db_session: Session):
        """Test analyzing requirements against different schema types"""
        
        # Create elements for both schema types
        eu_element = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="EU climate change reporting requirements"
        )
        
        uk_element = SchemaElement(
            schema_type=SchemaType.UK_SRD,
            element_code="ENV1",
            element_name="Environmental Impact",
            description="UK environmental impact disclosures"
        )
        
        db_session.add_all([eu_element, uk_element])
        db_session.commit()
        
        # Upload requirements
        requirements_content = "Report on environmental impact and climate change measures"
        
        files = {"file": ("req.txt", BytesIO(requirements_content.encode()), "text/plain")}
        data = {"client_name": "Cross Schema Client", "schema_type": "EU_ESRS_CSRD"}
        
        upload_response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert upload_response.status_code == 200
        req_id = upload_response.json()["id"]
        
        # Analyze against EU schema (original)
        eu_analysis = client.post(f"/api/client-requirements/{req_id}/analyze?schema_type=EU_ESRS_CSRD")
        assert eu_analysis.status_code == 200
        eu_result = eu_analysis.json()
        
        # Analyze against UK schema
        uk_analysis = client.post(f"/api/client-requirements/{req_id}/analyze?schema_type=UK_SRD")
        assert uk_analysis.status_code == 200
        uk_result = uk_analysis.json()
        
        # Both should have mappings but potentially different confidence scores
        assert len(eu_result["schema_mappings"]) > 0
        assert len(uk_result["schema_mappings"]) > 0
        assert eu_result["schema_type"] == "EU_ESRS_CSRD"
        assert uk_result["schema_type"] == "UK_SRD"
    
    def test_gap_analysis_with_partial_coverage(self, client: TestClient, db_session: Session):
        """Test gap analysis with realistic partial document coverage"""
        
        # Create comprehensive schema elements
        schema_elements = [
            SchemaElement(
                schema_type=SchemaType.EU_ESRS_CSRD,
                element_code="E1",
                element_name="Climate Change",
                description="Climate change mitigation and adaptation"
            ),
            SchemaElement(
                schema_type=SchemaType.EU_ESRS_CSRD,
                element_code="E2",
                element_name="Pollution",
                description="Pollution prevention and control"
            ),
            SchemaElement(
                schema_type=SchemaType.EU_ESRS_CSRD,
                element_code="S1",
                element_name="Own Workforce",
                description="Employment and working conditions"
            )
        ]
        db_session.add_all(schema_elements)
        db_session.commit()
        
        # Create document with partial coverage (only climate)
        document = Document(
            filename="climate_only.pdf",
            file_path="/docs/climate_only.pdf",
            file_size=1024,
            document_type=DocumentType.PDF,
            schema_type=SchemaType.EU_ESRS_CSRD,
            processing_status=ProcessingStatus.COMPLETED
        )
        db_session.add(document)
        db_session.commit()
        
        # Create chunk covering only climate element
        chunk = TextChunk(
            document_id=document.id,
            content="Climate change reporting requirements and greenhouse gas emissions",
            chunk_index=0,
            schema_elements=[schema_elements[0].id]  # Only climate
        )
        db_session.add(chunk)
        db_session.commit()
        
        # Upload comprehensive requirements
        requirements_content = json.dumps({
            "requirements": [
                "Report on greenhouse gas emissions and climate risks",
                "Disclose pollution prevention measures",
                "Provide workforce diversity information"
            ]
        })
        
        files = {"file": ("comprehensive_req.json", BytesIO(requirements_content.encode()), "application/json")}
        data = {"client_name": "Comprehensive Client", "schema_type": "EU_ESRS_CSRD"}
        
        upload_response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert upload_response.status_code == 200
        req_id = upload_response.json()["id"]
        
        # Perform gap analysis
        gap_response = client.get(f"/api/client-requirements/{req_id}/gap-analysis")
        assert gap_response.status_code == 200
        gap_analysis = gap_response.json()
        
        # Should show partial coverage
        assert gap_analysis["total_requirements"] == 3
        assert gap_analysis["covered_requirements"] < gap_analysis["total_requirements"]
        assert 0 < gap_analysis["coverage_percentage"] < 100
        
        # Should identify specific gaps
        assert len(gap_analysis["gaps"]["uncovered_requirements"]) > 0
        assert len(gap_analysis["gaps"]["uncovered_schema_elements"]) > 0
        
        # Should provide actionable recommendations
        assert len(gap_analysis["recommendations"]) > 0
        recommendations_text = " ".join(gap_analysis["recommendations"]).lower()
        assert any(keyword in recommendations_text for keyword in ["upload", "document", "coverage"])
    
    def test_requirements_update_workflow(self, client: TestClient, db_session: Session):
        """Test updating requirements mappings and re-analyzing"""
        
        # Create schema elements
        element1 = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E1",
            element_name="Climate Change",
            description="Climate change reporting"
        )
        element2 = SchemaElement(
            schema_type=SchemaType.EU_ESRS_CSRD,
            element_code="E3",
            element_name="Water Resources", 
            description="Water usage reporting"
        )
        db_session.add_all([element1, element2])
        db_session.commit()
        
        # Upload initial requirements
        requirements_content = "Report on environmental sustainability metrics"
        
        files = {"file": ("req.txt", BytesIO(requirements_content.encode()), "text/plain")}
        data = {"client_name": "Update Test Client", "schema_type": "EU_ESRS_CSRD"}
        
        upload_response = client.post("/api/client-requirements/upload", files=files, data=data)
        assert upload_response.status_code == 200
        req_id = upload_response.json()["id"]
        
        # Get initial mappings
        initial_response = client.get(f"/api/client-requirements/{req_id}")
        initial_mappings = initial_response.json()["schema_mappings"]
        
        # Update mappings to be more specific
        new_mappings = [
            {
                "requirement_id": "req_1",
                "schema_element_id": element1.id,
                "confidence_score": 0.95
            },
            {
                "requirement_id": "req_1",
                "schema_element_id": element2.id,
                "confidence_score": 0.85
            }
        ]
        
        update_response = client.put(f"/api/client-requirements/{req_id}/mappings", json=new_mappings)
        assert update_response.status_code == 200
        
        updated_req = update_response.json()
        assert len(updated_req["schema_mappings"]) == 2
        
        # Verify the mappings were updated correctly
        mapping_element_ids = [m["schema_element_id"] for m in updated_req["schema_mappings"]]
        assert element1.id in mapping_element_ids
        assert element2.id in mapping_element_ids
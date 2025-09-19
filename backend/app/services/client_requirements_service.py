"""
Client Requirements Service for processing client-specific reporting requirements,
analyzing them against regulatory schemas, and performing gap analysis.
"""
import json
import re
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.database import ClientRequirements, SchemaElement, Document, TextChunk
from ..models.schemas import (
    SchemaType, ClientRequirementsCreate, ClientRequirementsResponse,
    SchemaMapping, ProcessedRequirement
)
from .schema_service import SchemaService


class ClientRequirementsService:
    """Service for processing client requirements and mapping to regulatory schemas"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.schema_service = SchemaService(db_session)
    
    def process_requirements_file(self, file_content: str, filename: str, 
                                client_name: str, schema_type: SchemaType) -> ClientRequirementsResponse:
        """Process uploaded client requirements file and create requirements record"""
        
        # Parse requirements from file content
        parsed_requirements = self._parse_requirements_text(file_content, filename)
        
        # Analyze requirements and map to schema elements
        schema_mappings = self._analyze_and_map_requirements(parsed_requirements, schema_type)
        
        # Process individual requirements
        processed_requirements = self._process_individual_requirements(parsed_requirements, schema_mappings)
        
        # Create client requirements record
        requirements_data = ClientRequirementsCreate(
            client_name=client_name,
            requirements_text=file_content,
            schema_mappings=schema_mappings,
            processed_requirements=processed_requirements
        )
        
        return self.create_client_requirements(requirements_data)
    
    def _parse_requirements_text(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Parse requirements text into structured format"""
        requirements = []
        
        # Determine file type and parse accordingly
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == '.json':
            requirements = self._parse_json_requirements(content)
        elif file_ext in ['.txt', '.md']:
            requirements = self._parse_text_requirements(content)
        else:
            # Default text parsing for other formats
            requirements = self._parse_text_requirements(content)
        
        return requirements
    
    def _parse_json_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON formatted requirements"""
        try:
            data = json.loads(content)
            requirements = []
            
            if isinstance(data, dict):
                if 'requirements' in data:
                    for i, req in enumerate(data['requirements']):
                        if isinstance(req, str):
                            requirements.append({
                                'id': f"req_{i+1}",
                                'text': req,
                                'priority': 'medium'
                            })
                        elif isinstance(req, dict):
                            requirements.append({
                                'id': req.get('id', f"req_{i+1}"),
                                'text': req.get('text', req.get('requirement', '')),
                                'priority': req.get('priority', 'medium'),
                                'category': req.get('category', 'general')
                            })
                else:
                    # Treat entire object as single requirement
                    requirements.append({
                        'id': 'req_1',
                        'text': json.dumps(data, indent=2),
                        'priority': 'medium'
                    })
            elif isinstance(data, list):
                for i, req in enumerate(data):
                    if isinstance(req, str):
                        requirements.append({
                            'id': f"req_{i+1}",
                            'text': req,
                            'priority': 'medium'
                        })
                    elif isinstance(req, dict):
                        requirements.append({
                            'id': req.get('id', f"req_{i+1}"),
                            'text': req.get('text', str(req)),
                            'priority': req.get('priority', 'medium')
                        })
            
            return requirements
            
        except json.JSONDecodeError:
            # Fall back to text parsing
            return self._parse_text_requirements(content)
    
    def _parse_text_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Parse text formatted requirements"""
        requirements = []
        lines = content.split('\n')
        
        current_req = None
        req_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for numbered requirements (1., 2., etc.)
            numbered_match = re.match(r'^(\d+)\.?\s+(.+)', line)
            if numbered_match:
                if current_req:
                    requirements.append(current_req)
                
                current_req = {
                    'id': f"req_{numbered_match.group(1)}",
                    'text': numbered_match.group(2),
                    'priority': self._extract_priority(line)
                }
                continue
            
            # Check for bullet points (-, *, •)
            bullet_match = re.match(r'^[-*•]\s+(.+)', line)
            if bullet_match:
                if current_req:
                    requirements.append(current_req)
                
                current_req = {
                    'id': f"req_{req_counter}",
                    'text': bullet_match.group(1),
                    'priority': self._extract_priority(line)
                }
                req_counter += 1
                continue
            
            # Check for section headers (skip them)
            if (line.isupper() or line.startswith('#') or 
                line.endswith(':') or 
                (len(line.split()) <= 3 and not any(char.isdigit() for char in line))):
                # Skip headers but could be used for categorization
                continue
            
            # If we have a current requirement, append to its text
            if current_req:
                current_req['text'] += ' ' + line
            else:
                # Start new requirement
                current_req = {
                    'id': f"req_{req_counter}",
                    'text': line,
                    'priority': self._extract_priority(line)
                }
                req_counter += 1
        
        # Add the last requirement
        if current_req:
            requirements.append(current_req)
        
        # If no structured requirements found, treat entire content as one requirement
        if not requirements:
            requirements.append({
                'id': 'req_1',
                'text': content,
                'priority': 'medium'
            })
        
        return requirements
    
    def _extract_priority(self, text: str) -> str:
        """Extract priority from requirement text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['critical', 'urgent', 'high', 'mandatory', 'required']):
            return 'high'
        elif any(word in text_lower for word in ['low', 'optional', 'nice to have', 'future']):
            return 'low'
        else:
            return 'medium'
    
    def _analyze_and_map_requirements(self, requirements: List[Dict[str, Any]], 
                                    schema_type: SchemaType) -> List[SchemaMapping]:
        """Analyze requirements and map them to schema elements"""
        mappings = []
        
        for req in requirements:
            req_text = req['text']
            
            # Get schema mappings for this requirement
            element_mappings = self.schema_service.get_schema_mapping_for_requirements(
                req_text, schema_type
            )
            
            # Create schema mappings for top matches
            for mapping in element_mappings[:5]:  # Top 5 matches
                if mapping['confidence_score'] > 0.3:  # Minimum confidence threshold
                    mappings.append(SchemaMapping(
                        requirement_id=req['id'],
                        schema_element_id=mapping['schema_element_id'],
                        confidence_score=mapping['confidence_score']
                    ))
        
        return mappings
    
    def _process_individual_requirements(self, requirements: List[Dict[str, Any]], 
                                       mappings: List[SchemaMapping]) -> List[ProcessedRequirement]:
        """Process individual requirements and create structured records"""
        processed = []
        
        for req in requirements:
            # Find mappings for this requirement
            req_mappings = [m for m in mappings if m.requirement_id == req['id']]
            mapped_elements = [m.schema_element_id for m in req_mappings]
            
            processed_req = ProcessedRequirement(
                requirement_id=req['id'],
                requirement_text=req['text'],
                mapped_elements=mapped_elements,
                priority=req.get('priority', 'medium')
            )
            processed.append(processed_req)
        
        return processed
    
    def create_client_requirements(self, requirements_data: ClientRequirementsCreate) -> ClientRequirementsResponse:
        """Create new client requirements record"""
        
        # Convert Pydantic models to dict for JSON storage
        schema_mappings_dict = [mapping.model_dump() for mapping in requirements_data.schema_mappings] if requirements_data.schema_mappings else []
        processed_requirements_dict = [req.model_dump() for req in requirements_data.processed_requirements] if requirements_data.processed_requirements else []
        
        client_req = ClientRequirements(
            client_name=requirements_data.client_name,
            requirements_text=requirements_data.requirements_text,
            schema_mappings=schema_mappings_dict,
            processed_requirements=processed_requirements_dict
        )
        
        self.db.add(client_req)
        self.db.commit()
        self.db.refresh(client_req)
        
        return ClientRequirementsResponse.model_validate(client_req)
    
    def get_client_requirements(self, requirements_id: str) -> Optional[ClientRequirementsResponse]:
        """Get client requirements by ID"""
        client_req = self.db.query(ClientRequirements).filter(
            ClientRequirements.id == requirements_id
        ).first()
        
        if client_req:
            return ClientRequirementsResponse.model_validate(client_req)
        return None
    
    def list_client_requirements(self, client_name: Optional[str] = None) -> List[ClientRequirementsResponse]:
        """List all client requirements, optionally filtered by client name"""
        query = self.db.query(ClientRequirements)
        
        if client_name:
            query = query.filter(ClientRequirements.client_name.ilike(f"%{client_name}%"))
        
        client_reqs = query.order_by(ClientRequirements.upload_date.desc()).all()
        return [ClientRequirementsResponse.model_validate(req) for req in client_reqs]
    
    def perform_gap_analysis(self, requirements_id: str) -> Dict[str, Any]:
        """Perform gap analysis between client requirements and available documents"""
        client_req = self.db.query(ClientRequirements).filter(
            ClientRequirements.id == requirements_id
        ).first()
        
        if not client_req:
            raise ValueError(f"Client requirements not found: {requirements_id}")
        
        # Get all mapped schema elements
        mapped_element_ids = set()
        if client_req.schema_mappings:
            for mapping in client_req.schema_mappings:
                mapped_element_ids.add(mapping['schema_element_id'])
        
        # Get schema elements details
        mapped_elements = self.db.query(SchemaElement).filter(
            SchemaElement.id.in_(mapped_element_ids)
        ).all() if mapped_element_ids else []
        
        # Find available documents that cover these schema elements
        covered_elements = set()
        available_documents = []
        
        if mapped_element_ids:
            # Find text chunks that match these schema elements
            # Use a more compatible approach for JSON array matching
            matching_chunks = []
            all_chunks = self.db.query(TextChunk).all()
            
            for chunk in all_chunks:
                if chunk.schema_elements:
                    chunk_elements = set(chunk.schema_elements)
                    if chunk_elements.intersection(mapped_element_ids):
                        matching_chunks.append(chunk)
                        covered_elements.update(chunk.schema_elements)
            
            document_ids = set(chunk.document_id for chunk in matching_chunks)
            
            # Get document details
            if document_ids:
                documents = self.db.query(Document).filter(
                    Document.id.in_(document_ids)
                ).all()
                available_documents = [
                    {
                        'id': doc.id,
                        'filename': doc.filename,
                        'schema_type': doc.schema_type.value if doc.schema_type else None,
                        'upload_date': doc.upload_date.isoformat()
                    }
                    for doc in documents
                ]
        
        # Calculate coverage
        total_requirements = len(client_req.processed_requirements) if client_req.processed_requirements else 0
        covered_requirements = len([req for req in client_req.processed_requirements 
                                  if any(elem_id in covered_elements 
                                        for elem_id in req.get('mapped_elements', []))])
        
        coverage_percentage = (covered_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        # Identify gaps
        uncovered_elements = mapped_element_ids - covered_elements
        uncovered_element_details = []
        
        if uncovered_elements:
            uncovered_schema_elements = self.db.query(SchemaElement).filter(
                SchemaElement.id.in_(uncovered_elements)
            ).all()
            
            uncovered_element_details = [
                {
                    'id': elem.id,
                    'code': elem.element_code,
                    'name': elem.element_name,
                    'schema_type': elem.schema_type.value
                }
                for elem in uncovered_schema_elements
            ]
        
        # Identify requirements without coverage
        uncovered_requirements = []
        if client_req.processed_requirements:
            for req in client_req.processed_requirements:
                req_elements = set(req.get('mapped_elements', []))
                if not req_elements.intersection(covered_elements):
                    uncovered_requirements.append({
                        'id': req['requirement_id'],
                        'text': req['requirement_text'],
                        'priority': req.get('priority', 'medium')
                    })
        
        return {
            'requirements_id': requirements_id,
            'client_name': client_req.client_name,
            'total_requirements': total_requirements,
            'covered_requirements': covered_requirements,
            'coverage_percentage': round(coverage_percentage, 2),
            'available_documents': available_documents,
            'covered_schema_elements': len(covered_elements),
            'total_mapped_elements': len(mapped_element_ids),
            'gaps': {
                'uncovered_schema_elements': uncovered_element_details,
                'uncovered_requirements': uncovered_requirements
            },
            'recommendations': self._generate_gap_recommendations(uncovered_element_details, uncovered_requirements)
        }
    
    def _generate_gap_recommendations(self, uncovered_elements: List[Dict], 
                                    uncovered_requirements: List[Dict]) -> List[str]:
        """Generate recommendations based on gap analysis"""
        recommendations = []
        
        if uncovered_elements:
            schema_types = set(elem['schema_type'] for elem in uncovered_elements)
            for schema_type in schema_types:
                recommendations.append(
                    f"Upload additional {schema_type} regulatory documents to cover missing schema elements"
                )
        
        if uncovered_requirements:
            high_priority_uncovered = [req for req in uncovered_requirements if req['priority'] == 'high']
            if high_priority_uncovered:
                recommendations.append(
                    f"Prioritize finding documents for {len(high_priority_uncovered)} high-priority uncovered requirements"
                )
        
        if not uncovered_elements and not uncovered_requirements:
            recommendations.append("All requirements are covered by available documents")
        elif len(uncovered_requirements) < 3:
            recommendations.append("Good coverage achieved - only minor gaps remain")
        
        return recommendations
    
    def update_requirements_mapping(self, requirements_id: str, 
                                  new_mappings: List[SchemaMapping]) -> ClientRequirementsResponse:
        """Update schema mappings for existing client requirements"""
        client_req = self.db.query(ClientRequirements).filter(
            ClientRequirements.id == requirements_id
        ).first()
        
        if not client_req:
            raise ValueError(f"Client requirements not found: {requirements_id}")
        
        # Update mappings
        client_req.schema_mappings = [mapping.model_dump() for mapping in new_mappings]
        
        # Reprocess requirements with new mappings
        if client_req.processed_requirements:
            updated_processed = []
            for req in client_req.processed_requirements:
                req_mappings = [m for m in new_mappings if m.requirement_id == req['requirement_id']]
                req['mapped_elements'] = [m.schema_element_id for m in req_mappings]
                updated_processed.append(req)
            
            client_req.processed_requirements = updated_processed
        
        self.db.commit()
        self.db.refresh(client_req)
        
        return ClientRequirementsResponse.model_validate(client_req)
    
    def delete_client_requirements(self, requirements_id: str) -> bool:
        """Delete client requirements record"""
        client_req = self.db.query(ClientRequirements).filter(
            ClientRequirements.id == requirements_id
        ).first()
        
        if client_req:
            self.db.delete(client_req)
            self.db.commit()
            return True
        
        return False
"""
Schema Service for managing EU ESRS/CSRD and UK SRD schema definitions
and document classification against schema elements.
"""
import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import SchemaElement, Document, TextChunk
from ..models.schemas import SchemaType, SchemaElementCreate, SchemaElementResponse
from ..core.config import settings


class SchemaService:
    """Service for managing schema definitions and document classification"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = settings
        self.schema_data_path = Path(__file__).parent.parent.parent / "data" / "schemas"
    
    def load_schema_definitions(self, schema_type: SchemaType) -> List[SchemaElement]:
        """Load schema definitions from JSON files and store in database"""
        schema_file = self._get_schema_file_path(schema_type)
        
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # Clear existing schema elements for this type
        self.db.query(SchemaElement).filter(
            SchemaElement.schema_type == schema_type
        ).delete()
        
        # Load new schema elements
        elements = []
        for element_data in schema_data.get('elements', []):
            element = self._create_schema_element(element_data, schema_type)
            elements.append(element)
        
        self.db.commit()
        return elements
    
    def _get_schema_file_path(self, schema_type: SchemaType) -> Path:
        """Get the file path for a schema type"""
        if schema_type == SchemaType.EU_ESRS_CSRD:
            return self.schema_data_path / "eu_esrs_csrd.json"
        elif schema_type == SchemaType.UK_SRD:
            return self.schema_data_path / "uk_srd.json"
        else:
            raise ValueError(f"Unknown schema type: {schema_type}")
    
    def _create_schema_element(self, element_data: Dict, schema_type: SchemaType, 
                             parent_id: Optional[str] = None) -> SchemaElement:
        """Create a schema element from JSON data"""
        element = SchemaElement(
            schema_type=schema_type,
            element_code=element_data['code'],
            element_name=element_data['name'],
            description=element_data.get('description'),
            parent_element_id=parent_id,
            requirements=element_data.get('requirements', [])
        )
        
        self.db.add(element)
        self.db.flush()  # Get the ID
        
        # Handle child elements recursively
        for child_data in element_data.get('children', []):
            self._create_schema_element(child_data, schema_type, element.id)
        
        return element
    
    def get_schema_elements(self, schema_type: SchemaType, 
                          parent_id: Optional[str] = None) -> List[SchemaElementResponse]:
        """Get schema elements by type and optional parent"""
        query = self.db.query(SchemaElement).filter(
            SchemaElement.schema_type == schema_type
        )
        
        if parent_id is None:
            query = query.filter(SchemaElement.parent_element_id.is_(None))
        else:
            query = query.filter(SchemaElement.parent_element_id == parent_id)
        
        elements = query.all()
        return [SchemaElementResponse.from_orm(element) for element in elements]
    
    def classify_document(self, document: Document, content: str) -> List[str]:
        """Classify document content against schema elements"""
        if not document.schema_type:
            return []
        
        # Get all schema elements for the document's schema type
        schema_elements = self.db.query(SchemaElement).filter(
            SchemaElement.schema_type == document.schema_type
        ).all()
        
        matched_elements = []
        content_lower = content.lower()
        
        for element in schema_elements:
            if self._matches_schema_element(content_lower, element):
                matched_elements.append(element.id)
        
        return matched_elements
    
    def _matches_schema_element(self, content: str, element: SchemaElement) -> bool:
        """Check if content matches a schema element based on keywords and requirements"""
        # Check element name and code
        if element.element_name.lower() in content or element.element_code.lower() in content:
            return True
        
        # Check description keywords
        if element.description:
            description_words = element.description.lower().split()
            for word in description_words:
                if len(word) > 4 and word in content:  # Only check meaningful words
                    return True
        
        # Check requirements keywords
        if element.requirements:
            for requirement in element.requirements:
                requirement_words = requirement.lower().split()
                for word in requirement_words:
                    if len(word) > 4 and word in content:
                        return True
        
        return False
    
    def classify_text_chunks(self, document_id: str) -> int:
        """Classify all text chunks for a document and update their schema elements"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document or not document.schema_type:
            return 0
        
        text_chunks = self.db.query(TextChunk).filter(
            TextChunk.document_id == document_id
        ).all()
        
        classified_count = 0
        for chunk in text_chunks:
            matched_elements = self.classify_document(document, chunk.content)
            if matched_elements:
                chunk.schema_elements = matched_elements
                classified_count += 1
        
        self.db.commit()
        return classified_count
    
    def get_schema_mapping_for_requirements(self, requirements_text: str, 
                                          schema_type: SchemaType) -> List[Dict]:
        """Map client requirements to schema elements"""
        schema_elements = self.db.query(SchemaElement).filter(
            SchemaElement.schema_type == schema_type
        ).all()
        
        mappings = []
        requirements_lower = requirements_text.lower()
        
        for element in schema_elements:
            confidence = self._calculate_mapping_confidence(requirements_lower, element)
            if confidence > 0.3:  # Threshold for relevance
                mappings.append({
                    'schema_element_id': element.id,
                    'element_code': element.element_code,
                    'element_name': element.element_name,
                    'confidence_score': confidence
                })
        
        # Sort by confidence score descending
        mappings.sort(key=lambda x: x['confidence_score'], reverse=True)
        return mappings
    
    def _calculate_mapping_confidence(self, requirements_text: str, 
                                    element: SchemaElement) -> float:
        """Calculate confidence score for mapping requirements to schema element"""
        score = 0.0
        requirements_lower = requirements_text.lower()
        
        # Check element name match (partial and full)
        element_name_lower = element.element_name.lower()
        if element_name_lower in requirements_lower:
            score += 0.4
        else:
            # Check for partial matches of element name words
            element_words = element_name_lower.split()
            for word in element_words:
                if len(word) > 3 and word in requirements_lower:
                    score += 0.1
        
        # Check element code match
        if element.element_code.lower() in requirements_lower:
            score += 0.3
        
        # Enhanced keyword matching from description
        if element.description:
            description_lower = element.description.lower()
            
            # Key sustainability terms mapping
            climate_terms = ['climate', 'carbon', 'emissions', 'greenhouse', 'ghg', 'scope']
            water_terms = ['water', 'usage', 'consumption', 'conservation', 'marine']
            workforce_terms = ['employee', 'workforce', 'diversity', 'inclusion', 'working', 'employment']
            
            # Check for domain-specific terms
            if 'climate' in element_name_lower or 'e1' in element.element_code.lower():
                if any(term in requirements_lower for term in climate_terms):
                    score += 0.3
            
            if 'water' in element_name_lower or 'e3' in element.element_code.lower():
                if any(term in requirements_lower for term in water_terms):
                    score += 0.3
            
            if 'workforce' in element_name_lower or 's1' in element.element_code.lower():
                if any(term in requirements_lower for term in workforce_terms):
                    score += 0.3
            
            # General keyword matching
            description_words = set(word for word in description_lower.split() if len(word) > 3)
            requirements_words = set(word for word in requirements_lower.split() if len(word) > 3)
            common_words = description_words.intersection(requirements_words)
            
            if common_words and description_words:
                score += 0.2 * (len(common_words) / len(description_words))
        
        # Check requirements keywords if available
        if element.requirements:
            for requirement in element.requirements:
                requirement_lower = requirement.lower()
                requirement_words = set(word for word in requirement_lower.split() if len(word) > 3)
                requirements_words = set(word for word in requirements_lower.split() if len(word) > 3)
                common_words = requirement_words.intersection(requirements_words)
                
                if common_words and requirement_words:
                    score += 0.1 * (len(common_words) / len(requirement_words))
        
        return min(score, 1.0)  # Cap at 1.0
    
    def update_document_schema_classification(self, document_id: str, 
                                            schema_type: SchemaType) -> bool:
        """Update document schema type and reclassify its content"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        document.schema_type = schema_type
        
        # Reclassify all text chunks
        self.classify_text_chunks(document_id)
        
        self.db.commit()
        return True
    
    def get_unclassified_documents(self) -> List[Document]:
        """Get documents that haven't been classified with a schema type"""
        return self.db.query(Document).filter(
            Document.schema_type.is_(None)
        ).all()
    
    def initialize_schemas(self) -> Dict[str, int]:
        """Initialize all schema definitions from files"""
        results = {}
        
        for schema_type in SchemaType:
            try:
                elements = self.load_schema_definitions(schema_type)
                results[schema_type.value] = len(elements)
            except FileNotFoundError as e:
                results[schema_type.value] = f"Error: {str(e)}"
        
        return results
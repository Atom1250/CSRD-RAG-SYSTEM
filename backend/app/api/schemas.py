"""
API endpoints for schema management and document classification
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.database_config import get_db
from ..models.schemas import (
    SchemaType, SchemaElementResponse, DocumentResponse,
    SchemaMapping, ClientRequirementsCreate
)
from ..services.schema_service import SchemaService


router = APIRouter(prefix="/schemas", tags=["schemas"])


def get_schema_service(db: Session = Depends(get_db)) -> SchemaService:
    """Dependency to get schema service instance"""
    return SchemaService(db)


@router.post("/initialize", response_model=Dict[str, int])
async def initialize_schemas(
    schema_service: SchemaService = Depends(get_schema_service)
):
    """
    Initialize all schema definitions from JSON files.
    This loads EU ESRS/CSRD and UK SRD schema definitions into the database.
    """
    try:
        results = schema_service.initialize_schemas()
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize schemas: {str(e)}"
        )


@router.get("/elements/{schema_type}", response_model=List[SchemaElementResponse])
async def get_schema_elements(
    schema_type: SchemaType,
    parent_id: Optional[str] = None,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """
    Get schema elements by type and optional parent element.
    Returns hierarchical schema structure for the specified reporting standard.
    """
    try:
        elements = schema_service.get_schema_elements(schema_type, parent_id)
        return elements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve schema elements: {str(e)}"
        )


@router.post("/classify/document/{document_id}")
async def classify_document(
    document_id: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """
    Classify all text chunks for a document against its schema type.
    Updates the schema_elements field for each text chunk.
    """
    try:
        classified_count = schema_service.classify_text_chunks(document_id)
        return {
            "document_id": document_id,
            "classified_chunks": classified_count,
            "message": f"Successfully classified {classified_count} text chunks"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify document: {str(e)}"
        )


@router.put("/document/{document_id}/schema/{schema_type}")
async def update_document_schema(
    document_id: str,
    schema_type: SchemaType,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """
    Update document schema type and reclassify its content.
    This allows manual correction of document schema classification.
    """
    try:
        success = schema_service.update_document_schema_classification(document_id, schema_type)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "document_id": document_id,
            "schema_type": schema_type,
            "message": "Document schema updated and content reclassified"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document schema: {str(e)}"
        )


@router.get("/unclassified", response_model=List[DocumentResponse])
async def get_unclassified_documents(
    schema_service: SchemaService = Depends(get_schema_service)
):
    """
    Get all documents that haven't been classified with a schema type.
    These documents require manual schema assignment.
    """
    try:
        documents = schema_service.get_unclassified_documents()
        return [DocumentResponse.from_orm(doc) for doc in documents]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve unclassified documents: {str(e)}"
        )


@router.post("/map-requirements/{schema_type}")
async def map_client_requirements(
    schema_type: SchemaType,
    requirements_text: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """
    Map client requirements text to relevant schema elements.
    Returns schema elements with confidence scores for requirement mapping.
    """
    try:
        if not requirements_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requirements text cannot be empty"
            )
        
        mappings = schema_service.get_schema_mapping_for_requirements(
            requirements_text, schema_type
        )
        
        return {
            "schema_type": schema_type,
            "requirements_text": requirements_text,
            "mappings": mappings,
            "total_mappings": len(mappings)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to map requirements: {str(e)}"
        )


@router.get("/types", response_model=List[str])
async def get_schema_types():
    """
    Get all available schema types.
    Returns list of supported reporting standards.
    """
    return [schema_type.value for schema_type in SchemaType]


@router.get("/stats/{schema_type}")
async def get_schema_statistics(
    schema_type: SchemaType,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """
    Get statistics about schema elements and document classification.
    Provides overview of schema usage and document coverage.
    """
    try:
        # Get total schema elements
        elements = schema_service.get_schema_elements(schema_type)
        total_elements = len(elements)
        
        # Get documents using this schema
        from ..models.database import Document
        db = schema_service.db
        documents_with_schema = db.query(Document).filter(
            Document.schema_type == schema_type
        ).count()
        
        # Get classified text chunks
        from ..models.database import TextChunk
        classified_chunks = db.query(TextChunk).join(Document).filter(
            Document.schema_type == schema_type,
            TextChunk.schema_elements.isnot(None)
        ).count()
        
        total_chunks = db.query(TextChunk).join(Document).filter(
            Document.schema_type == schema_type
        ).count()
        
        classification_rate = (classified_chunks / total_chunks * 100) if total_chunks > 0 else 0
        
        return {
            "schema_type": schema_type,
            "total_elements": total_elements,
            "documents_using_schema": documents_with_schema,
            "classified_chunks": classified_chunks,
            "total_chunks": total_chunks,
            "classification_rate_percent": round(classification_rate, 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve schema statistics: {str(e)}"
        )
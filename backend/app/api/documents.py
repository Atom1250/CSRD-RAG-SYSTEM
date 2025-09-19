"""
Document management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.models.database_config import get_db
from app.models.schemas import (
    DocumentResponse, 
    DocumentFilters, 
    DocumentType, 
    SchemaType, 
    ProcessingStatus
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Dependency to get document service instance"""
    return DocumentService(db)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    schema_type: Optional[SchemaType] = Query(None, description="Schema type for document classification"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a new document
    
    - **file**: Document file (PDF, DOCX, or TXT)
    - **schema_type**: Optional schema type for classification (EU_ESRS_CSRD or UK_SRD)
    
    Returns the uploaded document information with metadata.
    """
    return await document_service.upload_document(file, schema_type)


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    schema_type: Optional[SchemaType] = Query(None, description="Filter by schema type"),
    processing_status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    filename_contains: Optional[str] = Query(None, description="Filter by filename containing text"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Retrieve all documents with optional filtering
    
    - **document_type**: Filter by document type (pdf, docx, txt)
    - **schema_type**: Filter by schema type (EU_ESRS_CSRD, UK_SRD)
    - **processing_status**: Filter by processing status (pending, processing, completed, failed)
    - **filename_contains**: Filter by filename containing specified text
    
    Returns a list of documents matching the filters.
    """
    filters = DocumentFilters(
        document_type=document_type,
        schema_type=schema_type,
        processing_status=processing_status,
        filename_contains=filename_contains
    )
    return document_service.get_documents(filters)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Retrieve a specific document by ID
    
    - **document_id**: Unique document identifier
    
    Returns the document information if found.
    """
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete a document and its associated file
    
    - **document_id**: Unique document identifier
    
    Returns success message if deleted.
    """
    success = document_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully", "document_id": document_id}


@router.get("/{document_id}/metadata", response_model=dict)
async def get_document_metadata(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Retrieve document metadata
    
    - **document_id**: Unique document identifier
    
    Returns the document metadata.
    """
    document = document_service.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document.document_metadata or {}


@router.put("/{document_id}/metadata")
async def update_document_metadata(
    document_id: str,
    metadata_update: dict,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Update document metadata
    
    - **document_id**: Unique document identifier
    - **metadata_update**: Metadata fields to update
    
    Returns the updated document information.
    """
    updated_document = document_service.update_document_metadata(document_id, metadata_update)
    if not updated_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return updated_document
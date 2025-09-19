"""
FastAPI endpoints for client requirements processing and management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ..models.database_config import get_db
from ..models.schemas import (
    SchemaType, ClientRequirementsCreate, ClientRequirementsResponse,
    SchemaMapping, ProcessedRequirement
)
from ..services.client_requirements_service import ClientRequirementsService


router = APIRouter(prefix="/client-requirements", tags=["client-requirements"])


@router.post("/upload", response_model=ClientRequirementsResponse)
async def upload_client_requirements(
    file: UploadFile = File(...),
    client_name: str = Form(...),
    schema_type: SchemaType = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process client requirements file
    
    Accepts various file formats (JSON, TXT, MD) and processes them
    to extract requirements and map them to regulatory schema elements.
    """
    # Validate file type
    allowed_extensions = {'.json', '.txt', '.md', '.csv'}
    file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    try:
        content = await file.read()
        file_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be in UTF-8 encoding"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading file: {str(e)}"
        )
    
    # Validate content is not empty
    if not file_content.strip():
        raise HTTPException(
            status_code=400,
            detail="File content cannot be empty"
        )
    
    # Process requirements
    try:
        service = ClientRequirementsService(db)
        result = service.process_requirements_file(
            file_content=file_content,
            filename=file.filename,
            client_name=client_name,
            schema_type=schema_type
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing requirements: {str(e)}"
        )


@router.post("/", response_model=ClientRequirementsResponse)
def create_client_requirements(
    requirements: ClientRequirementsCreate,
    db: Session = Depends(get_db)
):
    """
    Create client requirements from structured data
    
    Alternative to file upload for programmatic creation of requirements.
    """
    try:
        service = ClientRequirementsService(db)
        return service.create_client_requirements(requirements)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating requirements: {str(e)}"
        )


@router.get("/", response_model=List[ClientRequirementsResponse])
def list_client_requirements(
    client_name: Optional[str] = Query(None, description="Filter by client name"),
    db: Session = Depends(get_db)
):
    """
    List all client requirements with optional filtering
    """
    try:
        service = ClientRequirementsService(db)
        return service.list_client_requirements(client_name=client_name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing requirements: {str(e)}"
        )


@router.get("/{requirements_id}", response_model=ClientRequirementsResponse)
def get_client_requirements(
    requirements_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific client requirements by ID
    """
    try:
        service = ClientRequirementsService(db)
        result = service.get_client_requirements(requirements_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Client requirements not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving requirements: {str(e)}"
        )


@router.get("/{requirements_id}/gap-analysis")
def perform_gap_analysis(
    requirements_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform gap analysis between client requirements and available documents
    
    Returns detailed analysis of coverage, gaps, and recommendations.
    """
    try:
        service = ClientRequirementsService(db)
        return service.perform_gap_analysis(requirements_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing gap analysis: {str(e)}"
        )


@router.put("/{requirements_id}/mappings", response_model=ClientRequirementsResponse)
def update_requirements_mapping(
    requirements_id: str,
    mappings: List[SchemaMapping],
    db: Session = Depends(get_db)
):
    """
    Update schema mappings for existing client requirements
    
    Allows manual adjustment of automatic schema mappings.
    """
    try:
        service = ClientRequirementsService(db)
        return service.update_requirements_mapping(requirements_id, mappings)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating mappings: {str(e)}"
        )


@router.delete("/{requirements_id}")
def delete_client_requirements(
    requirements_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete client requirements record
    """
    try:
        service = ClientRequirementsService(db)
        success = service.delete_client_requirements(requirements_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Client requirements not found"
            )
        
        return {"message": "Client requirements deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting requirements: {str(e)}"
        )


@router.post("/{requirements_id}/analyze")
def analyze_requirements_text(
    requirements_id: str,
    schema_type: SchemaType,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Re-analyze existing requirements against a different schema type
    
    Useful for comparing requirements against multiple regulatory frameworks.
    """
    try:
        service = ClientRequirementsService(db)
        
        # Get existing requirements
        client_req = service.get_client_requirements(requirements_id)
        if not client_req:
            raise HTTPException(
                status_code=404,
                detail="Client requirements not found"
            )
        
        # Parse and analyze against new schema type
        parsed_requirements = service._parse_requirements_text(
            client_req.requirements_text, 
            f"requirements_{requirements_id}.txt"
        )
        
        # Get new mappings
        new_mappings = service._analyze_and_map_requirements(parsed_requirements, schema_type)
        
        # Process requirements with new mappings
        processed_requirements = service._process_individual_requirements(
            parsed_requirements, new_mappings
        )
        
        return {
            "requirements_id": requirements_id,
            "schema_type": schema_type.value,
            "parsed_requirements": parsed_requirements,
            "schema_mappings": [mapping.model_dump() for mapping in new_mappings],
            "processed_requirements": [req.model_dump() for req in processed_requirements]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing requirements: {str(e)}"
        )
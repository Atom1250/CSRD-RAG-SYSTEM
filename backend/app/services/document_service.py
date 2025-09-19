"""
Document service for handling file uploads, storage, and metadata management
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import mimetypes
import hashlib

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.database import Document, DocumentType, ProcessingStatus
from app.models.schemas import DocumentCreate, DocumentResponse, DocumentFilters
from app.core.config import settings


class DocumentService:
    """Service for managing document uploads and storage"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.upload_directory)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> DocumentType:
        """
        Validate uploaded file format and size
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            DocumentType: Validated document type
            
        Raises:
            HTTPException: If file validation fails
        """
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size {file.size} exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Get file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        
        # Validate file type
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_extension}' not supported. Allowed types: {settings.allowed_file_types}"
            )
        
        # Map extension to DocumentType
        type_mapping = {
            'pdf': DocumentType.PDF,
            'docx': DocumentType.DOCX,
            'txt': DocumentType.TXT
        }
        
        return type_mapping[file_extension]
    
    def extract_metadata(self, file: UploadFile, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from uploaded file
        
        Args:
            file: FastAPI UploadFile object
            file_path: Path to stored file
            
        Returns:
            Dict containing file metadata
        """
        metadata = {
            'original_filename': file.filename,
            'content_type': file.content_type,
            'upload_timestamp': datetime.utcnow().isoformat(),
        }
        
        # Get file stats
        if file_path.exists():
            stat = file_path.stat()
            metadata.update({
                'file_size_bytes': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # Calculate file hash for integrity checking
        if file_path.exists():
            metadata['file_hash'] = self._calculate_file_hash(file_path)
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            metadata['detected_mime_type'] = mime_type
        
        return metadata
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity checking"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename to avoid conflicts"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name = Path(original_filename).stem
        extension = Path(original_filename).suffix
        return f"{timestamp}_{name}{extension}"
    
    async def upload_document(
        self, 
        file: UploadFile, 
        schema_type: Optional[str] = None
    ) -> DocumentResponse:
        """
        Upload and store a document with metadata extraction
        
        Args:
            file: FastAPI UploadFile object
            schema_type: Optional schema type for classification
            
        Returns:
            DocumentResponse: Created document information
        """
        # Validate file
        document_type = self.validate_file(file)
        
        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = self.upload_dir / unique_filename
        
        try:
            # Save file to disk
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Get actual file size
            file_size = file_path.stat().st_size
            
            # Validate file size after upload
            if file_size > settings.max_file_size:
                file_path.unlink()  # Delete the file
                raise HTTPException(
                    status_code=413,
                    detail=f"File size {file_size} exceeds maximum allowed size of {settings.max_file_size} bytes"
                )
            
            # Extract metadata
            metadata = self.extract_metadata(file, file_path)
            
            # Create document record
            document_data = DocumentCreate(
                filename=file.filename,
                file_size=file_size,
                file_path=str(file_path),
                document_type=document_type,
                schema_type=schema_type,
                document_metadata=metadata
            )
            
            # Save to database
            db_document = Document(
                filename=document_data.filename,
                file_path=document_data.file_path,
                file_size=document_data.file_size,
                document_type=document_data.document_type,
                schema_type=document_data.schema_type,
                processing_status=ProcessingStatus.PENDING,
                document_metadata=document_data.document_metadata
            )
            
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            
            return DocumentResponse.model_validate(db_document)
            
        except Exception as e:
            # Clean up file if database operation fails
            if file_path.exists():
                file_path.unlink()
            
            if isinstance(e, HTTPException):
                raise e
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload document: {str(e)}"
            )
    
    def get_documents(self, filters: Optional[DocumentFilters] = None) -> List[DocumentResponse]:
        """
        Retrieve documents with optional filtering
        
        Args:
            filters: Optional filters for document retrieval
            
        Returns:
            List of DocumentResponse objects
        """
        query = self.db.query(Document)
        
        if filters:
            if filters.document_type:
                query = query.filter(Document.document_type == filters.document_type)
            if filters.schema_type:
                query = query.filter(Document.schema_type == filters.schema_type)
            if filters.processing_status:
                query = query.filter(Document.processing_status == filters.processing_status)
            if filters.filename_contains:
                query = query.filter(Document.filename.contains(filters.filename_contains))
            if filters.upload_date_from:
                query = query.filter(Document.upload_date >= filters.upload_date_from)
            if filters.upload_date_to:
                query = query.filter(Document.upload_date <= filters.upload_date_to)
        
        documents = query.order_by(Document.upload_date.desc()).all()
        return [DocumentResponse.model_validate(doc) for doc in documents]
    
    def get_document_by_id(self, document_id: str) -> Optional[DocumentResponse]:
        """
        Retrieve a specific document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            DocumentResponse or None if not found
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if document:
            return DocumentResponse.model_validate(document)
        return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated file
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # Delete file from filesystem
        file_path = Path(document.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                # Log error but continue with database deletion
                pass
        
        # Delete from database
        self.db.delete(document)
        self.db.commit()
        
        return True
    
    def update_document_metadata(
        self, 
        document_id: str, 
        metadata_update: Dict[str, Any]
    ) -> Optional[DocumentResponse]:
        """
        Update document metadata
        
        Args:
            document_id: Document ID
            metadata_update: Metadata fields to update
            
        Returns:
            Updated DocumentResponse or None if not found
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None
        
        # Update metadata
        if document.document_metadata:
            document.document_metadata.update(metadata_update)
        else:
            document.document_metadata = metadata_update
        
        self.db.commit()
        self.db.refresh(document)
        
        return DocumentResponse.model_validate(document)
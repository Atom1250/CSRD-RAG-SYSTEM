"""
Input validation utilities for backend API endpoints
"""
import re
import mimetypes
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from pydantic import BaseModel, validator, ValidationError


class ValidationResult(BaseModel):
    """Result of validation operation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class FileValidationConfig(BaseModel):
    """Configuration for file validation"""
    max_size: int = 50 * 1024 * 1024  # 50MB
    min_size: int = 1024  # 1KB
    allowed_mime_types: List[str] = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ]
    allowed_extensions: List[str] = ['.pdf', '.docx', '.txt']
    max_filename_length: int = 255
    forbidden_patterns: List[str] = [r'\.\.', r'[<>:"|?*]', r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$']


class TextValidationConfig(BaseModel):
    """Configuration for text validation"""
    min_length: int = 0
    max_length: int = 10000
    required: bool = False
    pattern: Optional[str] = None
    pattern_message: str = "Invalid format"


def validate_file(file: UploadFile, config: Optional[FileValidationConfig] = None) -> ValidationResult:
    """
    Validate uploaded file against configuration
    
    Args:
        file: FastAPI UploadFile object
        config: Validation configuration
        
    Returns:
        ValidationResult with validation status and errors
    """
    if config is None:
        config = FileValidationConfig()
    
    errors = []
    warnings = []
    
    # Check if file exists
    if not file or not file.filename:
        errors.append("No file provided")
        return ValidationResult(is_valid=False, errors=errors)
    
    # Validate filename
    filename = file.filename.strip()
    if not filename:
        errors.append("Filename cannot be empty")
    
    if len(filename) > config.max_filename_length:
        errors.append(f"Filename too long (max {config.max_filename_length} characters)")
    
    # Check for forbidden patterns in filename
    for pattern in config.forbidden_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            errors.append(f"Filename contains forbidden pattern: {pattern}")
    
    # Validate file extension
    file_extension = Path(filename).suffix.lower()
    if file_extension not in [ext.lower() for ext in config.allowed_extensions]:
        errors.append(
            f"File extension '{file_extension}' not allowed. "
            f"Allowed extensions: {', '.join(config.allowed_extensions)}"
        )
    
    # Validate MIME type
    content_type = file.content_type
    if content_type not in config.allowed_mime_types:
        # Try to guess MIME type from filename
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type and guessed_type in config.allowed_mime_types:
            warnings.append(f"MIME type mismatch, but filename suggests valid type: {guessed_type}")
        else:
            errors.append(
                f"File type '{content_type}' not allowed. "
                f"Allowed types: {', '.join(config.allowed_mime_types)}"
            )
    
    # Validate file size (if available)
    if hasattr(file, 'size') and file.size is not None:
        if file.size > config.max_size:
            errors.append(
                f"File size ({format_file_size(file.size)}) exceeds maximum "
                f"allowed size ({format_file_size(config.max_size)})"
            )
        
        if file.size < config.min_size:
            errors.append(
                f"File size ({format_file_size(file.size)}) below minimum "
                f"required size ({format_file_size(config.min_size)})"
            )
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_text(text: str, config: Optional[TextValidationConfig] = None) -> ValidationResult:
    """
    Validate text input against configuration
    
    Args:
        text: Text to validate
        config: Validation configuration
        
    Returns:
        ValidationResult with validation status and errors
    """
    if config is None:
        config = TextValidationConfig()
    
    errors = []
    warnings = []
    
    # Handle None or non-string input
    if text is None:
        text = ""
    else:
        text = str(text)
    
    trimmed_text = text.strip()
    
    # Required field validation
    if config.required and not trimmed_text:
        errors.append("This field is required")
        return ValidationResult(is_valid=False, errors=errors)
    
    # Length validation (only if text is provided)
    if trimmed_text:
        if len(trimmed_text) < config.min_length:
            errors.append(f"Minimum length is {config.min_length} characters")
        
        if len(trimmed_text) > config.max_length:
            errors.append(f"Maximum length is {config.max_length} characters")
        
        # Pattern validation
        if config.pattern:
            try:
                if not re.match(config.pattern, trimmed_text):
                    errors.append(config.pattern_message)
            except re.error as e:
                errors.append(f"Invalid validation pattern: {str(e)}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_email(email: str) -> ValidationResult:
    """Validate email address"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    config = TextValidationConfig(
        required=True,
        pattern=email_pattern,
        pattern_message="Please enter a valid email address"
    )
    return validate_text(email, config)


def validate_url(url: str, required: bool = False) -> ValidationResult:
    """Validate URL"""
    if not required and not url.strip():
        return ValidationResult(is_valid=True, errors=[])
    
    url_pattern = r'^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    config = TextValidationConfig(
        required=required,
        pattern=url_pattern,
        pattern_message="Please enter a valid URL (http:// or https://)"
    )
    return validate_text(url, config)


def validate_path(path: str) -> ValidationResult:
    """Validate file system path"""
    errors = []
    
    if not path.strip():
        errors.append("Path is required")
        return ValidationResult(is_valid=False, errors=errors)
    
    # Security checks
    if '..' in path:
        errors.append("Path cannot contain '..' for security reasons")
    
    if len(path) > 500:
        errors.append("Path is too long (maximum 500 characters)")
    
    # Check for invalid characters
    invalid_chars = ['<', '>', '"', '|', '?', '*']
    for char in invalid_chars:
        if char in path:
            errors.append(f"Path contains invalid character: '{char}'")
    
    # Check for reserved names (Windows)
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    path_parts = path.replace('\\', '/').split('/')
    for part in path_parts:
        if part.upper() in reserved_names:
            errors.append(f"Path contains reserved name: '{part}'")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )


def validate_schema_type(schema_type: str) -> ValidationResult:
    """Validate schema type"""
    valid_schema_types = ['EU_ESRS_CSRD', 'UK_SRD', 'OTHER']
    
    if not schema_type:
        return ValidationResult(is_valid=False, errors=["Schema type is required"])
    
    if schema_type not in valid_schema_types:
        return ValidationResult(
            is_valid=False,
            errors=[f"Invalid schema type. Must be one of: {', '.join(valid_schema_types)}"]
        )
    
    return ValidationResult(is_valid=True, errors=[])


def validate_query(query: str) -> ValidationResult:
    """Validate search/RAG query"""
    config = TextValidationConfig(
        required=True,
        min_length=3,
        max_length=1000
    )
    return validate_text(query, config)


def validate_json_data(data: Dict[str, Any], required_fields: List[str] = None) -> ValidationResult:
    """Validate JSON data structure"""
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a JSON object")
        return ValidationResult(is_valid=False, errors=errors)
    
    if required_fields:
        for field in required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")
            elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                errors.append(f"Required field '{field}' cannot be empty")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )


def validate_pagination_params(page: int, size: int, max_size: int = 100) -> ValidationResult:
    """Validate pagination parameters"""
    errors = []
    
    if page < 0:
        errors.append("Page number must be non-negative")
    
    if size <= 0:
        errors.append("Page size must be positive")
    
    if size > max_size:
        errors.append(f"Page size cannot exceed {max_size}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )


def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format"""
    if bytes_size == 0:
        return "0 Bytes"
    
    size_names = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_size >= 1024 and i < len(size_names) - 1:
        bytes_size /= 1024.0
        i += 1
    
    return f"{bytes_size:.2f} {size_names[i]}"


def create_validation_error(validation_result: ValidationResult, field_name: str = None) -> HTTPException:
    """Create HTTPException from validation result"""
    message = "Validation failed"
    if field_name:
        message = f"Validation failed for field '{field_name}'"
    
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "message": message,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings if validation_result.warnings else None
        }
    )


class ValidatedModel(BaseModel):
    """Base model with enhanced validation"""
    
    class Config:
        validate_assignment = True
        extra = "forbid"  # Forbid extra fields
    
    def validate_and_raise(self):
        """Validate model and raise HTTPException if invalid"""
        try:
            self.dict()  # This triggers validation
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Model validation failed",
                    "errors": [error["msg"] for error in e.errors()],
                    "details": e.errors()
                }
            )


# Decorator for endpoint validation
def validate_request(validator_func):
    """Decorator to validate request data"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request data from kwargs
            request_data = {}
            for key, value in kwargs.items():
                if not key.startswith('_'):  # Skip internal parameters
                    request_data[key] = value
            
            # Validate request data
            validation_result = validator_func(request_data)
            if not validation_result.is_valid:
                raise create_validation_error(validation_result)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
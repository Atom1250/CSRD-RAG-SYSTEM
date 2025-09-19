"""
Configuration management for CSRD RAG System
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "CSRD RAG System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = "sqlite:///./data/csrd_rag.db"
    database_echo: bool = False
    
    # Redis settings (for caching and Celery)
    redis_url: str = "redis://localhost:6379/0"
    
    # Vector database settings
    vector_db_type: str = "chroma"  # chroma or pinecone
    chroma_persist_directory: str = "./data/chroma_db"
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    
    # AI Model settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_embedding_model: str = "all-MiniLM-L6-v2"
    default_llm_model: str = "gpt-3.5-turbo"
    
    # RAG settings
    max_context_chunks: int = 10
    min_relevance_score: float = 0.3
    default_max_tokens: int = 1000
    default_temperature: float = 0.1
    
    # File storage settings
    upload_directory: str = "./data/documents"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = ["pdf", "docx", "txt"]
    
    # Document processing settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_document: int = 1000
    
    # Schema settings
    schema_directory: str = "./data/schemas"
    supported_schemas: List[str] = ["EU_ESRS_CSRD", "UK_SRD"]
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Remote directory settings
    remote_directory_sync_interval: int = 300  # seconds (5 minutes)
    remote_directory_batch_size: int = 10  # files per batch
    remote_directory_max_file_age: int = 86400  # seconds (24 hours)
    enable_remote_directory_monitoring: bool = False
    
    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        if not v or v == "postgresql://user:password@localhost:5432/csrd_rag":
            # Use environment variable or default for development
            return os.getenv("DATABASE_URL", v)
        return v
    
    @field_validator("upload_directory", "chroma_persist_directory", "schema_directory")
    @classmethod
    def create_directories(cls, v):
        """Ensure directories exist"""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
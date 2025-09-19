-- Database initialization script for CSRD RAG System

-- Create database if it doesn't exist (handled by Docker environment variables)
-- This script runs additional setup if needed

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we can prepare the database

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE csrd_rag TO csrd_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'CSRD RAG Database initialized successfully';
END $$;
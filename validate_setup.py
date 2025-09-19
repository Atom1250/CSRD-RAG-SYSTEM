#!/usr/bin/env python3
"""
Setup validation script for CSRD RAG System
"""
import os
import sys
from pathlib import Path

def validate_directory_structure():
    """Validate that all required directories exist"""
    required_dirs = [
        "backend/app/core",
        "backend/app/services", 
        "backend/app/models",
        "backend/app/api",
        "backend/tests",
        "frontend/src/components",
        "frontend/src/services",
        "frontend/src/utils",
        "config",
        "data/documents",
        "data/schemas"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    return missing_dirs

def validate_files():
    """Validate that required files exist"""
    required_files = [
        "backend/requirements.txt",
        "backend/main.py",
        "backend/app/core/config.py",
        "backend/pytest.ini",
        ".env",
        ".env.example",
        "README.md",
        ".gitignore",
        "setup.sh"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    return missing_files

def main():
    """Main validation function"""
    print("Validating CSRD RAG System setup...")
    
    # Check directory structure
    missing_dirs = validate_directory_structure()
    if missing_dirs:
        print("❌ Missing directories:")
        for dir_path in missing_dirs:
            print(f"  - {dir_path}")
    else:
        print("✅ Directory structure is complete")
    
    # Check required files
    missing_files = validate_files()
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    else:
        print("✅ All required files are present")
    
    # Check environment file
    if Path(".env").exists():
        print("✅ Environment configuration file exists")
    else:
        print("⚠️  .env file not found - copy from .env.example")
    
    # Summary
    if not missing_dirs and not missing_files:
        print("\n🎉 Setup validation successful!")
        print("\nNext steps:")
        print("1. Run ./setup.sh to create virtual environment and install dependencies")
        print("2. Update .env file with your configuration")
        print("3. Start the development server with: cd backend && python main.py")
    else:
        print("\n❌ Setup validation failed - please fix the missing items above")
        sys.exit(1)

if __name__ == "__main__":
    main()
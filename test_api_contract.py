#!/usr/bin/env python3
"""
API Contract Test - Validates that frontend and backend API contracts match
"""

import json
import sys
import re
from pathlib import Path

sys.path.append('backend')

def extract_typescript_interfaces(api_file_path):
    """Extract TypeScript interfaces from the frontend API file"""
    if not Path(api_file_path).exists():
        return {}
    
    content = Path(api_file_path).read_text()
    interfaces = {}
    
    # Regex to match interface definitions
    interface_pattern = r'export interface (\w+) \{([^}]+)\}'
    
    for match in re.finditer(interface_pattern, content, re.DOTALL):
        interface_name = match.group(1)
        interface_body = match.group(2)
        
        # Extract fields
        field_pattern = r'(\w+)(\?)?:\s*([^;]+);'
        fields = {}
        
        for field_match in re.finditer(field_pattern, interface_body):
            field_name = field_match.group(1)
            is_optional = field_match.group(2) == '?'
            field_type = field_match.group(3).strip()
            
            fields[field_name] = {
                'type': field_type,
                'optional': is_optional
            }
        
        interfaces[interface_name] = fields
    
    return interfaces

def get_backend_models():
    """Get backend Pydantic model definitions"""
    try:
        from backend.app.models.schemas import (
            DocumentResponse, SearchResult, RAGResponseResponse,
            SchemaElementResponse, ClientRequirementsResponse
        )
        
        models = {
            'Document': DocumentResponse,
            'SearchResult': SearchResult, 
            'RAGResponse': RAGResponseResponse,
            'Schema': SchemaElementResponse,
            'Report': ClientRequirementsResponse
        }
        
        return models
    except Exception as e:
        print(f"Warning: Could not import backend models: {e}")
        return {}

def compare_interfaces():
    """Compare frontend interfaces with backend models"""
    print("🔍 API Contract Validation")
    print("=" * 50)
    
    # Extract frontend interfaces
    frontend_interfaces = extract_typescript_interfaces("frontend-simple/src/services/api.ts")
    print(f"Found {len(frontend_interfaces)} frontend interfaces")
    
    # Get backend models
    backend_models = get_backend_models()
    print(f"Found {len(backend_models)} backend models")
    
    # Compare each interface
    results = []
    
    for interface_name, fields in frontend_interfaces.items():
        print(f"\n--- Validating {interface_name} ---")
        
        if interface_name not in backend_models:
            print(f"⚠️  Backend model for {interface_name} not found")
            results.append(False)
            continue
        
        backend_model = backend_models[interface_name]
        
        try:
            # Get model schema
            schema = backend_model.model_json_schema()
            backend_fields = schema.get('properties', {})
            required_fields = set(schema.get('required', []))
            
            print(f"Frontend fields: {len(fields)}")
            print(f"Backend fields: {len(backend_fields)}")
            
            # Check each frontend field
            field_matches = 0
            for field_name, field_info in fields.items():
                if field_name in backend_fields:
                    field_matches += 1
                    print(f"✓ {field_name}: Found in backend")
                else:
                    print(f"⚠️  {field_name}: Not found in backend")
            
            # Check required fields
            for field_name in required_fields:
                if field_name in fields:
                    if not fields[field_name]['optional']:
                        print(f"✓ {field_name}: Required field correctly defined")
                    else:
                        print(f"⚠️  {field_name}: Should be required but marked optional")
                else:
                    print(f"⚠️  {field_name}: Required field missing from frontend")
            
            match_percentage = (field_matches / len(fields)) * 100 if fields else 100
            print(f"Field match: {field_matches}/{len(fields)} ({match_percentage:.1f}%)")
            
            results.append(match_percentage >= 80)  # 80% match threshold
            
        except Exception as e:
            print(f"✗ Error validating {interface_name}: {e}")
            results.append(False)
    
    return all(results)

def validate_api_endpoints():
    """Validate that frontend API calls match backend endpoints"""
    print(f"\n🔗 API Endpoint Validation")
    print("=" * 50)
    
    api_file = Path("frontend-simple/src/services/api.ts")
    if not api_file.exists():
        print("✗ Frontend API file not found")
        return False
    
    content = api_file.read_text()
    
    # Extract API calls
    api_calls = []
    
    # Find axios calls
    axios_pattern = r'api\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'
    for match in re.finditer(axios_pattern, content):
        method = match.group(1).upper()
        endpoint = match.group(2)
        api_calls.append((method, endpoint))
    
    print(f"Found {len(api_calls)} API calls in frontend:")
    
    # Expected endpoints based on backend
    expected_endpoints = [
        ('GET', '/documents/'),
        ('POST', '/documents/upload'),
        ('DELETE', '/documents/{id}'),
        ('POST', '/search/'),
        ('POST', '/rag/query'),
        ('GET', '/schemas/'),
        ('GET', '/reports/'),
        ('POST', '/reports/generate'),
        ('GET', '/reports/{id}/download'),
        ('POST', '/client-requirements/upload'),
        ('GET', '/stats/dashboard')
    ]
    
    matches = 0
    for method, endpoint in api_calls:
        print(f"  {method} {endpoint}")
        
        # Check if this endpoint is expected (allowing for parameter variations)
        endpoint_base = re.sub(r'/\d+', '/{id}', endpoint)  # Replace numbers with {id}
        
        if (method, endpoint_base) in expected_endpoints:
            matches += 1
            print(f"    ✓ Matches expected backend endpoint")
        else:
            print(f"    ⚠️  No matching backend endpoint found")
    
    match_percentage = (matches / len(api_calls)) * 100 if api_calls else 100
    print(f"\nEndpoint match: {matches}/{len(api_calls)} ({match_percentage:.1f}%)")
    
    return match_percentage >= 80

def main():
    """Main validation function"""
    print("🧪 Frontend-Backend API Contract Test")
    print("=" * 60)
    
    # Run validations
    interface_valid = compare_interfaces()
    endpoint_valid = validate_api_endpoints()
    
    print(f"\n" + "=" * 60)
    print("📊 Contract Validation Summary")
    print("=" * 60)
    
    print(f"Interface Compatibility: {'✓ PASS' if interface_valid else '✗ FAIL'}")
    print(f"Endpoint Compatibility: {'✓ PASS' if endpoint_valid else '✗ FAIL'}")
    
    overall_success = interface_valid and endpoint_valid
    
    if overall_success:
        print(f"\n🎉 API Contract Validation PASSED!")
        print(f"Frontend and backend are compatible.")
        print(f"\nThe new simple frontend should work seamlessly with the existing backend.")
    else:
        print(f"\n⚠️  API Contract Validation FAILED!")
        print(f"There are compatibility issues that need to be addressed.")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit(main())
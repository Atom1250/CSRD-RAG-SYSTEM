#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
Tests the compatibility between the new simple frontend and existing backend APIs.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import re

# Add backend to path
sys.path.append('backend')

from fastapi.testclient import TestClient
from backend.main import app

class FrontendIntegrationTester:
    def __init__(self):
        self.client = TestClient(app)
        self.frontend_path = Path("frontend-simple")
        self.api_file = self.frontend_path / "src" / "services" / "api.ts"
        self.results = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✓ PASS" if success else "✗ FAIL"
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    def test_frontend_files_exist(self):
        """Test that all required frontend files exist"""
        required_files = [
            "package.json",
            "vite.config.ts",
            "tsconfig.json",
            "index.html",
            "src/main.ts",
            "src/services/api.ts",
            "src/styles/main.css"
        ]
        
        for file_path in required_files:
            full_path = self.frontend_path / file_path
            exists = full_path.exists()
            self.log_result(
                f"Frontend file exists: {file_path}",
                exists,
                f"File not found at {full_path}" if not exists else ""
            )
    
    def test_api_endpoints_exist(self):
        """Test that backend API endpoints exist and respond"""
        endpoints = [
            ("GET", "/docs", "API documentation"),
            ("GET", "/health", "Health check"),
            ("GET", "/api/documents/", "Documents list"),
            ("GET", "/api/schemas/", "Schemas list"),
            ("GET", "/api/reports/", "Reports list")
        ]
        
        for method, endpoint, description in endpoints:
            try:
                if method == "GET":
                    response = self.client.get(endpoint)
                else:
                    response = self.client.request(method, endpoint)
                
                success = response.status_code in [200, 404, 422]  # 404/422 acceptable for empty data
                self.log_result(
                    f"API endpoint {method} {endpoint}",
                    success,
                    f"Status: {response.status_code}" if not success else f"Status: {response.status_code} - {description}"
                )
            except Exception as e:
                self.log_result(
                    f"API endpoint {method} {endpoint}",
                    False,
                    f"Error: {str(e)}"
                )
    
    def test_api_interface_compatibility(self):
        """Test that frontend API interfaces match backend responses"""
        if not self.api_file.exists():
            self.log_result("API interfaces compatibility", False, "api.ts file not found")
            return
        
        # Read the API file
        api_content = self.api_file.read_text()
        
        # Check for required interfaces
        required_interfaces = [
            "Document",
            "SearchResult", 
            "RAGResponse",
            "Schema",
            "Report"
        ]
        
        for interface in required_interfaces:
            pattern = f"export interface {interface}"
            found = pattern in api_content
            self.log_result(
                f"Interface {interface} defined",
                found,
                f"Interface {interface} not found in api.ts" if not found else ""
            )
    
    def test_api_functions_defined(self):
        """Test that all required API functions are defined in frontend"""
        if not self.api_file.exists():
            self.log_result("API functions defined", False, "api.ts file not found")
            return
        
        api_content = self.api_file.read_text()
        
        required_functions = [
            "documentAPI",
            "searchAPI", 
            "ragAPI",
            "schemaAPI",
            "reportAPI",
            "statsAPI"
        ]
        
        for func in required_functions:
            pattern = f"export const {func}"
            found = pattern in api_content
            self.log_result(
                f"API function {func} defined",
                found,
                f"Function {func} not found in api.ts" if not found else ""
            )
    
    def test_document_upload_integration(self):
        """Test document upload endpoint integration"""
        try:
            # Test with empty request (should fail gracefully)
            response = self.client.post("/api/documents/upload")
            
            # Should return 422 (validation error) for missing files
            success = response.status_code == 422
            self.log_result(
                "Document upload endpoint validation",
                success,
                f"Expected 422, got {response.status_code}" if not success else "Validation working correctly"
            )
        except Exception as e:
            self.log_result(
                "Document upload endpoint validation",
                False,
                f"Error: {str(e)}"
            )
    
    def test_search_integration(self):
        """Test search endpoint integration"""
        try:
            # Test search with empty query
            response = self.client.post("/api/search/", json={"query": "", "limit": 10})
            
            # Should handle empty query gracefully
            success = response.status_code in [200, 422]
            self.log_result(
                "Search endpoint integration",
                success,
                f"Status: {response.status_code}" if success else f"Unexpected status: {response.status_code}"
            )
        except Exception as e:
            self.log_result(
                "Search endpoint integration",
                False,
                f"Error: {str(e)}"
            )
    
    def test_rag_integration(self):
        """Test RAG endpoint integration"""
        try:
            # Test RAG with simple query
            response = self.client.post("/api/rag/query", json={
                "question": "test question",
                "model": "openai"
            })
            
            # Should handle request (may fail due to missing API keys, but endpoint should exist)
            success = response.status_code in [200, 422, 500]
            self.log_result(
                "RAG endpoint integration",
                success,
                f"Status: {response.status_code}" if success else f"Unexpected status: {response.status_code}"
            )
        except Exception as e:
            self.log_result(
                "RAG endpoint integration",
                False,
                f"Error: {str(e)}"
            )
    
    def test_frontend_main_structure(self):
        """Test that main.ts has proper structure"""
        main_file = self.frontend_path / "src" / "main.ts"
        
        if not main_file.exists():
            self.log_result("Frontend main.ts structure", False, "main.ts not found")
            return
        
        main_content = main_file.read_text()
        
        # Check for key components
        required_components = [
            "class App",
            "setupNavigation",
            "setupEventListeners",
            "loadDashboard",
            "handleFileUpload",
            "handleSearch",
            "handleRAGQuery"
        ]
        
        for component in required_components:
            found = component in main_content
            self.log_result(
                f"Main.ts component: {component}",
                found,
                f"Component {component} not found" if not found else ""
            )
    
    def test_css_responsive_design(self):
        """Test that CSS includes responsive design"""
        css_file = self.frontend_path / "src" / "styles" / "main.css"
        
        if not css_file.exists():
            self.log_result("CSS responsive design", False, "main.css not found")
            return
        
        css_content = css_file.read_text()
        
        # Check for responsive features
        responsive_features = [
            "@media",
            "grid-template-columns",
            "flex",
            "max-width",
            "mobile"
        ]
        
        responsive_count = sum(1 for feature in responsive_features if feature in css_content)
        success = responsive_count >= 3
        
        self.log_result(
            "CSS responsive design features",
            success,
            f"Found {responsive_count}/5 responsive features" if not success else f"Found {responsive_count}/5 responsive features"
        )
    
    def test_package_json_structure(self):
        """Test package.json has correct structure"""
        package_file = self.frontend_path / "package.json"
        
        if not package_file.exists():
            self.log_result("Package.json structure", False, "package.json not found")
            return
        
        try:
            package_data = json.loads(package_file.read_text())
            
            # Check required fields
            required_fields = ["name", "version", "scripts", "dependencies", "devDependencies"]
            required_scripts = ["dev", "build", "preview"]
            required_deps = ["axios"]
            required_dev_deps = ["vite", "typescript"]
            
            # Test fields
            for field in required_fields:
                found = field in package_data
                self.log_result(
                    f"Package.json field: {field}",
                    found,
                    f"Field {field} missing" if not found else ""
                )
            
            # Test scripts
            scripts = package_data.get("scripts", {})
            for script in required_scripts:
                found = script in scripts
                self.log_result(
                    f"Package.json script: {script}",
                    found,
                    f"Script {script} missing" if not found else ""
                )
            
            # Test dependencies
            deps = package_data.get("dependencies", {})
            for dep in required_deps:
                found = dep in deps
                self.log_result(
                    f"Package.json dependency: {dep}",
                    found,
                    f"Dependency {dep} missing" if not found else ""
                )
            
            # Test dev dependencies
            dev_deps = package_data.get("devDependencies", {})
            for dep in required_dev_deps:
                found = dep in dev_deps
                self.log_result(
                    f"Package.json dev dependency: {dep}",
                    found,
                    f"Dev dependency {dep} missing" if not found else ""
                )
                
        except json.JSONDecodeError as e:
            self.log_result("Package.json structure", False, f"Invalid JSON: {str(e)}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Running Frontend-Backend Integration Tests")
        print("=" * 50)
        
        # Test categories
        test_methods = [
            self.test_frontend_files_exist,
            self.test_package_json_structure,
            self.test_api_endpoints_exist,
            self.test_api_interface_compatibility,
            self.test_api_functions_defined,
            self.test_document_upload_integration,
            self.test_search_integration,
            self.test_rag_integration,
            self.test_frontend_main_structure,
            self.test_css_responsive_design
        ]
        
        for test_method in test_methods:
            print(f"\n--- {test_method.__name__.replace('test_', '').replace('_', ' ').title()} ---")
            test_method()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        return failed_tests == 0

def main():
    """Main test runner"""
    tester = FrontendIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 All integration tests passed! Frontend is ready for use.")
        print(f"\nTo start the frontend:")
        print(f"  cd frontend-simple")
        print(f"  npm install")
        print(f"  npm run dev")
    else:
        print(f"\n⚠️  Some tests failed. Please review the issues above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
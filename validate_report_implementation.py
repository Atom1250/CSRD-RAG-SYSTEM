#!/usr/bin/env python3
"""
Validation script for Report Generation Workflow Interface implementation
"""
import os
import re
from pathlib import Path

def check_file_exists(file_path):
    """Check if a file exists and return its status"""
    if os.path.exists(file_path):
        return True, f"✓ {file_path} exists"
    else:
        return False, f"✗ {file_path} missing"

def check_file_content(file_path, patterns):
    """Check if file contains required patterns"""
    if not os.path.exists(file_path):
        return False, f"✗ {file_path} not found"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_patterns = []
        for pattern_name, pattern in patterns.items():
            if not re.search(pattern, content, re.MULTILINE | re.DOTALL):
                missing_patterns.append(pattern_name)
        
        if missing_patterns:
            return False, f"✗ {file_path} missing: {', '.join(missing_patterns)}"
        else:
            return True, f"✓ {file_path} contains all required patterns"
    
    except Exception as e:
        return False, f"✗ Error reading {file_path}: {str(e)}"

def validate_report_implementation():
    """Validate the report generation workflow implementation"""
    print("🔍 Validating Report Generation Workflow Interface Implementation")
    print("=" * 70)
    
    results = []
    
    # Check if required files exist
    required_files = [
        "frontend/src/services/reportService.ts",
        "frontend/src/pages/Reports.tsx",
        "frontend/src/services/reportService.test.ts",
        "frontend/src/pages/Reports.test.tsx",
        "frontend/src/pages/Reports.integration.test.tsx"
    ]
    
    print("\n📁 File Existence Check:")
    for file_path in required_files:
        exists, message = check_file_exists(file_path)
        results.append(exists)
        print(f"  {message}")
    
    # Check reportService.ts implementation
    print("\n🔧 Report Service Implementation:")
    service_patterns = {
        "ClientRequirement interface": r"interface ClientRequirement",
        "uploadClientRequirements method": r"async uploadClientRequirements\(",
        "validateRequirementsForReport method": r"async validateRequirementsForReport\(",
        "generateReport method": r"async generateReport\(",
        "downloadPDFReport method": r"async downloadPDFReport\(",
        "validateFile method": r"validateFile\(file: File\)",
        "formatFileSize method": r"formatFileSize\(bytes: number\)",
        "getValidationStatusColor method": r"getValidationStatusColor\(",
        "downloadBlob method": r"downloadBlob\(blob: Blob, filename: string\)"
    }
    
    exists, message = check_file_content("frontend/src/services/reportService.ts", service_patterns)
    results.append(exists)
    print(f"  {message}")
    
    # Check Reports.tsx implementation
    print("\n🎨 Reports Component Implementation:")
    component_patterns = {
        "useState hooks": r"useState<.*?>",
        "useEffect hook": r"useEffect\(\(\) => \{",
        "handleUploadRequirements": r"handleUploadRequirements.*async",
        "handleValidateRequirements": r"handleValidateRequirements.*async",
        "handleGenerateReport": r"handleGenerateReport.*async",
        "Stepper component": r"<Stepper.*activeStep",
        "Dialog component": r"<Dialog.*open=\{createDialogOpen\}",
        "File upload input": r"type=\"file\"",
        "Progress indicators": r"<LinearProgress|<CircularProgress",
        "Error handling": r"Alert.*severity=\"error\"",
        "Success feedback": r"Alert.*severity=\"success\"|Snackbar"
    }
    
    exists, message = check_file_content("frontend/src/pages/Reports.tsx", component_patterns)
    results.append(exists)
    print(f"  {message}")
    
    # Check test files
    print("\n🧪 Test Implementation:")
    test_patterns = {
        "Service tests": {
            "uploadClientRequirements test": r"describe.*uploadClientRequirements",
            "validateRequirementsForReport test": r"describe.*validateRequirementsForReport",
            "generateReport test": r"describe.*generateReport",
            "file validation test": r"describe.*validateFile",
            "mock setup": r"jest\.mock.*api"
        },
        "Component tests": {
            "render test": r"it.*renders.*correctly",
            "dialog test": r"it.*opens.*dialog",
            "file upload test": r"it.*handles.*file.*upload",
            "workflow test": r"it.*validates.*requirements",
            "error handling test": r"it.*handles.*errors"
        },
        "Integration tests": {
            "full workflow test": r"it.*completes.*full.*workflow",
            "API integration": r"mockedApi\.",
            "user interaction": r"fireEvent\.|userEvent\.",
            "async operations": r"waitFor\("
        }
    }
    
    test_files = [
        ("frontend/src/services/reportService.test.ts", test_patterns["Service tests"]),
        ("frontend/src/pages/Reports.test.tsx", test_patterns["Component tests"]),
        ("frontend/src/pages/Reports.integration.test.tsx", test_patterns["Integration tests"])
    ]
    
    for file_path, patterns in test_files:
        exists, message = check_file_content(file_path, patterns)
        results.append(exists)
        print(f"  {message}")
    
    # Check task requirements coverage
    print("\n📋 Task Requirements Coverage:")
    requirements_check = {
        "Client requirements upload interface": r"uploadClientRequirements|file.*upload|FormData",
        "File validation": r"validateFile|allowedTypes|maxSize",
        "Progress tracking": r"LinearProgress|CircularProgress|uploading|generating",
        "Status updates": r"setLoading|setUploading|setGenerating|status",
        "Report preview": r"previewReportStructure|ReportPreview|preview",
        "Download functionality": r"downloadPDFReport|downloadBlob|PDF.*download",
        "Error handling": r"try.*catch|error.*handling|Alert.*error",
        "User feedback": r"success.*message|Snackbar|Alert.*success"
    }
    
    # Check across all implementation files
    all_content = ""
    impl_files = [
        "frontend/src/services/reportService.ts",
        "frontend/src/pages/Reports.tsx"
    ]
    
    for file_path in impl_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"
    
    for req_name, pattern in requirements_check.items():
        if re.search(pattern, all_content, re.MULTILINE | re.DOTALL | re.IGNORECASE):
            results.append(True)
            print(f"  ✓ {req_name} implemented")
        else:
            results.append(False)
            print(f"  ✗ {req_name} missing or incomplete")
    
    # Summary
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"📊 Implementation Summary:")
    print(f"  Passed: {passed}/{total} checks ({percentage:.1f}%)")
    
    if percentage >= 90:
        print("  🎉 Excellent implementation! All major requirements covered.")
        return True
    elif percentage >= 75:
        print("  ✅ Good implementation! Minor issues may need attention.")
        return True
    elif percentage >= 50:
        print("  ⚠️  Partial implementation. Several requirements need work.")
        return False
    else:
        print("  ❌ Implementation incomplete. Major work required.")
        return False

if __name__ == "__main__":
    success = validate_report_implementation()
    exit(0 if success else 1)
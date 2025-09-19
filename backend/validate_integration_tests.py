#!/usr/bin/env python3
"""
Validation script for integration test framework

This script validates that the integration test framework is properly set up
and can run basic tests without requiring the full system to be running.
"""

import sys
import subprocess
import tempfile
import os
from pathlib import Path


def validate_test_structure():
    """Validate that test files are properly structured"""
    
    print("🔍 Validating test structure...")
    
    # Get the backend directory path
    backend_dir = Path(__file__).parent
    
    test_files = [
        backend_dir / "tests/test_integration_e2e.py",
        backend_dir / "tests/test_performance_benchmarks.py", 
        backend_dir / "tests/test_data_validation.py",
        backend_dir / "tests/test_quality_assurance.py"
    ]
    
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False
    
    print("✅ All test files present")
    return True


def validate_test_syntax():
    """Validate that test files have correct Python syntax"""
    
    print("🔍 Validating test syntax...")
    
    # Get the backend directory path
    backend_dir = Path(__file__).parent
    
    test_files = [
        backend_dir / "tests/test_integration_e2e.py",
        backend_dir / "tests/test_performance_benchmarks.py",
        backend_dir / "tests/test_data_validation.py", 
        backend_dir / "tests/test_quality_assurance.py"
    ]
    
    for test_file in test_files:
        try:
            with open(test_file, 'r') as f:
                compile(f.read(), test_file, 'exec')
            print(f"✅ {test_file} syntax valid")
        except SyntaxError as e:
            print(f"❌ {test_file} syntax error: {e}")
            return False
        except Exception as e:
            print(f"⚠️  {test_file} validation warning: {e}")
    
    return True


def validate_pytest_collection():
    """Validate that pytest can collect the tests"""
    
    print("🔍 Validating pytest test collection...")
    
    try:
        # Get the backend directory path
        backend_dir = Path(__file__).parent
        test_file = backend_dir / "tests/test_integration_e2e.py"
        
        # Run pytest in collection-only mode
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "--collect-only", "-q",
            str(test_file)
        ], capture_output=True, text=True, timeout=30, cwd=backend_dir)
        
        if result.returncode == 0:
            print("✅ Pytest can collect tests successfully")
            return True
        else:
            print(f"❌ Pytest collection failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Pytest collection timed out")
        return False
    except Exception as e:
        print(f"❌ Pytest collection error: {e}")
        return False


def validate_test_runner():
    """Validate that the test runner script is executable"""
    
    print("🔍 Validating test runner...")
    
    # Get the backend directory path
    backend_dir = Path(__file__).parent
    runner_path = backend_dir / "run_integration_tests.py"
    
    if not runner_path.exists():
        print("❌ Test runner script not found")
        return False
    
    if not os.access(runner_path, os.X_OK):
        print("❌ Test runner script not executable")
        return False
    
    # Test syntax
    try:
        with open(runner_path, 'r') as f:
            compile(f.read(), str(runner_path), 'exec')
        print("✅ Test runner syntax valid")
    except SyntaxError as e:
        print(f"❌ Test runner syntax error: {e}")
        return False
    
    print("✅ Test runner is properly configured")
    return True


def create_test_output_directory():
    """Create test output directory if it doesn't exist"""
    
    print("🔍 Setting up test output directory...")
    
    # Get the backend directory path
    backend_dir = Path(__file__).parent
    output_dir = backend_dir / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    # Create a test file to verify write permissions
    test_file = output_dir / "validation_test.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("Test output directory validation")
        test_file.unlink()  # Clean up
        print("✅ Test output directory ready")
        return True
    except Exception as e:
        print(f"❌ Cannot write to test output directory: {e}")
        return False


def run_basic_test_validation():
    """Run a basic test to validate the framework works"""
    
    print("🔍 Running basic test validation...")
    
    # Create a simple test file
    test_content = '''
import pytest

def test_basic_validation():
    """Basic validation test"""
    assert True

def test_framework_imports():
    """Test that required modules can be imported"""
    try:
        import asyncio
        import json
        import tempfile
        assert True
    except ImportError as e:
        pytest.fail(f"Required module import failed: {e}")
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_content)
        f.flush()
        
        try:
            # Run the basic test
            result = subprocess.run([
                sys.executable, "-m", "pytest", f.name, "-v"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Basic test validation passed")
                return True
            else:
                print(f"❌ Basic test validation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Basic test validation timed out")
            return False
        except Exception as e:
            print(f"❌ Basic test validation error: {e}")
            return False
        finally:
            os.unlink(f.name)


def main():
    """Main validation function"""
    
    print("🚀 Validating Integration Test Framework")
    print("=" * 50)
    
    validations = [
        ("Test Structure", validate_test_structure),
        ("Test Syntax", validate_test_syntax),
        ("Pytest Collection", validate_pytest_collection),
        ("Test Runner", validate_test_runner),
        ("Output Directory", create_test_output_directory),
        ("Basic Test", run_basic_test_validation)
    ]
    
    passed = 0
    total = len(validations)
    
    for name, validation_func in validations:
        print(f"\n📋 {name}:")
        try:
            if validation_func():
                passed += 1
            else:
                print(f"❌ {name} validation failed")
        except Exception as e:
            print(f"❌ {name} validation error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Integration test framework validation successful!")
        print("✅ Framework is ready for comprehensive testing")
        return True
    else:
        print("⚠️  Integration test framework validation incomplete")
        print("🔧 Please address the failed validations before running tests")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
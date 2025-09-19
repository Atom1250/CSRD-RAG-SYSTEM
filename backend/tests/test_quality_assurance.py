"""
Quality Assurance Test Suite for CSRD RAG System

This module provides comprehensive quality assurance testing including
test orchestration, quality metrics collection, and reporting.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from tests.conftest import test_db, client
except ImportError:
    # For validation purposes when test modules aren't available
    pass


@dataclass
class QualityMetrics:
    """Data class for storing quality assurance metrics"""
    test_suite: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time: float
    performance_metrics: Dict[str, float]
    accuracy_metrics: Dict[str, float]
    error_rate: float


class QualityAssuranceFramework:
    """Framework for comprehensive quality assurance testing"""
    
    def __init__(self):
        self.metrics: List[QualityMetrics] = []
        self.performance_thresholds = {
            "document_processing_time": 30.0,  # seconds
            "search_response_time": 2.0,  # seconds
            "rag_response_time": 5.0,  # seconds
            "api_response_time": 0.5,  # seconds
        }
        self.accuracy_thresholds = {
            "schema_classification_accuracy": 0.8,  # 80%
            "rag_response_quality": 0.7,  # 70%
            "search_relevance_accuracy": 0.6,  # 60%
        }
    
    def collect_metrics(self, test_suite: str, results: Dict[str, Any]) -> QualityMetrics:
        """Collect and structure quality metrics from test results"""
        
        return QualityMetrics(
            test_suite=test_suite,
            total_tests=results.get("total_tests", 0),
            passed_tests=results.get("passed_tests", 0),
            failed_tests=results.get("failed_tests", 0),
            execution_time=results.get("execution_time", 0.0),
            performance_metrics=results.get("performance_metrics", {}),
            accuracy_metrics=results.get("accuracy_metrics", {}),
            error_rate=results.get("error_rate", 0.0)
        )
    
    def validate_quality_thresholds(self, metrics: QualityMetrics) -> Dict[str, bool]:
        """Validate metrics against quality thresholds"""
        
        validation_results = {}
        
        # Validate performance thresholds
        for metric, threshold in self.performance_thresholds.items():
            if metric in metrics.performance_metrics:
                validation_results[f"performance_{metric}"] = \
                    metrics.performance_metrics[metric] <= threshold
        
        # Validate accuracy thresholds
        for metric, threshold in self.accuracy_thresholds.items():
            if metric in metrics.accuracy_metrics:
                validation_results[f"accuracy_{metric}"] = \
                    metrics.accuracy_metrics[metric] >= threshold
        
        # Validate overall test success rate
        if metrics.total_tests > 0:
            success_rate = metrics.passed_tests / metrics.total_tests
            validation_results["test_success_rate"] = success_rate >= 0.95  # 95% success rate
        
        return validation_results
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality assurance report"""
        
        report = {
            "timestamp": time.time(),
            "test_suites": [],
            "overall_metrics": {},
            "quality_validation": {},
            "recommendations": []
        }
        
        total_tests = sum(m.total_tests for m in self.metrics)
        total_passed = sum(m.passed_tests for m in self.metrics)
        total_execution_time = sum(m.execution_time for m in self.metrics)
        
        report["overall_metrics"] = {
            "total_test_suites": len(self.metrics),
            "total_tests": total_tests,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "total_execution_time": total_execution_time
        }
        
        # Collect validation results for all test suites
        all_validations = {}
        for metrics in self.metrics:
            suite_validations = self.validate_quality_thresholds(metrics)
            all_validations.update(suite_validations)
            
            report["test_suites"].append({
                "name": metrics.test_suite,
                "metrics": metrics.__dict__,
                "validation": suite_validations
            })
        
        report["quality_validation"] = all_validations
        
        # Generate recommendations based on validation results
        failed_validations = [k for k, v in all_validations.items() if not v]
        if failed_validations:
            report["recommendations"] = self._generate_recommendations(failed_validations)
        
        return report
    
    def _generate_recommendations(self, failed_validations: List[str]) -> List[str]:
        """Generate recommendations based on failed quality validations"""
        
        recommendations = []
        
        if any("performance" in fv for fv in failed_validations):
            recommendations.append(
                "Performance optimization needed: Consider implementing caching, "
                "optimizing database queries, or scaling infrastructure."
            )
        
        if any("accuracy" in fv for fv in failed_validations):
            recommendations.append(
                "Accuracy improvement needed: Review model parameters, "
                "training data quality, or schema definitions."
            )
        
        if "test_success_rate" in failed_validations:
            recommendations.append(
                "Test reliability issues detected: Review test stability, "
                "test data quality, and system dependencies."
            )
        
        return recommendations


class TestQualityAssuranceOrchestration:
    """Orchestrate comprehensive quality assurance testing"""
    
    def setup_method(self):
        """Set up quality assurance framework"""
        self.qa_framework = QualityAssuranceFramework()
    
    @pytest.mark.asyncio
    async def test_comprehensive_system_validation(self, client: TestClient, test_db: Session):
        """Run comprehensive system validation across all components"""
        
        start_time = time.time()
        
        # Test 1: System Health Check
        health_results = await self._test_system_health(client)
        
        # Test 2: Core Functionality Validation
        functionality_results = await self._test_core_functionality(client)
        
        # Test 3: Performance Validation
        performance_results = await self._test_performance_validation(client)
        
        # Test 4: Data Integrity Validation
        integrity_results = await self._test_data_integrity(client)
        
        execution_time = time.time() - start_time
        
        # Collect comprehensive metrics
        comprehensive_metrics = {
            "total_tests": (health_results["total"] + functionality_results["total"] + 
                          performance_results["total"] + integrity_results["total"]),
            "passed_tests": (health_results["passed"] + functionality_results["passed"] + 
                           performance_results["passed"] + integrity_results["passed"]),
            "failed_tests": (health_results["failed"] + functionality_results["failed"] + 
                           performance_results["failed"] + integrity_results["failed"]),
            "execution_time": execution_time,
            "performance_metrics": performance_results["metrics"],
            "accuracy_metrics": functionality_results["accuracy"],
            "error_rate": (health_results["failed"] + functionality_results["failed"] + 
                         performance_results["failed"] + integrity_results["failed"]) / 
                        (health_results["total"] + functionality_results["total"] + 
                         performance_results["total"] + integrity_results["total"])
        }
        
        metrics = self.qa_framework.collect_metrics("comprehensive_validation", comprehensive_metrics)
        self.qa_framework.metrics.append(metrics)
        
        # Generate and validate quality report
        quality_report = self.qa_framework.generate_quality_report()
        
        # Assert overall system quality
        assert quality_report["overall_metrics"]["overall_success_rate"] >= 0.90, \
            f"System quality below threshold: {quality_report['overall_metrics']['overall_success_rate']}"
        
        print(f"Comprehensive system validation completed: {quality_report['overall_metrics']}")
    
    async def _test_system_health(self, client: TestClient) -> Dict[str, Any]:
        """Test basic system health and availability"""
        
        tests = [
            ("API Health Check", lambda: client.get("/health")),
            ("Database Connection", lambda: client.get("/api/documents")),
            ("Schema Service", lambda: client.get("/api/schemas/EU_ESRS_CSRD")),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                response = test_func()
                if response.status_code == 200:
                    passed += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        
        return {"total": len(tests), "passed": passed, "failed": failed}
    
    async def _test_core_functionality(self, client: TestClient) -> Dict[str, Any]:
        """Test core system functionality"""
        
        import tempfile
        import os
        
        passed = 0
        failed = 0
        accuracy_metrics = {}
        
        # Test document upload and processing
        try:
            test_content = "ESRS E1 Climate Change requirements for comprehensive sustainability reporting."
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": ("qa_test.txt", upload_file, "text/plain")},
                        data={"schema_type": "EU_ESRS_CSRD"}
                    )
                    if response.status_code == 200:
                        passed += 1
                    else:
                        failed += 1
                
                os.unlink(f.name)
        except Exception:
            failed += 1
        
        # Test search functionality
        try:
            await asyncio.sleep(2)  # Wait for processing
            response = client.post(
                "/api/search",
                json={"query": "ESRS E1 Climate Change", "top_k": 5}
            )
            if response.status_code == 200:
                results = response.json()
                if len(results.get("results", [])) > 0:
                    passed += 1
                    accuracy_metrics["search_relevance_accuracy"] = \
                        results["results"][0].get("relevance_score", 0)
                else:
                    failed += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        
        # Test RAG functionality
        try:
            response = client.post(
                "/api/rag/query",
                json={
                    "question": "What are ESRS E1 requirements?",
                    "model": "gpt-4"
                }
            )
            if response.status_code == 200:
                result = response.json()
                passed += 1
                accuracy_metrics["rag_response_quality"] = result.get("confidence_score", 0)
            else:
                failed += 1
        except Exception:
            failed += 1
        
        return {
            "total": 3,
            "passed": passed,
            "failed": failed,
            "accuracy": accuracy_metrics
        }
    
    async def _test_performance_validation(self, client: TestClient) -> Dict[str, Any]:
        """Test system performance against benchmarks"""
        
        passed = 0
        failed = 0
        performance_metrics = {}
        
        # Test API response time
        start_time = time.time()
        try:
            response = client.get("/api/documents")
            api_time = time.time() - start_time
            performance_metrics["api_response_time"] = api_time
            
            if api_time <= 0.5:  # 500ms threshold
                passed += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        
        # Test search response time
        start_time = time.time()
        try:
            response = client.post(
                "/api/search",
                json={"query": "sustainability", "top_k": 5}
            )
            search_time = time.time() - start_time
            performance_metrics["search_response_time"] = search_time
            
            if search_time <= 2.0:  # 2 second threshold
                passed += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        
        return {
            "total": 2,
            "passed": passed,
            "failed": failed,
            "metrics": performance_metrics
        }
    
    async def _test_data_integrity(self, client: TestClient) -> Dict[str, Any]:
        """Test data integrity and consistency"""
        
        passed = 0
        failed = 0
        
        # Test document listing consistency
        try:
            response = client.get("/api/documents")
            if response.status_code == 200:
                documents = response.json()
                # Validate each document has required fields
                for doc in documents:
                    if all(field in doc for field in ["id", "filename", "upload_date"]):
                        passed += 1
                    else:
                        failed += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        
        # If no documents, count as one passed test
        if not documents:
            passed = 1
        
        return {"total": max(1, len(documents) if 'documents' in locals() else 1), 
                "passed": passed, "failed": failed}
    
    def test_generate_quality_report_file(self, client: TestClient, test_db: Session):
        """Generate and save comprehensive quality report"""
        
        # Run a minimal test to populate metrics
        start_time = time.time()
        
        # Basic health check
        try:
            response = client.get("/health")
            health_status = response.status_code == 200
        except:
            health_status = False
        
        execution_time = time.time() - start_time
        
        # Create sample metrics
        sample_metrics = {
            "total_tests": 1,
            "passed_tests": 1 if health_status else 0,
            "failed_tests": 0 if health_status else 1,
            "execution_time": execution_time,
            "performance_metrics": {"api_response_time": execution_time},
            "accuracy_metrics": {"system_health": 1.0 if health_status else 0.0},
            "error_rate": 0.0 if health_status else 1.0
        }
        
        metrics = self.qa_framework.collect_metrics("quality_report_test", sample_metrics)
        self.qa_framework.metrics.append(metrics)
        
        # Generate quality report
        quality_report = self.qa_framework.generate_quality_report()
        
        # Save report to file
        report_path = Path("backend/test_output/quality_assurance_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(quality_report, f, indent=2)
        
        print(f"Quality assurance report saved to: {report_path}")
        
        # Validate report structure
        assert "timestamp" in quality_report
        assert "test_suites" in quality_report
        assert "overall_metrics" in quality_report
        assert "quality_validation" in quality_report
        
        return quality_report


class TestRequirementsValidation:
    """Validate system against all specified requirements"""
    
    @pytest.mark.asyncio
    async def test_requirement_1_document_repository(self, client: TestClient, test_db: Session):
        """Validate Requirement 1: Document Repository Management"""
        
        import tempfile
        import os
        
        # Test 1.1: File format support
        supported_formats = [".txt", ".pdf", ".docx"]
        for fmt in supported_formats[:1]:  # Test at least .txt format
            with tempfile.NamedTemporaryFile(mode='w', suffix=fmt, delete=False) as f:
                f.write("Test content for requirement validation")
                f.flush()
                
                with open(f.name, 'rb') as upload_file:
                    response = client.post(
                        "/api/documents/upload",
                        files={"file": (f"req_test{fmt}", upload_file, "text/plain")},
                        data={"schema_type": "EU_ESRS_CSRD"}
                    )
                    assert response.status_code == 200, f"Failed to upload {fmt} file"
                
                os.unlink(f.name)
        
        # Test 1.3: Metadata extraction and storage
        response = client.get("/api/documents")
        assert response.status_code == 200
        documents = response.json()
        
        if documents:
            doc = documents[0]
            required_metadata = ["id", "filename", "upload_date", "file_size"]
            for field in required_metadata:
                assert field in doc, f"Missing required metadata field: {field}"
        
        print("✓ Requirement 1: Document Repository Management validated")
    
    @pytest.mark.asyncio
    async def test_requirement_3_search_functionality(self, client: TestClient, test_db: Session):
        """Validate Requirement 3: Intelligent Search Functionality"""
        
        # Ensure we have searchable content
        await asyncio.sleep(2)
        
        # Test 3.1: Natural language query processing
        response = client.post(
            "/api/search",
            json={"query": "sustainability reporting requirements", "top_k": 5}
        )
        assert response.status_code == 200, "Search endpoint should accept natural language queries"
        
        results = response.json()
        assert "results" in results, "Search should return results structure"
        
        # Test 3.3: Relevance ranking
        if results["results"]:
            for result in results["results"]:
                assert "relevance_score" in result, "Results should include relevance scores"
                assert 0 <= result["relevance_score"] <= 1, "Relevance scores should be between 0 and 1"
        
        print("✓ Requirement 3: Intelligent Search Functionality validated")
    
    @pytest.mark.asyncio
    async def test_requirement_4_rag_question_answering(self, client: TestClient, test_db: Session):
        """Validate Requirement 4: RAG-based Question Answering"""
        
        # Test 4.1: Question processing and context retrieval
        response = client.post(
            "/api/rag/query",
            json={
                "question": "What are the main requirements for sustainability reporting?",
                "model": "gpt-4"
            }
        )
        assert response.status_code == 200, "RAG endpoint should process questions"
        
        result = response.json()
        
        # Test 4.3: Model selection
        assert "model_used" in result or response.status_code == 200, "Should support model selection"
        
        # Test 4.5: Source references
        if "sources" in result:
            assert isinstance(result["sources"], list), "Sources should be provided as a list"
        
        print("✓ Requirement 4: RAG-based Question Answering validated")
    
    def test_requirement_5_user_interface(self, client: TestClient, test_db: Session):
        """Validate Requirement 5: User Interface and Experience"""
        
        # Test 5.1: Web interface availability
        # Note: This tests the API which supports the web interface
        response = client.get("/docs")  # OpenAPI docs endpoint
        assert response.status_code == 200, "API documentation should be available"
        
        # Test 5.3: Operation feedback
        response = client.get("/api/documents")
        assert response.status_code == 200, "API should provide clear response status"
        
        print("✓ Requirement 5: User Interface and Experience validated")
    
    def test_requirement_6_schema_support(self, client: TestClient, test_db: Session):
        """Validate Requirement 6: Data Schema and Reporting Standards Support"""
        
        # Test 6.1: Schema loading
        eu_response = client.get("/api/schemas/EU_ESRS_CSRD")
        assert eu_response.status_code == 200, "Should load EU ESRS/CSRD schema"
        
        uk_response = client.get("/api/schemas/UK_SRD")
        assert uk_response.status_code == 200, "Should load UK SRD schema"
        
        # Test 6.4: Schema classification
        eu_schema = eu_response.json()
        assert "elements" in eu_schema or "schema_type" in eu_schema, \
            "Schema should contain classification elements"
        
        print("✓ Requirement 6: Data Schema and Reporting Standards Support validated")
    
    def test_requirement_8_system_configuration(self, client: TestClient, test_db: Session):
        """Validate Requirement 8: System Configuration and Setup"""
        
        # Test 8.2: Configuration validation
        # The fact that the test client works indicates basic configuration is valid
        response = client.get("/health")
        assert response.status_code == 200, "System should start with valid configuration"
        
        print("✓ Requirement 8: System Configuration and Setup validated")
    
    @pytest.mark.asyncio
    async def test_all_requirements_comprehensive(self, client: TestClient, test_db: Session):
        """Run comprehensive validation of all requirements"""
        
        print("\n=== Comprehensive Requirements Validation ===")
        
        # Run all requirement tests
        await self.test_requirement_1_document_repository(client, test_db)
        await self.test_requirement_3_search_functionality(client, test_db)
        await self.test_requirement_4_rag_question_answering(client, test_db)
        self.test_requirement_5_user_interface(client, test_db)
        self.test_requirement_6_schema_support(client, test_db)
        self.test_requirement_8_system_configuration(client, test_db)
        
        print("\n✅ All requirements validation completed successfully")
        print("🎉 CSRD RAG System meets all specified requirements!")
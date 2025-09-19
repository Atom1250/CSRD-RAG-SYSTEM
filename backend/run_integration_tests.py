#!/usr/bin/env python3
"""
Integration Test Runner for CSRD RAG System

This script orchestrates comprehensive integration testing including:
- End-to-end user journey tests
- Schema classification accuracy tests
- RAG response quality tests
- Performance benchmarking
- Data validation and integrity tests
- Requirements validation
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any


class IntegrationTestRunner:
    """Orchestrate comprehensive integration testing"""
    
    def __init__(self):
        self.test_modules = [
            "tests.test_integration_e2e",
            "tests.test_performance_benchmarks", 
            "tests.test_data_validation",
            "tests.test_quality_assurance"
        ]
        
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration test suites"""
        
        print("🚀 Starting Comprehensive Integration Testing for CSRD RAG System")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # Run each test module
        for module in self.test_modules:
            print(f"\n📋 Running {module}...")
            result = self._run_test_module(module)
            self.results[module] = result
            
            if result["success"]:
                print(f"✅ {module} completed successfully")
            else:
                print(f"❌ {module} failed")
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report()
        self._save_report(report)
        
        return report
    
    def _run_test_module(self, module: str) -> Dict[str, Any]:
        """Run a specific test module using pytest"""
        
        try:
            # Run pytest for the specific module
            cmd = [
                sys.executable, "-m", "pytest", 
                f"{module.replace('.', '/')}.py",
                "-v", "--tb=short", "--json-report", 
                f"--json-report-file=test_output/{module}_report.json"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=Path(__file__).parent
            )
            
            # Parse results
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "execution_time": time.time() - self.start_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        total_execution_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        successful_modules = sum(1 for r in self.results.values() if r["success"])
        total_modules = len(self.results)
        
        report = {
            "timestamp": time.time(),
            "execution_time": total_execution_time,
            "summary": {
                "total_test_modules": total_modules,
                "successful_modules": successful_modules,
                "failed_modules": total_modules - successful_modules,
                "success_rate": successful_modules / total_modules if total_modules > 0 else 0
            },
            "module_results": self.results,
            "quality_assessment": self._assess_overall_quality(),
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _assess_overall_quality(self) -> Dict[str, Any]:
        """Assess overall system quality based on test results"""
        
        quality_score = 0
        max_score = 100
        
        # Base score from test success rate
        successful_modules = sum(1 for r in self.results.values() if r["success"])
        total_modules = len(self.results)
        base_score = (successful_modules / total_modules * 60) if total_modules > 0 else 0
        quality_score += base_score
        
        # Additional scoring based on specific test types
        if "tests.test_integration_e2e" in self.results and self.results["tests.test_integration_e2e"]["success"]:
            quality_score += 15  # End-to-end functionality
        
        if "tests.test_performance_benchmarks" in self.results and self.results["tests.test_performance_benchmarks"]["success"]:
            quality_score += 10  # Performance benchmarks
        
        if "tests.test_data_validation" in self.results and self.results["tests.test_data_validation"]["success"]:
            quality_score += 10  # Data integrity
        
        if "tests.test_quality_assurance" in self.results and self.results["tests.test_quality_assurance"]["success"]:
            quality_score += 5   # Quality assurance
        
        # Determine quality grade
        if quality_score >= 90:
            grade = "A"
            status = "Excellent"
        elif quality_score >= 80:
            grade = "B"
            status = "Good"
        elif quality_score >= 70:
            grade = "C"
            status = "Acceptable"
        elif quality_score >= 60:
            grade = "D"
            status = "Needs Improvement"
        else:
            grade = "F"
            status = "Poor"
        
        return {
            "quality_score": quality_score,
            "max_score": max_score,
            "grade": grade,
            "status": status,
            "assessment": self._get_quality_assessment_details(quality_score)
        }
    
    def _get_quality_assessment_details(self, score: float) -> List[str]:
        """Get detailed quality assessment based on score"""
        
        details = []
        
        if score >= 90:
            details.append("System demonstrates excellent quality across all test categories")
            details.append("Ready for production deployment")
            details.append("Meets or exceeds all quality benchmarks")
        elif score >= 80:
            details.append("System shows good quality with minor areas for improvement")
            details.append("Suitable for staging environment testing")
            details.append("Most quality benchmarks are met")
        elif score >= 70:
            details.append("System quality is acceptable but requires attention")
            details.append("Some quality benchmarks need improvement")
            details.append("Additional testing and optimization recommended")
        elif score >= 60:
            details.append("System quality needs significant improvement")
            details.append("Multiple quality benchmarks are not met")
            details.append("Extensive optimization required before deployment")
        else:
            details.append("System quality is poor and requires major improvements")
            details.append("Most quality benchmarks are failing")
            details.append("System not ready for any deployment")
        
        return details
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        failed_modules = [module for module, result in self.results.items() if not result["success"]]
        
        if "tests.test_integration_e2e" in failed_modules:
            recommendations.append(
                "End-to-end functionality issues detected. Review user journey workflows "
                "and ensure all system components are properly integrated."
            )
        
        if "tests.test_performance_benchmarks" in failed_modules:
            recommendations.append(
                "Performance benchmarks not met. Consider optimizing database queries, "
                "implementing caching, or scaling infrastructure resources."
            )
        
        if "tests.test_data_validation" in failed_modules:
            recommendations.append(
                "Data validation issues found. Review data integrity constraints, "
                "schema definitions, and document processing pipelines."
            )
        
        if "tests.test_quality_assurance" in failed_modules:
            recommendations.append(
                "Quality assurance framework issues detected. Review test coverage, "
                "quality metrics collection, and validation thresholds."
            )
        
        if not failed_modules:
            recommendations.append(
                "All integration tests passed successfully. System is ready for deployment. "
                "Consider implementing continuous integration to maintain quality."
            )
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]) -> None:
        """Save comprehensive report to file"""
        
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        json_path = output_dir / "integration_test_report.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save human-readable report
        text_path = output_dir / "integration_test_report.txt"
        with open(text_path, 'w') as f:
            self._write_human_readable_report(f, report)
        
        print(f"\n📊 Comprehensive report saved:")
        print(f"   JSON: {json_path}")
        print(f"   Text: {text_path}")
    
    def _write_human_readable_report(self, file, report: Dict[str, Any]) -> None:
        """Write human-readable test report"""
        
        file.write("CSRD RAG System - Integration Test Report\n")
        file.write("=" * 50 + "\n\n")
        
        # Summary
        summary = report["summary"]
        file.write(f"Test Execution Summary:\n")
        file.write(f"  Total Test Modules: {summary['total_test_modules']}\n")
        file.write(f"  Successful Modules: {summary['successful_modules']}\n")
        file.write(f"  Failed Modules: {summary['failed_modules']}\n")
        file.write(f"  Success Rate: {summary['success_rate']:.1%}\n")
        file.write(f"  Total Execution Time: {report['execution_time']:.2f} seconds\n\n")
        
        # Quality Assessment
        quality = report["quality_assessment"]
        file.write(f"Quality Assessment:\n")
        file.write(f"  Quality Score: {quality['quality_score']:.1f}/{quality['max_score']}\n")
        file.write(f"  Grade: {quality['grade']}\n")
        file.write(f"  Status: {quality['status']}\n\n")
        
        for detail in quality["assessment"]:
            file.write(f"  • {detail}\n")
        file.write("\n")
        
        # Module Results
        file.write("Module Results:\n")
        for module, result in report["module_results"].items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            file.write(f"  {module}: {status}\n")
            if not result["success"] and "error" in result:
                file.write(f"    Error: {result['error']}\n")
        file.write("\n")
        
        # Recommendations
        file.write("Recommendations:\n")
        for i, rec in enumerate(report["recommendations"], 1):
            file.write(f"  {i}. {rec}\n")
    
    def print_summary(self, report: Dict[str, Any]) -> None:
        """Print test summary to console"""
        
        print("\n" + "=" * 70)
        print("🎯 INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        summary = report["summary"]
        quality = report["quality_assessment"]
        
        print(f"📊 Results: {summary['successful_modules']}/{summary['total_test_modules']} modules passed")
        print(f"⏱️  Execution Time: {report['execution_time']:.2f} seconds")
        print(f"🏆 Quality Score: {quality['quality_score']:.1f}/{quality['max_score']} (Grade: {quality['grade']})")
        print(f"📈 Status: {quality['status']}")
        
        if summary['success_rate'] >= 0.8:
            print("\n🎉 Integration testing completed successfully!")
            print("✅ System is ready for deployment")
        else:
            print("\n⚠️  Integration testing completed with issues")
            print("🔧 System requires attention before deployment")
        
        print("\n📋 Next Steps:")
        for i, rec in enumerate(report["recommendations"][:3], 1):
            print(f"  {i}. {rec}")


def main():
    """Main entry point for integration test runner"""
    
    runner = IntegrationTestRunner()
    
    try:
        report = runner.run_all_tests()
        runner.print_summary(report)
        
        # Exit with appropriate code
        if report["summary"]["success_rate"] >= 0.8:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Integration testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Integration testing failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
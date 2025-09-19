# Integration Tests and Quality Assurance

This document describes the comprehensive integration testing framework implemented for the CSRD RAG System as part of Task 23.

## Overview

The integration testing framework provides comprehensive validation of the entire CSRD RAG system through:

- **End-to-End User Journey Tests**: Complete workflows from document upload to report generation
- **Schema Classification Accuracy Tests**: Automated validation of EU ESRS/CSRD and UK SRD schema classification
- **RAG Response Quality Tests**: Quality metrics for AI-generated responses and source citations
- **Performance Benchmarking**: Response time and throughput validation against defined benchmarks
- **Data Validation Tests**: Schema compliance and document integrity verification
- **Requirements Validation**: Comprehensive validation against all system requirements

## Test Structure

### Core Test Modules

1. **`test_integration_e2e.py`** - End-to-end user journey testing
   - Complete document upload to report generation workflows
   - Multi-schema document processing validation
   - Concurrent processing stress testing
   - Error recovery and system resilience testing

2. **`test_performance_benchmarks.py`** - Performance validation
   - Document processing performance benchmarks
   - Query response time validation
   - Concurrent load testing
   - System resource usage monitoring

3. **`test_data_validation.py`** - Data integrity and schema compliance
   - EU ESRS/CSRD schema compliance validation
   - UK SRD schema compliance validation
   - Document processing integrity verification
   - Database referential integrity testing

4. **`test_quality_assurance.py`** - Quality assurance framework
   - Comprehensive system validation orchestration
   - Quality metrics collection and reporting
   - Requirements validation against specifications
   - Quality threshold validation

### Supporting Infrastructure

- **`run_integration_tests.py`** - Test orchestration and reporting
- **`validate_integration_tests.py`** - Framework validation utility
- **`pytest_integration.ini`** - Test configuration
- **`test_output/`** - Generated reports and artifacts

## Performance Benchmarks

The system is validated against the following performance targets:

| Metric | Target | Description |
|--------|--------|-------------|
| Small Document Processing | ≤ 10s | Documents < 5KB |
| Medium Document Processing | ≤ 30s | Documents 5-50KB |
| Large Document Processing | ≤ 60s | Documents > 50KB |
| Search Query Response | ≤ 2s | Vector similarity search |
| RAG Query Response | ≤ 5s | AI-generated responses |
| API Response Time | ≤ 0.5s | Metadata operations |
| Concurrent Processing | ≤ 45s | 5 documents simultaneously |

## Quality Thresholds

The system must meet these quality benchmarks:

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Schema Classification Accuracy | ≥ 80% | Correct schema element detection |
| RAG Response Quality | ≥ 70% | Response relevance and accuracy |
| Search Relevance Accuracy | ≥ 60% | Search result relevance |
| Test Success Rate | ≥ 95% | Overall test pass rate |
| System Availability | ≥ 99% | Uptime during testing |

## Running the Tests

### Prerequisites

1. **System Setup**: Ensure the CSRD RAG system is properly configured
2. **Dependencies**: Install all required Python packages
3. **Database**: Test database should be available and accessible
4. **AI Models**: At least one AI model should be configured (GPT-4 recommended)

### Validation

Before running comprehensive tests, validate the framework:

```bash
cd backend
python3 validate_integration_tests.py
```

### Full Integration Test Suite

Run the complete integration test suite:

```bash
cd backend
python3 run_integration_tests.py
```

### Individual Test Modules

Run specific test categories:

```bash
# End-to-end tests
pytest tests/test_integration_e2e.py -v

# Performance benchmarks
pytest tests/test_performance_benchmarks.py -v

# Data validation
pytest tests/test_data_validation.py -v

# Quality assurance
pytest tests/test_quality_assurance.py -v
```

### Test Configuration

Customize test behavior using pytest options:

```bash
# Run with detailed output
pytest tests/ -v --tb=long

# Run specific test markers
pytest tests/ -m "performance" -v

# Generate JSON report
pytest tests/ --json-report --json-report-file=test_output/custom_report.json
```

## Test Reports

The framework generates comprehensive reports in the `test_output/` directory:

### Generated Reports

1. **`integration_test_report.json`** - Machine-readable comprehensive report
2. **`integration_test_report.txt`** - Human-readable summary report
3. **`quality_assurance_report.json`** - Quality metrics and validation results
4. **Individual module reports** - Detailed results for each test module

### Report Structure

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "execution_time": 120.5,
  "summary": {
    "total_test_modules": 4,
    "successful_modules": 4,
    "failed_modules": 0,
    "success_rate": 1.0
  },
  "quality_assessment": {
    "quality_score": 95.0,
    "grade": "A",
    "status": "Excellent"
  },
  "module_results": { ... },
  "recommendations": [ ... ]
}
```

## Test Categories and Markers

Tests are organized using pytest markers:

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.e2e` - End-to-end user journeys
- `@pytest.mark.quality` - Quality assurance tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.requires_models` - Tests requiring AI models

## Requirements Validation

The framework validates the system against all specified requirements:

### Validated Requirements

- **Requirement 1**: Document Repository Management
- **Requirement 3**: Intelligent Search Functionality
- **Requirement 4**: RAG-based Question Answering
- **Requirement 5**: User Interface and Experience
- **Requirement 6**: Data Schema and Reporting Standards Support
- **Requirement 8**: System Configuration and Setup

### Validation Process

Each requirement is tested through multiple test cases that verify:
- Functional compliance with acceptance criteria
- Performance within specified limits
- Error handling and edge cases
- Data integrity and consistency

## Continuous Integration

The integration test framework is designed for CI/CD integration:

### CI Configuration Example

```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate test framework
        run: python3 backend/validate_integration_tests.py
      - name: Run integration tests
        run: python3 backend/run_integration_tests.py
      - name: Upload test reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: backend/test_output/
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and PYTHONPATH is set correctly
2. **Database Connection**: Verify test database is accessible and properly configured
3. **AI Model Access**: Ensure API keys are configured for AI model services
4. **Timeout Issues**: Increase timeout values for slower environments
5. **Permission Errors**: Ensure write permissions for test output directory

### Debug Mode

Run tests with debug information:

```bash
pytest tests/ -v --tb=long --capture=no --log-cli-level=DEBUG
```

### Test Data Cleanup

Clean up test artifacts:

```bash
# Remove test output
rm -rf backend/test_output/*

# Clean test database (if using separate test DB)
python3 backend/clean_test_data.py
```

## Extending the Framework

### Adding New Test Cases

1. Create test methods in appropriate test modules
2. Use proper pytest markers for categorization
3. Follow naming conventions (`test_*`)
4. Include comprehensive assertions and error messages
5. Add performance benchmarks where applicable

### Custom Quality Metrics

Extend the quality assurance framework:

```python
class CustomQualityMetrics:
    def __init__(self):
        self.custom_thresholds = {
            "custom_metric": 0.85
        }
    
    def validate_custom_quality(self, results):
        # Custom validation logic
        pass
```

### Integration with Monitoring

Connect test results to monitoring systems:

```python
def send_metrics_to_monitoring(report):
    # Send quality metrics to monitoring system
    # e.g., Prometheus, Grafana, DataDog
    pass
```

## Quality Assurance Methodology

The integration testing framework follows these QA principles:

1. **Comprehensive Coverage**: All user journeys and system components are tested
2. **Performance Validation**: All operations meet defined performance benchmarks
3. **Data Integrity**: All data processing maintains consistency and accuracy
4. **Error Resilience**: System handles errors gracefully and recovers appropriately
5. **Requirements Traceability**: Every requirement is validated through specific tests
6. **Continuous Monitoring**: Quality metrics are tracked over time
7. **Automated Reporting**: Results are automatically documented and reported

## Conclusion

This integration testing framework provides comprehensive validation of the CSRD RAG system, ensuring:

- ✅ All requirements are met and validated
- ✅ Performance benchmarks are achieved
- ✅ Data integrity is maintained
- ✅ System quality meets production standards
- ✅ Continuous quality monitoring is enabled

The framework supports both development validation and production readiness assessment, providing confidence in system reliability and performance.
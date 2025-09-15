"""
Test Runner for Sprint 1 Implementation
======================================
Comprehensive test runner for all Sprint 1 components.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def run_all_tests():
    """Run all tests for Sprint 1 implementation."""
    print("🚀 Running Sprint 1 Test Suite")
    print("=" * 50)
    
    # Test directories
    test_dirs = [
        "tests/test_post_management_service.py",
        "tests/test_analytics_service.py", 
        "tests/test_post_management_api.py"
    ]
    
    # Run tests with coverage
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=app",  # Coverage for app directory
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing",  # Show missing lines
        "--cov-fail-under=90",  # Fail if coverage < 90%
        "--asyncio-mode=auto",  # Auto async mode
        "-x",  # Stop on first failure
    ]
    
    # Add test files
    pytest_args.extend(test_dirs)
    
    # Run pytest
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        print("Check the output above for details.")
    
    return exit_code

def run_specific_tests(test_pattern):
    """Run specific tests based on pattern."""
    print(f"🔍 Running tests matching: {test_pattern}")
    print("=" * 50)
    
    pytest_args = [
        "-v",
        "--tb=short",
        "-k", test_pattern,
        "--asyncio-mode=auto"
    ]
    
    exit_code = pytest.main(pytest_args)
    return exit_code

def run_performance_tests():
    """Run performance tests."""
    print("⚡ Running Performance Tests")
    print("=" * 50)
    
    # Performance test configuration
    pytest_args = [
        "-v",
        "--tb=short",
        "-m", "performance",
        "--asyncio-mode=auto",
        "--durations=10"  # Show 10 slowest tests
    ]
    
    exit_code = pytest.main(pytest_args)
    return exit_code

def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running Integration Tests")
    print("=" * 50)
    
    pytest_args = [
        "-v",
        "--tb=short",
        "-m", "integration",
        "--asyncio-mode=auto"
    ]
    
    exit_code = pytest.main(pytest_args)
    return exit_code

def main():
    """Main test runner function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            exit_code = run_all_tests()
        elif command == "unit":
            exit_code = run_specific_tests("not integration and not performance")
        elif command == "integration":
            exit_code = run_integration_tests()
        elif command == "performance":
            exit_code = run_performance_tests()
        elif command == "service":
            exit_code = run_specific_tests("TestPostManagementService or TestAnalyticsService")
        elif command == "api":
            exit_code = run_specific_tests("TestPostManagementAPI")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: all, unit, integration, performance, service, api")
            exit_code = 1
    else:
        # Default: run all tests
        exit_code = run_all_tests()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive Functionality Test
===============================
Tests all functionality to ensure nothing is broken after improvements
"""

import sys
import os
import asyncio
import json
import time
import subprocess
import requests
from typing import Dict, List, Any, Tuple
import logging

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FunctionalityTester:
    """Comprehensive functionality tester"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {}
        self.start_time = time.time()
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
        self.test_results[test_name] = {
            'success': success,
            'message': message,
            'timestamp': time.time()
        }
    
    def test_environment_setup(self) -> bool:
        """Test environment setup"""
        try:
            # Check if virtual environment exists
            if not os.path.exists('venv'):
                self.log_test("Virtual Environment", False, "Virtual environment not found")
                return False
            
            # Check if requirements are installed
            result = subprocess.run([
                'venv/bin/python', '-c', 
                'import fastapi, uvicorn, pymongo, motor, pydantic'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_test("Python Dependencies", False, f"Missing dependencies: {result.stderr}")
                return False
            
            # Check if frontend dependencies are installed
            if not os.path.exists('frontend/node_modules'):
                self.log_test("Frontend Dependencies", False, "Node modules not found")
                return False
            
            self.log_test("Environment Setup", True, "All dependencies installed")
            return True
            
        except Exception as e:
            self.log_test("Environment Setup", False, f"Error: {str(e)}")
            return False
    
    def test_backend_imports(self) -> bool:
        """Test backend imports"""
        try:
            # Test core imports
            from backend.app.core.config import get_settings
            from backend.app.core.database import get_database
            from backend.app.core.security import SecurityHeaders, InputValidator
            from backend.app.core.monitoring import MetricsCollector, HealthChecker
            
            # Test configuration
            settings = get_settings()
            if not settings.validate_configuration():
                self.log_test("Backend Configuration", False, "Configuration validation failed")
                return False
            
            self.log_test("Backend Imports", True, "All core modules imported successfully")
            return True
            
        except Exception as e:
            self.log_test("Backend Imports", False, f"Import error: {str(e)}")
            return False
    
    def test_backend_startup(self) -> bool:
        """Test backend startup"""
        try:
            # Start backend in background
            process = subprocess.Popen([
                'venv/bin/python', '-m', 'uvicorn', 
                'backend.app.main:app', '--host', '0.0.0.0', '--port', '8000'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for startup
            time.sleep(5)
            
            # Test health endpoint
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                if response.status_code == 200:
                    self.log_test("Backend Startup", True, "Backend started and responding")
                    process.terminate()
                    return True
                else:
                    self.log_test("Backend Startup", False, f"Health check failed: {response.status_code}")
                    process.terminate()
                    return False
            except requests.exceptions.RequestException as e:
                self.log_test("Backend Startup", False, f"Health check error: {str(e)}")
                process.terminate()
                return False
                
        except Exception as e:
            self.log_test("Backend Startup", False, f"Startup error: {str(e)}")
            return False
    
    def test_frontend_build(self) -> bool:
        """Test frontend build"""
        try:
            # Change to frontend directory
            original_dir = os.getcwd()
            os.chdir('frontend')
            
            # Run build
            result = subprocess.run(['npm', 'run', 'build'], 
                                  capture_output=True, text=True, timeout=300)
            
            os.chdir(original_dir)
            
            if result.returncode != 0:
                self.log_test("Frontend Build", False, f"Build failed: {result.stderr}")
                return False
            
            # Check if build output exists
            if not os.path.exists('frontend/.next'):
                self.log_test("Frontend Build", False, "Build output not found")
                return False
            
            self.log_test("Frontend Build", True, "Frontend built successfully")
            return True
            
        except Exception as e:
            self.log_test("Frontend Build", False, f"Build error: {str(e)}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code != 200:
                self.log_test("API Health Endpoint", False, f"Status: {response.status_code}")
                return False
            
            # Test API documentation
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            if response.status_code != 200:
                self.log_test("API Documentation", False, f"Status: {response.status_code}")
                return False
            
            # Test OpenAPI schema
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            if response.status_code != 200:
                self.log_test("OpenAPI Schema", False, f"Status: {response.status_code}")
                return False
            
            self.log_test("API Endpoints", True, "All API endpoints responding")
            return True
            
        except Exception as e:
            self.log_test("API Endpoints", False, f"API error: {str(e)}")
            return False
    
    def test_security_features(self) -> bool:
        """Test security features"""
        try:
            # Test security headers
            response = requests.get(f"{self.base_url}/health", timeout=10)
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Referrer-Policy'
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if missing_headers:
                self.log_test("Security Headers", False, f"Missing headers: {missing_headers}")
                return False
            
            # Test input validation
            from backend.app.core.security import InputValidator
            
            # Test email validation
            if not InputValidator.validate_email("test@example.com"):
                self.log_test("Email Validation", False, "Valid email rejected")
                return False
            
            if InputValidator.validate_email("invalid-email"):
                self.log_test("Email Validation", False, "Invalid email accepted")
                return False
            
            # Test password strength validation
            is_strong, errors = InputValidator.validate_password_strength("WeakPass")
            if is_strong:
                self.log_test("Password Validation", False, "Weak password accepted")
                return False
            
            is_strong, errors = InputValidator.validate_password_strength("StrongPass123!")
            if not is_strong:
                self.log_test("Password Validation", False, f"Strong password rejected: {errors}")
                return False
            
            self.log_test("Security Features", True, "All security features working")
            return True
            
        except Exception as e:
            self.log_test("Security Features", False, f"Security error: {str(e)}")
            return False
    
    def test_monitoring_features(self) -> bool:
        """Test monitoring features"""
        try:
            from backend.app.core.monitoring import MetricsCollector, HealthChecker
            
            # Test metrics collection
            metrics = MetricsCollector()
            metrics.increment_counter("test_counter")
            metrics.set_gauge("test_gauge", 42.0)
            metrics.record_timer("test_timer", 0.1)
            
            summary = metrics.get_metrics_summary()
            if not summary or 'counters' not in summary:
                self.log_test("Metrics Collection", False, "Metrics not collected properly")
                return False
            
            # Test health checker
            health_checker = HealthChecker()
            health_status = health_checker.get_overall_status()
            if health_status not in ['healthy', 'unhealthy', 'unknown']:
                self.log_test("Health Checker", False, f"Invalid health status: {health_status}")
                return False
            
            self.log_test("Monitoring Features", True, "All monitoring features working")
            return True
            
        except Exception as e:
            self.log_test("Monitoring Features", False, f"Monitoring error: {str(e)}")
            return False
    
    def test_docker_configuration(self) -> bool:
        """Test Docker configuration"""
        try:
            # Check if Docker files exist
            docker_files = [
                'docker-compose.yml',
                'docker-compose.dev.yml',
                'backend/Dockerfile',
                'backend/Dockerfile.dev',
                'frontend/Dockerfile',
                'frontend/Dockerfile.dev'
            ]
            
            missing_files = []
            for file_path in docker_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("Docker Configuration", False, f"Missing files: {missing_files}")
                return False
            
            # Test Docker Compose syntax
            result = subprocess.run(['docker-compose', 'config'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log_test("Docker Compose Syntax", False, f"Syntax error: {result.stderr}")
                return False
            
            self.log_test("Docker Configuration", True, "All Docker files valid")
            return True
            
        except Exception as e:
            self.log_test("Docker Configuration", False, f"Docker error: {str(e)}")
            return False
    
    def test_environment_templates(self) -> bool:
        """Test environment templates"""
        try:
            # Check if template files exist
            template_files = [
                'env.template',
                'frontend/env.template'
            ]
            
            missing_files = []
            for file_path in template_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("Environment Templates", False, f"Missing files: {missing_files}")
                return False
            
            # Check if template files have content
            for file_path in template_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if len(content) < 100:  # Minimum expected content
                        self.log_test("Environment Templates", False, f"Template {file_path} too short")
                        return False
            
            self.log_test("Environment Templates", True, "All templates valid")
            return True
            
        except Exception as e:
            self.log_test("Environment Templates", False, f"Template error: {str(e)}")
            return False
    
    def test_playwright_tests(self) -> bool:
        """Test Playwright tests"""
        try:
            # Check if Playwright tests exist
            test_files = [
                'final-working-tests.spec.ts',
                'simple-demo-test.spec.ts',
                'comprehensive-functionality-tests.spec.ts'
            ]
            
            existing_tests = []
            for test_file in test_files:
                if os.path.exists(test_file):
                    existing_tests.append(test_file)
            
            if not existing_tests:
                self.log_test("Playwright Tests", False, "No test files found")
                return False
            
            # Test Playwright configuration
            if not os.path.exists('playwright.config.js'):
                self.log_test("Playwright Tests", False, "Playwright config not found")
                return False
            
            self.log_test("Playwright Tests", True, f"Found {len(existing_tests)} test files")
            return True
            
        except Exception as e:
            self.log_test("Playwright Tests", False, f"Playwright error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all functionality tests"""
        logger.info("🧪 Starting Comprehensive Functionality Tests")
        logger.info("=" * 50)
        
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Backend Imports", self.test_backend_imports),
            ("Backend Startup", self.test_backend_startup),
            ("Frontend Build", self.test_frontend_build),
            ("API Endpoints", self.test_api_endpoints),
            ("Security Features", self.test_security_features),
            ("Monitoring Features", self.test_monitoring_features),
            ("Docker Configuration", self.test_docker_configuration),
            ("Environment Templates", self.test_environment_templates),
            ("Playwright Tests", self.test_playwright_tests),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test exception: {str(e)}")
                failed += 1
        
        # Generate summary
        total_time = time.time() - self.start_time
        success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
        
        summary = {
            'total_tests': passed + failed,
            'passed': passed,
            'failed': failed,
            'success_rate': success_rate,
            'total_time': total_time,
            'test_results': self.test_results
        }
        
        logger.info("=" * 50)
        logger.info(f"🎯 Test Summary:")
        logger.info(f"   Total Tests: {passed + failed}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Total Time: {total_time:.2f}s")
        logger.info("=" * 50)
        
        if failed == 0:
            logger.info("🎉 All tests passed! The project is fully functional.")
        else:
            logger.warning(f"⚠️  {failed} tests failed. Please check the issues above.")
        
        return summary


def main():
    """Main test runner"""
    tester = FunctionalityTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📊 Test results saved to test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
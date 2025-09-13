#!/usr/bin/env python3
"""
Basic Functionality Test
=======================
Tests basic functionality without requiring full environment setup
"""

import sys
import os
import json
import time
import subprocess
from typing import Dict, List, Any, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasicFunctionalityTester:
    """Basic functionality tester"""
    
    def __init__(self):
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
    
    def test_file_structure(self) -> bool:
        """Test file structure"""
        try:
            required_files = [
                'README.md',
                'package.json',
                'pyproject.toml',
                'backend/requirements.txt',
                'frontend/package.json',
                'backend/app/main.py',
                'frontend/app/page.tsx',
                'docker-compose.yml',
                'docker-compose.dev.yml',
                'env.template',
                'frontend/env.template',
                'setup.sh',
                'start_app.sh',
                'stop_app.sh'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("File Structure", False, f"Missing files: {missing_files}")
                return False
            
            self.log_test("File Structure", True, f"All {len(required_files)} required files present")
            return True
            
        except Exception as e:
            self.log_test("File Structure", False, f"Error: {str(e)}")
            return False
    
    def test_backend_structure(self) -> bool:
        """Test backend structure"""
        try:
            backend_files = [
                'backend/app/main.py',
                'backend/app/core/application.py',
                'backend/app/core/config.py',
                'backend/app/core/database.py',
                'backend/app/core/security.py',
                'backend/app/core/monitoring.py',
                'backend/requirements.txt',
                'backend/Dockerfile',
                'backend/Dockerfile.dev'
            ]
            
            missing_files = []
            for file_path in backend_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("Backend Structure", False, f"Missing files: {missing_files}")
                return False
            
            # Check if main.py has content
            with open('backend/app/main.py', 'r') as f:
                content = f.read()
                if len(content) < 50:
                    self.log_test("Backend Structure", False, "main.py is too short")
                    return False
            
            self.log_test("Backend Structure", True, f"All {len(backend_files)} backend files present")
            return True
            
        except Exception as e:
            self.log_test("Backend Structure", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_structure(self) -> bool:
        """Test frontend structure"""
        try:
            frontend_files = [
                'frontend/app/page.tsx',
                'frontend/package.json',
                'frontend/next.config.js',
                'frontend/tailwind.config.js',
                'frontend/tsconfig.json',
                'frontend/Dockerfile',
                'frontend/Dockerfile.dev'
            ]
            
            missing_files = []
            for file_path in frontend_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("Frontend Structure", False, f"Missing files: {missing_files}")
                return False
            
            # Check if package.json has required dependencies
            with open('frontend/package.json', 'r') as f:
                package_data = json.load(f)
                required_deps = ['next', 'react', 'typescript', 'tailwindcss']
                missing_deps = []
                for dep in required_deps:
                    if dep not in package_data.get('dependencies', {}) and dep not in package_data.get('devDependencies', {}):
                        missing_deps.append(dep)
                
                if missing_deps:
                    self.log_test("Frontend Structure", False, f"Missing dependencies: {missing_deps}")
                    return False
            
            self.log_test("Frontend Structure", True, f"All {len(frontend_files)} frontend files present")
            return True
            
        except Exception as e:
            self.log_test("Frontend Structure", False, f"Error: {str(e)}")
            return False
    
    def test_docker_configuration(self) -> bool:
        """Test Docker configuration"""
        try:
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
            
            # Check if docker-compose.yml has content
            with open('docker-compose.yml', 'r') as f:
                content = f.read()
                if 'version:' not in content or 'services:' not in content:
                    self.log_test("Docker Configuration", False, "docker-compose.yml is invalid")
                    return False
            
            self.log_test("Docker Configuration", True, f"All {len(docker_files)} Docker files present")
            return True
            
        except Exception as e:
            self.log_test("Docker Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_environment_templates(self) -> bool:
        """Test environment templates"""
        try:
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
            
            # Check if templates have content
            for file_path in template_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if len(content) < 100:  # Minimum expected content
                        self.log_test("Environment Templates", False, f"Template {file_path} too short")
                        return False
            
            self.log_test("Environment Templates", True, f"All {len(template_files)} templates valid")
            return True
            
        except Exception as e:
            self.log_test("Environment Templates", False, f"Error: {str(e)}")
            return False
    
    def test_scripts(self) -> bool:
        """Test scripts"""
        try:
            script_files = [
                'setup.sh',
                'start_app.sh',
                'stop_app.sh'
            ]
            
            missing_files = []
            for file_path in script_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("Scripts", False, f"Missing files: {missing_files}")
                return False
            
            # Check if scripts are executable
            for file_path in script_files:
                if not os.access(file_path, os.X_OK):
                    self.log_test("Scripts", False, f"Script {file_path} is not executable")
                    return False
            
            self.log_test("Scripts", True, f"All {len(script_files)} scripts present and executable")
            return True
            
        except Exception as e:
            self.log_test("Scripts", False, f"Error: {str(e)}")
            return False
    
    def test_documentation(self) -> bool:
        """Test documentation"""
        try:
            doc_files = [
                'README.md',
                'ISSUES_FIXED_SUMMARY.md',
                'TESTING_SUMMARY.md',
                'UI_VERIFICATION_COMPLETE.md',
                'PLAYWRIGHT_TEST_REPORT.md'
            ]
            
            existing_docs = []
            for file_path in doc_files:
                if os.path.exists(file_path):
                    existing_docs.append(file_path)
            
            if len(existing_docs) < 3:  # At least 3 documentation files
                self.log_test("Documentation", False, f"Only {len(existing_docs)} documentation files found")
                return False
            
            # Check if README has content
            with open('README.md', 'r') as f:
                content = f.read()
                if len(content) < 500:  # Minimum expected content
                    self.log_test("Documentation", False, "README.md too short")
                    return False
            
            self.log_test("Documentation", True, f"Found {len(existing_docs)} documentation files")
            return True
            
        except Exception as e:
            self.log_test("Documentation", False, f"Error: {str(e)}")
            return False
    
    def test_test_files(self) -> bool:
        """Test test files"""
        try:
            # Count test files
            test_count = 0
            
            # Python test files
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_count += 1
                    elif file.endswith('.spec.ts') or file.endswith('.test.js') or file.endswith('.test.ts'):
                        test_count += 1
            
            if test_count < 5:  # At least 5 test files
                self.log_test("Test Files", False, f"Only {test_count} test files found")
                return False
            
            self.log_test("Test Files", True, f"Found {test_count} test files")
            return True
            
        except Exception as e:
            self.log_test("Test Files", False, f"Error: {str(e)}")
            return False
    
    def test_configuration_files(self) -> bool:
        """Test configuration files"""
        try:
            config_files = [
                'pyproject.toml',
                'pytest.ini',
                'frontend/next.config.js',
                'frontend/tailwind.config.js',
                'frontend/tsconfig.json',
                'playwright.config.js'
            ]
            
            missing_files = []
            for file_path in config_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("Configuration Files", False, f"Missing files: {missing_files}")
                return False
            
            self.log_test("Configuration Files", True, f"All {len(config_files)} configuration files present")
            return True
            
        except Exception as e:
            self.log_test("Configuration Files", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all basic functionality tests"""
        logger.info("🧪 Starting Basic Functionality Tests")
        logger.info("=" * 50)
        
        tests = [
            ("File Structure", self.test_file_structure),
            ("Backend Structure", self.test_backend_structure),
            ("Frontend Structure", self.test_frontend_structure),
            ("Docker Configuration", self.test_docker_configuration),
            ("Environment Templates", self.test_environment_templates),
            ("Scripts", self.test_scripts),
            ("Documentation", self.test_documentation),
            ("Test Files", self.test_test_files),
            ("Configuration Files", self.test_configuration_files),
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
            logger.info("🎉 All tests passed! The project structure is complete.")
        else:
            logger.warning(f"⚠️  {failed} tests failed. Please check the issues above.")
        
        return summary


def main():
    """Main test runner"""
    tester = BasicFunctionalityTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open('basic_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📊 Test results saved to basic_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
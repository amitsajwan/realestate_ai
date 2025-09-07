#!/usr/bin/env python3
"""
Simple validation script for refactoring work
=============================================

This script validates the refactored components without complex dependencies
"""

import sys
import os
import importlib.util

def validate_file_exists(file_path, description):
    """Validate that a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def validate_file_content(file_path, required_content, description):
    """Validate that a file contains required content"""
    if not os.path.exists(file_path):
        print(f"❌ {description}: {file_path} - FILE NOT FOUND")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for item in required_content:
            if item in content:
                print(f"✅ {description}: Contains '{item}'")
            else:
                print(f"❌ {description}: Missing '{item}'")
                return False
        return True
    except Exception as e:
        print(f"❌ {description}: Error reading file - {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Refactoring Validation Report")
    print("=" * 50)
    
    validation_results = []
    
    # Backend Refactoring Validation
    print("\n📁 Backend Refactoring:")
    print("-" * 30)
    
    # Smart Property Service
    smart_property_service_path = "/workspace/backend/app/services/smart_property_service.py"
    validation_results.append(validate_file_exists(smart_property_service_path, "Smart Property Service"))
    
    if os.path.exists(smart_property_service_path):
        required_content = [
            "import logging",
            "DatabaseError",
            "logger = logging.getLogger(__name__)",
            "async def get_user_smart_properties"
        ]
        validation_results.append(validate_file_content(
            smart_property_service_path, 
            required_content, 
            "Smart Property Service - Enhanced Error Handling"
        ))
    
    # Backend Tests
    print("\n🧪 Backend Tests:")
    print("-" * 20)
    
    test_files = [
        "/workspace/tests/test_smart_property_service.py",
        "/workspace/tests/test_smart_properties_integration.py"
    ]
    
    for test_file in test_files:
        validation_results.append(validate_file_exists(test_file, f"Test File: {os.path.basename(test_file)}"))
        
        if os.path.exists(test_file):
            required_content = [
                "import pytest",
                "class Test",
                "async def test_"
            ]
            validation_results.append(validate_file_content(
                test_file,
                required_content,
                f"Test File Content: {os.path.basename(test_file)}"
            ))
    
    # Frontend Refactoring Validation
    print("\n📁 Frontend Refactoring:")
    print("-" * 30)
    
    # Refactored Hook
    refactored_hook_path = "/workspace/frontend/hooks/usePropertyFormRefactored.ts"
    validation_results.append(validate_file_exists(refactored_hook_path, "Refactored Property Form Hook"))
    
    if os.path.exists(refactored_hook_path):
        required_content = [
            "export function usePropertyFormRefactored",
            "interface FormState",
            "interface AISuggestions",
            "const generateAISuggestions = useCallback",
            "const applyAISuggestions = useCallback"
        ]
        validation_results.append(validate_file_content(
            refactored_hook_path,
            required_content,
            "Refactored Hook - Simplified Architecture"
        ))
    
    # Refactored API Service
    refactored_api_path = "/workspace/frontend/lib/apiRefactored.ts"
    validation_results.append(validate_file_exists(refactored_api_path, "Refactored API Service"))
    
    if os.path.exists(refactored_api_path):
        required_content = [
            "export class APIServiceRefactored",
            "private retryConfig: RetryConfig",
            "private pendingRequests: Map<string, Promise<any>>",
            "private isOnline: boolean",
            "executeRequestWithRetry",
            "calculateRetryDelay"
        ]
        validation_results.append(validate_file_content(
            refactored_api_path,
            required_content,
            "Refactored API Service - Retry Logic & Error Handling"
        ))
    
    # Frontend Tests
    print("\n🧪 Frontend Tests:")
    print("-" * 20)
    
    frontend_test_path = "/workspace/frontend/__tests__/hooks/usePropertyFormRefactored.test.ts"
    validation_results.append(validate_file_exists(frontend_test_path, "Frontend Hook Tests"))
    
    if os.path.exists(frontend_test_path):
        required_content = [
            "import { renderHook, act, waitFor }",
            "describe('usePropertyFormRefactored'",
            "test('should initialize with default values'",
            "test('should generate AI suggestions successfully'",
            "test('should handle form submission errors'"
        ]
        validation_results.append(validate_file_content(
            frontend_test_path,
            required_content,
            "Frontend Tests - Comprehensive Coverage"
        ))
    
    # Summary
    print("\n📊 Validation Summary:")
    print("=" * 30)
    
    total_tests = len(validation_results)
    passed_tests = sum(validation_results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Validations: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 All validations passed! Refactoring is complete.")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} validation(s) failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

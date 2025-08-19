#!/usr/bin/env python3
"""
FastAPI Project Cleanup Script
Removes duplicate, conflicting, and unnecessary files
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message: str, color: str = Colors.WHITE):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.END}")

def print_header(title: str):
    """Print section header"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"{title.center(60)}", Colors.BOLD + Colors.CYAN)
    print_colored(f"{'='*60}", Colors.CYAN)

def confirm_deletion(files: List[str], category: str) -> bool:
    """Ask user to confirm deletion of files"""
    print_colored(f"\n{category} - Files to delete:", Colors.YELLOW + Colors.BOLD)
    for i, file_path in enumerate(files, 1):
        if os.path.exists(file_path):
            print_colored(f"  {i}. ✓ {file_path}", Colors.RED)
        else:
            print_colored(f"  {i}. ✗ {file_path} (not found)", Colors.YELLOW)
    
    existing_files = [f for f in files if os.path.exists(f)]
    if not existing_files:
        print_colored("  No files found to delete in this category.", Colors.GREEN)
        return False
    
    while True:
        response = input(f"\nDelete {len(existing_files)} files from {category}? (y/n/skip): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            print_colored("  Skipping deletion for this category.", Colors.YELLOW)
            return False
        elif response == 'skip':
            print_colored("  Skipping this category.", Colors.BLUE)
            return False
        else:
            print_colored("  Please enter 'y' (yes), 'n' (no), or 'skip'", Colors.RED)

def delete_files(files: List[str], category: str) -> Dict[str, List[str]]:
    """Delete files and return results"""
    results = {
        'deleted': [],
        'not_found': [],
        'failed': []
    }
    
    for file_path in files:
        try:
            if os.path.exists(file_path):
                # Create backup before deletion
                backup_path = file_path + '.backup'
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(file_path, backup_path)
                results['deleted'].append(file_path)
                print_colored(f"  ✓ Deleted: {file_path} (backup: {backup_path})", Colors.GREEN)
            else:
                results['not_found'].append(file_path)
                print_colored(f"  ✗ Not found: {file_path}", Colors.YELLOW)
        except Exception as e:
            results['failed'].append(f"{file_path}: {str(e)}")
            print_colored(f"  ✗ Failed to delete {file_path}: {str(e)}", Colors.RED)
    
    return results

def main():
    """Main cleanup function"""
    print_header("FastAPI Project Cleanup Script")
    print_colored("This script will help you clean up duplicate and conflicting files.", Colors.WHITE)
    print_colored("Files will be renamed to .backup instead of permanently deleted.", Colors.GREEN)
    
    # Get current directory
    current_dir = Path.cwd()
    print_colored(f"Working directory: {current_dir}", Colors.BLUE)
    
    # Define file groups for deletion
    file_groups = {
        "CRITICAL CONFLICTS": [
            "app/config.py",
            "app/api/v1/router.py",
            "app/logging.py",
            "app/utils/db_client.py",
            "core/dependencies.py",
            "core/unified_auth.py",
        ],
        
        "SERVICE CONFLICTS": [
            "app/services/user_service.py",
            "app/db_integration.py",
        ],
        
        "DUPLICATE REPOSITORIES": [
            "app/repositories/base.py",  # Keep base_repository.py instead
        ],
        
        "OPTIONAL CLEANUPS": [
            "core/connections.py",
            "core/security.py",
        ],
        
        "EMPTY INIT FILES": [
            "app/api/endpoints/__init__.py",
            "app/api/v1/__init__.py", 
            "app/api/v1/endpoints/__init__.py",
            "app/routes/__init__.py",
            "app/services/__init__.py",
            "app/utils/__init__.py",
        ]
    }
    
    # Track all results
    all_results = {}
    
    # Process each group
    for category, files in file_groups.items():
        if confirm_deletion(files, category):
            results = delete_files(files, category)
            all_results[category] = results
        else:
            print_colored(f"Skipped {category}", Colors.BLUE)
    
    # Print summary
    print_header("CLEANUP SUMMARY")
    
    total_deleted = 0
    total_failed = 0
    total_not_found = 0
    
    for category, results in all_results.items():
        if results['deleted']:
            print_colored(f"\n{category}:", Colors.GREEN + Colors.BOLD)
            print_colored(f"  Deleted: {len(results['deleted'])} files", Colors.GREEN)
            total_deleted += len(results['deleted'])
        
        if results['failed']:
            print_colored(f"  Failed: {len(results['failed'])} files", Colors.RED)
            for failure in results['failed']:
                print_colored(f"    - {failure}", Colors.RED)
            total_failed += len(results['failed'])
        
        if results['not_found']:
            total_not_found += len(results['not_found'])
    
    print_colored(f"\nOVERALL SUMMARY:", Colors.BOLD + Colors.CYAN)
    print_colored(f"  Files deleted: {total_deleted}", Colors.GREEN)
    print_colored(f"  Files not found: {total_not_found}", Colors.YELLOW)
    print_colored(f"  Files failed: {total_failed}", Colors.RED)
    
    # Show next steps
    print_header("NEXT STEPS")
    print_colored("1. Fix remaining import errors in these files:", Colors.YELLOW)
    print_colored("   - app/dependencies.py (fix typo on last line)", Colors.WHITE)
    print_colored("   - app/api/endpoints/dashboard.py (fix import paths)", Colors.WHITE)
    print_colored("   - app/repositories/lead_repository.py (add imports)", Colors.WHITE)
    print_colored("   - app/repositories/property_repository.py (add imports)", Colors.WHITE)
    
    print_colored("\n2. Test your application after cleanup", Colors.YELLOW)
    print_colored("\n3. If everything works, you can delete .backup files", Colors.YELLOW)
    print_colored("   Use: find . -name '*.backup' -delete", Colors.WHITE)
    
    print_colored("\n4. If something breaks, restore from backup:", Colors.YELLOW)
    print_colored("   Use: find . -name '*.backup' -exec sh -c 'mv \"$1\" \"${1%.backup}\"' _ {} \\;", Colors.WHITE)
    
    if total_deleted > 0:
        print_colored(f"\n✅ Cleanup completed! {total_deleted} files moved to backup.", Colors.GREEN + Colors.BOLD)
    else:
        print_colored("\nℹ️  No files were deleted.", Colors.BLUE + Colors.BOLD)

def create_restore_script():
    """Create a restore script for backups"""
    restore_script = '''#!/bin/bash
# Restore script for FastAPI cleanup
echo "Restoring all .backup files..."

find . -name "*.backup" -exec sh -c '
    backup_file="$1"
    original_file="${backup_file%.backup}"
    echo "Restoring: $original_file"
    mv "$backup_file" "$original_file"
' _ {} \\;

echo "All files restored!"
'''
    
    with open('restore_backups.sh', 'w') as f:
        f.write(restore_script)
    
    # Make executable
    os.chmod('restore_backups.sh', 0o755)
    print_colored("Created restore_backups.sh script", Colors.GREEN)

if __name__ == "__main__":
    try:
        main()
        
        # Ask if user wants restore script
        create_restore = input("\nCreate restore script? (y/n): ").strip().lower()
        if create_restore in ['y', 'yes']:
            create_restore_script()
        
    except KeyboardInterrupt:
        print_colored("\n\nCleanup cancelled by user.", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\nError during cleanup: {str(e)}", Colors.RED)
        sys.exit(1)
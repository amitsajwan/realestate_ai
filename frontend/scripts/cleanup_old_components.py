#!/usr/bin/env python3
"""
Script to safely remove old fragmented components and update imports
"""

import os
import re
from pathlib import Path

# Components to remove (these are now replaced by UnifiedPublishingDashboard)
COMPONENTS_TO_REMOVE = [
    "frontend/components/PostManagement/",
    "frontend/components/social_publishing/",
    "frontend/components/PropertyManagement.tsx",
    "frontend/components/ModernPublishingWorkflow.tsx",
]

# Files that might import these components
FILES_TO_UPDATE = [
    "frontend/app/page.tsx",
    "frontend/app/social-publishing/page.tsx",
]

def backup_component(component_path):
    """Backup a component before removal"""
    if os.path.exists(component_path):
        backup_path = f"{component_path}.backup"
        if os.path.isdir(component_path):
            import shutil
            shutil.copytree(component_path, backup_path)
        else:
            import shutil
            shutil.copy2(component_path, backup_path)
        print(f"✅ Backed up {component_path} to {backup_path}")

def remove_component(component_path):
    """Remove a component after backup"""
    if os.path.exists(component_path):
        if os.path.isdir(component_path):
            import shutil
            shutil.rmtree(component_path)
        else:
            os.remove(component_path)
        print(f"🗑️  Removed {component_path}")

def update_imports_in_file(file_path):
    """Update imports in a file to remove references to deleted components"""
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remove imports for deleted components
    import_patterns = [
        r"import.*PostManagement.*from.*['\"].*['\"];?\n",
        r"import.*SocialPublishing.*from.*['\"].*['\"];?\n",
        r"import.*PropertyManagement.*from.*['\"].*['\"];?\n",
        r"import.*ModernPublishingWorkflow.*from.*['\"].*['\"];?\n",
    ]
    
    for pattern in import_patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # Remove case statements for deleted components
    case_patterns = [
        r"case 'posts':\s*\n\s*return <PostManagementDashboard.*?/>\s*\n",
        r"case 'property-management':\s*\n\s*return <PropertyManagement.*?/>\s*\n",
    ]
    
    for pattern in case_patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📝 Updated imports in {file_path}")
    else:
        print(f"ℹ️  No changes needed in {file_path}")

def main():
    print("🧹 Starting cleanup of old fragmented components...")
    print("=" * 60)
    
    # Step 1: Backup components
    print("\n📦 Step 1: Backing up components...")
    for component in COMPONENTS_TO_REMOVE:
        backup_component(component)
    
    # Step 2: Update imports in files
    print("\n📝 Step 2: Updating imports...")
    for file_path in FILES_TO_UPDATE:
        update_imports_in_file(file_path)
    
    # Step 3: Remove components
    print("\n🗑️  Step 3: Removing components...")
    for component in COMPONENTS_TO_REMOVE:
        remove_component(component)
    
    print("\n✅ Cleanup completed!")
    print("\n📋 Summary:")
    print("- Old fragmented components have been backed up and removed")
    print("- Import statements have been updated")
    print("- Navigation now uses the unified Property Marketing Hub")
    print("\n🚀 Next steps:")
    print("1. Test the application to ensure everything works")
    print("2. Remove backup files once you're confident everything is working")
    print("3. Update any remaining references in other files if needed")

if __name__ == "__main__":
    main()

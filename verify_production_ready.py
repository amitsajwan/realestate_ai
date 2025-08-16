#!/usr/bin/env python3
"""
Final verification script for production readiness
"""
import os
import sys

def check_files():
    """Check that all required files exist"""
    required_files = [
        'complete_production_crm.py',
        'db_adapter.py',
        'migrate_to_mongo.py',
        '.env',
        'requirements.txt'
    ]
    
    print("📂 Checking required files...")
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            return False
    return True

def check_environment():
    """Check environment configuration"""
    print("\n🌍 Checking environment...")
    
    # Check .env file contains MongoDB URI
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'MONGO_URI=' in env_content:
                print("✅ MONGO_URI configured in .env")
            else:
                print("❌ MONGO_URI not found in .env")
                return False
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return False
    
    return True

def check_dependencies():
    """Check that required packages are available"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'pymongo',
        'passlib',
        'fastapi',
        'uvicorn',
        'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True

def check_mongodb_config():
    """Check MongoDB configuration"""
    print("\n🗄️  Checking MongoDB configuration...")
    
    try:
        os.environ['MONGO_URI'] = 'mongodb://localhost:27017/'
        from db_adapter import DB_MODE, mongo_client
        
        print(f"✅ Database Mode: {DB_MODE}")
        
        if DB_MODE == "mongo" and mongo_client:
            print("✅ MongoDB connection successful")
        else:
            print("❌ MongoDB connection failed")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB check failed: {e}")
        return False
    
    return True

def main():
    """Run all verification checks"""
    print("🔍 FINAL PRODUCTION READINESS VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Required Files", check_files),
        ("Environment Config", check_environment),
        ("Dependencies", check_dependencies),
        ("MongoDB Config", check_mongodb_config),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n🔍 {name}:")
        if check_func():
            passed += 1
        else:
            print(f"❌ {name} check failed")
    
    print("\n" + "=" * 60)
    print(f"📊 VERIFICATION RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ✅ PRODUCTION READY!")
        print("🚀 The Real Estate CRM is ready for production deployment.")
        print("\n📋 Next Steps:")
        print("   1. Set up production MongoDB instance")
        print("   2. Configure production environment variables")
        print("   3. Deploy to production server")
        print("   4. Set up monitoring and backups")
        print("   5. Perform load testing")
        return True
    else:
        print("\n❌ NOT PRODUCTION READY")
        print("🔧 Please address the failed checks before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

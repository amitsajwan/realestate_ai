#!/usr/bin/env python3
"""
Real Estate AI CRM Application Launcher
========================================

This script ensures proper environment setup and launches the application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Ensure we're running Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    if sys.prefix == sys.base_prefix:
        print("⚠️  Not in a virtual environment. Proceeding anyway...")
    else:
        print("✅ Virtual environment detected")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def check_environment_file():
    """Check if .env file exists with required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("📝 Creating default .env file...")
        create_default_env()
    else:
        print("✅ .env file found")

def create_default_env():
    """Create a default .env file"""
    default_env = """# Security
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# URLs
BASE_URL=http://localhost:8003
FRONTEND_URL=http://localhost:3000

# Database Configuration
MONGO_URI=mongodb://localhost:27017/

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Feature Flags
AI_DISABLE_IMAGE_GENERATION=true

# API Keys (add your own)
GROQ_API_KEY=your_groq_api_key_here

# Facebook Configuration (optional)
FB_APP_ID=your_app_id_here
FB_APP_SECRET=your_app_secret_here
FB_PAGE_ID=your_page_id_here
FB_PAGE_TOKEN=your_page_token_here
FB_GRAPH_API_VERSION=v19.0

# External APIs (Optional)
STABILITY_API_KEY=your_stability_api_key_here
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
"""
    
    with open(".env", "w") as f:
        f.write(default_env)
    print("✅ Default .env file created")

def run_application():
    """Launch the FastAPI application"""
    print("🚀 Starting Real Estate AI CRM...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8003",
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

def main():
    """Main launcher function"""
    print("=" * 60)
    print("🏠 Real Estate AI CRM Application Launcher")
    print("=" * 60)
    
    check_python_version()
    check_virtual_environment()
    check_environment_file()
    install_dependencies()
    
    print("\n" + "=" * 60)
    print("🎯 Application will be available at: http://localhost:8003")
    print("📚 API Documentation: http://localhost:8003/docs")
    print("🔄 Interactive API: http://localhost:8003/redoc")
    print("=" * 60 + "\n")
    
    run_application()

if __name__ == "__main__":
    main()

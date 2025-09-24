#!/usr/bin/env python3
"""
Development Authentication Setup Script
======================================
Sets up development authentication system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import init_database, get_database
from app.services.development_auth_service import development_auth_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_development_auth():
    """Setup development authentication"""
    try:
        logger.info("🚀 Setting up development authentication...")
        
        # Initialize database
        logger.info("📊 Initializing database...")
        await init_database()
        
        # Setup development user
        logger.info("👤 Setting up development user...")
        user = await development_auth_service.ensure_development_user_exists()
        user_email = user.get('email', 'test@example.com') if isinstance(user, dict) else user.email
        logger.info(f"✅ Development user created: {user_email}")
        
        # Generate development tokens
        logger.info("🔑 Generating development tokens...")
        tokens = await development_auth_service.get_development_tokens()
        logger.info("✅ Development tokens generated")
        
        print("\n" + "="*60)
        print("🎉 DEVELOPMENT AUTHENTICATION SETUP COMPLETE!")
        print("="*60)
        print(f"📧 Email: {tokens['user']['email']}")
        print(f"🔑 Access Token: {tokens['access_token'][:50]}...")
        print(f"👤 User ID: {tokens['user']['id']}")
        print("\n📋 Development Endpoints:")
        print("  • GET  /api/v1/auth/dev/tokens")
        print("  • POST /api/v1/auth/dev/login")
        print("  • POST /api/v1/auth/dev/setup-user")
        print("\n🔧 Usage:")
        print("  • Use the access token in Authorization header: 'Bearer <token>'")
        print("  • Or use the development login endpoint with credentials")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(setup_development_auth())

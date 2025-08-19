# quick_fix.py - Run this to fix the immediate startup issues

import os
import sys
from pathlib import Path

def create_missing_files():
    """Create missing files to prevent import errors"""
    
    project_root = Path.cwd()
    
    # Create missing __init__.py files
    missing_inits = [
        "app/__init__.py",
        "app/core/__init__.py", 
        "app/repositories/__init__.py",
        "app/services/__init__.py",
        "app/schemas/__init__.py",
        "app/api/__init__.py",
        "app/api/v1/__init__.py",
        "app/api/v1/endpoints/__init__.py"
    ]
    
    for init_file in missing_inits:
        init_path = project_root / init_file
        init_path.parent.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.write_text("# Auto-generated __init__.py\n")
            print(f"✅ Created {init_file}")
    
    # Create a minimal database utility if it doesn't exist
    utils_db_path = project_root / "app" / "utils" / "db_client.py"
    if not utils_db_path.exists():
        utils_db_path.parent.mkdir(parents=True, exist_ok=True)
        utils_db_path.write_text("""# Legacy database client compatibility
import motor.motor_asyncio
from core.config import settings

_client = None
_database = None

def get_db_client():
    global _client, _database
    if _database is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
        db_name = settings.DATABASE_NAME
        _database = _client[db_name]
    return _database
""")
        print("✅ Created app/utils/db_client.py")
    
    # Create missing model files
    models_agent_path = project_root / "models" / "agent.py"
    if not models_agent_path.exists():
        models_agent_path.parent.mkdir(parents=True, exist_ok=True)
        models_agent_path.write_text("""# Agent model
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class Agent(BaseModel):
    email: EmailStr
    name: str
    whatsapp: str
    photo_url: Optional[str] = None
    tagline: Optional[str] = None
    about: Optional[str] = None
    status: str = "active"
    onboarding_completed: bool = False
    created_at: datetime = None
    
    def dict(self, *args, **kwargs):
        return super().model_dump(*args, **kwargs)
""")
        print("✅ Created models/agent.py")
    
    # Create missing utility files
    utils_ai_path = project_root / "app" / "utils" / "ai.py"
    if not utils_ai_path.exists():
        utils_ai_path.write_text("""# AI utilities
def generate_branding(name: str):
    return {
        "tagline": f"Your trusted real estate partner - {name}",
        "about": f"Professional real estate agent {name} helping you find your dream property."
    }
""")
        print("✅ Created app/utils/ai.py")
    
    utils_whatsapp_path = project_root / "app" / "utils" / "whatsapp.py" 
    if not utils_whatsapp_path.exists():
        utils_whatsapp_path.write_text("""# WhatsApp utilities
def connect_whatsapp(agent):
    # Placeholder for WhatsApp connection
    print(f"WhatsApp connection simulated for {agent.name}")
    return True
""")
        print("✅ Created app/utils/whatsapp.py")
    
    print("\n🎉 Missing files created successfully!")
    print("Now run: python -m uvicorn app.main:app --reload --port 8080")

if __name__ == "__main__":
    create_missing_files()
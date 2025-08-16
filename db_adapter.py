"""
Database Adapter (Mongo Only)
=============================
MongoDB-backed repository utilities for the production CRM.
SQLite support has been removed.
"""

import os
from datetime import datetime
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import hashlib
from passlib.context import CryptContext
from core.config import settings

# --- Configuration ---
MONGO_URI = settings.MONGO_URI  # Use from settings
DB_MODE = "mongo"

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- MongoDB Client Setup ---
mongo_client = None
db = None

try:
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not configured. Set it in environment variables.")
    mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = mongo_client.realestate_crm
    # Send a ping to confirm a successful connection
    mongo_client.admin.command('ping')
    print("✅ MongoDB connection successful.")
except Exception as e:
    raise RuntimeError(f"MongoDB initialization failed: {e}")

# --- Database Utilities ---
def get_db_connection():
    """Returns the active Mongo database client."""
    return db

def close_db_connection(conn):
    """No-op for Mongo."""
    return None

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    # Handle legacy SHA-256 passwords
    if not hashed_password.startswith("$2b$"):
        legacy_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        if legacy_hash == hashed_password:
            return True
    return pwd_context.verify(plain_password, hashed_password)

def needs_rehash(hashed_password: str) -> bool:
    """Checks if a password needs to be rehashed to the latest scheme."""
    return not hashed_password.startswith("$2b$")

# --- Data Transformation ---
def mongo_to_dict(item):
    """Converts a MongoDB document to a JSON-serializable dict."""
    if not item:
        return None
    item["id"] = str(item["_id"])
    del item["_id"]
    if "agent_id" in item and isinstance(item["agent_id"], ObjectId):
        item["agent_id"] = str(item["agent_id"])
    return item

# --- Repository Interface ---
# This is a simplified example. A more robust implementation might use classes.

class UserRepository:
    def __init__(self, db_conn):
        self.db = db_conn

    def find_by_email(self, email):
        user = self.db.users.find_one({"email": email})
        return mongo_to_dict(user)

    def get_user_by_email(self, email):
        """Get user by email address - alias for find_by_email"""
        return self.find_by_email(email)

    def get_user_by_id(self, user_id: str):
        try:
            obj_id = ObjectId(user_id)
        except Exception:
            # Support legacy/non-ObjectId ids if any
            doc = self.db.users.find_one({"id": user_id})
            return mongo_to_dict(doc)
        doc = self.db.users.find_one({"_id": obj_id})
        return mongo_to_dict(doc)

    def create_user(self, user_data):
        """Create a new user with hashed password."""
        # Hash the password
        user_data['password_hash'] = pwd_context.hash(user_data.pop('password'))
        user_data['created_at'] = datetime.now()
        result = self.db.users.insert_one(user_data)
        return str(result.inserted_id)

    def authenticate_user(self, email, password):
        """Authenticate user with email and password."""
        user = self.get_user_by_email(email)
        if user and verify_password(password, user['password_hash']):
            # If using legacy hash, upgrade to bcrypt for better security
            if needs_rehash(user['password_hash']):
                new_hash = pwd_context.hash(password)
                self.update_password(str(user.get('id')), new_hash)
                user['password_hash'] = new_hash
            return user
        return None

    def create(self, user_data):
        # Convert agent_id to ObjectId if it exists
        if 'agent_id' in user_data and isinstance(user_data['agent_id'], str):
            try:
                user_data['agent_id'] = ObjectId(user_data['agent_id'])
            except Exception:
                pass
        result = self.db.users.insert_one(user_data)
        return str(result.inserted_id)

    def update_password(self, user_id, new_hash):
        self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": new_hash}}
        )

    # --- Facebook Fields Helpers ---
    def update_user_fields(self, user_id: str, fields: dict):
        """Generic setter for user document fields (e.g., fb tokens/page info)."""
        try:
            oid = ObjectId(user_id)
        except Exception:
            raise ValueError("Invalid user_id for Mongo")
        update = {"$set": {**fields, "updated_at": datetime.now()}}
        self.db.users.update_one({"_id": oid}, update)

    def get_user_fields(self, user_id: str, fields: list[str]):
        try:
            oid = ObjectId(user_id)
        except Exception:
            raise ValueError("Invalid user_id for Mongo")
        proj = {k: 1 for k in fields}
        doc = self.db.users.find_one({"_id": oid}, proj)
        return mongo_to_dict(doc)

# You would create similar repository classes for Leads, Properties, etc.
# For this migration, we will keep the logic more direct in the main script
# to avoid a full-scale refactoring right now.

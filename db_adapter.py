"""
Database Adapter
================
Handles connections to either MongoDB or SQLite based on environment settings.
Provides a consistent repository interface for the application.
"""

import os
import sqlite3
from datetime import datetime
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import hashlib
from passlib.context import CryptContext
from core.config import settings

# --- Configuration ---
MONGO_URI = settings.MONGO_URI  # Use from settings
DB_PATH = "production_crm.db"
DB_MODE = "mongo" if MONGO_URI else "sqlite"

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- MongoDB Client Setup ---
mongo_client = None
db = None

if DB_MODE == "mongo":
    try:
        mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
        db = mongo_client.realestate_crm
        # Send a ping to confirm a successful connection
        mongo_client.admin.command('ping')
        print("✅ MongoDB connection successful.")
    except errors.ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        mongo_client = None
        db = None
        DB_MODE = "sqlite" # Fallback to SQLite if Mongo connection fails

# --- Database Utilities ---
def get_db_connection():
    """Returns the active database connection/client."""
    if DB_MODE == "mongo":
        return db
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def close_db_connection(conn):
    """Closes a database connection if it's SQLite."""
    if DB_MODE == "sqlite":
        conn.close()

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

def sqlite_to_dict(row):
    """Converts a SQLite row to a dict."""
    if not row:
        return None
    return dict(row)

# --- Repository Interface ---
# This is a simplified example. A more robust implementation might use classes.

class UserRepository:
    def __init__(self, db_conn):
        self.db = db_conn

    def find_by_email(self, email):
        if DB_MODE == "mongo":
            user = self.db.users.find_one({"email": email})
            return mongo_to_dict(user)
        else:
            cur = self.db.cursor()
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cur.fetchone()
            return sqlite_to_dict(row)

    def get_user_by_email(self, email):
        """Get user by email address - alias for find_by_email"""
        return self.find_by_email(email)

    def create_user(self, user_data):
        """Create a new user with hashed password."""
        # Hash the password
        user_data['password_hash'] = pwd_context.hash(user_data.pop('password'))
        
        if DB_MODE == "mongo":
            user_data['created_at'] = datetime.now()
            result = self.db.users.insert_one(user_data)
            return str(result.inserted_id)
        else:
            # SQLite implementation
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO users (email, password_hash, first_name, last_name, phone, experience, areas, property_types, languages, facebook_connected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_data['email'], user_data['password_hash'], user_data['first_name'], 
                  user_data['last_name'], user_data.get('phone'), user_data.get('experience'),
                  user_data.get('areas'), user_data.get('property_types'), user_data.get('languages'),
                  user_data.get('facebook_connected', 0)))
            self.db.commit()
            return cur.lastrowid

    def authenticate_user(self, email, password):
        """Authenticate user with email and password."""
        user = self.get_user_by_email(email)
        if user and verify_password(password, user['password_hash']):
            # If using legacy hash, upgrade to bcrypt for better security
            if needs_rehash(user['password_hash']):
                new_hash = pwd_context.hash(password)
                self.update_password(str(user.get('_id', user.get('id'))), new_hash)
                user['password_hash'] = new_hash
            return user
        return None

    def create(self, user_data):
        if DB_MODE == "mongo":
            # Convert agent_id to ObjectId if it exists
            if 'agent_id' in user_data and isinstance(user_data['agent_id'], str):
                user_data['agent_id'] = ObjectId(user_data['agent_id'])
            result = self.db.users.insert_one(user_data)
            return str(result.inserted_id)
        else:
            # SQLite implementation for user creation
            # This part needs to be adapted from the original script
            pass

    def update_password(self, user_id, new_hash):
        if DB_MODE == "mongo":
            self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password_hash": new_hash}}
            )
        else:
            cur = self.db.cursor()
            cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
            self.db.commit()

# You would create similar repository classes for Leads, Properties, etc.
# For this migration, we will keep the logic more direct in the main script
# to avoid a full-scale refactoring right now.

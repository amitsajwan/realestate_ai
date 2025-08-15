"""
One-time Data Migration Script
==============================
Migrates data from the SQLite database (`production_crm.db`) to MongoDB.

Instructions:
1. Ensure your MongoDB server is running.
2. Set the MONGO_URI environment variable.
   Example (PowerShell): $env:MONGO_URI="mongodb://localhost:27017/"
3. Run this script from your terminal:
   .\\env\\Scripts\\python.exe .\\migrate_to_mongo.py
"""

import os
import sqlite3
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import sys

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("❌ MONGO_URI environment variable not set. Exiting.")
    sys.exit(1)

SQLITE_DB_PATH = "production_crm.db"

# --- Main Migration Logic ---
def migrate_data():
    """Connects to both databases and migrates data."""
    
    # --- Connect to MongoDB ---
    try:
        mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
        mongo_db = mongo_client.realestate_crm
        mongo_client.admin.command('ping')
        print("✅ MongoDB connection successful.")
    except errors.ConnectionFailure as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        return

    # --- Connect to SQLite ---
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()
        print("✅ SQLite connection successful.")
    except sqlite3.Error as e:
        print(f"❌ Could not connect to SQLite: {e}")
        return

    print("\n🚀 Starting data migration...")

    # --- Migrate Users ---
    print("  - Migrating users...")
    sqlite_cur.execute("SELECT * FROM users")
    users = sqlite_cur.fetchall()
    
    # Clear existing users to avoid duplicates on re-run
    if "users" in mongo_db.list_collection_names():
        mongo_db.users.delete_many({})
        print("    - Cleared existing users collection.")

    user_id_map = {}
    for user in users:
        user_dict = dict(user)
        sqlite_id = user_dict.pop("id")
        
        # Rename columns to match MongoDB conventions if desired
        user_dict["firstName"] = user_dict.pop("first_name")
        user_dict["lastName"] = user_dict.pop("last_name")
        user_dict["propertyTypes"] = user_dict.pop("property_types")
        user_dict["createdAt"] = user_dict.pop("created_at")
        
        # Insert into MongoDB
        result = mongo_db.users.insert_one(user_dict)
        user_id_map[sqlite_id] = result.inserted_id
    
    print(f"    - Migrated {len(users)} users.")

    # --- Migrate Leads ---
    print("  - Migrating leads...")
    sqlite_cur.execute("SELECT * FROM leads")
    leads = sqlite_cur.fetchall()

    if "leads" in mongo_db.list_collection_names():
        mongo_db.leads.delete_many({})
        print("    - Cleared existing leads collection.")

    for lead in leads:
        lead_dict = dict(lead)
        lead_dict.pop("id")
        
        # Map the agent's SQLite ID to their new MongoDB ObjectId
        sqlite_agent_id = lead_dict.pop("agent_id")
        if sqlite_agent_id in user_id_map:
            lead_dict["agent_id"] = user_id_map[sqlite_agent_id]
        
        lead_dict["propertyType"] = lead_dict.pop("property_type")
        lead_dict["createdAt"] = lead_dict.pop("created_at")
        
        mongo_db.leads.insert_one(lead_dict)
        
    print(f"    - Migrated {len(leads)} leads.")

    # --- Migrate Properties ---
    print("  - Migrating properties...")
    sqlite_cur.execute("SELECT * FROM properties")
    properties = sqlite_cur.fetchall()

    if "properties" in mongo_db.list_collection_names():
        mongo_db.properties.delete_many({})
        print("    - Cleared existing properties collection.")

    for prop in properties:
        prop_dict = dict(prop)
        prop_dict.pop("id")
        
        sqlite_agent_id = prop_dict.pop("agent_id")
        if sqlite_agent_id in user_id_map:
            prop_dict["agent_id"] = user_id_map[sqlite_agent_id]
            
        prop_dict["propertyType"] = prop_dict.pop("property_type")
        prop_dict["areaSqft"] = prop_dict.pop("area_sqft")
        prop_dict["createdAt"] = prop_dict.pop("created_at")
        
        mongo_db.properties.insert_one(prop_dict)
        
    print(f"    - Migrated {len(properties)} properties.")

    # --- Close connections ---
    sqlite_conn.close()
    mongo_client.close()
    
    print("\n🎉 Migration complete!")

if __name__ == "__main__":
    migrate_data()

"""Facebook connection repository with MongoDB persistence and token encryption."""
import os
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict
from cryptography.fernet import Fernet
from pymongo import MongoClient

class FacebookRepository:
    """Repository for Facebook connections with encrypted token storage."""
    
    def __init__(self, db=None):
        if db is None:
            from db_adapter import get_db_connection
            self.db = get_db_connection()
        else:
            self.db = db
            
        # Initialize encryption for tokens
        secret_key = os.getenv("SECRET_KEY", "demo_secret_key_change_in_production")
        key_material = secret_key.encode()[:32].ljust(32, b"0")
        self.cipher = Fernet(base64.urlsafe_b64encode(key_material))
    
    async def save_connection(self, user_email: str, connection_data: dict) -> bool:
        """Save Facebook connection with encrypted tokens."""
        try:
            # Encrypt sensitive tokens
            encrypted_data = connection_data.copy()
            if 'page_token' in encrypted_data:
                encrypted_data['page_token'] = self.cipher.encrypt(
                    encrypted_data['page_token'].encode()
                ).decode()
            if 'user_token' in encrypted_data:
                encrypted_data['user_token'] = self.cipher.encrypt(
                    encrypted_data['user_token'].encode()
                ).decode()
            
            # Add metadata
            encrypted_data.update({
                'user_email': user_email,
                'updated_at': datetime.utcnow(),
                'created_at': encrypted_data.get('connected_at', datetime.utcnow())
            })
            
            # Upsert to MongoDB
            result = self.db.facebook_connections.update_one(
                {"user_email": user_email},
                {"$set": encrypted_data},
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            print(f"Error saving Facebook connection: {e}")
            return False
    
    async def get_connection(self, user_email: str) -> Optional[dict]:
        """Get Facebook connection with decrypted tokens."""
        try:
            doc = self.db.facebook_connections.find_one({"user_email": user_email})
            if not doc:
                return None
            
            # Decrypt sensitive tokens
            if 'page_token' in doc:
                try:
                    doc['page_token'] = self.cipher.decrypt(
                        doc['page_token'].encode()
                    ).decode()
                except:
                    doc['page_token'] = None
                    
            if 'user_token' in doc:
                try:
                    doc['user_token'] = self.cipher.decrypt(
                        doc['user_token'].encode()
                    ).decode()
                except:
                    doc['user_token'] = None
            
            # Remove MongoDB _id
            if '_id' in doc:
                del doc['_id']
                
            return doc
            
        except Exception as e:
            print(f"Error getting Facebook connection: {e}")
            return None
    
    async def delete_connection(self, user_email: str) -> bool:
        """Delete Facebook connection."""
        try:
            result = self.db.facebook_connections.delete_one({"user_email": user_email})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting Facebook connection: {e}")
            return False
    
    async def is_token_expired(self, user_email: str) -> bool:
        """Check if Facebook tokens are expired."""
        connection = await self.get_connection(user_email)
        if not connection:
            return True
            
        # Check if connected_at is older than 50 days (Facebook page tokens last ~60 days)
        connected_at = connection.get('connected_at')
        if isinstance(connected_at, str):
            connected_at = datetime.fromisoformat(connected_at.replace('Z', ''))
        
        if connected_at and datetime.utcnow() - connected_at > timedelta(days=50):
            return True
            
        return False

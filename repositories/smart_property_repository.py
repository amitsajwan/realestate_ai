"""Smart properties repository with MongoDB persistence."""
from datetime import datetime
from typing import List, Optional, Dict
from bson.objectid import ObjectId

class SmartPropertyRepository:
    """Repository for smart properties with MongoDB storage."""
    
    def __init__(self, db=None):
        if db is None:
            from db_adapter import get_db_connection
            self.db = get_db_connection()
        else:
            self.db = db
    
    async def create_property(self, property_data: dict, user_email: str) -> str:
        """Create a smart property in MongoDB."""
        try:
            # Prepare document
            doc = {
                **property_data,
                'user_email': user_email,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'status': 'active'
            }
            
            # Insert into MongoDB
            result = self.db.smart_properties.insert_one(doc)
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error creating smart property: {e}")
            raise
    
    async def get_properties(self, user_email: str) -> List[dict]:
        """Get all smart properties for a user."""
        try:
            cursor = self.db.smart_properties.find(
                {"user_email": user_email}
            ).sort("created_at", -1)
            
            properties = []
            for doc in cursor:
                # Convert ObjectId to string
                doc['id'] = str(doc['_id'])
                del doc['_id']
                
                # Convert datetime to ISO string
                if 'created_at' in doc:
                    doc['created_at'] = doc['created_at'].isoformat()
                if 'updated_at' in doc:
                    doc['updated_at'] = doc['updated_at'].isoformat()
                
                properties.append(doc)
            
            return properties
            
        except Exception as e:
            print(f"Error getting smart properties: {e}")
            return []
    
    async def get_property(self, property_id: str, user_email: str) -> Optional[dict]:
        """Get a specific smart property."""
        try:
            doc = self.db.smart_properties.find_one({
                "_id": ObjectId(property_id),
                "user_email": user_email
            })
            
            if doc:
                doc['id'] = str(doc['_id'])
                del doc['_id']
                
                # Convert datetime to ISO string
                if 'created_at' in doc:
                    doc['created_at'] = doc['created_at'].isoformat()
                if 'updated_at' in doc:
                    doc['updated_at'] = doc['updated_at'].isoformat()
            
            return doc
            
        except Exception as e:
            print(f"Error getting smart property: {e}")
            return None
    
    async def update_property(self, property_id: str, updates: dict, user_email: str) -> bool:
        """Update a smart property."""
        try:
            updates['updated_at'] = datetime.utcnow()
            
            result = self.db.smart_properties.update_one(
                {"_id": ObjectId(property_id), "user_email": user_email},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating smart property: {e}")
            return False
    
    async def mark_posted_to_facebook(self, property_id: str, post_id: str, user_email: str) -> bool:
        """Mark property as posted to Facebook."""
        return await self.update_property(
            property_id, 
            {
                'facebook_post_id': post_id,
                'posted_to_facebook': True,
                'facebook_posted_at': datetime.utcnow()
            }, 
            user_email
        )

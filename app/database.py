#!/usr/bin/env python3
"""
Database Module
===============
Handles database connections and operations for PropertyAI
"""

import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # ✅ Use absolute path to ensure database is found from any context
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.db_path = os.path.join(project_root, "propertyai.db")
        else:
            self.db_path = db_path
        
        logger.info(f"🔍 Database path: {self.db_path}")
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        # ✅ Remove Row factory to ensure compatibility with regular cursor
        # conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    whatsapp TEXT,
                    company TEXT,
                    experience_years TEXT,
                    specialization_areas TEXT,
                    tagline TEXT,
                    social_bio TEXT,
                    about TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    pincode TEXT,
                    languages TEXT,
                    logo_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Properties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT,
                    bedrooms TEXT,
                    price REAL,
                    price_unit TEXT,
                    city TEXT,
                    area TEXT,
                    address TEXT,
                    carpet_area REAL,
                    built_up_area REAL,
                    floor TEXT,
                    furnishing TEXT,
                    possession TEXT,
                    amenities TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Facebook pages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facebook_pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    page_id TEXT NOT NULL,
                    page_name TEXT,
                    page_token TEXT,
                    access_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    property_id INTEGER,
                    page_id TEXT,
                    content TEXT,
                    language TEXT,
                    status TEXT DEFAULT 'pending',
                    facebook_post_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (property_id) REFERENCES properties (id)
                )
            ''')
            
            conn.commit()
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
        finally:
            conn.close()
    
    def save_user_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Save user profile to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE user_id = ?', (profile_data['user_id'],))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                cursor.execute('''
                    UPDATE users SET
                        name = ?, email = ?, phone = ?, whatsapp = ?, company = ?,
                        experience_years = ?, specialization_areas = ?, tagline = ?,
                        social_bio = ?, about = ?, address = ?, city = ?, state = ?,
                        pincode = ?, languages = ?, logo_url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (
                    profile_data.get('name'), profile_data.get('email'), profile_data.get('phone'),
                    profile_data.get('whatsapp'), profile_data.get('company'), profile_data.get('experience_years'),
                    profile_data.get('specialization_areas'), profile_data.get('tagline'), profile_data.get('social_bio'),
                    profile_data.get('about'), profile_data.get('address'), profile_data.get('city'),
                    profile_data.get('state'), profile_data.get('pincode'), json.dumps(profile_data.get('languages', [])),
                    profile_data.get('logo_url'), profile_data['user_id']
                ))
            else:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users (
                        user_id, name, email, phone, whatsapp, company, experience_years,
                        specialization_areas, tagline, social_bio, about, address, city,
                        state, pincode, languages, logo_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile_data['user_id'], profile_data.get('name'), profile_data.get('email'),
                    profile_data.get('phone'), profile_data.get('whatsapp'), profile_data.get('company'),
                    profile_data.get('experience_years'), profile_data.get('specialization_areas'),
                    profile_data.get('tagline'), profile_data.get('social_bio'), profile_data.get('about'),
                    profile_data.get('address'), profile_data.get('city'), profile_data.get('state'),
                    profile_data.get('pincode'), json.dumps(profile_data.get('languages', [])),
                    profile_data.get('logo_url')
                ))
            
            conn.commit()
            logger.info(f"✅ User profile saved to database: {profile_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                profile = dict(user)
                # Parse languages JSON
                if profile.get('languages'):
                    try:
                        profile['languages'] = json.loads(profile['languages'])
                    except:
                        profile['languages'] = []
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Database get error: {e}")
            return None
        finally:
            conn.close()
    
    def save_property(self, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save property to database and return the saved property with ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO properties (
                    user_id, title, type, bedrooms, price, price_unit, city, area,
                    address, carpet_area, built_up_area, floor, furnishing, possession,
                    amenities, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                property_data['user_id'], property_data['title'], property_data.get('type'),
                property_data.get('bedrooms'), property_data.get('price'), property_data.get('price_unit'),
                property_data.get('city'), property_data.get('area'), property_data.get('address'),
                property_data.get('carpet_area'), property_data.get('built_up_area'), property_data.get('floor'),
                property_data.get('furnishing'), property_data.get('possession'),
                json.dumps(property_data.get('amenities', [])), property_data.get('description')
            ))
            
            property_id = cursor.lastrowid
            conn.commit()
            
            # ✅ Return the complete property data with ID
            saved_property = {
                **property_data,
                'id': property_id,
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Property saved to database: {property_id}")
            return saved_property
            
        except Exception as e:
            logger.error(f"❌ Database property save error: {e}")
            return None
        finally:
            conn.close()
    
    def get_user_properties(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all properties for a user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # ✅ Use regular cursor instead of Row factory for better compatibility
            query = 'SELECT id, user_id, title, type, bedrooms, price, price_unit, city, area, address, carpet_area, built_up_area, floor, furnishing, possession, amenities, description, status, created_at, updated_at FROM properties WHERE user_id = ? ORDER BY created_at DESC'
            logger.info(f"🔍 Executing query: {query} with user_id: {user_id}")
            
            cursor.execute(query, (user_id,))
            properties = cursor.fetchall()
            
            logger.info(f"🔍 Raw query results: {properties}")
            
            result = []
            for prop in properties:
                # ✅ Convert tuple to dict with explicit field names
                property_dict = {
                    'id': prop[0],
                    'user_id': prop[1],
                    'title': prop[2],
                    'type': prop[3],
                    'bedrooms': prop[4],
                    'price': prop[5],
                    'price_unit': prop[6],
                    'city': prop[7],
                    'area': prop[8],
                    'address': prop[9],
                    'carpet_area': prop[10],
                    'built_up_area': prop[11],
                    'floor': prop[12],
                    'furnishing': prop[13],
                    'possession': prop[14],
                    'amenities': prop[15],
                    'description': prop[16],
                    'status': prop[17],
                    'created_at': prop[18],
                    'updated_at': prop[19]
                }
                
                logger.info(f"🔍 Property dict: {property_dict}")
                
                # Parse amenities JSON
                if property_dict.get('amenities'):
                    try:
                        property_dict['amenities'] = json.loads(property_dict['amenities'])
                    except:
                        property_dict['amenities'] = []
                
                # ✅ FIXED: Ensure numeric fields maintain consistent types
                if property_dict['id'] is not None:
                    property_dict['id'] = int(property_dict['id'])
                
                # ✅ FIXED: Convert price back to int if it was originally int
                if property_dict['price'] is not None:
                    # Check if price is a whole number (float with .0)
                    if isinstance(property_dict['price'], float) and property_dict['price'].is_integer():
                        property_dict['price'] = int(property_dict['price'])
                    elif isinstance(property_dict['price'], float):
                        # Keep as float if it has decimal places
                        pass
                
                # ✅ FIXED: Convert carpet_area and built_up_area back to int if they were originally int
                if property_dict['carpet_area'] is not None:
                    if isinstance(property_dict['carpet_area'], float) and property_dict['carpet_area'].is_integer():
                        property_dict['carpet_area'] = int(property_dict['carpet_area'])
                
                if property_dict['built_up_area'] is not None:
                    if isinstance(property_dict['built_up_area'], float) and property_dict['built_up_area'].is_integer():
                        property_dict['built_up_area'] = int(property_dict['built_up_area'])
                
                result.append(property_dict)
            
            logger.info(f"✅ Retrieved {len(result)} properties for user {user_id}")
            logger.info(f"✅ Final result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Database get properties error: {e}")
            return []
        finally:
            conn.close()
    
    def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get property by ID from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # ✅ Use explicit field selection to avoid tuple conversion issues
            cursor.execute('SELECT id, user_id, title, type, bedrooms, price, price_unit, city, area, address, carpet_area, built_up_area, floor, furnishing, possession, amenities, description, status, created_at, updated_at FROM properties WHERE id = ?', (property_id,))
            property_data = cursor.fetchone()
            
            if property_data:
                # ✅ Convert tuple to dict with explicit field names
                property_dict = {
                    'id': property_data[0],
                    'user_id': property_data[1],
                    'title': property_data[2],
                    'type': property_data[3],
                    'bedrooms': property_data[4],
                    'price': property_data[5],
                    'price_unit': property_data[6],
                    'city': property_data[7],
                    'area': property_data[8],
                    'address': property_data[9],
                    'carpet_area': property_data[10],
                    'built_up_area': property_data[11],
                    'floor': property_data[12],
                    'furnishing': property_data[13],
                    'possession': property_data[14],
                    'amenities': property_data[15],
                    'description': property_data[16],
                    'status': property_data[17],
                    'created_at': property_data[18],
                    'updated_at': property_data[19]
                }
                
                # Parse amenities JSON
                if property_dict.get('amenities'):
                    try:
                        property_dict['amenities'] = json.loads(property_dict['amenities'])
                    except:
                        property_dict['amenities'] = []
                
                # ✅ FIXED: Ensure numeric fields maintain consistent types
                if property_dict['id'] is not None:
                    property_dict['id'] = int(property_dict['id'])
                
                # ✅ FIXED: Convert price back to int if it was originally int
                if property_dict['price'] is not None:
                    if isinstance(property_dict['price'], float) and property_dict['price'].is_integer():
                        property_dict['price'] = int(property_dict['price'])
                
                # ✅ FIXED: Convert carpet_area and built_up_area back to int if they were originally int
                if property_dict['carpet_area'] is not None:
                    if isinstance(property_dict['carpet_area'], float) and property_dict['carpet_area'].is_integer():
                        property_dict['carpet_area'] = int(property_dict['carpet_area'])
                
                if property_dict['built_up_area'] is not None:
                    if isinstance(property_dict['built_up_area'], float) and property_dict['built_up_area'].is_integer():
                        property_dict['built_up_area'] = int(property_dict['built_up_area'])
                
                # Map database fields to expected format for listings
                mapped_property = {
                    "id": property_dict.get("id"),
                    "address": property_dict.get("address", ""),
                    "city": property_dict.get("city", "Mumbai"),
                    "state": property_dict.get("state", "Maharashtra"),
                    "price": f"₹{property_dict.get('price', 'Price on Request')}" if property_dict.get('price') else "Price on Request",
                    "property_type": property_dict.get("type", "Apartment"),
                    "bedrooms": int(property_dict.get("bedrooms", 2)) if property_dict.get("bedrooms") else 2,
                    "bathrooms": 1,  # Default value since bathrooms not in DB schema
                    "features": property_dict.get("amenities", [])
                }
                
                logger.info(f"✅ Retrieved property by ID {property_id}: {mapped_property}")
                return mapped_property
            
            logger.warn(f"⚠️ No property found with ID: {property_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Database get property by ID error: {e}")
            return None
        finally:
            conn.close()

# Global database instance
db = Database()

#!/usr/bin/env python3
"""
Database Module - FIXED VERSION
===============================
Enhanced database connections and operations with proper user credentials handling
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
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database tables with user credentials table"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table (for profiles)
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
            
            # NEW: User credentials table for secure authentication
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
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
            logger.info("✅ Database initialized successfully with user credentials table")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
        finally:
            conn.close()
    
    def save_user_credentials(self, credentials_data: Dict[str, Any]) -> bool:
        """Save user credentials securely to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM user_credentials WHERE email = ?', (credentials_data['email'],))
            existing_user = cursor.fetchone()
            
            if existing_user:
                logger.warning(f"User with email {credentials_data['email']} already exists")
                return False
            
            # Insert new user credentials
            cursor.execute('''
                INSERT INTO user_credentials (
                    user_id, full_name, email, password_hash
                ) VALUES (?, ?, ?, ?)
            ''', (
                credentials_data['user_id'],
                credentials_data['full_name'],
                credentials_data['email'],
                credentials_data['password_hash']
            ))
            
            conn.commit()
            logger.info(f"✅ User credentials saved securely: {credentials_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving user credentials: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user credentials by email"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM user_credentials WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting user by email: {e}")
            return None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user credentials by user_id"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM user_credentials WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting user by ID: {e}")
            return None
        finally:
            conn.close()
    
    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_credentials 
                SET last_login = CURRENT_TIMESTAMP, failed_login_attempts = 0
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating last login: {e}")
            return False
        finally:
            conn.close()
    
    def increment_failed_login(self, email: str) -> bool:
        """Increment failed login attempts for rate limiting"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_credentials 
                SET failed_login_attempts = failed_login_attempts + 1
                WHERE email = ?
            ''', (email,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error incrementing failed login: {e}")
            return False
        finally:
            conn.close()
    
    # Keep existing methods for profiles and properties...
    
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
    
    # Keep all existing property methods unchanged...
    
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

# Global database instance
db = Database()


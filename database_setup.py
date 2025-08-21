#!/usr/bin/env python3
"""
Database Setup for PropertyAI Real Estate CRM
=============================================

This script sets up the SQLite database with all required tables
for the login and onboarding functionality.
"""

import sqlite3
import bcrypt
import json
from datetime import datetime
from pathlib import Path

# Database file path
DB_PATH = "propertyai.db"

def create_database():
    """Create the database and all required tables"""
    
    # Create database directory if it doesn't exist
    Path("data").mkdir(exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🗄️  Creating PropertyAI database...")
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            company VARCHAR(255),
            role VARCHAR(50) DEFAULT 'agent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create agent_profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            company_name VARCHAR(255),
            experience_years INTEGER,
            specialization_areas TEXT,
            languages TEXT,
            phone VARCHAR(20),
            whatsapp VARCHAR(20),
            profile_photo_url VARCHAR(500),
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create agent_branding table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_branding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            tagline VARCHAR(255),
            primary_color VARCHAR(7),
            secondary_color VARCHAR(7),
            accent_color VARCHAR(7),
            brand_voice TEXT,
            about_section TEXT,
            ai_preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create onboarding_progress table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS onboarding_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            step_1_completed BOOLEAN DEFAULT 0,
            step_2_completed BOOLEAN DEFAULT 0,
            step_3_completed BOOLEAN DEFAULT 0,
            step_4_completed BOOLEAN DEFAULT 0,
            step_5_completed BOOLEAN DEFAULT 0,
            step_6_completed BOOLEAN DEFAULT 0,
            onboarding_completed BOOLEAN DEFAULT 0,
            current_step INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    # Create properties table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(255) NOT NULL,
            price VARCHAR(50),
            location VARCHAR(255),
            type VARCHAR(100),
            bedrooms INTEGER,
            bathrooms INTEGER,
            area VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Available',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create facebook_posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facebook_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            page_id VARCHAR(255),
            message TEXT,
            post_id VARCHAR(255),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("✅ Database tables created successfully!")
    
    # Insert demo user data
    insert_demo_data(cursor)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("✅ Database setup completed!")
    print(f"📁 Database file: {DB_PATH}")

def insert_demo_data(cursor):
    """Insert demo user data"""
    
    print("👤 Inserting demo user data...")
    
    # Demo user password hash
    demo_password = "demo123"
    password_hash = bcrypt.hashpw(demo_password.encode(), bcrypt.gensalt()).decode()
    
    # Insert demo user
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO users (email, password_hash, name, company, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('demo@mumbai.com', password_hash, 'Demo User', 'Mumbai Real Estate', 'agent'))
        
        # Get the user ID
        user_id = cursor.lastrowid
        
        # Insert demo profile
        cursor.execute('''
            INSERT OR REPLACE INTO agent_profiles 
            (user_id, company_name, experience_years, specialization_areas, languages, phone, whatsapp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Mumbai Real Estate', 5, 'Mumbai, Bandra, Powai', 'English, Hindi, Marathi', '+91-9876543210', '+91-9876543210'))
        
        # Insert demo branding
        cursor.execute('''
            INSERT OR REPLACE INTO agent_branding 
            (user_id, tagline, primary_color, secondary_color, accent_color, brand_voice, about_section)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Your Trusted Partner in Mumbai Real Estate', '#2E86AB', '#A23B72', '#F18F01', 'Professional, Trustworthy, Innovative', 'Demo User is a dedicated real estate professional committed to helping you find your perfect home.'))
        
        # Insert demo properties
        cursor.execute('''
            INSERT OR REPLACE INTO properties 
            (user_id, title, price, location, type, bedrooms, bathrooms, area, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Luxury Apartment in Bandra', '₹2.5 Cr', 'Bandra West, Mumbai', 'Apartment', 3, 2, '1500 sq ft', 'Beautiful luxury apartment with sea view'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO properties 
            (user_id, title, price, location, type, bedrooms, bathrooms, area, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Modern Villa in Powai', '₹5.2 Cr', 'Powai, Mumbai', 'Villa', 4, 3, '2800 sq ft', 'Spacious modern villa with garden'))
        
        print("✅ Demo data inserted successfully!")
        
    except sqlite3.IntegrityError as e:
        print(f"⚠️  Demo data already exists: {e}")

def get_database_connection():
    """Get a database connection"""
    return sqlite3.connect(DB_PATH)

def test_database():
    """Test the database connection and data"""
    
    print("🧪 Testing database...")
    
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Test users table
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"👥 Users in database: {user_count}")
    
    # Test demo user
    cursor.execute("SELECT email, name, company FROM users WHERE email = ?", ('demo@mumbai.com',))
    user = cursor.fetchone()
    if user:
        print(f"✅ Demo user found: {user[1]} ({user[0]}) at {user[2]}")
    else:
        print("❌ Demo user not found")
    
    # Test properties
    cursor.execute("SELECT COUNT(*) FROM properties")
    property_count = cursor.fetchone()[0]
    print(f"🏠 Properties in database: {property_count}")
    
    # Test branding
    cursor.execute("SELECT COUNT(*) FROM agent_branding")
    branding_count = cursor.fetchone()[0]
    print(f"🎨 Branding records: {branding_count}")
    
    conn.close()
    print("✅ Database test completed!")

if __name__ == "__main__":
    print("🚀 PropertyAI Database Setup")
    print("=" * 40)
    
    # Create database
    create_database()
    
    # Test database
    test_database()
    
    print("\n🎉 Database setup completed successfully!")
    print("📋 Next steps:")
    print("   1. Update simple_backend.py to use database")
    print("   2. Test login with demo@mumbai.com / demo123")
    print("   3. Test onboarding flow")
    print("   4. Verify data persistence")

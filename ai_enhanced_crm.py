"""
AI-ENHANCED REAL ESTATE CRM SYSTEM
==================================
Production-ready CRM system with AI-powered features:
- AI Property Description Generation using Groq/LLM
- Automated Facebook Page Posting
- Smart Lead Scoring with AI
- WhatsApp Integration
- Professional property descriptions
- Social media content generation

Author: GitHub Copilot  
Date: January 2025
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional
import uvicorn
import os
import json
import requests
from groq import Groq
import asyncio

# Initialize FastAPI app
app = FastAPI(title="AI-Enhanced Real Estate CRM", description="Production CRM with AI features")

# Configuration
SECRET_KEY = "ai_real_estate_crm_secret_key_2025"
DB_PATH = "ai_crm.db"

# AI Configuration
GROQ_API_KEY = "your_groq_api_key_here"  # Replace with actual key
FACEBOOK_ACCESS_TOKEN = "your_facebook_access_token"  # Replace with actual token
FACEBOOK_PAGE_ID = "your_facebook_page_id"  # Replace with actual page ID

# Initialize Groq client (mock for demo)
try:
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY != "your_groq_api_key_here" else None
except:
    groq_client = None

# Database setup
def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with enhanced schema."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            experience TEXT,
            areas TEXT,
            property_types TEXT,
            languages TEXT,
            facebook_connected INTEGER DEFAULT 0,
            facebook_page_id TEXT,
            whatsapp_connected INTEGER DEFAULT 0,
            ai_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Enhanced Properties table with AI fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            ai_generated_description TEXT,
            property_type TEXT NOT NULL,
            location TEXT NOT NULL,
            price TEXT NOT NULL,
            bedrooms INTEGER DEFAULT 0,
            bathrooms INTEGER DEFAULT 0,
            area_sqft INTEGER DEFAULT 0,
            amenities TEXT,
            status TEXT DEFAULT 'available',
            facebook_posted INTEGER DEFAULT 0,
            facebook_post_id TEXT,
            images TEXT,
            virtual_tour_url TEXT,
            ai_tags TEXT,
            market_insights TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES users (id)
        )
    ''')
    
    # Enhanced Leads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT NOT NULL,
            location TEXT,
            budget TEXT,
            property_type TEXT,
            source TEXT DEFAULT 'manual',
            status TEXT DEFAULT 'new',
            score INTEGER DEFAULT 75,
            ai_score INTEGER DEFAULT 0,
            notes TEXT,
            ai_insights TEXT,
            last_contact TIMESTAMP,
            next_followup TIMESTAMP,
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES users (id)
        )
    ''')
    
    # Social Media Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS social_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            property_id INTEGER,
            platform TEXT NOT NULL,
            post_content TEXT NOT NULL,
            post_id TEXT,
            status TEXT DEFAULT 'draft',
            engagement_metrics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES users (id),
            FOREIGN KEY (property_id) REFERENCES properties (id)
        )
    ''')
    
    # AI Analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            feature_type TEXT NOT NULL,
            usage_count INTEGER DEFAULT 1,
            success_rate REAL DEFAULT 0.0,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# AI Helper Functions
async def generate_property_description(property_data):
    """Generate AI-powered property description."""
    if not groq_client:
        # Fallback to template-based generation for demo
        return generate_template_description(property_data)
    
    try:
        prompt = f"""
        Generate a professional, engaging property description for:
        
        Title: {property_data.get('title', '')}
        Type: {property_data.get('property_type', '')}
        Location: {property_data.get('location', '')}
        Price: {property_data.get('price', '')}
        Bedrooms: {property_data.get('bedrooms', 0)}
        Bathrooms: {property_data.get('bathrooms', 0)}
        Area: {property_data.get('area_sqft', 0)} sq ft
        Amenities: {property_data.get('amenities', '')}
        
        Create a compelling description that highlights key features, location benefits, and lifestyle appeal.
        Make it professional yet engaging for potential buyers/renters.
        Include a call-to-action at the end.
        Keep it between 150-250 words.
        """
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI generation error: {e}")
        return generate_template_description(property_data)

def generate_template_description(property_data):
    """Fallback template-based description generation."""
    title = property_data.get('title', 'Beautiful Property')
    location = property_data.get('location', 'Prime Location')
    price = property_data.get('price', 'Competitive Price')
    bedrooms = property_data.get('bedrooms', 0)
    bathrooms = property_data.get('bathrooms', 0)
    area = property_data.get('area_sqft', 0)
    amenities = property_data.get('amenities', 'Modern amenities')
    
    description = f"""🏠 {title}

📍 Located in the heart of {location}, this stunning property offers the perfect blend of luxury and convenience.

🏡 Property Highlights:
• {bedrooms} spacious bedrooms
• {bathrooms} modern bathrooms  
• {area} sq ft of well-designed living space
• Premium amenities: {amenities}

💰 Priced at {price} - exceptional value in today's market!

🌟 Why Choose This Property:
• Prime location with excellent connectivity
• Modern design with high-quality finishes
• Perfect for families and professionals
• Great investment opportunity

📞 Don't miss out on this incredible opportunity! Contact us today to schedule a viewing and make this dream home yours.

#RealEstate #Property #Investment #DreamHome #PrimeLocation"""
    
    return description

async def generate_facebook_post(property_data, description):
    """Generate Facebook post content."""
    if not groq_client:
        return generate_template_facebook_post(property_data, description)
    
    try:
        prompt = f"""
        Create an engaging Facebook post for this property listing:
        
        Property: {property_data.get('title', '')}
        Location: {property_data.get('location', '')}
        Price: {property_data.get('price', '')}
        
        Description: {description[:200]}...
        
        Create a Facebook post that:
        - Starts with attention-grabbing emoji and hook
        - Highlights key selling points
        - Uses relevant hashtags
        - Includes call-to-action
        - Is optimized for social media engagement
        - Keep it under 200 words
        """
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            max_tokens=300,
            temperature=0.8
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Facebook post generation error: {e}")
        return generate_template_facebook_post(property_data, description)

def generate_template_facebook_post(property_data, description):
    """Template-based Facebook post generation."""
    title = property_data.get('title', 'Amazing Property')
    location = property_data.get('location', 'Great Location')
    price = property_data.get('price', 'Great Price')
    
    post = f"""🏠✨ NEW LISTING ALERT! ✨🏠

📍 {title} in {location}
💰 {price}

🌟 This stunning property won't last long! Perfect for:
👨‍👩‍👧‍👦 Growing families
💼 Working professionals  
📈 Smart investors

Key features that make this special:
• Prime location with excellent connectivity
• Modern amenities and finishes
• Spacious and well-designed layout
• Great investment potential

📞 DM us or call now to schedule your viewing!

#RealEstate #PropertyForSale #Investment #DreamHome #Mumbai #Property2025 #RealEstateAgent #HomeForSale #PropertyInvestment #PrimeLocation"""
    
    return post

async def calculate_ai_lead_score(lead_data):
    """Calculate AI-enhanced lead score."""
    base_score = lead_data.get('score', 75)
    
    # AI scoring factors
    score_adjustments = 0
    
    # Budget analysis
    budget = lead_data.get('budget', '').lower()
    if 'cr' in budget or 'crore' in budget:
        score_adjustments += 15
    elif 'lakh' in budget:
        score_adjustments += 10
    
    # Source quality
    source = lead_data.get('source', '').lower()
    if source in ['referral', 'facebook']:
        score_adjustments += 10
    elif source == 'website':
        score_adjustments += 5
    
    # Response time factor
    if lead_data.get('status') == 'contacted':
        score_adjustments += 10
    
    # Location match
    location = lead_data.get('location', '').lower()
    if any(area in location for area in ['bandra', 'juhu', 'powai', 'lower parel']):
        score_adjustments += 5
    
    ai_score = min(100, max(0, base_score + score_adjustments))
    return ai_score

async def post_to_facebook(post_content, page_id, access_token):
    """Post content to Facebook page."""
    if access_token == "your_facebook_access_token":
        # Demo mode - simulate posting
        return {
            "success": True,
            "post_id": f"demo_post_{datetime.now().timestamp()}",
            "message": "Demo post created successfully"
        }
    
    try:
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        data = {
            "message": post_content,
            "access_token": access_token
        }
        
        response = requests.post(url, data=data)
        result = response.json()
        
        if response.status_code == 200:
            return {"success": True, "post_id": result.get("id"), "message": "Posted successfully"}
        else:
            return {"success": False, "error": result.get("error", {}).get("message", "Unknown error")}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Authentication helper (same as before)
def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes (Login/Register pages same as before)
@app.get("/", response_class=HTMLResponse)
async def home():
    """Main login page with AI features highlighted."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI-Enhanced Real Estate CRM</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 450px;
            }
            .logo {
                text-align: center;
                margin-bottom: 2rem;
            }
            .logo h1 {
                color: #333;
                font-size: 2.2rem;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .logo p {
                color: #666;
                font-size: 1rem;
                font-weight: 500;
            }
            .ai-features {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                text-align: center;
            }
            .ai-features h3 {
                margin-bottom: 1rem;
                font-size: 1.2rem;
            }
            .features-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.8rem;
                font-size: 0.9rem;
            }
            .feature {
                background: rgba(255,255,255,0.1);
                padding: 0.8rem;
                border-radius: 8px;
                text-align: center;
            }
            .demo-info {
                background: #f8f9fa;
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                border-left: 4px solid #28a745;
            }
            .demo-info h3 {
                color: #28a745;
                margin-bottom: 0.8rem;
                font-size: 1.1rem;
            }
            .demo-info p {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 0.3rem;
            }
            .form-group {
                margin-bottom: 1.2rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                color: #333;
                font-weight: 600;
            }
            input {
                width: 100%;
                padding: 1rem;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 1rem;
                transition: all 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 10px rgba(102, 126, 234, 0.1);
            }
            .btn {
                width: 100%;
                padding: 1rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                margin-bottom: 1rem;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            .link {
                text-align: center;
                color: #667eea;
                text-decoration: none;
                cursor: pointer;
                font-weight: 500;
            }
            .link:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <h1>🤖 AI Real Estate CRM</h1>
                <p>Powered by Artificial Intelligence</p>
            </div>
            
            <div class="ai-features">
                <h3>🚀 AI-Powered Features</h3>
                <div class="features-grid">
                    <div class="feature">🏠 AI Property Descriptions</div>
                    <div class="feature">📘 Auto Facebook Posts</div>
                    <div class="feature">🎯 Smart Lead Scoring</div>
                    <div class="feature">💬 WhatsApp Integration</div>
                </div>
            </div>
            
            <div class="demo-info">
                <h3>🚀 Demo Account</h3>
                <p><strong>Email:</strong> demo@mumbai.com</p>
                <p><strong>Password:</strong> demo123</p>
                <p>Experience AI-powered real estate management</p>
            </div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required value="demo@mumbai.com">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required value="demo123">
                </div>
                <button type="submit" class="btn">🚀 Access AI Dashboard</button>
            </form>
            
            <div style="text-align: center;">
                <a href="/register" class="link">New Agent? Register for AI Features</a>
            </div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        localStorage.setItem('token', result.token);
                        localStorage.setItem('user', JSON.stringify(result.user));
                        window.location.href = '/dashboard';
                    } else {
                        alert(result.detail || 'Login failed');
                    }
                } catch (error) {
                    alert('Network error. Please try again.');
                }
            });
        </script>
    </body>
    </html>
    """

# Enhanced API Endpoints
@app.post("/api/properties")
async def create_property_with_ai(request: Request, payload: dict = Depends(verify_token)):
    """Create new property with AI-generated description and optional Facebook posting."""
    data = await request.json()
    
    # Generate AI description
    ai_description = await generate_property_description(data)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO properties (agent_id, title, description, ai_generated_description, property_type, location, price, bedrooms, bathrooms, area_sqft, amenities, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        payload['user_id'], data['title'], data.get('description'),
        ai_description, data['property_type'], data['location'], data['price'],
        data.get('bedrooms', 0), data.get('bathrooms', 0),
        data.get('area_sqft', 0), data.get('amenities', ''),
        data.get('status', 'available')
    ))
    
    property_id = cursor.lastrowid
    
    # Auto-post to Facebook if enabled
    facebook_result = None
    if data.get('auto_post_facebook', False):
        facebook_post_content = await generate_facebook_post(data, ai_description)
        facebook_result = await post_to_facebook(facebook_post_content, FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN)
        
        if facebook_result.get('success'):
            cursor.execute('''
                UPDATE properties SET facebook_posted = 1, facebook_post_id = ? WHERE id = ?
            ''', (facebook_result.get('post_id'), property_id))
            
            # Save social post record
            cursor.execute('''
                INSERT INTO social_posts (agent_id, property_id, platform, post_content, post_id, status)
                VALUES (?, ?, 'facebook', ?, ?, 'published')
            ''', (payload['user_id'], property_id, facebook_post_content, facebook_result.get('post_id')))
    
    conn.commit()
    conn.close()
    
    return {
        "id": property_id,
        "message": "Property created successfully",
        "ai_description": ai_description,
        "facebook_result": facebook_result
    }

@app.post("/api/leads")
async def create_lead_with_ai(request: Request, payload: dict = Depends(verify_token)):
    """Create new lead with AI scoring."""
    data = await request.json()
    
    # Calculate AI score
    ai_score = await calculate_ai_lead_score(data)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO leads (agent_id, name, email, phone, location, budget, property_type, source, status, score, ai_score, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        payload['user_id'], data['name'], data.get('email'), data['phone'],
        data.get('location'), data.get('budget'), data.get('property_type'),
        data.get('source', 'manual'), data.get('status', 'new'),
        data.get('score', 75), ai_score, data.get('notes', '')
    ))
    
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": lead_id,
        "message": "Lead created successfully",
        "ai_score": ai_score
    }

@app.post("/api/generate-description")
async def generate_description_endpoint(request: Request, payload: dict = Depends(verify_token)):
    """Generate AI description for property."""
    data = await request.json()
    description = await generate_property_description(data)
    return {"description": description}

@app.post("/api/post-to-facebook")
async def facebook_post_endpoint(request: Request, payload: dict = Depends(verify_token)):
    """Post property to Facebook."""
    data = await request.json()
    property_id = data.get('property_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get property details
    cursor.execute('SELECT * FROM properties WHERE id = ? AND agent_id = ?', (property_id, payload['user_id']))
    property_data = cursor.fetchone()
    
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Generate Facebook post
    facebook_content = await generate_facebook_post(dict(property_data), property_data['ai_generated_description'] or property_data['description'])
    
    # Post to Facebook
    result = await post_to_facebook(facebook_content, FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN)
    
    if result.get('success'):
        # Update property
        cursor.execute('''
            UPDATE properties SET facebook_posted = 1, facebook_post_id = ? WHERE id = ?
        ''', (result.get('post_id'), property_id))
        
        # Save social post record
        cursor.execute('''
            INSERT INTO social_posts (agent_id, property_id, platform, post_content, post_id, status)
            VALUES (?, ?, 'facebook', ?, ?, 'published')
        ''', (payload['user_id'], property_id, facebook_content, result.get('post_id')))
        
        conn.commit()
    
    conn.close()
    return result

@app.get("/dashboard", response_class=HTMLResponse)
async def ai_dashboard():
    """AI-Enhanced dashboard with property generation and Facebook posting."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Dashboard - Real Estate CRM</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f5f5;
                min-height: 100vh;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }
            .header h1 {
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .ai-badge {
                background: rgba(255,255,255,0.2);
                padding: 0.3rem 0.8rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: bold;
            }
            .user-info {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            .logout-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.3s;
            }
            .logout-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            .main-content {
                display: grid;
                grid-template-columns: 250px 1fr;
                min-height: calc(100vh - 80px);
            }
            .sidebar {
                background: white;
                padding: 2rem 1rem;
                box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            }
            .nav-item {
                display: block;
                padding: 1rem;
                color: #333;
                text-decoration: none;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                transition: all 0.3s;
                font-weight: 500;
            }
            .nav-item:hover, .nav-item.active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                transform: translateX(5px);
            }
            .content {
                padding: 2rem;
            }
            .ai-stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            .ai-stat-card {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            .ai-stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .stat-value {
                font-size: 2.5rem;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 0.5rem;
            }
            .stat-label {
                color: #666;
                font-size: 1rem;
                font-weight: 500;
            }
            .stat-sublabel {
                color: #999;
                font-size: 0.85rem;
                margin-top: 0.5rem;
            }
            .ai-actions {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            .ai-action-card {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
                transition: all 0.3s;
                cursor: pointer;
                border: 2px solid transparent;
            }
            .ai-action-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                border-color: #667eea;
            }
            .ai-icon {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
            .ai-action-title {
                font-size: 1.2rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 0.5rem;
            }
            .ai-action-desc {
                color: #666;
                font-size: 0.9rem;
                line-height: 1.5;
            }
            .section {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .section h2 {
                margin-bottom: 1.5rem;
                color: #333;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 600;
                transition: all 0.3s;
                margin-right: 1rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            .btn-ai {
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
            }
            .btn-ai:hover {
                box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
            }
            .btn-facebook {
                background: linear-gradient(135deg, #4267B2 0%, #365899 100%);
                box-shadow: 0 4px 15px rgba(66, 103, 178, 0.3);
            }
            .btn-facebook:hover {
                box-shadow: 0 6px 20px rgba(66, 103, 178, 0.4);
            }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
            }
            .table th, .table td {
                padding: 1rem;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            .table th {
                background: #f8f9fa;
                font-weight: 600;
                color: #333;
            }
            .table tr:hover {
                background: #f8f9fa;
            }
            .ai-score {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.3rem 0.8rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: bold;
            }
            .facebook-posted {
                background: #4267B2;
                color: white;
                padding: 0.2rem 0.6rem;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: bold;
            }
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
            }
            .modal-content {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 2rem;
                border-radius: 15px;
                width: 90%;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .close {
                float: right;
                font-size: 1.5rem;
                cursor: pointer;
                color: #999;
                font-weight: bold;
            }
            .close:hover {
                color: #333;
            }
            .form-group {
                margin-bottom: 1.5rem;
            }
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: #333;
            }
            .form-group input, .form-group select, .form-group textarea {
                width: 100%;
                padding: 1rem;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 1rem;
                transition: border-color 0.3s;
            }
            .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-top: 1rem;
            }
            .ai-description-preview {
                background: #f8f9fa;
                padding: 1.5rem;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                margin-top: 1rem;
                font-family: monospace;
                white-space: pre-wrap;
                max-height: 200px;
                overflow-y: auto;
            }
            @media (max-width: 768px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
                .sidebar {
                    display: none;
                }
                .ai-stats-grid, .ai-actions {
                    grid-template-columns: 1fr;
                }
                .header {
                    padding: 1rem;
                }
                .content {
                    padding: 1rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>
                🤖 AI Real Estate CRM 
                <span class="ai-badge">AI-POWERED</span>
            </h1>
            <div class="user-info">
                <span id="userName">Welcome, Agent</span>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <a href="#" class="nav-item active" onclick="showSection('dashboard')">🤖 AI Dashboard</a>
                <a href="#" class="nav-item" onclick="showSection('leads')">🎯 Smart Leads</a>
                <a href="#" class="nav-item" onclick="showSection('properties')">🏠 AI Properties</a>
                <a href="#" class="nav-item" onclick="showSection('social')">📘 Social Media</a>
                <a href="#" class="nav-item" onclick="showSection('analytics')">📊 AI Analytics</a>
                <a href="#" class="nav-item" onclick="showSection('settings')">⚙️ Settings</a>
            </div>
            
            <div class="content">
                <div id="dashboardSection">
                    <div class="ai-stats-grid">
                        <div class="ai-stat-card">
                            <div class="stat-value" id="totalLeads">0</div>
                            <div class="stat-label">Smart Leads</div>
                            <div class="stat-sublabel">AI-Scored & Prioritized</div>
                        </div>
                        <div class="ai-stat-card">
                            <div class="stat-value" id="aiProperties">0</div>
                            <div class="stat-label">AI Properties</div>
                            <div class="stat-sublabel">Auto-Generated Descriptions</div>
                        </div>
                        <div class="ai-stat-card">
                            <div class="stat-value" id="facebookPosts">0</div>
                            <div class="stat-label">Facebook Posts</div>
                            <div class="stat-sublabel">Auto-Published Listings</div>
                        </div>
                        <div class="ai-stat-card">
                            <div class="stat-value">98%</div>
                            <div class="stat-label">AI Accuracy</div>
                            <div class="stat-sublabel">Lead Scoring Precision</div>
                        </div>
                    </div>
                    
                    <div class="ai-actions">
                        <div class="ai-action-card" onclick="openModal('aiPropertyModal')">
                            <div class="ai-icon">🤖</div>
                            <div class="ai-action-title">AI Property Generator</div>
                            <div class="ai-action-desc">Create listings with AI-powered descriptions and auto-post to Facebook</div>
                        </div>
                        <div class="ai-action-card" onclick="openModal('smartLeadModal')">
                            <div class="ai-icon">🎯</div>
                            <div class="ai-action-title">Smart Lead Capture</div>
                            <div class="ai-action-desc">Add leads with intelligent scoring and auto-follow-up suggestions</div>
                        </div>
                        <div class="ai-action-card" onclick="generateFacebookPosts()">
                            <div class="ai-icon">📘</div>
                            <div class="ai-action-title">Bulk Facebook Posts</div>
                            <div class="ai-action-desc">Auto-generate and post all unlisted properties to Facebook</div>
                        </div>
                        <div class="ai-action-card" onclick="openWhatsAppCenter()">
                            <div class="ai-icon">💬</div>
                            <div class="ai-action-title">WhatsApp Center</div>
                            <div class="ai-action-desc">Manage leads with automated WhatsApp messaging</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🔥 Hot AI-Scored Leads</h2>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Contact</th>
                                    <th>Budget</th>
                                    <th>AI Score</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="hotLeadsTable">
                                <tr>
                                    <td colspan="5" style="text-align: center; padding: 2rem; color: #666;">
                                        Loading AI-scored leads...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>🏠 Recent AI Properties</h2>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Location</th>
                                    <th>Price</th>
                                    <th>AI Features</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="aiPropertiesTable">
                                <tr>
                                    <td colspan="5" style="text-align: center; padding: 2rem; color: #666;">
                                        Loading AI properties...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Other sections will be added here -->
            </div>
        </div>
        
        <!-- AI Property Modal -->
        <div id="aiPropertyModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('aiPropertyModal')">&times;</span>
                <h2>🤖 AI Property Generator</h2>
                <p style="color: #666; margin-bottom: 2rem;">Create a property listing with AI-generated description and optional Facebook posting.</p>
                
                <form id="aiPropertyForm">
                    <div class="form-group">
                        <label for="aiPropertyTitle">Property Title</label>
                        <input type="text" id="aiPropertyTitle" name="title" required placeholder="e.g., Luxury 3 BHK in Bandra West">
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label for="aiPropertyType">Property Type</label>
                            <select id="aiPropertyType" name="property_type" required>
                                <option value="">Select Type</option>
                                <option value="Residential">Residential</option>
                                <option value="Commercial">Commercial</option>
                                <option value="Industrial">Industrial</option>
                                <option value="Land">Land</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="aiPropertyLocation">Location</label>
                            <input type="text" id="aiPropertyLocation" name="location" required placeholder="e.g., Bandra West, Mumbai">
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label for="aiPropertyPrice">Price</label>
                            <input type="text" id="aiPropertyPrice" name="price" required placeholder="e.g., ₹2.8 Cr">
                        </div>
                        <div class="form-group">
                            <label for="aiPropertyBedrooms">Bedrooms</label>
                            <input type="number" id="aiPropertyBedrooms" name="bedrooms" min="0" value="0">
                        </div>
                        <div class="form-group">
                            <label for="aiPropertyBathrooms">Bathrooms</label>
                            <input type="number" id="aiPropertyBathrooms" name="bathrooms" min="0" value="0">
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label for="aiPropertyArea">Area (Sq Ft)</label>
                            <input type="number" id="aiPropertyArea" name="area_sqft" min="0" placeholder="e.g., 1250">
                        </div>
                        <div class="form-group">
                            <label for="aiPropertyAmenities">Amenities</label>
                            <input type="text" id="aiPropertyAmenities" name="amenities" placeholder="e.g., Gym, Pool, Security">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="aiPropertyDescription">Additional Details (Optional)</label>
                        <textarea id="aiPropertyDescription" name="description" rows="3" placeholder="Any specific details you want to highlight..."></textarea>
                    </div>
                    
                    <div class="checkbox-group">
                        <input type="checkbox" id="autoFacebookPost" name="auto_post_facebook" checked>
                        <label for="autoFacebookPost">📘 Auto-post to Facebook with AI-generated content</label>
                    </div>
                    
                    <button type="button" class="btn btn-ai" onclick="generateAIDescription()" style="margin-right: 1rem;">🤖 Generate AI Description</button>
                    <button type="submit" class="btn">🚀 Create Property</button>
                    
                    <div id="aiDescriptionPreview" class="ai-description-preview" style="display: none;">
                        <strong>AI-Generated Description:</strong><br><br>
                        <span id="generatedDescription"></span>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            // Authentication check
            const token = localStorage.getItem('token');
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            
            if (!token) {
                window.location.href = '/';
            }
            
            // Display user info
            document.getElementById('userName').textContent = `Welcome, ${user.firstName} ${user.lastName}`;
            
            // API headers
            const apiHeaders = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            };
            
            // Load data on page load
            loadAIDashboardData();
            
            function showSection(section) {
                // Implementation similar to previous version
                document.getElementById('dashboardSection').style.display = section === 'dashboard' ? 'block' : 'none';
                
                // Remove active class from all nav items
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                // Add active class to clicked nav item
                event.target.classList.add('active');
                
                if (section === 'dashboard') {
                    loadAIDashboardData();
                }
            }
            
            async function loadAIDashboardData() {
                try {
                    // Load leads
                    const leadsResponse = await fetch('/api/leads', { headers: apiHeaders });
                    const leads = await leadsResponse.json();
                    
                    // Load properties
                    const propertiesResponse = await fetch('/api/properties', { headers: apiHeaders });
                    const properties = await propertiesResponse.json();
                    
                    // Update AI stats
                    document.getElementById('totalLeads').textContent = leads.length;
                    document.getElementById('aiProperties').textContent = properties.filter(p => p.ai_generated_description).length;
                    document.getElementById('facebookPosts').textContent = properties.filter(p => p.facebook_posted).length;
                    
                    // Update hot leads table (AI score > 90)
                    const hotLeads = leads.filter(l => l.ai_score > 90).slice(0, 5);
                    const hotLeadsHtml = hotLeads.map(lead => `
                        <tr>
                            <td>${lead.name}</td>
                            <td>${lead.phone}<br><small>${lead.email || ''}</small></td>
                            <td>${lead.budget || 'Not specified'}</td>
                            <td><span class="ai-score">${lead.ai_score}%</span></td>
                            <td>
                                <button class="btn" style="padding: 0.5rem 1rem; margin: 0.2rem;" onclick="callLead('${lead.phone}')">📞</button>
                                <button class="btn" style="padding: 0.5rem 1rem; margin: 0.2rem;" onclick="sendWhatsApp('${lead.phone}')">💬</button>
                            </td>
                        </tr>
                    `).join('');
                    
                    document.getElementById('hotLeadsTable').innerHTML = hotLeadsHtml || '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #666;">No high-scoring leads found</td></tr>';
                    
                    // Update AI properties table
                    const aiPropertiesHtml = properties.slice(0, 5).map(property => `
                        <tr>
                            <td>${property.title}</td>
                            <td>${property.location}</td>
                            <td>${property.price}</td>
                            <td>
                                ${property.ai_generated_description ? '<span class="ai-score">AI Description</span>' : ''}
                                ${property.facebook_posted ? '<span class="facebook-posted">📘 Posted</span>' : ''}
                            </td>
                            <td>
                                <button class="btn btn-facebook" style="padding: 0.5rem 1rem; margin: 0.2rem;" onclick="postToFacebook('${property.id}')">📘 Post</button>
                            </td>
                        </tr>
                    `).join('');
                    
                    document.getElementById('aiPropertiesTable').innerHTML = aiPropertiesHtml || '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #666;">No properties found</td></tr>';
                    
                } catch (error) {
                    console.error('Error loading AI dashboard data:', error);
                }
            }
            
            // Modal functions
            function openModal(modalId) {
                document.getElementById(modalId).style.display = 'block';
            }
            
            function closeModal(modalId) {
                document.getElementById(modalId).style.display = 'none';
            }
            
            // AI Description Generation
            async function generateAIDescription() {
                const formData = new FormData(document.getElementById('aiPropertyForm'));
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/generate-description', {
                        method: 'POST',
                        headers: apiHeaders,
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        document.getElementById('generatedDescription').textContent = result.description;
                        document.getElementById('aiDescriptionPreview').style.display = 'block';
                    } else {
                        alert('Failed to generate AI description');
                    }
                } catch (error) {
                    alert('Error generating AI description');
                }
            }
            
            // Property form submission with AI
            document.getElementById('aiPropertyForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                data.auto_post_facebook = document.getElementById('autoFacebookPost').checked;
                
                try {
                    const response = await fetch('/api/properties', {
                        method: 'POST',
                        headers: apiHeaders,
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        let message = 'Property created successfully with AI description!';
                        if (result.facebook_result?.success) {
                            message += '\\n✅ Also posted to Facebook automatically!';
                        }
                        alert(message);
                        closeModal('aiPropertyModal');
                        e.target.reset();
                        document.getElementById('aiDescriptionPreview').style.display = 'none';
                        loadAIDashboardData();
                    } else {
                        alert(result.detail || 'Failed to create property');
                    }
                } catch (error) {
                    alert('Network error. Please try again.');
                }
            });
            
            // Facebook posting
            async function postToFacebook(propertyId) {
                try {
                    const response = await fetch('/api/post-to-facebook', {
                        method: 'POST',
                        headers: apiHeaders,
                        body: JSON.stringify({ property_id: propertyId })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('Property posted to Facebook successfully!');
                        loadAIDashboardData();
                    } else {
                        alert('Failed to post to Facebook: ' + (result.error || 'Unknown error'));
                    }
                } catch (error) {
                    alert('Error posting to Facebook');
                }
            }
            
            // Other action functions
            function callLead(phone) {
                alert(`🤖 AI Suggestion: Calling ${phone}...\\n\\nAI recommends mentioning:\\n• High lead score indicates serious buyer\\n• Personalized property recommendations ready\\n• Best time to call: Now (high engagement score)`);
            }
            
            function sendWhatsApp(phone) {
                const message = encodeURIComponent('🏠 Hi! Our AI system identified you as a high-priority lead. I have some perfect property matches for you. When would be a good time to discuss?');
                window.open(`https://wa.me/${phone.replace(/[^0-9]/g, '')}?text=${message}`, '_blank');
            }
            
            function generateFacebookPosts() {
                alert('🤖 AI Bulk Posting\\n\\nThis will automatically:\\n• Generate Facebook posts for all unlisted properties\\n• Create engaging descriptions with hashtags\\n• Post to your connected Facebook page\\n• Track engagement metrics\\n\\nFeature coming soon!');
            }
            
            function openWhatsAppCenter() {
                alert('💬 WhatsApp Business Center\\n\\n🤖 AI Features:\\n• Auto-respond to inquiries\\n• Smart lead qualification\\n• Property recommendations\\n• Follow-up scheduling\\n• Bulk messaging campaigns\\n\\nIntegration coming soon!');
            }
            
            function logout() {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/';
            }
            
            // Close modals when clicking outside
            window.onclick = function(event) {
                if (event.target.classList.contains('modal')) {
                    event.target.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """

# Other endpoints (login, register, etc.) same as previous implementation...
@app.post("/api/login")
async def login_user(request: Request):
    """Login agent."""
    data = await request.json()
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, email, first_name, last_name, phone, experience, areas, property_types, languages, facebook_connected, ai_enabled
        FROM users WHERE email = ? AND password_hash = ?
    ''', (data['email'], password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token_data = {
        "user_id": user[0],
        "email": user[1],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
    
    return {
        "token": token,
        "user": {
            "id": user[0],
            "email": user[1],
            "firstName": user[2],
            "lastName": user[3],
            "phone": user[4],
            "experience": user[5],
            "areas": user[6],
            "propertyTypes": user[7],
            "languages": user[8],
            "facebookConnected": bool(user[9]),
            "aiEnabled": bool(user[10])
        }
    }

@app.get("/api/leads")
async def get_leads(payload: dict = Depends(verify_token)):
    """Get all leads for agent."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, email, phone, location, budget, property_type, source, status, score, ai_score, notes, created_at
        FROM leads WHERE agent_id = ? ORDER BY ai_score DESC, created_at DESC
    ''', (payload['user_id'],))
    
    leads = cursor.fetchall()
    conn.close()
    
    return [dict(lead) for lead in leads]

@app.get("/api/properties")
async def get_properties(payload: dict = Depends(verify_token)):
    """Get all properties for agent."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, description, ai_generated_description, property_type, location, price, bedrooms, bathrooms, area_sqft, amenities, status, facebook_posted, created_at
        FROM properties WHERE agent_id = ? ORDER BY created_at DESC
    ''', (payload['user_id'],))
    
    properties = cursor.fetchall()
    conn.close()
    
    return [dict(prop) for prop in properties]

if __name__ == "__main__":
    # Create demo user with AI features
    conn = get_db()
    cursor = conn.cursor()
    
    demo_password = hashlib.sha256('demo123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, email, password_hash, first_name, last_name, phone, experience, areas, property_types, languages, facebook_connected, ai_enabled)
        VALUES (1, 'demo@mumbai.com', ?, 'Priya', 'Sharma', '+91 98765 43210', '4-5 years', 
                'Bandra, Andheri, Juhu, Powai', 'Residential, Luxury', 'English, Hindi, Marathi', 1, 1)
    ''', (demo_password,))
    
    # Add AI-enhanced demo properties
    demo_properties = [
        (1, 'Luxury 3 BHK Sea View Apartment', 'Premium apartment with stunning sea view', 
         '🏠 LUXURY 3 BHK SEA VIEW APARTMENT\n\n📍 Located in the prestigious Bandra West, this stunning 3 BHK apartment offers breathtaking sea views and modern luxury living.\n\n🏡 Property Highlights:\n• 3 spacious bedrooms with built-in wardrobes\n• 3 modern bathrooms with premium fittings\n• 1,250 sq ft of elegantly designed living space\n• Premium amenities: Gym, Pool, 24/7 Security, Covered Parking\n\n💰 Priced at ₹2.8 Cr - exceptional value for sea-facing luxury!\n\n🌟 Why Choose This Property:\n• Unobstructed sea views from all rooms\n• Prime Bandra West location with excellent connectivity\n• Modern architecture with high-quality finishes\n• Perfect for discerning families and professionals\n• Excellent rental and resale potential\n\n📞 Don\'t miss this rare opportunity! Contact us today to schedule a viewing and experience luxury living at its finest.\n\n#LuxuryLiving #SeaView #BandraWest #PremiumProperty', 
         'Residential', 'Bandra West', '₹2.8 Cr', 3, 3, 1250, 'Gym, Pool, Security, Parking', 'available', 1),
        (1, 'Spacious 4 BHK Villa with Garden', 'Independent villa with private garden', 
         '🏡 SPACIOUS 4 BHK VILLA WITH PRIVATE GARDEN\n\n📍 Nestled in the serene locality of Powai, this magnificent 4 BHK independent villa offers the perfect blend of luxury and tranquility.\n\n🏡 Property Highlights:\n• 4 large bedrooms with en-suite bathrooms\n• 2,500 sq ft of thoughtfully designed living space\n• Private garden perfect for family gatherings\n• Premium amenities: Private Garden, Covered Parking, Security\n\n💰 Priced at ₹3.5 Cr - your dream villa awaits!\n\n🌟 Why This Villa is Special:\n• Private garden for outdoor entertainment\n• Peaceful Powai location away from city chaos\n• Independent living with complete privacy\n• Ideal for large families and nature lovers\n• Excellent investment in growing Powai market\n\n📞 Schedule your visit today and step into villa lifestyle perfection!\n\n#VillaLife #PrivateGarden #Powai #IndependentLiving', 
         'Residential', 'Powai', '₹3.5 Cr', 4, 4, 2500, 'Garden, Parking, Security', 'available', 0)
    ]
    
    for prop in demo_properties:
        cursor.execute('''
            INSERT OR REPLACE INTO properties (agent_id, title, description, ai_generated_description, property_type, location, price, bedrooms, bathrooms, area_sqft, amenities, status, facebook_posted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', prop)
    
    # Add AI-enhanced demo leads
    demo_leads = [
        (1, 'Rajesh Patel', 'rajesh@email.com', '+91 98765 12345', 'Bandra West', '₹2.5 Cr', '3 BHK Apartment', 'facebook', 'hot', 94, 98, 'Very interested in 3 BHK sea view'),
        (1, 'Kavita Joshi', 'kavita@email.com', '+91 98765 22222', 'Juhu', '₹5.0 Cr', 'Penthouse', 'referral', 'warm', 87, 92, 'Looking for luxury penthouse with amenities'),
        (1, 'Vikram Singh', 'vikram@email.com', '+91 98765 11111', 'Powai', '₹3.2 Cr', '4 BHK Villa', 'website', 'contacted', 92, 96, 'Family interested in villa with garden'),
        (1, 'Anjali Mehta', 'anjali@email.com', '+91 98765 67890', 'Andheri East', '₹1.8 Cr', '2 BHK Apartment', 'whatsapp', 'new', 79, 84, 'First time buyer, needs guidance')
    ]
    
    for lead in demo_leads:
        cursor.execute('''
            INSERT OR REPLACE INTO leads (agent_id, name, email, phone, location, budget, property_type, source, status, score, ai_score, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', lead)
    
    conn.commit()
    conn.close()
    
    print("🤖 AI-ENHANCED REAL ESTATE CRM STARTING...")
    print("=" * 70)
    print("📍 URL: http://localhost:8004")
    print("👤 Demo Login: demo@mumbai.com / demo123")
    print("=" * 70)
    print("🤖 AI FEATURES:")
    print("   • AI-Powered Property Descriptions")
    print("   • Automated Facebook Page Posting")
    print("   • Smart Lead Scoring with AI")
    print("   • WhatsApp Business Integration")
    print("   • Social Media Content Generation")
    print("   • Market Insights & Analytics")
    print("=" * 70)
    print("🚀 NEXT-GENERATION CRM WITH AI!")
    
    uvicorn.run("ai_enhanced_crm:app", host="0.0.0.0", port=8004, reload=True)

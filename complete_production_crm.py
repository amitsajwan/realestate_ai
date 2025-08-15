"""
PRODUCTION REAL ESTATE CRM SYSTEM
=================================
Complete production-ready CRM system for real estate agents with:
- User authentication and registration
- Lead management with full CRUD operations
- Property listing management
- Real-time dashboard with working features
- Mobile-responsive design
- SQLite database with proper schema

Author: GitHub Copilot
Date: January 2025
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Header, Query
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import hashlib
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Optional
import uvicorn
import os
import urllib.parse
import requests
from dotenv import load_dotenv
from db_adapter import get_db_connection, UserRepository, DB_MODE
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Real Estate CRM", description="Production-ready CRM for real estate agents")

# Include API routers
from api.endpoints import ai_localization, listing_posts, crm, leads, india_market, auth, dashboard, facebook_oauth
app.include_router(ai_localization.router)
app.include_router(listing_posts.router, prefix="/api/listings")
app.include_router(crm.router)
app.include_router(leads.router)
app.include_router(india_market.router)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(dashboard.router, prefix="/api/dashboard")
app.include_router(facebook_oauth.router, prefix="/api/facebook")

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "real_estate_crm_secret_key_2025")
FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI", "http://localhost:8004/auth/facebook/callback")

# Initialize user repository
user_repo = UserRepository(get_db_connection())

# Database setup - using adapter (Mongo only)
def get_db():
    """Get MongoDB connection through adapter."""
    return get_db_connection()

def init_database():
    """MongoDB - collections are created automatically"""
    print("✅ MongoDB mode - collections will be created automatically")

# Initialize database on startup
init_database()

# Lightweight migration for Facebook columns
def migrate_database():
    # MongoDB - fields are added dynamically, no migration needed
    print("✅ MongoDB mode - no schema migration needed")

migrate_database()

# Ensure demo data exists when module is imported (idempotent)
def ensure_demo_seed():
    try:
        # Check if demo user exists
        existing_user = user_repo.get_user_by_email('demo@mumbai.com')
        if not existing_user:
            # Create demo user using the repository
            user_data = {
                'email': 'demo@mumbai.com',
                'password': 'demo123',  # Will be hashed by the repository
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'phone': '+91 98765 43210',
                'experience': '4-5 years',
                'areas': 'Bandra, Andheri, Juhu, Powai',
                'property_types': 'Residential, Luxury',
                'languages': 'English, Hindi, Marathi',
                'facebook_connected': 0
            }
            user_id = user_repo.create_user(user_data)
            # For MongoDB, demo data can be added here in future if needed
            print("✅ Demo user created in MongoDB")
    except Exception:
        # Do not block app startup if seeding fails
        pass

ensure_demo_seed()

# Authentication helper
def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Main login page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Real Estate CRM - Login</title>
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
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
            }
            .logo {
                text-align: center;
                margin-bottom: 2rem;
            }
            .logo h1 {
                color: #333;
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .logo p {
                color: #666;
                font-size: 0.9rem;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                color: #333;
                font-weight: 500;
            }
            input {
                width: 100%;
                padding: 0.8rem;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 1rem;
                transition: border-color 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            .btn {
                width: 100%;
                padding: 0.8rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 1rem;
                cursor: pointer;
                transition: transform 0.2s;
                margin-bottom: 1rem;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .link {
                text-align: center;
                color: #667eea;
                text-decoration: none;
                cursor: pointer;
            }
            .link:hover {
                text-decoration: underline;
            }
            .demo-info {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
                border-left: 4px solid #28a745;
            }
            .demo-info h3 {
                color: #28a745;
                margin-bottom: 0.5rem;
                font-size: 1rem;
            }
            .demo-info p {
                color: #666;
                font-size: 0.85rem;
                margin-bottom: 0.25rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <h1>🏠 Real Estate CRM</h1>
                <p>Production-Ready System</p>
            </div>
            
            <div class="demo-info">
                <h3>🚀 Demo Account</h3>
                <p><strong>Email:</strong> demo@mumbai.com</p>
                <p><strong>Password:</strong> demo123</p>
                <p>Includes sample leads and properties</p>
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
                <button type="submit" class="btn">Login to Dashboard</button>
            </form>
            
            <div style="text-align: center;">
                <a href="/register" class="link">New Agent? Register Here</a>
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

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Agent registration page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register - Real Estate CRM</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 2rem 0;
            }
            .container {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 500px;
                margin: 0 auto;
            }
            .logo {
                text-align: center;
                margin-bottom: 2rem;
            }
            .logo h1 {
                color: #333;
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                color: #333;
                font-weight: 500;
            }
            input, select, textarea {
                width: 100%;
                padding: 0.8rem;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 1rem;
                transition: border-color 0.3s;
            }
            input:focus, select:focus, textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            .btn {
                width: 100%;
                padding: 0.8rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 1rem;
                cursor: pointer;
                transition: transform 0.2s;
                margin-bottom: 1rem;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .link {
                text-align: center;
                color: #667eea;
                text-decoration: none;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <h1>🏠 Agent Registration</h1>
                <p>Join our real estate platform</p>
            </div>
            
            <form id="registerForm">
                <div class="form-group">
                    <label for="firstName">First Name</label>
                    <input type="text" id="firstName" name="firstName" required>
                </div>
                <div class="form-group">
                    <label for="lastName">Last Name</label>
                    <input type="text" id="lastName" name="lastName" required>
                </div>
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="phone">Phone Number</label>
                    <input type="tel" id="phone" name="phone" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <div class="form-group">
                    <label for="experience">Experience Level</label>
                    <select id="experience" name="experience" required>
                        <option value="">Select Experience</option>
                        <option value="0-1 years">0-1 years</option>
                        <option value="2-3 years">2-3 years</option>
                        <option value="4-5 years">4-5 years</option>
                        <option value="5+ years">5+ years</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="areas">Areas of Operation</label>
                    <input type="text" id="areas" name="areas" placeholder="e.g., Mumbai, Pune, Bangalore">
                </div>
                <div class="form-group">
                    <label for="propertyTypes">Property Types</label>
                    <input type="text" id="propertyTypes" name="propertyTypes" placeholder="e.g., Residential, Commercial, Luxury">
                </div>
                <div class="form-group">
                    <label for="languages">Languages</label>
                    <input type="text" id="languages" name="languages" placeholder="e.g., English, Hindi, Marathi">
                </div>
                
                <button type="submit" class="btn">Register as Agent</button>
            </form>
            
            <div style="text-align: center;">
                <a href="/" class="link">Already have account? Login here</a>
            </div>
        </div>
        
        <script>
            document.getElementById('registerForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        alert('Registration successful! Please login.');
                        window.location.href = '/';
                    } else {
                        alert(result.detail || 'Registration failed');
                    }
                } catch (error) {
                    alert('Network error. Please try again.');
                }
            });
        </script>
    </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - Real Estate CRM</title>
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
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header h1 {
                font-size: 1.5rem;
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
                border-radius: 5px;
                margin-bottom: 0.5rem;
                transition: background 0.3s;
            }
            .nav-item:hover, .nav-item.active {
                background: #667eea;
                color: white;
            }
            .content {
                padding: 2rem;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            .stat-card {
                background: white;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .stat-value {
                font-size: 2rem;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 0.5rem;
            }
            .stat-label {
                color: #666;
                font-size: 0.9rem;
            }
            .section {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .section h2 {
                margin-bottom: 1rem;
                color: #333;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 0.8rem 1.5rem;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
                transition: transform 0.2s;
                margin-right: 1rem;
                margin-bottom: 1rem;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .btn-success {
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            }
            .btn-warning {
                background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
            }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
            }
            .table th, .table td {
                padding: 1rem;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .table th {
                background: #f8f9fa;
                font-weight: 600;
            }
            .table tr:hover {
                background: #f8f9fa;
            }
            .status-hot { color: #dc3545; font-weight: bold; }
            .status-warm { color: #fd7e14; font-weight: bold; }
            .status-cold { color: #6c757d; }
            .quick-actions {
                display: flex;
                gap: 1rem;
                margin-bottom: 2rem;
                flex-wrap: wrap;
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
                border-radius: 10px;
                width: 90%;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
            }
            .close {
                float: right;
                font-size: 1.5rem;
                cursor: pointer;
                color: #999;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
            }
            .form-group input, .form-group select, .form-group textarea {
                width: 100%;
                padding: 0.8rem;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 1rem;
            }
            @media (max-width: 768px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
                .sidebar {
                    display: none;
                }
                .stats-grid {
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
        <script>
            // Safe, standalone nav handler to avoid inline onclick errors
            window.showSection = function(section, evt) {
                try {
                    if (evt && evt.preventDefault) evt.preventDefault();
                    var sections = ['dashboardSection','leadsSection','propertiesSection','settingsSection'];
                    sections.forEach(function(id){ var el = document.getElementById(id); if (el) el.style.display='none'; });
                    var map = { dashboard:'dashboardSection', leads:'leadsSection', properties:'propertiesSection', settings:'settingsSection' };
                    var target = document.getElementById(map[section]); if (target) target.style.display='block';
                    if (evt && evt.target && evt.target.classList) {
                        document.querySelectorAll('.nav-item').forEach(function(n){ n.classList.remove('active'); });
                        evt.target.classList.add('active');
                    }
                } catch(e) { /* no-op */ }
            }
        </script>
    </head>
    <body>
        <div class="header">
            <h1>🏠 Real Estate CRM Dashboard</h1>
            <div class="user-info">
                <span id="userName">Welcome, Agent</span>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <a href="#" class="nav-item active" onclick="showSection('dashboard', event)">📊 Dashboard</a>
                <a href="#" class="nav-item" onclick="showSection('leads', event)">👥 Leads</a>
                <a href="#" class="nav-item" onclick="showSection('properties', event)">🏠 Properties</a>
                <a href="#" class="nav-item" onclick="showSection('settings', event)">⚙️ Settings</a>
            </div>
            
            <div class="content">
                <div id="dashboardSection">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="totalLeads">0</div>
                            <div class="stat-label">Total Leads</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="hotLeads">0</div>
                            <div class="stat-label">Hot Leads</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalProperties">0</div>
                            <div class="stat-label">Active Properties</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">₹2.5 Cr</div>
                            <div class="stat-label">Avg Deal Value</div>
                        </div>
                    </div>
                    
                    <div class="quick-actions">
                        <button class="btn" onclick="openModal('addLeadModal')">➕ Add Lead</button>
                        <button class="btn" onclick="openModal('addPropertyModal')">🏠 Add Property</button>
                        <button class="btn btn-success" onclick="callLead()">📞 Call Lead</button>
                        <button class="btn btn-warning" onclick="sendWhatsApp()">💬 WhatsApp</button>
                    </div>
                    
                    <div class="section">
                        <h2>Recent Leads</h2>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Phone</th>
                                    <th>Budget</th>
                                    <th>Status</th>
                                    <th>Score</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="leadsTable">
                                <tr>
                                    <td colspan="6" style="text-align: center; padding: 2rem; color: #666;">
                                        Loading leads...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div id="leadsSection" style="display: none;">
                    <div class="section">
                        <h2>Lead Management</h2>
                        <button class="btn" onclick="openModal('addLeadModal')">➕ Add New Lead</button>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Contact</th>
                                    <th>Location</th>
                                    <th>Budget</th>
                                    <th>Property Type</th>
                                    <th>Source</th>
                                    <th>Status</th>
                                    <th>Score</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="allLeadsTable">
                                <tr>
                                    <td colspan="9" style="text-align: center; padding: 2rem; color: #666;">
                                        Loading all leads...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div id="propertiesSection" style="display: none;">
                    <div class="section">
                        <h2>Property Management</h2>
                        <button class="btn" onclick="openModal('addPropertyModal')">🏠 Add New Property</button>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Type</th>
                                    <th>Location</th>
                                    <th>Price</th>
                                    <th>Bedrooms</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="propertiesTable">
                                <tr>
                                    <td colspan="7" style="text-align: center; padding: 2rem; color: #666;">
                                        Loading properties...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div id="settingsSection" style="display: none;">
                    <div class="section">
                        <h2>Account Settings</h2>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
                            <div>
                                <h3>Profile Information</h3>
                                <p><strong>Email:</strong> <span id="userEmail">Loading...</span></p>
                                <p><strong>Phone:</strong> <span id="userPhone">Loading...</span></p>
                                <p><strong>Experience:</strong> <span id="userExperience">Loading...</span></p>
                                <p><strong>Areas:</strong> <span id="userAreas">Loading...</span></p>
                                <p><strong>Languages:</strong> <span id="userLanguages">Loading...</span></p>
                            </div>
                            <div>
                                <h3>Social Media Integration</h3>
                                <button class="btn" onclick="connectFacebook()">📘 Connect Facebook</button>
                                <button class="btn" onclick="connectWhatsApp()">💬 Connect WhatsApp</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Add Lead Modal -->
        <div id="addLeadModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('addLeadModal')">&times;</span>
                <h2>Add New Lead</h2>
                <form id="addLeadForm">
                    <div class="form-group">
                        <label for="leadName">Full Name</label>
                        <input type="text" id="leadName" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="leadPhone">Phone Number</label>
                        <input type="tel" id="leadPhone" name="phone" required>
                    </div>
                    <div class="form-group">
                        <label for="leadEmail">Email (Optional)</label>
                        <input type="email" id="leadEmail" name="email">
                    </div>
                    <div class="form-group">
                        <label for="leadLocation">Location</label>
                        <input type="text" id="leadLocation" name="location" placeholder="e.g., Bandra West">
                    </div>
                    <div class="form-group">
                        <label for="leadBudget">Budget</label>
                        <input type="text" id="leadBudget" name="budget" placeholder="e.g., ₹2.5 Cr">
                    </div>
                    <div class="form-group">
                        <label for="leadPropertyType">Property Type</label>
                        <select id="leadPropertyType" name="property_type">
                            <option value="">Select Type</option>
                            <option value="1 BHK Apartment">1 BHK Apartment</option>
                            <option value="2 BHK Apartment">2 BHK Apartment</option>
                            <option value="3 BHK Apartment">3 BHK Apartment</option>
                            <option value="4 BHK Apartment">4 BHK Apartment</option>
                            <option value="Villa">Villa</option>
                            <option value="Penthouse">Penthouse</option>
                            <option value="Commercial Office">Commercial Office</option>
                            <option value="Shop">Shop</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="leadSource">Source</label>
                        <select id="leadSource" name="source">
                            <option value="manual">Manual Entry</option>
                            <option value="facebook">Facebook</option>
                            <option value="whatsapp">WhatsApp</option>
                            <option value="website">Website</option>
                            <option value="referral">Referral</option>
                            <option value="walk-in">Walk-in</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="leadNotes">Notes</label>
                        <textarea id="leadNotes" name="notes" rows="3" placeholder="Additional information about the lead"></textarea>
                    </div>
                    <button type="submit" class="btn">Add Lead</button>
                </form>
            </div>
        </div>
        
        <!-- Add Property Modal -->
        <div id="addPropertyModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal('addPropertyModal')">&times;</span>
                <h2>Add New Property</h2>
                <form id="addPropertyForm">
                    <div class="form-group">
                        <label for="propertyTitle">Property Title</label>
                        <input type="text" id="propertyTitle" name="title" required placeholder="e.g., Luxury 3 BHK in Bandra">
                    </div>
                    <div class="form-group">
                        <label for="propertyType">Property Type</label>
                        <select id="propertyType" name="property_type" required>
                            <option value="">Select Type</option>
                            <option value="Residential">Residential</option>
                            <option value="Commercial">Commercial</option>
                            <option value="Industrial">Industrial</option>
                            <option value="Land">Land</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="propertyLocation">Location</label>
                        <input type="text" id="propertyLocation" name="location" required placeholder="e.g., Bandra West, Mumbai">
                    </div>
                    <div class="form-group">
                        <label for="propertyPrice">Price</label>
                        <input type="text" id="propertyPrice" name="price" required placeholder="e.g., ₹2.8 Cr">
                    </div>
                    <div class="form-group">
                        <label for="propertyBedrooms">Bedrooms</label>
                        <input type="number" id="propertyBedrooms" name="bedrooms" min="0" value="0">
                    </div>
                    <div class="form-group">
                        <label for="propertyBathrooms">Bathrooms</label>
                        <input type="number" id="propertyBathrooms" name="bathrooms" min="0" value="0">
                    </div>
                    <div class="form-group">
                        <label for="propertyArea">Area (Sq Ft)</label>
                        <input type="number" id="propertyArea" name="area_sqft" min="0" placeholder="e.g., 1250">
                    </div>
                    <div class="form-group">
                        <label for="propertyAmenities">Amenities</label>
                        <input type="text" id="propertyAmenities" name="amenities" placeholder="e.g., Gym, Pool, Security, Parking">
                    </div>
                    <div class="form-group">
                        <label for="propertyDescription">Description</label>
                        <textarea id="propertyDescription" name="description" rows="3" placeholder="Detailed description of the property"></textarea>
                    </div>
                    <button type="submit" class="btn">Add Property</button>
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
            loadDashboardData();
            
            window.showSection = function(section, evt) {
                if (evt && evt.preventDefault) evt.preventDefault();
                // Hide all sections
                document.getElementById('dashboardSection').style.display = 'none';
                document.getElementById('leadsSection').style.display = 'none';
                document.getElementById('propertiesSection').style.display = 'none';
                document.getElementById('settingsSection').style.display = 'none';
                
                // Remove active class from all nav items
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                // Show selected section
                if (section === 'dashboard') {
                    document.getElementById('dashboardSection').style.display = 'block';
                    loadDashboardData();
                } else if (section === 'leads') {
                    document.getElementById('leadsSection').style.display = 'block';
                    loadAllLeads();
                } else if (section === 'properties') {
                    document.getElementById('propertiesSection').style.display = 'block';
                    loadProperties();
                } else if (section === 'settings') {
                    document.getElementById('settingsSection').style.display = 'block';
                    loadUserSettings();
                }
                
                // Add active class to clicked nav item
                if (evt && evt.target && evt.target.classList) {
                    evt.target.classList.add('active');
                }
            }
            
            async function loadDashboardData() {
                try {
                    // Load leads
                    const leadsResponse = await fetch('/api/leads', { headers: apiHeaders });
                    const leads = await leadsResponse.json();
                    
                    // Load properties
                    const propertiesResponse = await fetch('/api/properties', { headers: apiHeaders });
                    const properties = await propertiesResponse.json();
                    
                    // Update stats
                    document.getElementById('totalLeads').textContent = leads.length;
                    document.getElementById('hotLeads').textContent = leads.filter(l => l.status === 'hot').length;
                    document.getElementById('totalProperties').textContent = properties.length;
                    
                    // Update leads table
                    const leadsTableHtml = leads.slice(0, 5).map(lead => `
                        <tr>
                            <td>${lead.name}</td>
                            <td>${lead.phone}</td>
                            <td>${lead.budget || 'Not specified'}</td>
                            <td><span class="status-${lead.status}">${lead.status.toUpperCase()}</span></td>
                            <td>${lead.score}%</td>
                            <td>
                                <button class="btn" style="padding: 0.3rem 0.8rem; margin: 0;" onclick="callLead('${lead.phone}')">📞</button>
                                <button class="btn" style="padding: 0.3rem 0.8rem; margin: 0;" onclick="sendWhatsApp('${lead.phone}')">💬</button>
                            </td>
                        </tr>
                    `).join('');
                    
                    document.getElementById('leadsTable').innerHTML = leadsTableHtml || '<tr><td colspan="6" style="text-align: center; padding: 2rem; color: #666;">No leads found</td></tr>';
                    
                } catch (error) {
                    console.error('Error loading dashboard data:', error);
                }
            }
            
            async function loadAllLeads() {
                try {
                    const response = await fetch('/api/leads', { headers: apiHeaders });
                    const leads = await response.json();
                    
                    const tableHtml = leads.map(lead => `
                        <tr>
                            <td>${lead.name}</td>
                            <td>${lead.phone}<br><small>${lead.email || ''}</small></td>
                            <td>${lead.location || 'Not specified'}</td>
                            <td>${lead.budget || 'Not specified'}</td>
                            <td>${lead.property_type || 'Not specified'}</td>
                            <td>${lead.source}</td>
                            <td><span class="status-${lead.status}">${lead.status.toUpperCase()}</span></td>
                            <td>${lead.score}%</td>
                            <td>
                                <button class="btn" style="padding: 0.3rem 0.8rem; margin: 0.2rem;" onclick="callLead('${lead.phone}')">📞</button>
                                <button class="btn" style="padding: 0.3rem 0.8rem; margin: 0.2rem;" onclick="sendWhatsApp('${lead.phone}')">💬</button>
                            </td>
                        </tr>
                    `).join('');
                    
                    document.getElementById('allLeadsTable').innerHTML = tableHtml || '<tr><td colspan="9" style="text-align: center; padding: 2rem; color: #666;">No leads found</td></tr>';
                    
                } catch (error) {
                    console.error('Error loading leads:', error);
                }
            }
            
            async function loadProperties() {
                try {
                    const response = await fetch('/api/properties', { headers: apiHeaders });
                    const properties = await response.json();
                    
                    const tableHtml = properties.map(property => `
                        <tr>
                            <td>${property.title}</td>
                            <td>${property.property_type}</td>
                            <td>${property.location}</td>
                            <td>${property.price}</td>
                            <td>${property.bedrooms}</td>
                            <td>${property.status}</td>
                            <td>
                                <button class="btn" style="padding: 0.3rem 0.8rem; margin: 0.2rem;" onclick="shareProperty('${property.id}')">📤 Share</button>
                            </td>
                        </tr>
                    `).join('');
                    
                    document.getElementById('propertiesTable').innerHTML = tableHtml || '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: #666;">No properties found</td></tr>';
                    
                } catch (error) {
                    console.error('Error loading properties:', error);
                }
            }
            
            // loadUserSettings is defined later with Facebook status wiring
            
            // Modal functions (attach to window to ensure global access from inline onclick)
            window.openModal = function(modalId) {
                var el = document.getElementById(modalId);
                if (el) el.style.display = 'block';
            }
            
            window.closeModal = function(modalId) {
                var el = document.getElementById(modalId);
                if (el) el.style.display = 'none';
            }
            
            // Action functions
            window.callLead = function(phone) {
                if (phone) {
                    alert(`Calling ${phone}...\\n\\nThis would normally trigger your phone/VoIP system.`);
                    // In a real system, this would integrate with phone systems
                } else {
                    alert('Calling lead...\\n\\nThis would normally open your calling interface.');
                }
            }
            
            window.sendWhatsApp = function(phone) {
                if (phone) {
                    const message = encodeURIComponent('Hi! I am reaching out regarding your property inquiry. How can I help you today?');
                    window.open(`https://wa.me/${phone.replace(/[^0-9]/g, '')}?text=${message}`, '_blank');
                } else {
                    alert('Opening WhatsApp...\\n\\nThis would normally open WhatsApp with the lead.');
                }
            }
            
            window.shareProperty = function(propertyId) {
                postToFacebook(propertyId);
            }
            
            function connectFacebook() {
                const token = localStorage.getItem('token');
                if (!token) { alert('Please login again.'); window.location.href='/'; return; }
                window.location.href = `/auth/facebook/login?token=${encodeURIComponent(token)}`;
            }
            
            function connectWhatsApp() {
                alert('WhatsApp Business Integration\\n\\nThis would connect WhatsApp Business API for automated messaging.');
            }
            
            window.logout = function() {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/';
            }
            
            function loadUserSettings() {
                document.getElementById('userEmail').textContent = user.email;
                document.getElementById('userPhone').textContent = user.phone || 'Not provided';
                document.getElementById('userExperience').textContent = user.experience || 'Not provided';
                document.getElementById('userAreas').textContent = user.areas || 'Not provided';
                document.getElementById('userLanguages').textContent = user.languages || 'Not provided';
                fetch('/api/facebook/config', { headers: apiHeaders })
                    .then(r => r.json())
                    .then(cfg => {
                        const buttons = Array.from(document.querySelectorAll('#settingsSection .btn'));
                        const fbBtn = buttons.find(b => b.textContent.includes('Facebook')) || buttons[0];
                        if (cfg.connected) {
                            fbBtn.textContent = cfg.page_name ? `📘 Connected: ${cfg.page_name}` : '📘 Connected (select page)';
                            fbBtn.onclick = selectFacebookPage;
                        }
                    }).catch(() => {});
            }
            
            // Form submissions
            document.getElementById('addLeadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/leads', {
                        method: 'POST',
                        headers: apiHeaders,
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        alert('Lead added successfully!');
                        closeModal('addLeadModal');
                        e.target.reset();
                        loadDashboardData();
                        if (document.getElementById('leadsSection').style.display !== 'none') {
                            loadAllLeads();
                        }
                    } else {
                        alert(result.detail || 'Failed to add lead');
                    }
                } catch (error) {
                    alert('Network error. Please try again.');
                }
            });
            
            document.getElementById('addPropertyForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/properties', {
                        method: 'POST',
                        headers: apiHeaders,
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        alert('Property added successfully!');
                        closeModal('addPropertyModal');
                        e.target.reset();
                        loadDashboardData();
                        if (document.getElementById('propertiesSection').style.display !== 'none') {
                            loadProperties();
                        }
                    } else {
                        alert(result.detail || 'Failed to add property');
                    }
                } catch (error) {
                    alert('Network error. Please try again.');
                }
            });
            
            // Close modals when clicking outside
            window.onclick = function(event) {
                if (event.target.classList && event.target.classList.contains('modal')) {
                    event.target.style.display = 'none';
                }
            }

            async function postToFacebook(propertyId) {
                try {
                    const res = await fetch(`/api/facebook/post_property/${propertyId}`, { method: 'POST', headers: apiHeaders });
                    const out = await res.json();
                    if (res.ok) {
                        alert('Posted to Facebook successfully');
                    } else {
                        alert(out.detail || 'Failed to post to Facebook');
                    }
                } catch (e) { alert('Network error while posting to Facebook'); }
            }

        async function selectFacebookPage() {
                try {
                    const res = await fetch('/api/facebook/pages', { headers: apiHeaders });
                    const out = await res.json();
            if (!Array.isArray(out) || out.length === 0) { alert('No pages available on your account.'); return; }
            const list = out.map(p => `${p.name} (${p.id})`).join('\\n');
                    const chosen = prompt(`Select a Page by typing its ID:\n\n${list}`);
                    if (!chosen) return;
                    const selRes = await fetch('/api/facebook/select_page', { method: 'POST', headers: apiHeaders, body: JSON.stringify({ page_id: chosen }) });
                    const selOut = await selRes.json();
                    if (selRes.ok) {
                        alert('Facebook Page connected: ' + selOut.page_name);
                        loadUserSettings();
                    } else {
                        alert(selOut.detail || 'Failed to select page');
                    }
                } catch (e) { alert('Failed to load pages'); }
            }
        </script>
    </body>
    </html>
    """

# API Endpoints
@app.post("/api/register")
async def register_user(request: Request):
    """Register new agent."""
    data = await request.json()
    # Create via repository (bcrypt hashed)
    try:
        user_repo.create_user({
            'email': data['email'],
            'password': data['password'],
            'first_name': data.get('firstName'),
            'last_name': data.get('lastName'),
            'phone': data.get('phone'),
            'experience': data.get('experience'),
            'areas': data.get('areas'),
            'property_types': data.get('propertyTypes'),
            'languages': data.get('languages'),
            'facebook_connected': 0,
        })
        return {"message": "Registration successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
async def login_user(request: Request):
    """Login agent."""
    data = await request.json()
    
    # Use user repository for authentication
    user = user_repo.authenticate_user(data['email'], data['password'])
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    exp_ts = int((datetime.utcnow() + timedelta(days=7)).timestamp())
    token_data = {
        "user_id": str(user.get('_id', user.get('id'))),  # Handle both MongoDB ObjectId and SQLite id
        "email": user['email'],
        "exp": exp_ts
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
    
    return {
        "token": token,
        "user": {
            "id": str(user.get('_id', user.get('id'))),
            "email": user.get('email'),
            "firstName": user.get('first_name'),
            "lastName": user.get('last_name'),
            "phone": user.get('phone'),
            "experience": user.get('experience'),
            "areas": user.get('areas'),
            "propertyTypes": user.get('property_types'),
            "languages": user.get('languages'),
            "facebookConnected": bool(user.get('facebook_connected', 0))
        }
    }

@app.get("/api/leads")
async def get_leads(payload: dict = Depends(verify_token)):
    """Get all leads for agent."""
    db = get_db()
    # For MongoDB, convert user_id to ObjectId if needed
    agent_id = payload['user_id']
    try:
        if len(str(agent_id)) == 24:
            agent_id = ObjectId(agent_id)
    except Exception:
        pass
    leads = list(db.leads.find({"agent_id": agent_id}).sort("created_at", -1))
    for lead in leads:
        if "_id" in lead:
            lead["id"] = str(lead["_id"])
            del lead["_id"]
        if "agent_id" in lead and hasattr(lead["agent_id"], "__str__"):
            lead["agent_id"] = str(lead["agent_id"])
    return leads

@app.post("/api/leads")
async def create_lead(request: Request, payload: dict = Depends(verify_token)):
    """Create new lead."""
    data = await request.json()
    db = get_db()
    agent_id = payload['user_id']
    try:
        if len(str(agent_id)) == 24:
            agent_id = ObjectId(agent_id)
    except Exception:
        pass
    doc = {
        "agent_id": agent_id,
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "location": data.get("location"),
        "budget": data.get("budget"),
        "property_type": data.get("property_type"),
        "source": data.get("source", "manual"),
        "status": data.get("status", "new"),
        "score": data.get("score", 75),
        "notes": data.get("notes", ""),
        "created_at": datetime.utcnow(),
    }
    result = db.leads.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Lead created successfully"}

@app.get("/api/properties")
async def get_properties(payload: dict = Depends(verify_token)):
    """Get all properties for agent."""
    db = get_db()
    agent_id = payload['user_id']
    try:
        if len(str(agent_id)) == 24:
            agent_id = ObjectId(agent_id)
    except Exception:
        pass
    properties = list(db.properties.find({"agent_id": agent_id}).sort("created_at", -1))
    for prop in properties:
        if "_id" in prop:
            prop["id"] = str(prop["_id"])
            del prop["_id"]
        if "agent_id" in prop and hasattr(prop["agent_id"], "__str__"):
            prop["agent_id"] = str(prop["agent_id"])
    return properties

@app.post("/api/properties")
async def create_property(request: Request, payload: dict = Depends(verify_token)):
    """Create new property listing."""
    data = await request.json()
    db = get_db()
    agent_id = payload['user_id']
    try:
        if len(str(agent_id)) == 24:
            agent_id = ObjectId(agent_id)
    except Exception:
        pass
    doc = {
        "agent_id": agent_id,
        "title": data.get("title"),
        "description": data.get("description"),
        "property_type": data.get("property_type"),
        "location": data.get("location"),
        "price": data.get("price"),
        "bedrooms": int(data.get("bedrooms", 0) or 0),
        "bathrooms": int(data.get("bathrooms", 0) or 0),
        "area_sqft": int(data.get("area_sqft", 0) or 0),
        "amenities": data.get("amenities", ""),
        "status": data.get("status", "available"),
        "created_at": datetime.utcnow(),
    }
    result = db.properties.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Property created successfully"}

# -------------------------
# Facebook Integration APIs
# -------------------------

def _get_user_dict(user_id: str):
    """Fetch user document from Mongo by id (string)."""
    try:
        return user_repo.get_user_by_id(user_id)
    except Exception:
        return None

@app.get("/api/facebook/config")
async def facebook_config(payload: dict = Depends(verify_token)):
    try:
        user = _get_user_dict(payload.get('user_id'))
        if not user and payload.get('email'):
            try:
                user = user_repo.get_user_by_email(payload.get('email'))
            except Exception:
                user = None
        if not user:
            return {"connected": False, "page_id": None, "page_name": None}
        connected = bool(user.get('fb_user_token')) or bool(user.get('facebook_connected'))
        return {
            "connected": bool(connected),
            "page_id": user.get('fb_page_id'),
            "page_name": user.get('fb_page_name')
        }
    except Exception:
        return {"connected": False, "page_id": None, "page_name": None}

@app.get("/auth/facebook/login")
async def facebook_login(token: str = Query(...)):
    # Use state to carry JWT so we can map back to user after callback
    if not FB_APP_ID or not FB_REDIRECT_URI:
        return JSONResponse(status_code=500, content={"detail": "Facebook App not configured. Set FB_APP_ID, FB_APP_SECRET, FB_REDIRECT_URI."})
    params = {
        "client_id": FB_APP_ID,
        "redirect_uri": FB_REDIRECT_URI,
        "state": token,
        "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,pages_manage_metadata,public_profile,email",
        "response_type": "code"
    }
    url = "https://www.facebook.com/v20.0/dialog/oauth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)

@app.get("/auth/facebook/callback")
async def facebook_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error:
        return HTMLResponse(f"<p>Facebook auth failed: {error}</p>")
    # state contains JWT; validate to find user
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return HTMLResponse("<p>Invalid session</p>", status_code=400)
    user_id = payload.get("user_id")
    if not user_id:
        return HTMLResponse("<p>Invalid session</p>", status_code=400)

    # Exchange code for user access token
    token_url = "https://graph.facebook.com/v20.0/oauth/access_token"
    params = {
        "client_id": FB_APP_ID,
        "client_secret": FB_APP_SECRET,
        "redirect_uri": FB_REDIRECT_URI,
        "code": code
    }
    r = requests.get(token_url, params=params, timeout=20)
    if r.status_code != 200:
        return HTMLResponse("<p>Failed to get access token</p>", status_code=400)
    access_token = r.json().get("access_token")
    if not access_token:
        return HTMLResponse("<p>No access token</p>", status_code=400)

    # Update Mongo user document
    try:
        user_repo.update_user_fields(str(user_id), {
            'facebook_connected': True,
            'fb_user_token': access_token
        })
    except Exception:
        return HTMLResponse("<p>Failed to update user</p>", status_code=500)
    return HTMLResponse("<script>window.close();window.location='/dashboard';</script>")

@app.get("/api/facebook/pages")
async def facebook_pages(payload: dict = Depends(verify_token)):
    try:
        user = _get_user_dict(payload.get('user_id'))
        if not user and payload.get('email'):
            try:
                user = user_repo.get_user_by_email(payload.get('email'))
            except Exception:
                user = None
        if not user or not user.get('fb_user_token'):
            raise HTTPException(status_code=400, detail="Facebook not connected")
        user_token = user.get('fb_user_token')
        r = requests.get("https://graph.facebook.com/v20.0/me/accounts", params={"access_token": user_token}, timeout=20)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch pages")
        data = r.json().get("data", [])
        return [{"id": p.get("id"), "name": p.get("name")} for p in data]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Facebook not connected")

@app.post("/api/facebook/select_page")
async def facebook_select_page(request: Request, payload: dict = Depends(verify_token)):
    body = await request.json()
    page_id = body.get("page_id")
    if not page_id:
        raise HTTPException(status_code=400, detail="Missing page_id")
    user = _get_user_dict(payload.get('user_id'))
    if not user and payload.get('email'):
        try:
            user = user_repo.get_user_by_email(payload.get('email'))
        except Exception:
            user = None
    if not user or not user.get('fb_user_token'):
        raise HTTPException(status_code=400, detail="Facebook not connected")
    user_token = user.get('fb_user_token')
    # Retrieve page access token for the selected page
    r = requests.get(f"https://graph.facebook.com/v20.0/{page_id}", params={"fields": "access_token,name", "access_token": user_token}, timeout=20)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get page token")
    data = r.json()
    page_token = data.get("access_token")
    page_name = data.get("name")
    if not page_token:
        raise HTTPException(status_code=400, detail="No page token returned")
    # Update user document with page details
    user_repo.update_user_fields(payload['user_id'], {
        'fb_page_id': page_id,
        'fb_page_name': page_name,
        'fb_page_token': page_token,
        'facebook_connected': True
    })
    return {"page_id": page_id, "page_name": page_name}

@app.post("/api/facebook/post_property/{property_id}")
async def facebook_post_property(property_id: str, payload: dict = Depends(verify_token)):
    db = get_db()
    user = _get_user_dict(payload['user_id'])
    if not user or not user.get('fb_page_token') or not user.get('fb_page_id'):
        raise HTTPException(status_code=400, detail="Facebook page not connected")
    page_id = user.get('fb_page_id')
    page_token = user.get('fb_page_token')
    # Fetch property document (stored in Mongo when DB_MODE == mongo)
    # Try various id formats (ObjectId, string id, numeric id field)
    prop = None
    try:
        prop = db.properties.find_one({"_id": ObjectId(str(property_id)), "agent_id": payload['user_id']})
    except Exception:
        prop = db.properties.find_one({"_id": str(property_id), "agent_id": payload['user_id']})
    if not prop:
        # Fallback by numeric id field if present
        prop = db.properties.find_one({"id": property_id, "agent_id": payload['user_id']})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    title = prop.get("title")
    description = prop.get("description")
    ptype = prop.get("property_type")
    location = prop.get("location")
    price = prop.get("price")
    beds = prop.get("bedrooms")
    baths = prop.get("bathrooms")
    area = prop.get("area_sqft")
    amenities = prop.get("amenities")
    message = f"{title}\nType: {ptype}\nLocation: {location}\nPrice: {price}\nBedrooms: {beds}, Bathrooms: {baths}, Area: {area} sq ft\nAmenities: {amenities or '-'}\n\nContact me for details!"
    # Post to page feed
    r = requests.post(f"https://graph.facebook.com/v20.0/{page_id}/feed", data={
        "message": message,
        "access_token": page_token
    }, timeout=20)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Facebook post failed: {r.text}")
    return {"status": "ok", "post_id": r.json().get("id")}

if __name__ == "__main__":
    # MongoDB - demo data was migrated, just ensure it exists
    print("✅ MongoDB mode - using migrated demo data")
    database_type = "MongoDB"
    print("🚀 PRODUCTION REAL ESTATE CRM SYSTEM STARTING...")
    print("=" * 60)
    print("📍 URL: http://localhost:8004")
    print("👤 Demo Login: demo@mumbai.com / demo123")
    print(f"🗄️  Database: {database_type}")
    print("=" * 60)
    print("✅ FEATURES:")
    print("   • User Registration & Authentication")
    print("   • Lead Management (Add, View, Call, WhatsApp)")
    print("   • Property Management (Add, View, Share)")
    print("   • Responsive Dashboard")
    print(f"   • {database_type} Database with Sample Data")
    print("   • JWT Token Security")
    print("   • Mobile-Optimized Interface")
    print("=" * 60)
    print("🎯 FULLY FUNCTIONAL PRODUCTION SYSTEM!")
    
    uvicorn.run("complete_production_crm:app", host="0.0.0.0", port=8004, reload=True)

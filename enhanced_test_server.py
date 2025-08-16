"""
Enhanced Test Server with Issue Fixes
Includes demo endpoints and improved authentication
"""
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import logging
import asyncio
import os
import sys

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Real Estate CRM - Enhanced Test Server",
    description="Enhanced server with demo endpoints and fixed authentication",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
try:
    from api.endpoints.simple_auth import router as auth_router
    from api.endpoints.demo_endpoints import router as demo_router
    
    app.include_router(auth_router)
    app.include_router(demo_router)
    
    logger.info("✅ Successfully loaded authentication and demo endpoints")
    
except ImportError as e:
    logger.error(f"❌ Failed to import routers: {e}")
    
    # Fallback: create minimal endpoints
    @app.post("/api/login")
    async def fallback_login(request: Request):
        body = await request.json()
        if body.get("email") == "demo@mumbai.com" and body.get("password") == "demo123":
            return {
                "token": "demo-token-12345",
                "user": {"email": "demo@mumbai.com", "name": "Demo User"},
                "success": True
            }
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    @app.get("/api/demo/status")
    async def fallback_status():
        return {"status": "running", "message": "Fallback endpoints active"}

# Static files
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

templates_path = Path("templates")

# Routes
@app.get("/")
async def home():
    """Home page"""
    template_file = templates_path / "index.html"
    if template_file.exists():
        return FileResponse(template_file)
    else:
        return HTMLResponse("""
        <html>
        <head><title>Real Estate CRM</title></head>
        <body>
            <h1>Real Estate CRM - Enhanced Test Server</h1>
            <p>Server is running! Go to <a href="/login">Login Page</a></p>
            <ul>
                <li><a href="/login">Login</a></li>
                <li><a href="/dashboard">Dashboard</a></li>
                <li><a href="/api/demo/status">API Status</a></li>
            </ul>
        </body>
        </html>
        """)

@app.get("/login")
async def login_page():
    """Login page"""
    template_file = templates_path / "login.html"
    if template_file.exists():
        return FileResponse(template_file)
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Real Estate CRM</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100">
            <div class="min-h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-md w-96">
                    <h2 class="text-2xl font-bold mb-6">Login</h2>
                    <form id="loginForm" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium">Email</label>
                            <input type="email" id="email" value="demo@mumbai.com" 
                                   class="w-full p-2 border rounded">
                        </div>
                        <div>
                            <label class="block text-sm font-medium">Password</label>
                            <input type="password" id="password" value="demo123"
                                   class="w-full p-2 border rounded">
                        </div>
                        <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded">
                            Login
                        </button>
                    </form>
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
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email, password})
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        localStorage.setItem('authToken', data.token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        window.location.href = '/dashboard';
                    } else {
                        alert('Login failed: ' + data.message);
                    }
                } catch (error) {
                    alert('Login error: ' + error.message);
                }
            });
            </script>
        </body>
        </html>
        """)

@app.get("/dashboard")
async def dashboard_page():
    """Dashboard page"""
    template_file = templates_path / "dashboard.html"
    if template_file.exists():
        return FileResponse(template_file)
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Real Estate CRM</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50">
            <div class="min-h-screen">
                <nav class="bg-white shadow-sm border-b">
                    <div class="max-w-7xl mx-auto px-4">
                        <div class="flex justify-between h-16">
                            <div class="flex space-x-8">
                                <a href="#" class="nav-item flex items-center px-3 py-2 text-sm font-medium">
                                    📊 Dashboard
                                </a>
                                <a href="#" class="nav-item flex items-center px-3 py-2 text-sm font-medium">
                                    👥 Leads  
                                </a>
                                <a href="#" class="nav-item flex items-center px-3 py-2 text-sm font-medium">
                                    🤖 Smart Properties
                                </a>
                                <a href="#" class="nav-item flex items-center px-3 py-2 text-sm font-medium">
                                    ⚙️ Settings
                                </a>
                            </div>
                            <div class="flex items-center">
                                <span id="userName" class="text-sm text-gray-700">Demo User</span>
                            </div>
                        </div>
                    </div>
                </nav>
                
                <main class="max-w-7xl mx-auto py-6 px-4">
                    <div id="dashboardSection" class="section">
                        <h1 class="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
                        <div id="dashboardContent" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div class="bg-white p-6 rounded-lg shadow">
                                <h3 class="text-lg font-medium">Total Leads</h3>
                                <p class="text-3xl font-bold text-blue-600">Loading...</p>
                            </div>
                            <div class="bg-white p-6 rounded-lg shadow">
                                <h3 class="text-lg font-medium">Properties</h3>
                                <p class="text-3xl font-bold text-green-600">Loading...</p>
                            </div>
                            <div class="bg-white p-6 rounded-lg shadow">
                                <h3 class="text-lg font-medium">API Status</h3>
                                <p class="text-3xl font-bold text-purple-600">Loading...</p>
                            </div>
                        </div>
                    </div>
                    
                    <div id="leadsSection" class="section hidden">
                        <h1 class="text-3xl font-bold text-gray-900 mb-8">Leads Management</h1>
                        <div class="bg-white rounded-lg shadow">
                            <div class="p-6">
                                <button class="bg-blue-500 text-white px-4 py-2 rounded mb-4">
                                    + Add Lead
                                </button>
                                <div id="leadsContent">Loading leads...</div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="smart-propertiesSection" class="section hidden">
                        <h1 class="text-3xl font-bold text-gray-900 mb-8">Smart Properties</h1>
                        <div class="bg-white rounded-lg shadow">
                            <div class="p-6">
                                <button class="bg-green-500 text-white px-4 py-2 rounded mb-4">
                                    + Add Smart Property
                                </button>
                                <div id="propertiesContent">Loading properties...</div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="settingsSection" class="section hidden">
                        <h1 class="text-3xl font-bold text-gray-900 mb-8">Settings</h1>
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-medium mb-4">Account Settings</h3>
                            <div class="space-y-4">
                                <div>
                                    <label class="block text-sm font-medium">Name</label>
                                    <input type="text" value="Demo User" class="w-full p-2 border rounded">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium">Email</label>
                                    <input type="email" value="demo@mumbai.com" class="w-full p-2 border rounded">
                                </div>
                                <button class="bg-blue-500 text-white px-4 py-2 rounded">
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
            
            <script>
            // Navigation functionality
            function showSection(sectionName) {
                // Hide all sections
                document.querySelectorAll('.section').forEach(section => {
                    section.classList.add('hidden');
                });
                
                // Show selected section
                const targetSection = document.getElementById(sectionName + 'Section');
                if (targetSection) {
                    targetSection.classList.remove('hidden');
                }
                
                // Load section data
                loadSectionData(sectionName);
            }
            
            // Add click handlers to navigation
            document.querySelectorAll('.nav-item').forEach((item, index) => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const sections = ['dashboard', 'leads', 'smart-properties', 'settings'];
                    showSection(sections[index]);
                });
            });
            
            // Load data for different sections
            async function loadSectionData(sectionName) {
                const token = localStorage.getItem('authToken');
                const headers = token ? {'Authorization': `Bearer ${token}`} : {};
                
                try {
                    if (sectionName === 'dashboard') {
                        const response = await fetch('/api/demo/dashboard', {headers});
                        const data = await response.json();
                        
                        if (data.success) {
                            document.getElementById('dashboardContent').innerHTML = `
                                <div class="bg-white p-6 rounded-lg shadow">
                                    <h3 class="text-lg font-medium">Total Leads</h3>
                                    <p class="text-3xl font-bold text-blue-600">${data.dashboard.leads.total}</p>
                                </div>
                                <div class="bg-white p-6 rounded-lg shadow">
                                    <h3 class="text-lg font-medium">Properties</h3>
                                    <p class="text-3xl font-bold text-green-600">${data.dashboard.properties.total}</p>
                                </div>
                                <div class="bg-white p-6 rounded-lg shadow">
                                    <h3 class="text-lg font-medium">API Status</h3>
                                    <p class="text-3xl font-bold text-purple-600">✅ Working</p>
                                </div>
                            `;
                        }
                    } else if (sectionName === 'leads') {
                        const response = await fetch('/api/demo/leads', {headers});
                        const data = await response.json();
                        
                        if (data.success) {
                            document.getElementById('leadsContent').innerHTML = data.leads.map(lead => `
                                <div class="border-b py-4">
                                    <h4 class="font-medium">${lead.name}</h4>
                                    <p class="text-sm text-gray-600">${lead.email} | ${lead.phone}</p>
                                    <p class="text-sm"><span class="bg-blue-100 px-2 py-1 rounded">${lead.status}</span></p>
                                </div>
                            `).join('');
                        }
                    } else if (sectionName === 'smart-properties') {
                        const response = await fetch('/api/demo/properties', {headers});
                        const data = await response.json();
                        
                        if (data.success) {
                            document.getElementById('propertiesContent').innerHTML = data.properties.map(prop => `
                                <div class="border-b py-4">
                                    <h4 class="font-medium">${prop.title}</h4>
                                    <p class="text-sm text-gray-600">${prop.location} | ${prop.area}</p>
                                    <p class="text-sm font-bold text-green-600">${prop.price}</p>
                                </div>
                            `).join('');
                        }
                    }
                } catch (error) {
                    console.error('Error loading section data:', error);
                }
            }
            
            // Initialize dashboard
            showSection('dashboard');
            
            // Set user name
            const user = localStorage.getItem('user');
            if (user) {
                const userData = JSON.parse(user);
                document.getElementById('userName').textContent = userData.name || 'Demo User';
            }
            </script>
        </body>
        </html>
        """)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "server": "Enhanced Test Server",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/login",
            "demo_leads": "/api/demo/leads", 
            "demo_properties": "/api/demo/properties",
            "demo_dashboard": "/api/demo/dashboard"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Enhanced Test Server")
    print("🔧 Includes demo endpoints and fixed authentication")
    print("📊 Dashboard: http://localhost:8003/dashboard")
    print("🔐 Login: http://localhost:8003/login")
    print("📡 API Status: http://localhost:8003/api/demo/status")
    
    uvicorn.run(
        "enhanced_test_server:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )

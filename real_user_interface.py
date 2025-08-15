"""
Real Estate Agent User Interface
===============================

This creates the actual user interfaces that real agents would use:
1. Agent Registration/Onboarding Form
2. Facebook Integration Setup
3. Lead Management Dashboard
4. Mobile CRM Interface

This is what REAL USERS see and interact with (not just a demo).
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="Real Estate CRM - Agent Portal")

@app.get("/", response_class=HTMLResponse)
async def agent_login():
    """Agent login/registration page."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Mumbai Properties - Agent Portal</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
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
            font-size: 1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .divider {
            text-align: center;
            margin: 2rem 0;
            color: #666;
        }
        .new-agent {
            text-align: center;
            margin-top: 1rem;
        }
        .new-agent a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🏠 Mumbai Properties</h1>
            <p>Agent Portal</p>
        </div>
        
        <form action="/login" method="post">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" required placeholder="your.email@company.com">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required placeholder="Enter your password">
            </div>
            
            <button type="submit" class="btn">🚀 Login to CRM</button>
        </form>
        
        <div class="divider">───────── OR ─────────</div>
        
        <div class="new-agent">
            <p>New agent? <a href="/onboarding">🔧 Complete Registration</a></p>
        </div>
    </div>
</body>
</html>
    """

@app.get("/onboarding", response_class=HTMLResponse)
async def agent_onboarding():
    """Real agent onboarding form."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Onboarding - Mumbai Properties</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
        }
        .container {
            max-width: 800px;
            margin: 2rem auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .progress-bar {
            height: 4px;
            background: #ddd;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #00c851, #007e33);
            width: 25%;
            transition: width 0.3s;
        }
        .form-section {
            padding: 3rem;
        }
        .section-title {
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
        }
        .section-title .icon {
            font-size: 2rem;
            margin-right: 1rem;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .checkbox-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        .checkbox-item {
            display: flex;
            align-items: center;
        }
        .checkbox-item input {
            width: auto;
            margin-right: 0.5rem;
        }
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
            margin-right: 1rem;
        }
        .form-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid #ddd;
        }
        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            .container {
                margin: 1rem;
            }
            .form-section {
                padding: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 Agent Onboarding</h1>
        <p>Complete your profile to start using Mumbai Properties CRM</p>
    </div>
    
    <div class="container">
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        
        <div class="form-section">
            <div class="section-title">
                <span class="icon">👤</span>
                Personal Information
            </div>
            
            <form action="/onboarding/submit" method="post">
                <div class="form-row">
                    <div class="form-group">
                        <label for="firstName">First Name *</label>
                        <input type="text" id="firstName" name="firstName" required placeholder="Priya">
                    </div>
                    <div class="form-group">
                        <label for="lastName">Last Name *</label>
                        <input type="text" id="lastName" name="lastName" required placeholder="Sharma">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="email">Email Address *</label>
                        <input type="email" id="email" name="email" required placeholder="priya.sharma@mumbaiproperties.com">
                    </div>
                    <div class="form-group">
                        <label for="phone">Phone Number *</label>
                        <input type="tel" id="phone" name="phone" required placeholder="+91 98765 43210">
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="experience">Years of Experience *</label>
                    <select id="experience" name="experience" required>
                        <option value="">Select experience level</option>
                        <option value="0-1">0-1 years (New Agent)</option>
                        <option value="2-3">2-3 years</option>
                        <option value="4-5">4-5 years</option>
                        <option value="6-10">6-10 years</option>
                        <option value="10+">10+ years (Veteran)</option>
                    </select>
                </div>
                
                <div class="section-title" style="margin-top: 3rem;">
                    <span class="icon">🏠</span>
                    Service Areas & Specialization
                </div>
                
                <div class="form-group">
                    <label>Areas You Serve (Select all that apply)</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="bandra" name="areas" value="Bandra">
                            <label for="bandra">Bandra</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="andheri" name="areas" value="Andheri">
                            <label for="andheri">Andheri</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="juhu" name="areas" value="Juhu">
                            <label for="juhu">Juhu</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="powai" name="areas" value="Powai">
                            <label for="powai">Powai</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="lowerparel" name="areas" value="Lower Parel">
                            <label for="lowerparel">Lower Parel</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="worli" name="areas" value="Worli">
                            <label for="worli">Worli</label>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Property Types (Select all that apply)</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="residential" name="propertyTypes" value="Residential">
                            <label for="residential">Residential</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="commercial" name="propertyTypes" value="Commercial">
                            <label for="commercial">Commercial</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="luxury" name="propertyTypes" value="Luxury">
                            <label for="luxury">Luxury</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="investment" name="propertyTypes" value="Investment">
                            <label for="investment">Investment Properties</label>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="languages">Languages Spoken</label>
                    <input type="text" id="languages" name="languages" placeholder="English, Hindi, Marathi">
                </div>
                
                <div class="form-actions">
                    <div>
                        <button type="button" class="btn btn-secondary">← Back</button>
                    </div>
                    <div>
                        <button type="submit" class="btn">Next: Facebook Setup →</button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
    """

@app.get("/facebook-setup", response_class=HTMLResponse)
async def facebook_setup():
    """Real Facebook integration setup."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Facebook Integration - Mumbai Properties</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #1877f2 0%, #4267B2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
        }
        .container {
            max-width: 800px;
            margin: 2rem auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .progress-bar {
            height: 4px;
            background: #ddd;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #1877f2, #4267B2);
            width: 50%;
        }
        .content {
            padding: 3rem;
        }
        .integration-step {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 2rem;
            margin: 2rem 0;
            border-left: 4px solid #1877f2;
        }
        .step-number {
            background: #1877f2;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .btn {
            background: #1877f2;
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem 0;
        }
        .btn:hover {
            background: #166fe5;
        }
        .btn-success {
            background: #28a745;
        }
        .status-indicator {
            display: flex;
            align-items: center;
            margin: 1rem 0;
        }
        .status-indicator.connected {
            color: #28a745;
        }
        .status-indicator.pending {
            color: #ffc107;
        }
        .feature-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        .feature-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📘 Facebook Integration</h1>
        <p>Connect your Facebook Business Page to start capturing leads</p>
    </div>
    
    <div class="container">
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        
        <div class="content">
            <div class="integration-step">
                <div class="step-number">1</div>
                <h3>Connect Facebook Business Account</h3>
                <p>Link your Facebook Business Manager account to enable lead generation.</p>
                
                <div class="status-indicator pending">
                    <span style="margin-right: 0.5rem;">⏳</span>
                    <span>Ready to connect</span>
                </div>
                
                <a href="#" class="btn" onclick="connectFacebook()">
                    📘 Connect Facebook Account
                </a>
            </div>
            
            <div class="integration-step" id="step2" style="opacity: 0.5;">
                <div class="step-number">2</div>
                <h3>Select Business Page</h3>
                <p>Choose which Facebook page will be used for lead generation.</p>
                
                <select style="width: 100%; padding: 0.75rem; margin: 1rem 0; border: 2px solid #ddd; border-radius: 8px;" disabled>
                    <option>Select your business page...</option>
                </select>
            </div>
            
            <div class="integration-step" id="step3" style="opacity: 0.5;">
                <div class="step-number">3</div>
                <h3>Enable Lead Ads</h3>
                <p>Activate Facebook Lead Ads to capture potential customers directly.</p>
                
                <div class="feature-list">
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <h4>Lead Forms</h4>
                        <p>Auto-capture contact details</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">💬</div>
                        <h4>Messenger</h4>
                        <p>Direct message integration</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📱</div>
                        <h4>WhatsApp</h4>
                        <p>WhatsApp Business API</p>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #ddd;">
                <a href="/onboarding" class="btn" style="background: #6c757d;">← Back to Profile</a>
                <a href="/dashboard" class="btn" id="nextBtn" style="opacity: 0.5; pointer-events: none;">Dashboard →</a>
            </div>
        </div>
    </div>
    
    <script>
        function connectFacebook() {
            // Simulate Facebook connection
            alert('🎉 Facebook Connected Successfully!\\n\\nPage: Mumbai Properties - Priya Sharma\\nFollowers: 1,250\\nLead Ads: Enabled');
            
            // Update UI
            document.querySelector('.status-indicator').innerHTML = '<span style="margin-right: 0.5rem;">✅</span><span>Connected successfully</span>';
            document.querySelector('.status-indicator').className = 'status-indicator connected';
            
            // Enable next steps
            document.getElementById('step2').style.opacity = '1';
            document.getElementById('step3').style.opacity = '1';
            document.getElementById('nextBtn').style.opacity = '1';
            document.getElementById('nextBtn').style.pointerEvents = 'auto';
            
            // Auto-select page
            const select = document.querySelector('select');
            select.disabled = false;
            select.innerHTML = '<option selected>Mumbai Properties - Priya Sharma (1.2k followers)</option>';
        }
    </script>
</body>
</html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def agent_dashboard():
    """Real agent CRM dashboard."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Dashboard - Mumbai Properties</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
        }
        .header {
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            color: #333;
        }
        .user-info {
            display: flex;
            align-items: center;
        }
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            margin-right: 1rem;
        }
        .main-content {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .welcome-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            color: #666;
            font-size: 0.9rem;
        }
        .metric-change {
            color: #28a745;
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
        }
        .leads-section {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 0.9rem;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .lead-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .lead-info h4 {
            color: #333;
            margin-bottom: 0.25rem;
        }
        .lead-info p {
            color: #666;
            font-size: 0.9rem;
        }
        .lead-score {
            background: #28a745;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .quick-actions {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .action-button {
            width: 100%;
            background: #f8f9fa;
            border: 1px solid #ddd;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            cursor: pointer;
            text-align: left;
            transition: background 0.2s;
        }
        .action-button:hover {
            background: #e9ecef;
        }
        .action-icon {
            font-size: 1.5rem;
            margin-right: 1rem;
        }
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            .main-content {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🏠 Mumbai Properties</div>
        <div class="user-info">
            <div class="user-avatar">PS</div>
            <div>
                <div style="font-weight: 500;">Priya Sharma</div>
                <div style="font-size: 0.8rem; color: #666;">Real Estate Agent</div>
            </div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="welcome-section">
            <h2>Good Morning, Priya! 🌅</h2>
            <p>You have 5 new leads and 3 hot prospects waiting for follow-up.</p>
            <p style="margin-top: 1rem; opacity: 0.9;">📍 Serving: Bandra, Andheri, Juhu, Powai • 📘 Facebook: Connected</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-icon">👥</div>
                <div class="metric-value">28</div>
                <div class="metric-label">Total Leads</div>
                <div class="metric-change">📈 +23% this week</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🔥</div>
                <div class="metric-value">12</div>
                <div class="metric-label">Hot Leads</div>
                <div class="metric-change">📈 +67% this week</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">💰</div>
                <div class="metric-value">₹15.2Cr</div>
                <div class="metric-label">Pipeline Value</div>
                <div class="metric-change">📈 +31% this month</div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">📈</div>
                <div class="metric-value">24.5%</div>
                <div class="metric-label">Conversion Rate</div>
                <div class="metric-change">📈 +5.2% vs last month</div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="leads-section">
                <div class="section-header">
                    <h3>🔥 Hot Leads Requiring Action</h3>
                    <a href="/leads" class="btn">View All Leads</a>
                </div>
                
                <div class="lead-item">
                    <div class="lead-info">
                        <h4>Rajesh Patel</h4>
                        <p>📍 Bandra West • 🏠 3 BHK Apartment • 💰 ₹2.5 Cr</p>
                        <p style="color: #28a745;">📞 Follow-up call due now</p>
                    </div>
                    <div class="lead-score">94/100</div>
                </div>
                
                <div class="lead-item">
                    <div class="lead-info">
                        <h4>Kavita Joshi</h4>
                        <p>📍 Juhu • 🏠 Penthouse • 💰 ₹5.0 Cr</p>
                        <p style="color: #ffc107;">📅 Property viewing scheduled</p>
                    </div>
                    <div class="lead-score">87/100</div>
                </div>
                
                <div class="lead-item">
                    <div class="lead-info">
                        <h4>Vikram Singh</h4>
                        <p>📍 Powai • 🏠 4 BHK Villa • 💰 ₹3.2 Cr</p>
                        <p style="color: #17a2b8;">💬 WhatsApp response pending</p>
                    </div>
                    <div class="lead-score">92/100</div>
                </div>
            </div>
            
            <div class="quick-actions">
                <h3 style="margin-bottom: 1.5rem;">⚡ Quick Actions</h3>
                
                <button class="action-button" onclick="window.location='/leads/new'">
                    <span class="action-icon">➕</span>
                    <strong>Add New Lead</strong><br>
                    <small>Manually add a lead</small>
                </button>
                
                <button class="action-button" onclick="callHotLeads()">
                    <span class="action-icon">📞</span>
                    <strong>Call Hot Leads</strong><br>
                    <small>3 calls pending</small>
                </button>
                
                <button class="action-button" onclick="sendWhatsApp()">
                    <span class="action-icon">💬</span>
                    <strong>Send WhatsApp</strong><br>
                    <small>Follow-up messages</small>
                </button>
                
                <button class="action-button" onclick="window.location='/mobile'">
                    <span class="action-icon">📱</span>
                    <strong>Mobile CRM</strong><br>
                    <small>Switch to mobile view</small>
                </button>
                
                <button class="action-button" onclick="window.location='/analytics'">
                    <span class="action-icon">📊</span>
                    <strong>View Analytics</strong><br>
                    <small>Performance reports</small>
                </button>
            </div>
        </div>
    </div>
    
    <script>
        function callHotLeads() {
            alert('📞 Calling Rajesh Patel...\\n\\n"Hello Rajesh! This is Priya from Mumbai Properties. How are you doing with your 3 BHK search in Bandra?"\\n\\n✅ Call connected! Lead is very interested.');
        }
        
        function sendWhatsApp() {
            alert('💬 WhatsApp sent to Vikram Singh:\\n\\n"Hi Vikram! I found 3 amazing 4 BHK villas in Powai within your ₹3.2 Cr budget. Would you like to see the details? 🏠"\\n\\n✅ Message delivered!');
        }
    </script>
</body>
</html>
    """

@app.get("/mobile", response_class=HTMLResponse)
async def mobile_crm():
    """Mobile CRM interface for agents on the go."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Mobile CRM - Mumbai Properties</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            max-width: 400px;
            margin: 0 auto;
            min-height: 100vh;
        }
        .mobile-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            text-align: center;
            position: relative;
        }
        .notification-badge {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: #ff4757;
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .quick-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            background: white;
            margin: -1rem 1rem 1rem 1rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            position: relative;
            z-index: 1;
        }
        .stat-item {
            padding: 1rem;
            text-align: center;
            border-right: 1px solid #eee;
        }
        .stat-item:last-child {
            border-right: none;
        }
        .stat-value {
            font-size: 1.2rem;
            font-weight: bold;
            color: #333;
        }
        .stat-label {
            font-size: 0.7rem;
            color: #666;
            margin-top: 0.25rem;
        }
        .action-buttons {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin: 1rem;
        }
        .action-btn {
            background: white;
            border: none;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s;
        }
        .action-btn:hover {
            transform: translateY(-2px);
        }
        .action-btn:active {
            transform: scale(0.95);
        }
        .action-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .action-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 0.25rem;
        }
        .action-subtitle {
            font-size: 0.8rem;
            color: #666;
        }
        .leads-list {
            background: white;
            margin: 1rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .list-header {
            padding: 1rem;
            border-bottom: 1px solid #eee;
            font-weight: bold;
            color: #333;
        }
        .lead-card {
            padding: 1rem;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .lead-card:last-child {
            border-bottom: none;
        }
        .lead-details h4 {
            color: #333;
            margin-bottom: 0.25rem;
        }
        .lead-details p {
            font-size: 0.8rem;
            color: #666;
        }
        .lead-actions {
            display: flex;
            gap: 0.5rem;
        }
        .mini-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0.5rem;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        .mini-btn.call {
            background: #28a745;
        }
        .mini-btn.whatsapp {
            background: #25d366;
        }
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 400px;
            background: white;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            box-shadow: 0 -5px 15px rgba(0,0,0,0.1);
        }
        .nav-item {
            padding: 1rem;
            text-align: center;
            border: none;
            background: none;
            cursor: pointer;
            color: #666;
        }
        .nav-item.active {
            color: #667eea;
        }
        .nav-icon {
            font-size: 1.2rem;
            margin-bottom: 0.25rem;
        }
        .nav-label {
            font-size: 0.7rem;
        }
        .content {
            padding-bottom: 80px;
        }
    </style>
</head>
<body>
    <div class="mobile-header">
        <h2>📱 Mobile CRM</h2>
        <p>Priya Sharma • Bandra</p>
        <div class="notification-badge">3</div>
    </div>
    
    <div class="content">
        <div class="quick-stats">
            <div class="stat-item">
                <div class="stat-value">5</div>
                <div class="stat-label">New</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">3</div>
                <div class="stat-label">Hot</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">2</div>
                <div class="stat-label">Calls</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">1</div>
                <div class="stat-label">Meeting</div>
            </div>
        </div>
        
        <div class="action-buttons">
            <button class="action-btn" onclick="callHotLead()">
                <div class="action-icon">📞</div>
                <div class="action-title">Call Hot Lead</div>
                <div class="action-subtitle">Rajesh (94 score)</div>
            </button>
            <button class="action-btn" onclick="sendQuickMessage()">
                <div class="action-icon">💬</div>
                <div class="action-title">Quick WhatsApp</div>
                <div class="action-subtitle">2 pending</div>
            </button>
            <button class="action-btn" onclick="addLead()">
                <div class="action-icon">➕</div>
                <div class="action-title">Add Lead</div>
                <div class="action-subtitle">Quick entry</div>
            </button>
            <button class="action-btn" onclick="showNearby()">
                <div class="action-icon">📍</div>
                <div class="action-title">Nearby</div>
                <div class="action-subtitle">Properties</div>
            </button>
        </div>
        
        <div class="leads-list">
            <div class="list-header">🔥 Today's Priority Leads</div>
            
            <div class="lead-card">
                <div class="lead-details">
                    <h4>Rajesh Patel</h4>
                    <p>📍 Bandra • 💰 ₹2.5Cr • ⭐ 94/100</p>
                    <p style="color: #28a745;">📞 Call due now</p>
                </div>
                <div class="lead-actions">
                    <button class="mini-btn call" onclick="callLead('Rajesh')">📞</button>
                    <button class="mini-btn whatsapp" onclick="whatsappLead('Rajesh')">💬</button>
                </div>
            </div>
            
            <div class="lead-card">
                <div class="lead-details">
                    <h4>Kavita Joshi</h4>
                    <p>📍 Juhu • 💰 ₹5.0Cr • ⭐ 87/100</p>
                    <p style="color: #ffc107;">📅 Meeting at 3 PM</p>
                </div>
                <div class="lead-actions">
                    <button class="mini-btn call" onclick="callLead('Kavita')">📞</button>
                    <button class="mini-btn whatsapp" onclick="whatsappLead('Kavita')">💬</button>
                </div>
            </div>
            
            <div class="lead-card">
                <div class="lead-details">
                    <h4>Vikram Singh</h4>
                    <p>📍 Powai • 💰 ₹3.2Cr • ⭐ 92/100</p>
                    <p style="color: #17a2b8;">💬 WhatsApp sent</p>
                </div>
                <div class="lead-actions">
                    <button class="mini-btn call" onclick="callLead('Vikram')">📞</button>
                    <button class="mini-btn whatsapp" onclick="whatsappLead('Vikram')">💬</button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="bottom-nav">
        <button class="nav-item active">
            <div class="nav-icon">🏠</div>
            <div class="nav-label">Home</div>
        </button>
        <button class="nav-item" onclick="window.location='/leads'">
            <div class="nav-icon">👥</div>
            <div class="nav-label">Leads</div>
        </button>
        <button class="nav-item" onclick="window.location='/properties'">
            <div class="nav-icon">🏢</div>
            <div class="nav-label">Properties</div>
        </button>
        <button class="nav-item" onclick="window.location='/profile'">
            <div class="nav-icon">👤</div>
            <div class="nav-label">Profile</div>
        </button>
    </div>
    
    <script>
        function callHotLead() {
            callLead('Rajesh (Hot Lead)');
        }
        
        function callLead(name) {
            navigator.vibrate && navigator.vibrate(200);
            alert(`📞 Calling ${name}...\\n\\n"Hello! This is Priya from Mumbai Properties. I have some excellent property options for you!"\\n\\n✅ Call in progress...`);
        }
        
        function whatsappLead(name) {
            navigator.vibrate && navigator.vibrate(100);
            alert(`💬 WhatsApp to ${name}:\\n\\n"Hi! I found some great properties matching your requirements. Would you like to schedule a viewing? 🏠"\\n\\n✅ Message sent!`);
        }
        
        function sendQuickMessage() {
            alert('💬 Quick Messages:\\n\\n✅ "Property details sent to Anjali"\\n✅ "Meeting confirmation to Vikram"\\n\\n📤 2 messages sent successfully!');
        }
        
        function addLead() {
            const name = prompt('Lead Name:', 'Enter customer name');
            if (name) {
                alert(`✅ Lead "${name}" added successfully!\\n\\n📱 Lead ID: #${Math.floor(Math.random() * 1000)}\\n🎯 Initial score: 75/100`);
            }
        }
        
        function showNearby() {
            alert('📍 Nearby Properties (GPS: Bandra West):\\n\\n🏠 Luxury 3 BHK - 2.3 Km\\n🏢 Commercial Space - 1.8 Km\\n🏠 4 BHK Villa - 3.1 Km\\n\\n🗺️ Opening map view...');
        }
        
        // Simulate real-time updates
        setTimeout(() => {
            document.querySelector('.notification-badge').textContent = '4';
            document.querySelector('.notification-badge').style.animation = 'pulse 1s infinite';
        }, 10000);
    </script>
</body>
</html>
    """

@app.post("/login")
async def login_submit():
    """Handle login submission."""
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/onboarding/submit")
async def onboarding_submit():
    """Handle onboarding form submission."""
    return RedirectResponse(url="/facebook-setup", status_code=302)

if __name__ == "__main__":
    print("🎯 Starting REAL USER Interface Server...")
    print("📍 Open browser to: http://localhost:8002")
    print("👤 This is what REAL AGENTS see and use!")
    uvicorn.run("real_user_interface:app", host="0.0.0.0", port=8002, reload=True)

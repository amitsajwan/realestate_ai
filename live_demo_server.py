"""
Live Web Demo Server for Real Estate Agent Journey
=================================================

This creates a live web interface for demonstrating the complete agent journey.
Perfect for real-time client demos and presentations.
"""

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from datetime import datetime
from complete_agent_journey_demo import AgentJourneyDemo

app = FastAPI(title="Real Estate Agent Journey - Live Demo")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize demo
demo_instance = None

@app.get("/", response_class=HTMLResponse)
async def demo_homepage():
    """Live demo homepage."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Agent Journey - Live Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.3rem;
            opacity: 0.9;
        }
        
        .demo-controls {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .btn {
            background: linear-gradient(45deg, #00c851, #007e33);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 10px;
            font-size: 1.1rem;
            cursor: pointer;
            margin: 0.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .demo-output {
            background: rgba(0,0,0,0.4);
            border-radius: 10px;
            padding: 2rem;
            margin-top: 2rem;
            font-family: 'Monaco', 'Menlo', monospace;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .step-indicator {
            display: flex;
            justify-content: center;
            margin: 2rem 0;
            flex-wrap: wrap;
        }
        
        .step {
            background: rgba(255,255,255,0.2);
            border-radius: 50px;
            padding: 0.5rem 1rem;
            margin: 0.25rem;
            font-size: 0.9rem;
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        .step.active {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            animation: pulse 2s infinite;
        }
        
        .step.completed {
            background: linear-gradient(45deg, #00c851, #007e33);
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }
        
        .feature-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .progress-bar {
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            height: 10px;
            margin: 1rem 0;
            overflow: hidden;
        }
        
        .progress-fill {
            background: linear-gradient(45deg, #00c851, #007e33);
            height: 100%;
            width: 0%;
            transition: width 0.5s ease;
        }
        
        .mobile-preview {
            position: fixed;
            top: 50%;
            right: 2rem;
            transform: translateY(-50%);
            width: 300px;
            height: 600px;
            background: #000;
            border-radius: 25px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: none;
        }
        
        .mobile-screen {
            width: 100%;
            height: 100%;
            background: white;
            border-radius: 20px;
            color: #333;
            font-size: 0.8rem;
            padding: 1rem;
            overflow-y: auto;
        }
        
        @media (max-width: 768px) {
            .mobile-preview {
                display: none;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .container {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Real Estate Agent Journey</h1>
            <p>Live Demo - From Onboarding to Success</p>
        </div>
        
        <div class="demo-controls">
            <h3>🎬 Live Demo Controls</h3>
            <div style="margin: 1rem 0;">
                <button class="btn" onclick="startFullDemo()">🚀 Start Complete Journey</button>
                <button class="btn" onclick="startStepByStep()">📋 Step-by-Step Demo</button>
                <button class="btn" onclick="showMobileView()">📱 Mobile Experience</button>
                <button class="btn" onclick="resetDemo()">🔄 Reset Demo</button>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressBar"></div>
            </div>
        </div>
        
        <div class="step-indicator">
            <div class="step" id="step1">📝 Onboarding</div>
            <div class="step" id="step2">📘 Facebook</div>
            <div class="step" id="step3">🎯 Leads</div>
            <div class="step" id="step4">📊 Dashboard</div>
            <div class="step" id="step5">📞 Management</div>
            <div class="step" id="step6">🤖 AI Insights</div>
            <div class="step" id="step7">📈 Analytics</div>
            <div class="step" id="step8">📱 Mobile</div>
        </div>
        
        <div class="demo-output" id="demoOutput">
            <div style="text-align: center; color: #ccc; margin: 2rem 0;">
                <h3>🎭 Demo Output Console</h3>
                <p>Click "Start Complete Journey" to begin the live demonstration</p>
                <p>Watch as Priya Sharma's agent journey unfolds in real-time...</p>
            </div>
        </div>
        
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">👤</div>
                <h3>Agent Onboarding</h3>
                <p>Complete profile setup, certification verification, and area specialization</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">📱</div>
                <h3>Lead Generation</h3>
                <p>Multi-channel lead capture from Facebook, WhatsApp, website, and referrals</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h3>AI Insights</h3>
                <p>Smart recommendations, market intelligence, and performance optimization</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>Analytics</h3>
                <p>Real-time dashboards, conversion tracking, and ROI analysis</p>
            </div>
        </div>
    </div>
    
    <div class="mobile-preview" id="mobilePreview">
        <div class="mobile-screen" id="mobileScreen">
            <h4>📱 Mobile CRM</h4>
            <div style="margin: 1rem 0;">
                <strong>Today's Summary</strong><br>
                📈 5 New Leads<br>
                🔥 3 Hot Leads<br>
                📞 2 Calls Due<br>
                📅 1 Meeting
            </div>
            <div style="background: #f0f0f0; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <strong>Quick Actions</strong><br>
                📞 Call Hot Leads<br>
                💬 Send WhatsApp<br>
                📅 Schedule Meeting<br>
                📍 Add Property
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentStep = 0;
        const steps = ['step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8'];
        
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8001/ws/demo');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDemoOutput(data);
            };
            
            ws.onclose = function() {
                console.log('WebSocket connection closed');
            };
            
            ws.onerror = function(error) {
                console.log('WebSocket error:', error);
                const output = document.getElementById('demoOutput');
                output.innerHTML += '<div style="color: #ffff00;">🔄 Running demo directly (WebSocket unavailable)...</div>';
                runDemoDirectly();
            };
        }
        
        function updateDemoOutput(data) {
            const output = document.getElementById('demoOutput');
            
            if (data.type === 'step_start') {
                updateStepIndicator(data.step);
                output.innerHTML += `<div style="color: #00ff00; font-weight: bold; margin: 1rem 0;">\\n🎬 ${data.message}</div>`;
            } else if (data.type === 'step_content') {
                output.innerHTML += `<div style="margin: 0.5rem 0;">${data.message}</div>`;
            } else if (data.type === 'step_complete') {
                completeStep(data.step);
                updateProgress((data.step / 8) * 100);
            }
            
            output.scrollTop = output.scrollHeight;
        }
        
        function updateStepIndicator(stepNum) {
            // Reset all steps
            steps.forEach(step => {
                document.getElementById(step).className = 'step';
            });
            
            // Mark completed steps
            for (let i = 0; i < stepNum - 1; i++) {
                document.getElementById(steps[i]).className = 'step completed';
            }
            
            // Mark active step
            if (stepNum <= 8) {
                document.getElementById(steps[stepNum - 1]).className = 'step active';
            }
        }
        
        function completeStep(stepNum) {
            if (stepNum <= 8) {
                document.getElementById(steps[stepNum - 1]).className = 'step completed';
            }
        }
        
        function updateProgress(percentage) {
            document.getElementById('progressBar').style.width = percentage + '%';
        }
        
        async function startFullDemo() {
            const output = document.getElementById('demoOutput');
            output.innerHTML = '<div style="color: #00ff00; font-weight: bold;">🚀 Starting Complete Agent Journey Demo...</div>';
            
            try {
                const response = await fetch('/start-demo', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    output.innerHTML += '<div style="color: #00ff00;">✅ Demo server ready!</div>';
                    connectWebSocket();
                } else {
                    output.innerHTML += '<div style="color: #ff0000;">❌ Failed to start demo</div>';
                }
            } catch (error) {
                output.innerHTML += '<div style="color: #ff0000;">❌ Error: ' + error.message + '</div>';
                output.innerHTML += '<div style="color: #ffff00;">🔄 Falling back to direct demo...</div>';
                runDemoDirectly();
            }
        }
        
        async function runDemoDirectly() {
            const output = document.getElementById('demoOutput');
            const steps = [
                "📝 STEP 1: Agent Onboarding & Profile Setup",
                "📘 STEP 2: Facebook Integration & Page Setup", 
                "🎯 STEP 3: Real-time Lead Generation & Capture",
                "📊 STEP 4: CRM Dashboard Overview",
                "📞 STEP 5: Lead Management & Follow-ups",
                "🤖 STEP 6: AI-Powered Insights & Recommendations",
                "📈 STEP 7: Performance Analytics & Reporting",
                "📱 STEP 8: Mobile Experience Demo"
            ];
            
            for (let i = 0; i < steps.length; i++) {
                updateStepIndicator(i + 1);
                output.innerHTML += `<div style="color: #00ff00; font-weight: bold; margin: 1rem 0;">\\n${steps[i]}</div>`;
                output.innerHTML += `<div style="margin: 0.5rem 0;">✅ ${steps[i].split(':')[1]} completed successfully</div>`;
                completeStep(i + 1);
                updateProgress(((i + 1) / 8) * 100);
                
                // Scroll to bottom
                output.scrollTop = output.scrollHeight;
                
                // Wait before next step
                await new Promise(resolve => setTimeout(resolve, 1500));
            }
            
            output.innerHTML += '<div style="color: #00ff00; font-weight: bold; margin: 2rem 0;">🎉 Complete Agent Journey Demo Finished!</div>';
            output.innerHTML += '<div style="color: #ccc;">💡 Business Impact: 23% more leads, ₹15.2 Cr pipeline, 67% faster response</div>';
        }
        
        async function startStepByStep() {
            const output = document.getElementById('demoOutput');
            output.innerHTML = '<div style="color: #00ff00; font-weight: bold;">📋 Starting Step-by-Step Demo...</div>';
            output.innerHTML += '<div style="color: #ffff00;">Use the controls below to navigate through each step manually.</div>';
        }
        
        function showMobileView() {
            const mobilePreview = document.getElementById('mobilePreview');
            mobilePreview.style.display = mobilePreview.style.display === 'block' ? 'none' : 'block';
        }
        
        function resetDemo() {
            const output = document.getElementById('demoOutput');
            output.innerHTML = `
                <div style="text-align: center; color: #ccc; margin: 2rem 0;">
                    <h3>🎭 Demo Output Console</h3>
                    <p>Click "Start Complete Journey" to begin the live demonstration</p>
                    <p>Watch as Priya Sharma's agent journey unfolds in real-time...</p>
                </div>
            `;
            
            // Reset progress
            updateProgress(0);
            
            // Reset steps
            steps.forEach(step => {
                document.getElementById(step).className = 'step';
            });
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Real Estate Agent Journey Demo Loaded');
        });
    </script>
</body>
</html>
    """

@app.websocket("/ws/demo")
async def websocket_demo(websocket: WebSocket):
    """WebSocket endpoint for live demo updates."""
    await websocket.accept()
    
    try:
        global demo_instance
        demo_instance = AgentJourneyDemo()
        await demo_instance.initialize_demo()
        
        # Send initialization message
        await websocket.send_text(json.dumps({
            "type": "step_start",
            "step": 0,
            "message": "Demo initialized successfully!"
        }))
        
        # Run demo steps with real-time updates
        steps = [
            ("Agent Onboarding", demo_instance.step_1_agent_onboarding),
            ("Facebook Integration", demo_instance.step_2_facebook_integration),
            ("Lead Generation", demo_instance.step_3_lead_generation),
            ("CRM Dashboard", demo_instance.step_4_crm_dashboard),
            ("Lead Management", demo_instance.step_5_lead_management),
            ("AI Insights", demo_instance.step_6_ai_insights),
            ("Performance Analytics", demo_instance.step_7_performance_analytics),
            ("Mobile Experience", demo_instance.step_8_mobile_experience)
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            await websocket.send_text(json.dumps({
                "type": "step_start",
                "step": i,
                "message": f"STEP {i}: {step_name.upper()}"
            }))
            
            # Execute step and capture output
            try:
                result = await step_func()
                await websocket.send_text(json.dumps({
                    "type": "step_content",
                    "step": i,
                    "message": f"✅ {step_name} completed successfully"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "step_content",
                    "step": i,
                    "message": f"❌ {step_name} failed: {str(e)}"
                }))
            
            await websocket.send_text(json.dumps({
                "type": "step_complete",
                "step": i,
                "message": f"Step {i} complete"
            }))
            
            await asyncio.sleep(1)  # Brief pause between steps
            
        # Send completion message
        await websocket.send_text(json.dumps({
            "type": "demo_complete",
            "message": "🎉 Complete Agent Journey Demo Finished!"
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Demo error: {str(e)}"
        }))
    finally:
        await websocket.close()

@app.post("/start-demo")
async def start_demo():
    """Start the demo process."""
    try:
        return {"success": True, "message": "Demo started"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/demo-status")
async def demo_status():
    """Get current demo status."""
    global demo_instance
    
    if demo_instance:
        return {
            "active": True,
            "leads_created": len(demo_instance.leads_created) if demo_instance.leads_created else 0,
            "interactions": len(demo_instance.interactions_logged) if demo_instance.interactions_logged else 0
        }
    else:
        return {"active": False}

if __name__ == "__main__":
    import uvicorn
    print("🎬 Starting Live Demo Server...")
    print("📍 Open browser to: http://localhost:8001")
    print("🎭 Perfect for client presentations and stakeholder demos")
    uvicorn.run("live_demo_server:app", host="0.0.0.0", port=8001, reload=True)

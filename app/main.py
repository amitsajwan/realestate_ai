# app/main.py - FastAPI application entrypoint

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from fastapi.templating import Jinja2Templates
from pathlib import Path as SysPath
from fastapi.staticfiles import StaticFiles

from core.config import settings

# Optional database integration
try:
	from app.core.database import connect_to_mongo, close_mongo_connection
	HAS_DATABASE = True
except Exception:
	HAS_DATABASE = False
	print("⚠️  Using legacy/no database setup")

if os.getenv("SKIP_DB") == "1":
	HAS_DATABASE = False

# Collect routers to include
routers_to_include = []

# Simple auth (provides /api/login)
try:
	from api.endpoints.simple_auth import router as simple_auth_router
	routers_to_include.append(("SimpleAuth", simple_auth_router, ""))
except Exception:
	print("⚠️  SimpleAuth router not found")

# API v1 (if present)
try:
	from app.api.v1.router import api_router
	routers_to_include.append(("API v1", api_router, "/api/v1"))
except Exception:
	print("⚠️  API v1 router not found")

# Agent Onboarding (HTML + APIs)
try:
	from app.api.endpoints.agent_onboarding import router as onboarding_router
	routers_to_include.append(("AgentOnboarding", onboarding_router, ""))
except Exception:
	print("⚠️  AgentOnboarding router not found")

# AI Localization (try both module paths)
_ai_loc_added = False
try:
	from app.api.endpoints.ai_localization import router as ai_localization_router
	routers_to_include.append(("AILocalization", ai_localization_router, ""))
	_ai_loc_added = True
except Exception:
	pass
if not _ai_loc_added:
	try:
		from api.endpoints.ai_localization import router as ai_localization_router
		routers_to_include.append(("AILocalization", ai_localization_router, ""))
	except Exception:
		print("⚠️  AILocalization router not found")

# Branding suggestions API (LLM-powered)
try:
	from api.endpoints.branding import router as branding_router
	routers_to_include.append(("Branding", branding_router, ""))
except Exception:
	print("⚠️  Branding router not found")

# Legacy route groups if present
for name, module_path in [
	("Proxy", "app.routes.proxy"),
	("Auth", "app.routes.auth"),
	("Leads", "app.routes.leads"),
	("Properties", "app.routes.properties"),
	("System", "app.routes.system"),
]:
	try:
		module = __import__(module_path, fromlist=["router"])
		routers_to_include.append((name, getattr(module, "router"), ""))
	except Exception:
		print(f"⚠️  {name} router not found")

# Logging
logging.basicConfig(
	level=logging.DEBUG if settings.DEBUG else logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info("Starting Real Estate AI CRM...")
	if HAS_DATABASE:
		try:
			await connect_to_mongo()
			logger.info("✅ Database connected")
		except Exception as e:
			logger.error(f"❌ Database connection failed: {e}")
	else:
		logger.info("📊 Running without database integration")

	yield

	if HAS_DATABASE:
		try:
			await close_mongo_connection()
			logger.info("📊 Database connection closed")
		except Exception as e:
			logger.error(f"Database shutdown error: {e}")
	logger.info("👋 Application shutdown complete")


# FastAPI app
app = FastAPI(
	title="Real Estate AI CRM",
	version="2.0.0",
	description="AI-Powered Real Estate CRM System",
	lifespan=lifespan,
)

# Templates
_app_templates = SysPath(__file__).parent / "templates"
_root_templates = SysPath(__file__).parent.parent / "templates"
templates_root = Jinja2Templates(directory=str(_root_templates))
templates_app = Jinja2Templates(
	directory=str(_app_templates if (_app_templates / "onboarding.html").exists() else _root_templates)
)

# Static files
static_path = SysPath(__file__).parent.parent / "static"
if static_path.exists():
	app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# WebSocket endpoint
@app.websocket("/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
	await websocket.accept()
	try:
		while True:
			data = await websocket.receive_text()
			await websocket.send_text(f"Message text was: {data}")
	except WebSocketDisconnect:
		logger.info(f"Client {client_id} disconnected")


# CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:8080", "http://localhost:5173"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
	logger.error(f"Global exception: {str(exc)}", exc_info=True)
	return JSONResponse(
		status_code=500,
		content={
			"error": "Internal server error",
			"detail": str(exc) if settings.DEBUG else "An error occurred",
		},
	)


# Include routers
for name, router, prefix in routers_to_include:
	app.include_router(router, prefix=prefix)
	logger.info(f"✅ Included {name} router at {prefix}")


# Public pages
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
	return templates_root.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
	return templates_root.TemplateResponse("dashboard.html", {"request": request})


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request):
	return templates_app.TemplateResponse("onboarding.html", {"request": request})


# Health and API root
@app.get("/health")
async def health_check():
	return {
		"status": "healthy",
		"service": "real-estate-ai-crm",
		"version": "2.0.0",
		"debug": settings.DEBUG,
	}


@app.get("/api")
async def api_root():
	return {
		"message": "Real Estate AI CRM API",
		"version": "2.0.0",
		"docs": "/docs",
		"health": "/health",
		"frontend": settings.FRONTEND_URL,
		"available_routes": [
			{"name": name, "prefix": prefix} for name, _, prefix in routers_to_include
		],
	}


if __name__ == "__main__":
	import uvicorn
	logger.info(f"Starting server on {settings.BASE_URL}")
	uvicorn.run(
		"app.main:app",
		host="0.0.0.0",
		port=8080,
		reload=settings.DEBUG,
		log_level="debug" if settings.DEBUG else "info",
	)


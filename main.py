import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.config import settings
from db_adapter import get_db_connection

MODE = settings.MODE  # 'production' or 'development'

app = FastAPI(title="Real Estate AI CRM Unified")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(ROOT_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Register routers; all use the same DB adapter
try:
    from api.endpoints import (
        auth, leads, properties, listing_posts, ai_localization, smart_properties, facebook_oauth, facebook_pages
    )
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(leads.router, prefix="/leads", tags=["leads"])
    app.include_router(properties.router, prefix="/properties", tags=["properties"])
    app.include_router(listing_posts.router, prefix="/listing-posts", tags=["listing-posts"])
    app.include_router(ai_localization.router, prefix="/ai-localization", tags=["ai-localization"])
    app.include_router(smart_properties.router, prefix="/smart-properties", tags=["smart-properties"])
    app.include_router(facebook_oauth.router, prefix="/facebook-oauth", tags=["facebook-oauth"])
    app.include_router(facebook_pages.router, prefix="/facebook-pages", tags=["facebook-pages"])
except Exception as e:
    print(f"⚠️ Router registration failed: {e}")

db = get_db_connection(MODE)
def get_db():
    return db

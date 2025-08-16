from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Real Estate CRM (Modular)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# Mount static folder at /static
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(ROOT_DIR, "templates"))

# Temporarily disabled auth middleware for Facebook testing
# @app.middleware("http")
# async def auth_redirect_middleware(request: Request, call_next):
#     """Redirect anonymous users from protected pages to login.
#
#     Minimal check: if path is /dashboard and there's no Authorization header,
#     send a 302 to "/". This will be replaced with proper JWT/cookie validation later.
#     """
#     if request.url.path.rstrip("/") == "/dashboard":
#         has_header = bool(request.headers.get("authorization"))
#         has_cookie = bool(request.cookies.get("auth"))
#         if not (has_header or has_cookie):
#             return RedirectResponse(url="/", status_code=302)
#     return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Routers
try:
    from .routes import system as system_routes  # type: ignore
    app.include_router(system_routes.router)
    from .routes import proxy as proxy_routes  # type: ignore
    app.include_router(proxy_routes.router)
    from .routes import auth as auth_routes  # type: ignore
    app.include_router(auth_routes.router)
    from .routes import leads as leads_routes  # type: ignore
    app.include_router(leads_routes.router)
    from .routes import properties as properties_routes  # type: ignore
    app.include_router(properties_routes.router)
    
    # Add Facebook Integration Routes
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.endpoints import facebook_oauth, facebook_pages  # type: ignore
    app.include_router(facebook_oauth.router, prefix="/api/facebook", tags=["facebook"])
    app.include_router(facebook_pages.router, prefix="/api/facebook", tags=["facebook"])
    print("✅ Facebook API routes loaded successfully!")
except Exception as e:
    # Routes optional during early modularization
    print(f"⚠️ Some routes not available: {e}")
    pass

import os
from fastapi import APIRouter, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
import requests
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

TARGET = os.getenv("BASE_URL")

async def _forward(method: str, path: str, request: Request) -> Response:
    
    url = f"{TARGET}{path}"
    print(f"Forwarding {method} request to {url}")
    headers = {}
    # Forward selected headers
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    content_type = request.headers.get("content-type")
    if content_type:
        headers["Content-Type"] = content_type

    params = dict(request.query_params)
    data = await request.body()

    def _do_request():
        return requests.request(
            method=method,
            url=url,
            params=params if method.upper() == "GET" else None,
            data=data if method.upper() != "GET" else None,
            headers=headers,
            timeout=15,
        )

    try:
        resp = await run_in_threadpool(_do_request)
        media_type = resp.headers.get("content-type", "application/json")
        return Response(content=resp.content, status_code=resp.status_code, media_type=media_type)
    except requests.exceptions.RequestException:
        return Response(content=b'{"error":"upstream unavailable"}', status_code=502, media_type="application/json")

# --- AUTH & FACEBOOK ROUTES ---

@router.post("/api/login")
async def proxy_login(request: Request):
    return await _forward("POST", "/api/login", request)

@router.get("/auth/facebook/login")
async def proxy_facebook_login_get(request: Request):
    print((f"Request headers: {dict(request.headers)}"))
    logger.info("Received GET /auth/facebook/login request")
    logger.info(f"Request headers: {dict(request.headers)}")
    response = await _forward("GET", "/api/v1/facebook/login", request)
    logger.info(f"Response status code: {response.status_code}")
    return response

@router.post("/auth/facebook/login")
async def proxy_facebook_login_post(request: Request):
    print(" ###############      ")
    logger.info("Received POST /auth/facebook/login request")
    logger.info(f"Request headers: {dict(request.headers)}")
    response = await _forward("POST", "/api/v1/facebook/login", request)
    logger.info(f"Response status code: {response.status_code}")
    return response

@router.get("/api/facebook/config")
async def proxy_facebook_config(request: Request):
    print("=============== Facebook Config GET ===============")
    # Avoid infinite loop by checking if we're already proxying
    if "X-Forwarded-For" in request.headers:
        return Response(content=b'{"error":"recursive proxy call detected"}', status_code=400, media_type="application/json")
    return await _forward("GET", "/api/facebook/config", request)

@router.post("/api/facebook/config")
async def proxy_facebook_config_post(request: Request):
    return await _forward("POST", "/api/facebook/config", request)

@router.get("/api/facebook/leads")
async def proxy_facebook_leads(request: Request):
    return await _forward("GET", "/api/facebook/leads", request)

@router.post("/api/facebook/leads")
async def proxy_facebook_leads_post(request: Request):
    return await _forward("POST", "/api/facebook/leads", request)

# --- LEADS ROUTES ---

@router.get("/api/leads")
async def proxy_get_leads(request: Request):
    return await _forward("GET", "/api/leads", request)

@router.post("/api/leads")
async def proxy_post_lead(request: Request):
    return await _forward("POST", "/api/leads", request)

@router.put("/api/leads/{lead_id}")
async def proxy_put_lead(request: Request):
    return await _forward("PUT", request.url.path, request)

@router.delete("/api/leads/{lead_id}")
async def proxy_delete_lead(request: Request):
    return await _forward("DELETE", request.url.path, request)

# --- PROPERTIES ROUTES ---


@router.get("/api/properties")
async def proxy_get_properties(request: Request):
    # Forward to the versioned path your main app expects
    return await _forward("GET", "/api/v1/properties/", request)

@router.post("/api/properties")
async def proxy_post_property(request: Request):
    # Forward to the versioned path your main app expects
    return await _forward("POST", "/api/v1/properties/", request)

@router.put("/api/properties/{property_id}")
async def proxy_put_property(request: Request):
    return await _forward("PUT", request.url.path, request)

@router.delete("/api/properties/{property_id}")
async def proxy_delete_property(request: Request):
    return await _forward("DELETE", request.url.path, request)

@router.get("/api/smart-properties")
async def proxy_smart_properties(request: Request):
    return await _forward("GET", "/api/smart-properties", request)

@router.post("/api/smart-properties")
async def proxy_smart_properties_post(request: Request):
    return await _forward("POST", "/api/smart-properties", request)

# --- USER MANAGEMENT ROUTES ---

@router.get("/api/users")
async def proxy_get_users(request: Request):
    return await _forward("GET", "/api/users", request)

@router.post("/api/users")
async def proxy_post_user(request: Request):
    return await _forward("POST", "/api/users", request)

@router.put("/api/users/{user_id}")
async def proxy_put_user(request: Request):
    return await _forward("PUT", request.url.path, request)

@router.delete("/api/users/{user_id}")
async def proxy_delete_user(request: Request):
    return await _forward("DELETE", request.url.path, request)

# --- DASHBOARD, ANALYTICS, REPORTS ---

@router.get("/api/dashboard")
async def proxy_dashboard(request: Request):
    return await _forward("GET", "/api/dashboard", request)

@router.get("/api/analytics")
async def proxy_analytics(request: Request):
    return await _forward("GET", "/api/analytics", request)

@router.get("/api/reports")
async def proxy_reports(request: Request):
    return await _forward("GET", "/api/reports", request)

# --- SETTINGS ROUTES ---

@router.get("/api/settings")
async def proxy_settings(request: Request):
    return await _forward("GET", "/api/settings", request)

@router.post("/api/settings")
async def proxy_settings_post(request: Request):
    return await _forward("POST", "/api/settings", request)

@router.put("/api/settings")
async def proxy_settings_put(request: Request):
    return await _forward("PUT", "/api/settings", request)

# --- GENERIC CATCH-ALL ROUTE FOR /api ---
@router.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_generic_api(request: Request):
    return await _forward(request.method, request.url.path, request)
import os
import asyncio
import logging
import json
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.runnables import RunnableConfig

from branding_to_post_graph import build_graph, BrandingPostState
from core.config import settings
from core.session_manager import session_manager
from core.dependencies import get_current_user
from api.endpoints.auth import router as auth_router
from repositories.user_repository import get_user_repository, UserRepository
from services.facebook_branding import update_page_branding

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(client_id)s] - %(message)s')
logger = logging.getLogger("realestate-ai")

# --- FastAPI App Setup ---
app = FastAPI(title="Real Estate AI Assistant Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # More restrictive CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Include Facebook OAuth router
from api.endpoints.facebook_oauth import router as facebook_oauth_router
app.include_router(facebook_oauth_router, prefix="/api/facebook", tags=["facebook"])

# Include listing posts router
from api.endpoints.listing_posts import router as listing_posts_router
app.include_router(listing_posts_router, prefix="/api/listings", tags=["listings"])

# Include leads router
from api.endpoints.leads import router as leads_router
app.include_router(leads_router, tags=["leads"])

# Include dashboard router
from api.endpoints.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

# Include India market router
from api.endpoints.india_market import router as india_router
app.include_router(india_router, tags=["india-market"])

# Include AI localization router
from api.endpoints.ai_localization import router as ai_localization_router
app.include_router(ai_localization_router, tags=["ai-localization"])

# Include CRM router
from api.endpoints.crm import router as crm_router
app.include_router(crm_router, tags=["crm"])

os.makedirs("generated_images", exist_ok=True)
app.mount("/generated_images", StaticFiles(directory="generated_images"), name="generated_images")

# --- Templates ---
templates_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    autoescape=select_autoescape(["html", "xml"]),
)

# --- Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.graph = build_graph()

    async def connect(self, client_id: str, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active_connections[client_id] = ws
        
        # Create session in Redis
        await session_manager.create_session(client_id, user_id, {"client_id": client_id})
        logger.info("Client connected", extra={"client_id": client_id, "user_id": user_id})

    async def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        await session_manager.delete_session(client_id)
        logger.info("Client disconnected", extra={"client_id": client_id})

    async def run_graph_part(self, client_id: str, state_update: dict):
        """Merge updates into the current session state and run the LangGraph workflow"""
        session = await session_manager.get_session(client_id)
        if session is None:
            logger.error("No session found for client", extra={"client_id": client_id})
            return

        # Get current state from session
        current_state = session.get("data", {})
        
        # Merge incoming state updates (parse features if provided as CSV string)
        merged_update = dict(state_update or {})
        if "features" in merged_update and isinstance(merged_update["features"], str):
            merged_update["features"] = [f.strip() for f in merged_update["features"].split(",") if f.strip()]
        current_state.update(merged_update)
        
        # Update session
        await session_manager.update_session(client_id, current_state)

        config = RunnableConfig(configurable={
            "client_id": client_id,
            "user_id": session["user_id"],
            "websocket": self.active_connections.get(client_id)
        })

        try:
            async for event in self.graph.astream_events(current_state, config, version="v1"):
                kind = event.get("event")

                # Prefer node-level end events for streaming updates
                if kind == "on_node_end":
                    node_name = event.get("name")
                    output = (event.get("data") or {}).get("output")
                    if output:
                        # Persist node output into session state (shallow merge)
                        if isinstance(output, dict):
                            await session_manager.update_session(client_id, output)

                        await self.active_connections[client_id].send_json({
                            "type": "update",
                            "step": node_name,
                            "data": output
                        })

                        # Special handling: prompt UI for missing property info
                        if node_name == "check_requirements":
                            missing = (output or {}).get("missing_info") or []
                            if isinstance(missing, list) and missing:
                                await self.active_connections[client_id].send_json({
                                    "type": "request_input",
                                    "step": node_name,
                                    "fields": missing
                                })

        except Exception as e:
            logger.exception("Error during graph execution for client %s", client_id, extra={"client_id": client_id})
            await self.active_connections[client_id].send_json({"type": "error", "message": str(e)})

manager = ConnectionManager()

# --- WebSocket Endpoint with Authentication ---
@app.websocket("/chat/{client_id}")
async def chat_ws(ws: WebSocket, client_id: str, token: str = None):
    # Simple token validation for WebSocket (you'd want more robust auth in production)
    if not token:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # Validate token and get user
        from jose import jwt
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Get user from repository
        user_repo = UserRepository()
        user = await user_repo.get_user(username)
        if not user:
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
    except Exception:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(client_id, user.id, ws)
    try:
        while True:
            raw_data = await ws.receive_text()
            message = json.loads(raw_data)

            state_update = {}
            message_type = message.get("type")

            if message_type == "initial_input":
                state_update["user_input"] = message.get("user_input")
                asyncio.create_task(manager.run_graph_part(client_id, state_update))

            elif message_type == "details_input":
                details = message.get("details", {})
                state_update.update({
                    "location": details.get("location"),
                    "price": details.get("price"),
                    "bedrooms": details.get("bedrooms"),
                    "features": [f.strip() for f in details.get("features", "").split(',')],
                    "should_post": bool(details.get("should_post")),
                    "missing_info": []
                })
                asyncio.create_task(manager.run_graph_part(client_id, state_update))

    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Unhandled error in websocket for client {client_id}: {e}")
        await manager.disconnect(client_id)

# --- Root Check ---
@app.get("/")
def root():
    return {"message": "Real Estate AI Assistant Backend is running!"}

# --- Agent Microsite (SSR) ---
@app.get("/agents/{username}", response_class=HTMLResponse)
async def agent_site(username: str):
    # TODO: Replace with DB lookup for real agent profile
    # For now, render a simple page from token-derived username and defaults
    profile = {
        "username": username,
        "brand_name": username.replace("-", " ").title(),
        "tagline": "Trusted Real Estate Advisor",
        "bio": "Helping clients buy and sell with confidence across our local market.",
        "website": None,
        "email": None,
        "phone": None,
        "location": None,
        "facebook_url": None,
        "instagram_url": None,
        "linkedin_url": None,
    }
    tpl = templates_env.get_template("agent_site.html")
    return tpl.render(profile=profile)

# --- Branding Sync Endpoint (Prototype) ---
from pydantic import BaseModel

class BrandingUpdate(BaseModel):
    about: str | None = None
    website: str | None = None
    username: str | None = None
    page_id: str | None = None  # optional override

@app.post("/agents/{username}/branding")
async def apply_branding(username: str, body: BrandingUpdate, current_user: dict = Depends(get_current_user)):
    # In production: resolve the user's connected page_id + page token from DB
    # For now: use env-configured page and token
    page_id = body.page_id or settings.FB_PAGE_ID
    page_token = settings.FB_PAGE_TOKEN
    if not page_id or not page_token:
        raise HTTPException(status_code=400, detail="Facebook Page credentials not configured")

    result = update_page_branding(
        page_id,
        page_token,
        about=body.about,
        website=body.website,
        username=body.username,
    )
    return {"status": "ok", "results": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)

import logging
import os
from dotenv import load_dotenv
from typing import Optional, List, TypedDict
import json

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import requests

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
try:
    llm = ChatGroq(model="llama3-70b-8192", temperature=0.4)
except Exception as e:
    logger.error(f"Failed to initialize ChatGroq. Ensure GROQ_API_KEY is set. Error: {e}")
    llm = None

# Import your Facebook posting function
from post_to_facebook_with_image import post_to_facebook, post_text_to_facebook
from PIL import Image, ImageDraw, ImageFont

# --- Graph State Definition ---
# The WebSocket object is REMOVED from the state.
class BrandingPostState(TypedDict, total=False):
    user_input: Optional[str]
    brand_suggestions: Optional[str]
    visual_prompts: Optional[str]
    image_path: Optional[str] # Web-accessible path for the UI
    location: Optional[str]
    price: Optional[str]
    bedrooms: Optional[str]
    features: List[str]
    base_post: Optional[str]
    missing_info: List[str]
    post_result: Optional[dict]
    client_id: Optional[str]
    should_post: Optional[bool]

# --- Helper function to send messages to UI ---
async def send_ui_message(config: RunnableConfig, message: dict):
    # The websocket object is passed in the 'configurable' part of the config
    ws = config["configurable"].get("websocket")
    if ws:
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")

# --- Graph Nodes (Now accepting `config`) ---

async def create_branding_node(state: BrandingPostState, config: RunnableConfig) -> dict:
    logger.info("Node: create_branding", extra={"client_id": config["configurable"]["client_id"]})
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You're an expert real estate marketer. Generate 3 distinct brand names and slogans for a real estate project based on the user's idea. Provide a brief rationale for each. Format as Markdown."),
        ("user", "Business Idea: {user_input}")
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({"user_input": state.get("user_input", "")})
        return {"brand_suggestions": result.strip()}
    except Exception as e:
        logger.error(f"Error in create_branding_node: {e}", extra={"client_id": config["configurable"]["client_id"]})
        await send_ui_message(config, {"type": "error", "message": f"Could not generate branding: {e}"})
        return {}

async def create_visual_prompt_node(state: BrandingPostState, config: RunnableConfig) -> dict:
    logger.info("Node: create_visuals", extra={"client_id": config["configurable"]["client_id"]})
    raw_branding = state.get("brand_suggestions", "")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a creative director specializing in photorealistic AI imagery. Write a detailed, single-paragraph SDXL prompt for a modern real estate visual. Focus on architecture, lighting, and luxurious details. Do not include negative prompts."),
        ("user", "Use this branding concept as inspiration:\n{branding_concept}")
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({"branding_concept": raw_branding})
        logger.info(f"Generated visual prompt: {result.strip()}", extra={"client_id": config["configurable"]["client_id"]})
        return {"visual_prompts": result.strip()}
    except Exception as e:
        logger.error(f"Error in create_visual_prompt_node: {e}", extra={"client_id": config["configurable"]["client_id"]})
        await send_ui_message(config, {"type": "error", "message": f"Could not generate visual prompt: {e}"})
        return {}


async def generate_image_node(state: BrandingPostState, config: RunnableConfig) -> dict:
    # Respect env flag to disable image generation entirely
    DISABLE_IMAGE_GEN = os.getenv("AI_DISABLE_IMAGE_GENERATION", "false").lower() in ("1", "true", "yes", "on")
    if DISABLE_IMAGE_GEN:
        await send_ui_message(config, {"type": "info", "message": "Image generation is disabled by configuration."})
        return {"image_path": None}

    client_id = config["configurable"]["client_id"]
    logger.info("Node: generate_image", extra={"client_id": client_id})
    prompt = state.get("visual_prompts", "A beautiful modern house")
    
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

    if not HF_TOKEN:
        msg = "HUGGINGFACE_API_TOKEN not set. Skipping image generation."
        logger.error(msg, extra={"client_id": client_id})
        await send_ui_message(config, {"type": "error", "message": msg})
        # Create placeholder image
        os.makedirs("generated_images", exist_ok=True)
        filename = f"{client_id}_placeholder.jpg"
        server_path = os.path.join("generated_images", filename)
        _create_placeholder_image(server_path)
        return {"image_path": f"/generated_images/{filename}"}

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Accept": "image/png"
    }
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        response.raise_for_status() # Raise an exception for bad status codes
        # Some HF endpoints may return JSON while the model warms up
        ctype = response.headers.get("content-type", "")
        if "image" not in ctype:
            msg = f"Unexpected response from image API (content-type: {ctype})."
            logger.error(msg, extra={"client_id": client_id})
            await send_ui_message(config, {"type": "error", "message": msg})
            return {"image_path": None}
        image_bytes = response.content
        os.makedirs("generated_images", exist_ok=True)
        filename = f"{client_id}_property_image.jpg"
        server_path = os.path.join("generated_images", filename)
        with open(server_path, "wb") as f:
            f.write(image_bytes)
        web_path = f"/generated_images/{filename}"
        logger.info(f"Image successfully generated and saved to {web_path}", extra={"client_id": client_id})
        return {"image_path": web_path}
    except Exception as e:
        logger.error(f"Image generation failed: {e}", extra={"client_id": client_id})
        await send_ui_message(config, {"type": "error", "message": f"Image generation failed: {e}"})
        # Create placeholder image on failure
        os.makedirs("generated_images", exist_ok=True)
        filename = f"{client_id}_placeholder.jpg"
        server_path = os.path.join("generated_images", filename)
        _create_placeholder_image(server_path)
        return {"image_path": f"/generated_images/{filename}"}


async def check_requirements_node(state: BrandingPostState, config: RunnableConfig) -> dict:
    client_id = config["configurable"]["client_id"]
    logger.info("Node: check_requirements", extra={"client_id": client_id})
    missing = []
    if not state.get("location"): missing.append("location")
    if not state.get("price"): missing.append("price")
    if not state.get("bedrooms"): missing.append("bedrooms")
    if not state.get("features"): missing.append("features")
    # Do not send UI events here; main.py streams node outputs and sends a single request_input
    return {"missing_info": missing}

def decide_what_to_do_next(state: BrandingPostState) -> str:
    if state.get("missing_info"):
        return "pause_for_details"
    else:
        return "generate_post"

async def generate_post_node(state: BrandingPostState, config: RunnableConfig) -> dict:
    client_id = config["configurable"]["client_id"]
    logger.info("Node: generate_post", extra={"client_id": client_id})
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You're a world-class real estate copywriter. Write a catchy, emoji-rich Facebook post using the details below. Include relevant hashtags and a call to action."),
        ("user", "Property in {location}, priced at {price}, with {bedrooms} bedrooms and features: {features}. Use these branding ideas as inspiration: {brand_suggestions}")
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        result = await chain.ainvoke({
            "location": state["location"],
            "price": state["price"],
            "bedrooms": state["bedrooms"],
            "features": ", ".join(state.get("features", [])),
            "brand_suggestions": state.get("brand_suggestions", "")
        })
        return {"base_post": result.strip()}
    except Exception as e:
        logger.error(f"Error in generate_post_node: {e}", extra={"client_id": client_id})
        await send_ui_message(config, {"type": "error", "message": f"Could not generate post: {e}"})
        return {}


async def post_to_facebook_node(state: BrandingPostState, config: RunnableConfig) -> dict:
    client_id = config["configurable"]["client_id"]
    logger.info("Node: post_to_facebook", extra={"client_id": client_id})
    DISABLE_IMAGE_GEN = os.getenv("AI_DISABLE_IMAGE_GENERATION", "false").lower() in ("1", "true", "yes", "on")

    if DISABLE_IMAGE_GEN:
        # Post text-only
        message = state.get("base_post", "")
        if not message:
            msg = "Nothing to post: generated post text is empty."
            logger.error(msg, extra={"client_id": client_id})
            await send_ui_message(config, {"type": "final", "message": msg})
            return {"post_result": {"status": "error", "message": msg}}
        result = post_text_to_facebook(message)
    else:
        image_server_path = (state.get("image_path") or "").lstrip('/')
        if not os.path.exists(image_server_path):
            msg = f"Image not found at {image_server_path}. Cannot post to Facebook."
            logger.error(msg, extra={"client_id": client_id})
            await send_ui_message(config, {"type": "final", "message": msg})
            return {"post_result": {"status": "error", "message": msg}}
        result = post_to_facebook(
            caption=state.get("base_post", ""), 
            image_path=image_server_path
        )
    # Send the final status message to the UI
    final_msg = result.get("message")
    if result.get("status") == "success" and result.get("url"):
        final_msg += f"\nLink: {result['url']}"
    elif result.get("status") == "error" and result.get("details"):
        final_msg += f"\nDetails: {result['details']}"
    await send_ui_message(config, {"type": "final", "message": final_msg})
    return {"post_result": result}

async def announce_preview_final_node(state: BrandingPostState, config: RunnableConfig) -> dict:
    # Tell UI that preview is ready and posting was skipped
    msg = "Preview ready. Posting is disabled."
    await send_ui_message(config, {"type": "final", "message": msg})
    return {"post_result": {"status": "preview", "message": msg}}

# --- Graph Definition ---
def build_graph():
    if not llm:
        raise ValueError("LLM not initialized. Check GROQ_API_KEY.")
        
    workflow = StateGraph(BrandingPostState)

    # Read env flag once for the graph construction
    DISABLE_IMAGE_GEN = os.getenv("AI_DISABLE_IMAGE_GENERATION", "false").lower() in ("1", "true", "yes", "on")

    workflow.add_node("create_branding", create_branding_node)
    if not DISABLE_IMAGE_GEN:
        workflow.add_node("create_visuals", create_visual_prompt_node)
        workflow.add_node("generate_image", generate_image_node)
    workflow.add_node("check_requirements", check_requirements_node)
    workflow.add_node("generate_post", generate_post_node)
    workflow.add_node("post_to_facebook", post_to_facebook_node)
    workflow.add_node("announce_preview_final", announce_preview_final_node)
    workflow.add_node("pause_for_details", lambda state, config: {}) # Dummy node for pausing

    workflow.set_entry_point("create_branding")
    if not DISABLE_IMAGE_GEN:
        workflow.add_edge("create_branding", "create_visuals")
        workflow.add_edge("create_visuals", "generate_image")
        workflow.add_edge("generate_image", "check_requirements")
    else:
        # Skip visuals and image generation, go straight to requirements
        workflow.add_edge("create_branding", "check_requirements")
    
    workflow.add_conditional_edges(
        "check_requirements",
        decide_what_to_do_next,
        {
            "generate_post": "generate_post",
            "pause_for_details": END 
        }
    )
    
    # After generating the post, decide whether to publish or just preview
    def decide_post_or_preview(state: BrandingPostState) -> str:
        if state.get("should_post") is True:
            return "post_to_facebook"
        return "announce_preview_final"

    workflow.add_conditional_edges(
        "generate_post",
        decide_post_or_preview,
        {
            "post_to_facebook": "post_to_facebook",
            "announce_preview_final": "announce_preview_final",
        },
    )
    workflow.add_edge("post_to_facebook", END)
    workflow.add_edge("announce_preview_final", END)

    return workflow.compile()

# --- Helpers ---
def _create_placeholder_image(path: str):
    try:
        img = Image.new("RGB", (1024, 1024), color=(240, 243, 248))
        draw = ImageDraw.Draw(img)
        text = "Property Visual\nPlaceholder"
        font = ImageFont.load_default()
        # Center the text approximately
        try:
            w, h = draw.multiline_textbbox((0, 0), text, font=font)[2:]
        except Exception:
            w, h = draw.textlength(text, font=font), 40
        draw.multiline_text(((1024 - w) / 2, (1024 - h) / 2), text, fill=(60, 60, 60), font=font, align="center")
        img.save(path, format="JPEG", quality=85)
    except Exception:
        # As a last resort, write an empty file so the UI path exists
        with open(path, "wb") as f:
            f.write(b"")

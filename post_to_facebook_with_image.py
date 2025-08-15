import os
import requests
from dotenv import load_dotenv

load_dotenv()

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
# Support multiple env var names for the page token
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN") or os.getenv("FB_PAGE_ACCESS_TOKEN")

GRAPH_API_VERSION = os.getenv("FB_GRAPH_API_VERSION", "v19.0")

def post_to_facebook(caption: str, image_path: str):
    """
    Post a photo with caption to a Facebook Page.
    Returns a dict: {status: 'success'|'error', message, post_id?, url?, details?}
    """
    try:
        if not FB_PAGE_ID or not FB_PAGE_TOKEN:
            return {
                "status": "error",
                "message": "Facebook credentials missing. Set FB_PAGE_ID and FB_PAGE_TOKEN in .env",
            }

        if not os.path.exists(image_path):
            return {"status": "error", "message": f"Image not found at path: {image_path}"}

        post_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}/photos"

        with open(image_path, "rb") as image_file:
            files = {"source": image_file}
            data = {
                "caption": caption or "",
                "access_token": FB_PAGE_TOKEN,
                # "published": "true"  # default is true
            }

            response = requests.post(post_url, files=files, data=data, timeout=60)
            # Raise HTTP errors for consistent handling
            try:
                response.raise_for_status()
            except Exception:
                pass
            # Parse body
            try:
                result = response.json()
            except Exception:
                result = {"error": {"message": "Non-JSON response from Facebook."}}

        if response.ok and "id" in result:
            post_id = result["id"]
            url = f"https://www.facebook.com/{post_id}"
            return {
                "status": "success",
                "message": "✅ Posted successfully to Facebook!",
                "post_id": post_id,
                "url": url,
            }
        else:
            fb_error = (result or {}).get("error", {})
            err_msg = fb_error.get("message") or f"HTTP {response.status_code}"
            err_code = fb_error.get("code")
            err_type = fb_error.get("type")
            return {
                "status": "error",
                "message": f"❌ Failed to post to Facebook: {err_msg}",
                "details": {"code": err_code, "type": err_type, "raw": result},
            }

    except Exception as e:
        return {"status": "error", "message": f"Exception posting to Facebook: {e}"}


def post_text_to_facebook(message: str):
    """Post a text-only message to the Facebook Page feed."""
    try:
        if not FB_PAGE_ID or not FB_PAGE_TOKEN:
            return {
                "status": "error",
                "message": "Facebook credentials missing. Set FB_PAGE_ID and FB_PAGE_TOKEN in .env",
            }

        if not message:
            return {"status": "error", "message": "Message is empty."}

        post_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}/feed"
        data = {
            "message": message,
            "access_token": FB_PAGE_TOKEN,
        }
        response = requests.post(post_url, data=data, timeout=60)
        try:
            response.raise_for_status()
        except Exception:
            pass
        try:
            result = response.json()
        except Exception:
            result = {"error": {"message": "Non-JSON response from Facebook."}}

        if response.ok and "id" in result:
            post_id = result["id"]
            url = f"https://www.facebook.com/{post_id}"
            return {
                "status": "success",
                "message": "✅ Posted text successfully to Facebook!",
                "post_id": post_id,
                "url": url,
            }
        else:
            fb_error = (result or {}).get("error", {})
            err_msg = fb_error.get("message") or f"HTTP {response.status_code}"
            err_code = fb_error.get("code")
            err_type = fb_error.get("type")
            return {
                "status": "error",
                "message": f"❌ Failed to post text to Facebook: {err_msg}",
                "details": {"code": err_code, "type": err_type, "raw": result},
            }
    except Exception as e:
        return {"status": "error", "message": f"Exception posting text to Facebook: {e}"}

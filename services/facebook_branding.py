import requests
from typing import Optional, Dict

from core.config import settings

GRAPH_API_VERSION = settings.FB_GRAPH_API_VERSION


def update_page_branding(
    page_id: str,
    access_token: str,
    *,
    about: Optional[str] = None,
    website: Optional[str] = None,
    username: Optional[str] = None,
) -> Dict:
    """Attempt to update Facebook Page branding fields where permitted.

    Note: Many Page fields require specific permissions and may not be editable via API
    depending on app review status and Page type. This function attempts safe fields
    and returns the Graph API response per field.
    """
    results = {}
    base_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}"

    # Update 'about' (Page bio)
    if about is not None:
        try:
            r = requests.post(
                base_url,
                data={
                    "about": about,
                    "access_token": access_token,
                },
                timeout=30,
            )
            results["about"] = {"status": r.status_code, "body": _safe_json(r)}
        except Exception as e:
            results["about"] = {"error": str(e)}

    # Update website link
    if website is not None:
        try:
            r = requests.post(
                base_url,
                data={
                    "website": website,
                    "access_token": access_token,
                },
                timeout=30,
            )
            results["website"] = {"status": r.status_code, "body": _safe_json(r)}
        except Exception as e:
            results["website"] = {"error": str(e)}

    # Update username (often restricted)
    if username is not None:
        try:
            r = requests.post(
                base_url,
                data={
                    "username": username,
                    "access_token": access_token,
                },
                timeout=30,
            )
            results["username"] = {"status": r.status_code, "body": _safe_json(r)}
        except Exception as e:
            results["username"] = {"error": str(e)}

    return results


def _safe_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text[:500]}

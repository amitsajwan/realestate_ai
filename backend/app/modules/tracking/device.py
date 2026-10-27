"""A short device label from the user agent, for the Live panel: "Android phone · Chrome", "iPhone · Instagram app".

Only the label is stored, never the user agent itself. Robots that run pages like a browser (headless Chrome, Lighthouse,
page-speed tests) do not say "bot" (service.is_bot), so they are named here and kept out of the visitor counts."""
from typing import Optional

from .origin import app_of

HEADLESS = ("headlesschrome", "lighthouse", "pagespeed", "ptst", "gtmetrix", "pingdom", "uptime", "phantomjs", "puppeteer",
            "playwright", "selenium")
APP_NAMES = {"instagram": "Instagram app", "facebook": "Facebook app", "linkedin": "LinkedIn app", "snapchat": "Snapchat app"}


def is_headless(user_agent: Optional[str]) -> bool:
    ua = (user_agent or "").lower()
    return any(m in ua for m in HEADLESS)


def _device(ua: str) -> Optional[str]:
    if "iphone" in ua:
        return "iPhone"
    if "ipad" in ua:
        return "iPad"
    if "android" in ua:
        return "Android phone" if "mobile" in ua else "Android tablet"
    if "cros" in ua:
        return "Chromebook"
    if "windows" in ua:
        return "Windows computer"
    if "macintosh" in ua or "mac os x" in ua:
        return "Mac"
    if "linux" in ua:
        return "Linux computer"
    return None


def _browser(ua: str) -> Optional[str]:
    # order matters: Edge, Samsung and Opera also say "Chrome"; Chrome on iPhone says "Safari" and CriOS
    for mark, name in (("edg", "Edge"), ("samsungbrowser", "Samsung Internet"), ("opr/", "Opera"), ("firefox", "Firefox"),
                       ("fxios", "Firefox"), ("crios", "Chrome"), ("chrome", "Chrome"), ("safari", "Safari")):
        if mark in ua:
            return name
    return None


def label(user_agent: Optional[str]) -> Optional[str]:
    """'Android phone · Chrome'; an in-app browser names the app ('iPhone · Instagram app'); None when nothing is known."""
    ua = (user_agent or "").lower()
    if not ua:
        return None
    app = app_of(user_agent)
    parts = [_device(ua), APP_NAMES.get(app) if app else _browser(ua)]
    return " · ".join(p for p in parts if p) or None

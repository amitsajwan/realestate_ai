"""Check every service key the server has against its service, from inside the backend container (the keys never leave the VM).

    sudo docker compose exec -T backend python scripts/keys_check.py      # on the VM, in deploy/gcp
    .\\deploy\\gcp\\keys.ps1 -Verify                                         # the same, from your PC

Each key is OK (the service accepted it), FAILED (refused, or the service could not be reached: the reason is shown), EMPTY (not
set) or SKIP (set, but nothing to check it against, e.g. a base URL is missing). Only the last 4 characters of a key are printed.
Every check is a cheap read: a model or voice list, one 1-unit YouTube lookup, one Serper search (1 credit), a Google token for the
Search Console key, the Facebook page / WhatsApp number the token belongs to. Exit code 1 when any key FAILED.
"""
import base64
import json
import os
import sys
from typing import Callable, List, Optional, Tuple

import httpx

GROQ = "https://api.groq.com/openai/v1"
TIMEOUT = 20

Result = Tuple[str, str]           # (status, note)
Check = Callable[[httpx.Client, str], Result]


def env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def tail(v: str) -> str:
    return f"...{v[-4:]}" if len(v) > 4 else "..."


def _reason(r: httpx.Response) -> str:
    try:
        body = r.json()
        err = body.get("error") if isinstance(body, dict) else None
        msg = (err.get("message") if isinstance(err, dict) else err) or (body.get("message") if isinstance(body, dict) else "")
    except Exception:
        msg = r.text
    return f"HTTP {r.status_code}: {str(msg or '').strip()[:120]}"


def _ok(r: httpx.Response, note: str = "") -> Result:
    return ("OK", note) if r.status_code < 400 else ("FAILED", _reason(r))


def openai_compatible(base_vars: Tuple[str, ...], default_base: Optional[str]) -> Check:
    """A key for an OpenAI-compatible API (Groq, OpenRouter, Gemini's OpenAI endpoint): list its models with the key, at the base
    URL the app uses (the first of `base_vars` that is set, else `default_base`). OpenRouter lists models without a key, so there
    the key's own info is asked for instead."""
    def check(c: httpx.Client, key: str) -> Result:
        base = (next((env(v) for v in base_vars if env(v)), "") or default_base or "").rstrip("/")
        if not base:
            return ("SKIP", f"{' / '.join(base_vars)} not set")
        url = f"{base}/key" if "openrouter.ai" in base else f"{base}/models"
        return _ok(c.get(url, headers={"Authorization": f"Bearer {key}"}), base)
    return check


def serper(c: httpx.Client, key: str) -> Result:
    r = c.post("https://google.serper.dev/search", headers={"X-API-KEY": key},
               json={"q": "new launch projects in Kharadi Pune", "gl": "in", "num": 1})
    return _ok(r, "1 search credit used")


def youtube(c: httpx.Client, key: str) -> Result:
    return _ok(c.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "id", "id": "dQw4w9WgXcQ", "key": key}))


def google_tts(c: httpx.Client, key: str) -> Result:
    return _ok(c.get("https://texttospeech.googleapis.com/v1/voices", params={"languageCode": "hi-IN", "key": key}))


def gemini(c: httpx.Client, key: str) -> Result:
    return _ok(c.get("https://generativelanguage.googleapis.com/v1beta/models", params={"pageSize": 1, "key": key}))


def search_console(c: httpx.Client, raw: str) -> Result:
    """The base64 service-account file: it must decode, and Google must give it a token for Search Console (read-only)."""
    try:
        sa = json.loads(base64.b64decode(raw))
    except Exception:
        return ("FAILED", "not a base64 service-account key file")
    if not all(sa.get(k) for k in ("client_email", "private_key", "token_uri")):
        return ("FAILED", "the file has no client_email / private_key / token_uri")
    import asyncio

    from app.modules.areastats import searchconsole

    async def get_token() -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT) as ac:
            return await searchconsole.token(sa, ac)
    try:
        asyncio.run(get_token())
    except httpx.HTTPStatusError as e:
        return ("FAILED", _reason(e.response))
    return ("OK", f"token for {sa['client_email']} (add it in Search Console as a user if pages stay at 0)")


def meta_page(c: httpx.Client, token: str) -> Result:
    v = env("META_GRAPH_VERSION", "v23.0")
    r = c.get(f"https://graph.facebook.com/{v}/me", params={"fields": "id,name", "access_token": token})
    if r.status_code >= 400:
        return ("FAILED", _reason(r))
    me, page = r.json(), env("META_PAGE_ID")
    if page and str(me.get("id")) != page:
        return ("FAILED", f"the token belongs to {me.get('name')} ({me.get('id')}), not META_PAGE_ID {page}")
    return ("OK", f"page: {me.get('name')}")


def whatsapp(c: httpx.Client, token: str) -> Result:
    number = env("WHATSAPP_PHONE_NUMBER_ID")
    if not number:
        return ("SKIP", "WHATSAPP_PHONE_NUMBER_ID is not set")
    v = env("WHATSAPP_GRAPH_VERSION", "v23.0")
    r = c.get(f"https://graph.facebook.com/{v}/{number}", params={"fields": "display_phone_number", "access_token": token})
    return _ok(r, f"number: {r.json().get('display_phone_number')}" if r.status_code < 400 else "")


# (key, what it is for, its check): the same keys deploy/gcp/keys.ps1 lists
CHECKS: List[Tuple[str, str, Check]] = [
    ("SERPER_API_KEY", "Google results for hot projects", serper),
    ("YOUTUBE_API_KEY", "YouTube videos for hot projects", youtube),
    ("GOOGLE_TTS_API_KEY", "Reel voice-overs", google_tts),
    ("GEMINI_API_KEY", "Gemini (voice, fallback AI)", gemini),
    ("GSC_SA_KEY_B64", "Search Console reader", search_console),
    ("AI_LLM_API_KEY", "Text AI", openai_compatible(("AI_LLM_BASE_URL",), GROQ)),
    ("GROQ_API_KEY", "Text AI (Groq)", openai_compatible((), GROQ)),
    ("AI_LLM_FALLBACK_API_KEY", "Text AI fallback", openai_compatible(("AI_LLM_FALLBACK_BASE_URL",), None)),
    ("AI_STT_API_KEY", "Speech to text", openai_compatible(("AI_STT_BASE_URL",), GROQ)),
    ("AI_VISION_API_KEY", "Photo review", openai_compatible(("AI_VISION_BASE_URL", "AI_LLM_BASE_URL"), GROQ)),
    ("AI_VISION_FALLBACK_API_KEY", "Photo review fallback",
     openai_compatible(("AI_VISION_FALLBACK_BASE_URL", "AI_LLM_FALLBACK_BASE_URL"), None)),
    ("META_PAGE_ACCESS_TOKEN", "Facebook / Instagram posting", meta_page),
    ("WHATSAPP_ACCESS_TOKEN", "WhatsApp", whatsapp),
]


def run(client: httpx.Client, checks=CHECKS) -> List[Tuple[str, str, str, str, str]]:
    """[(key, for, status, last 4, note)] for every key: a failing check is FAILED with its reason, never a crash."""
    out = []
    for name, purpose, check in checks:
        value = env(name)
        if not value:
            out.append((name, purpose, "EMPTY", "", ""))
            continue
        try:
            status, note = check(client, value)
        except httpx.HTTPError as e:
            status, note = "FAILED", f"could not reach the service ({type(e).__name__})"
        except Exception as e:  # a check's own bug must not hide the other keys
            status, note = "FAILED", f"check error: {type(e).__name__}: {str(e)[:100]}"
        out.append((name, purpose, status, tail(value), note))
    return out


def main() -> int:
    with httpx.Client(timeout=TIMEOUT) as c:
        rows = run(c)
    for name, purpose, status, last, note in rows:
        print(f"{status:7} {name:27} {last:9} {purpose}" + (f"  -- {note}" if note else ""))
    return 1 if any(r[2] == "FAILED" for r in rows) else 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # /app, for app.modules.* imports
    sys.exit(main())

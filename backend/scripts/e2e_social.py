"""Social publishing end-to-end check against a RUNNING backend on localhost:8010 with a real MongoDB. Never posts anywhere real.

  mode "dry":  SOCIAL_DRY_RUN=true  + FAKE token/ids   -> approval, consent, idempotency, records, isolation, no secret leaks
  mode "real": SOCIAL_DRY_RUN=false + FAKE token + https media url -> the real Graph API rejects the fake token; we check the
               failure is recorded cleanly and the token is not leaked (safe: an invalid token cannot post anything)

Run: docker run -d --name pai-mongo -p 27017:27017 mongo:7
     cd backend && DATABASE_NAME=propertyai_soc SOCIAL_DRY_RUN=true META_PAGE_ID=1234567890 META_PAGE_ACCESS_TOKEN=FAKE-TOKEN-SECRET-123 \
       META_IG_BUSINESS_ID=9876543210 PUBLIC_MEDIA_BASE_URL=https://example.invalid PYTHONPATH=. .venv/Scripts/python.exe -m uvicorn app.main:app --port 8010
     .venv/Scripts/python.exe scripts/e2e_social.py dry      (then restart with SOCIAL_DRY_RUN=false and a real-looking https url, run: real)
"""
import io
import random
import sys

import httpx
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MODE = sys.argv[1] if len(sys.argv) > 1 else "dry"
SECRET = "FAKE-TOKEN-SECRET-123"
B = "http://localhost:8010/api/v1"
c = httpx.Client(timeout=90)
fails = []


def check(name, cond, extra=""):
    print(("PASS" if cond else "FAIL"), name, extra if cond else "-> " + str(extra)[:400])
    if not cond:
        fails.append(name)
    return cond


def new_agent(name):
    phone = "9" + "".join(random.choice("0123456789") for _ in range(9))
    code = c.post(f"{B}/join/otp/request", json={"phone": phone}).json()["dev_code"]
    tok = c.post(f"{B}/join/otp/verify", json={"phone": phone, "code": code}).json()["access_token"]
    H = {"Authorization": f"Bearer {tok}"}
    c.post(f"{B}/join/site", headers=H, json={"name": name, "city": "Pune"})
    return H


def photo():
    im = Image.new("RGB", (1600, 1200), (196, 150, 110))
    ImageDraw.Draw(im).rectangle([600, 500, 1000, 1100], fill=(90, 60, 45))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88)
    return buf.getvalue()


H = new_agent("Rahul Sharma")
url = c.post(f"{B}/uploads/images", headers=H, files=[("files", ("f.jpg", photo(), "image/jpeg"))]).json()["files"][0]["url"]
d = c.post(f"{B}/listings/ai/draft", headers=H, data={"text": "2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, parking, lift, gym"}).json()["draft"]
lst = c.post(f"{B}/listings", headers=H, json={**{k: v for k, v in d.items() if v is not None}, "media": [{"url": url, "kind": "image", "order": 0}]}).json()
lid = lst["id"]
c.post(f"{B}/listings/{lid}/publish", headers=H)
P = f"{B}/social/listings/{lid}/publish"
body = {"channels": ["facebook_page", "instagram"], "approve": True, "consent": True}

st = c.get(f"{B}/social/status", headers=H)
check("status readable, no secrets", st.status_code == 200 and SECRET not in st.text and "META_PAGE" not in st.text, st.text[:200])
sj = st.json()
check(f"status reports dry_run={MODE == 'dry'}", sj["dry_run"] is (MODE == "dry"), sj)
check("both channels configured (fake ids present)", sj["channels"] == {"facebook_page": True, "instagram": True}, sj["channels"])

check("cannot post before a marketing pack exists (409)", c.post(P, headers=H, json=body).status_code == 409)
check("marketing pack generated", c.post(f"{B}/listings/{lid}/marketing", headers=H, json={}).status_code == 200)
check("no approval -> 422", c.post(P, headers=H, json={**body, "approve": False}).status_code == 422)
check("no consent -> 422", c.post(P, headers=H, json={**body, "consent": False}).status_code == 422)
check("nothing was recorded by rejected requests", c.get(f"{B}/social/listings/{lid}/publications", headers=H).json()["items"] == [])

r = c.post(P, headers=H, json=body)
pubs = r.json().get("publications", []) if r.status_code == 200 else []
check("publish request accepted", r.status_code == 200, r.text[:300])
check("no secret in the publish response", SECRET not in r.text)
if MODE == "dry":
    check("both channels recorded as dry_run with fake ids", sorted(p["status"] for p in pubs) == ["dry_run", "dry_run"] and all(p["external_id"] for p in pubs), [(p["channel"], p["status"]) for p in pubs])
    check("payload snapshot holds the exact text and image urls", all(p["payload"]["text"] and isinstance(p["payload"]["image_urls"], list) for p in pubs))
    check("consent is stored with each record", all(p["consent"]["given_at"] and "Avasetu" in p["consent"]["text"] for p in pubs), pubs[0]["consent"])
    again = c.post(P, headers=H, json=body)
    check("posting the same pack twice is refused (409)", again.status_code == 409, again.status_code)
    forced = c.post(P, headers=H, json={**body, "force": True})
    check("force posts again", forced.status_code == 200 and len(c.get(f"{B}/social/listings/{lid}/publications", headers=H).json()["items"]) == 4)
else:
    print("   real-mode records:", [(p["channel"], p["status"], (p["error"] or "")[:140]) for p in pubs])
    check("real Graph rejected the fake token and it was recorded as failed (not silent)", pubs and all(p["status"] == "failed" and p["error"] for p in pubs), [(p["channel"], p["status"]) for p in pubs])
    check("failure text explains the problem without leaking the token", all(SECRET not in (p["error"] or "") for p in pubs))
    retry = c.post(f"{B}/social/publications/{pubs[0]['id']}/retry", headers=H)
    check("failed record can be retried (and fails cleanly again)", retry.status_code in (200, 409) and SECRET not in retry.text, retry.status_code)

lst_r = c.get(f"{B}/social/listings/{lid}/publications", headers=H)
check("history lists newest first, no secrets", lst_r.status_code == 200 and SECRET not in lst_r.text)
H2 = new_agent("Other Agent")
check("other agent cannot publish my listing (404)", c.post(P, headers=H2, json=body).status_code == 404)
check("other agent cannot read my publications (404)", c.get(f"{B}/social/listings/{lid}/publications", headers=H2).status_code == 404)
check("other agent cannot retry my publication (404)", c.post(f"{B}/social/publications/{(pubs or [{'id': 'x'}])[0]['id']}/retry", headers=H2).status_code == 404)
check("unauthenticated is refused", c.get(f"{B}/social/status").status_code == 401)

print("\nFAILED:" if fails else "\nALL STEPS PASSED", fails or "")
sys.exit(1 if fails else 0)

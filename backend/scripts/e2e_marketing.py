"""Sprint 3 end-to-end check against a RUNNING backend on localhost:8010 with a real MongoDB.

Covers the marketing pack (copy for every channel + rendered image cards using a real uploaded photo), reverse matching
("N buyers match this property"), property performance and recommended actions, plus owner isolation.

Run: docker run -d --name pai-mongo -p 27017:27017 mongo:7
     cd backend && DATABASE_NAME=propertyai_mkt PYTHONPATH=. .venv/Scripts/python.exe -m uvicorn app.main:app --port 8010
     .venv/Scripts/python.exe scripts/e2e_marketing.py      (run from backend/ so ./uploads resolves)
"""
import io
import random
import sys
import urllib.parse

import httpx
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # captions contain emoji; Windows consoles default to cp1252

B = "http://localhost:8010/api/v1"
UA = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile Safari/604.1"}
c = httpx.Client(timeout=60)
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
    slug = c.post(f"{B}/join/site", headers=H, json={"name": name, "city": "Pune"}).json()["slug"]
    return H, slug


def photo_bytes():
    im = Image.new("RGB", (1600, 1200), (196, 150, 110))
    d = ImageDraw.Draw(im)
    for i in range(0, 1200, 60):
        d.rectangle([80, 200 + i // 3, 1520, 260 + i // 3], outline=(255, 255, 255), width=3)
    d.rectangle([600, 500, 1000, 1100], fill=(90, 60, 45))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def upload_photo(H):
    r = c.post(f"{B}/uploads/images", headers=H, files=[("files", ("flat.jpg", photo_bytes(), "image/jpeg"))])
    return r.json()["files"][0]["url"] if r.status_code == 200 else None


def add_listing(H, text, photo=None):
    d = c.post(f"{B}/listings/ai/draft", headers=H, data={"text": text}).json()["draft"]
    body = {k: v for k, v in d.items() if v is not None}
    if photo:
        body["media"] = [{"url": photo, "kind": "image", "order": 0}]
    lst = c.post(f"{B}/listings", headers=H, json=body).json()
    c.post(f"{B}/listings/{lst['id']}/publish", headers=H)
    return lst["id"]


def enquire(slug, lid, anon, name, phone, message, events=(), view_lid=None, **extra):
    """Buyer browses `view_lid` (default: the listing they enquire about), then enquires on `lid`."""
    for t in events:
        c.post(f"{B}/t/event", headers=UA, json={"agent_slug": slug, "anon_id": anon, "listing_id": view_lid or lid, "source": "instagram", "type": t})
    return c.post(f"{B}/t/inquiry", headers=UA, json={"agent_slug": slug, "anon_id": anon, "listing_id": lid, "source": "instagram",
                                                       "name": name, "phone": phone, "message": message, "consent": True, **extra})


H, slug = new_agent("Rahul Sharma")
photo = upload_photo(H)
check("photo uploaded", bool(photo), photo)
baner = add_listing(H, "2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, 3rd floor of 12, semi furnished, parking, lift, gym", photo)
wakad = add_listing(H, "3 BHK for sale in Wakad Pune, 1450 sq ft carpet, 1.25 crore, ready to move, clubhouse, swimming pool")
draft_only = c.post(f"{B}/listings", headers=H, json={"title": "half done"}).json()["id"]

# buyers. All three enquired about the Wakad flat, so the (new) Baner flat is fresh news for each of them.
# Priya browsed the Baner flat 3 times and tapped WhatsApp, then enquired on Wakad wanting a 2 BHK in Baner.
enquire(slug, wakad, "anon-priya-0001", "Priya Sharma", "9876500001", "Is a 2 BHK in Baner available?",
        events=["listing_view", "listing_view", "listing_view", "whatsapp_click"], view_lid=baner, bhk=2, budget_min_inr=8000000,
        budget_max_inr=9000000, timeline="1_3_months", financing="home_loan", localities=["Baner"])
enquire(slug, wakad, "anon-amit-0002", "Amit Kulkarni", "9876500002", "Looking for 3bhk under 1.3 crore, need it next month, home loan", events=["listing_view"])
enquire(slug, wakad, "anon-neha-0003", "Neha Joshi", "9876500003", "Budget 2 crore, 4 bhk villa please", events=[])

# ---- marketing pack
r = c.post(f"{B}/listings/{baner}/marketing", headers=H, json={})
check("pack generated", r.status_code == 200, r.status_code)
pk = r.json()
check("angle is factual and readable", "Baner" in pk["angle"] and "2 BHK" in pk["angle"], pk["angle"])
check("Instagram caption + hashtags", len(pk["instagram"]["caption"]) > 40 and 1 <= len(pk["instagram"]["hashtags"]) <= 12, pk["instagram"]["hashtags"])
check("copy never invents facts", all(x not in (pk["instagram"]["caption"] + pk["facebook"]["post"] + pk["whatsapp"]["message"]).lower()
                                       for x in ("swimming pool", "clubhouse", "metro", "guaranteed", "best price")))
check("price and locality present in WhatsApp text", "85" in pk["whatsapp"]["message"] and "Baner" in pk["whatsapp"]["message"], pk["whatsapp"]["message"])
check("share link points at the listing", f"/agent/{slug}/listings/{baner}" in pk["share_url"] and "src=whatsapp" in pk["share_url"], pk["share_url"])
check("reel script has beats and a CTA", len(pk["reel"]["beats"]) >= 4 and bool(pk["reel"]["cta"]), [b["seconds"] for b in pk["reel"]["beats"]])
imgs = pk["instagram"]["images"] + ([pk["whatsapp"]["status_image"]] if pk["whatsapp"]["status_image"] else [])
check("cover, facts, amenities, cta and status cards", {i["kind"] for i in imgs} >= {"cover", "facts", "amenities", "cta", "status"}, [i["kind"] for i in imgs])
sizes_ok = True
for i in imgs:
    g = c.get(i["url"])
    im = Image.open(io.BytesIO(g.content)) if g.status_code == 200 else None
    ok = g.status_code == 200 and g.headers.get("content-type", "").startswith("image/") and im is not None and im.size == (i["width"], i["height"]) and len(g.content) < 400_000
    if not ok:
        sizes_ok = False
        print("   bad image", i["kind"], g.status_code, g.headers.get("content-type"), len(g.content))
check("every image downloads as a small JPEG of the declared size", sizes_ok)
cover = Image.open(io.BytesIO(c.get(next(i for i in imgs if i["kind"] == "cover")["url"]).content)).convert("RGB")
px = cover.getpixel((540, 200))
check("cover uses the agent's photo as background (not a flat fallback)", px != (0, 0, 0), px)
g = c.get(f"{B}/listings/{baner}/marketing", headers=H)
check("saved pack readable", g.status_code == 200 and g.json()["version"] == 1, g.status_code)
r2 = c.post(f"{B}/listings/{baner}/marketing", headers=H, json={"language": "hi"}).json()
check("regenerate bumps the version, Hindi reported", r2["version"] == 2 and r2["language"] in ("hi", "en"), (r2["version"], r2["language"]))
check("draft listing cannot be marketed (409)", c.post(f"{B}/listings/{draft_only}/marketing", headers=H, json={}).status_code == 409)
check("no pack yet for the Wakad flat (404)", c.get(f"{B}/listings/{wakad}/marketing", headers=H).status_code == 404)

# ---- reverse matching
m = c.get(f"{B}/inbox/matching-leads", headers=H, params={"listing_id": baner}).json()
names = [b["name"] for b in m["buyers"]]
check("only Priya matches the Baner flat (3 BHK and 4 BHK / 2 Cr buyers do not)", names == ["Priya Sharma"], names)
top = m["buyers"][0]
check("match has percent and reasons", top["match_pct"] >= 60 and top["reasons"], (top["match_pct"], top["reasons"]))
check("draft is honest and carries a wa.me link", top["draft"]["whatsapp_url"].startswith("https://wa.me/919876500001?text=") and "Priya" in top["draft"]["message"]
      and urllib.parse.unquote(top["draft"]["whatsapp_url"].split("text=", 1)[1]) == top["draft"]["message"], top["draft"]["message"])
check("draft links to the property", f"/listings/{baner}" in top["draft"]["message"], top["draft"]["message"])

# ---- performance
perf = {p["listing_id"]: p for p in c.get(f"{B}/inbox/performance", headers=H).json()["items"]}
pb = perf[baner]
check("Baner performance: 3 views by 1 visitor, no enquiry on it directly", pb["views"] == 3 and pb["unique_visitors"] == 1 and pb["enquiries"] == 0, pb)
pw = perf[wakad]
check("Wakad performance: 3 enquiries, qualified ones counted", pw["enquiries"] == 3 and pw["qualified"] >= 2, pw)
check("by_source counts enquiries", pw["by_source"].get("instagram") == 3, pw["by_source"])

# ---- recommended actions
t = c.get(f"{B}/inbox/today", headers=H).json()
types = [a["type"] for a in t["actions"]]
check("actions include call, and create_marketing for the Wakad flat", "call" in types and any(a["type"] == "create_marketing" and a["listing_id"] == wakad for a in t["actions"]), types)
check("no create_marketing for the Baner flat that has a pack", not any(a["type"] == "create_marketing" and a["listing_id"] == baner for a in t["actions"]))
check("send_property names exactly the 1 matching buyer for the Baner flat", any(a["type"] == "send_property" and a["listing_id"] == baner and a.get("buyer_count") == 1 for a in t["actions"]), t["actions"])
check("no send_property for the Wakad flat (all three already enquired on it)", not any(a["type"] == "send_property" and a["listing_id"] == wakad for a in t["actions"]), t["actions"])
check("existing /today fields intact", {"counts", "hot_buyers", "follow_ups", "headline"} <= set(t))

# ---- isolation
H2, _ = new_agent("Other Agent")
check("other agent cannot generate my pack", c.post(f"{B}/listings/{baner}/marketing", headers=H2, json={}).status_code == 404)
check("other agent cannot read my pack", c.get(f"{B}/listings/{baner}/marketing", headers=H2).status_code == 404)
check("other agent cannot see matching leads for my listing", c.get(f"{B}/inbox/matching-leads", headers=H2, params={"listing_id": baner}).status_code == 404)
check("other agent sees no performance", c.get(f"{B}/inbox/performance", headers=H2).json()["items"] == [])

print("\nFAILED:" if fails else "\nALL STEPS PASSED", fails or "")
sys.exit(1 if fails else 0)

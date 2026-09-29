"""Sprint 2 end-to-end check against a RUNNING backend on localhost:8010 with a real MongoDB.

Covers buyer qualification: requirement stated + inferred from the message, AI summary, next action, matching
listings, follow-up draft, follow-up scheduling and the "Your business today" endpoint, plus owner isolation.

Run: docker run -d --name pai-mongo -p 27017:27017 mongo:7
     cd backend && DATABASE_NAME=propertyai_qual PYTHONPATH=. .venv/Scripts/python.exe -m uvicorn app.main:app --port 8010
     .venv/Scripts/python.exe scripts/e2e_qualification.py
"""
import json
import random
import sys
import urllib.parse

import httpx

B = "http://localhost:8010/api/v1"
UA = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile Safari/604.1"}
c = httpx.Client(timeout=30)
fails = []


def check(name, cond, extra=""):
    print(("PASS" if cond else "FAIL"), name, extra if cond else "-> " + str(extra)[:300])
    if not cond:
        fails.append(name)
    return cond


def new_agent(name):
    phone = "9" + "".join(random.choice("0123456789") for _ in range(9))
    code = c.post(f"{B}/join/otp/request", json={"phone": phone}).json()["dev_code"]
    tok = c.post(f"{B}/join/otp/verify", json={"phone": phone, "code": code}).json()["access_token"]
    H = {"Authorization": f"Bearer {tok}"}
    site = c.post(f"{B}/join/site", headers=H, json={"name": name, "city": "Pune"}).json()
    return H, site["slug"]


def add_listing(H, text):
    d = c.post(f"{B}/listings/ai/draft", headers=H, data={"text": text}).json()["draft"]
    lst = c.post(f"{B}/listings", headers=H, json={k: v for k, v in d.items() if v is not None}).json()
    c.post(f"{B}/listings/{lst['id']}/publish", headers=H)
    return lst["id"]


def enquire(slug, lid, anon, name, phone, message, events=(), **extra):
    for t in events:
        c.post(f"{B}/t/event", headers=UA, json={"agent_slug": slug, "anon_id": anon, "listing_id": lid, "source": "instagram", "type": t})
    body = {"agent_slug": slug, "anon_id": anon, "listing_id": lid, "source": "instagram", "name": name, "phone": phone,
            "message": message, "consent": True, **extra}
    return c.post(f"{B}/t/inquiry", headers=UA, json=body)


H, slug = new_agent("Rahul Sharma")
baner = add_listing(H, "2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, 3rd floor of 12")
wakad = add_listing(H, "3 BHK for sale in Wakad Pune, 1450 sq ft carpet, 1.25 crore, ready to move")
kharadi = add_listing(H, "1 BHK for rent in Kharadi Pune, 620 sq ft carpet, 22000 per month")
check("3 listings live", len(c.get(f"{B}/listings", headers=H).json()["items"]) == 3)

# A) buyer fills the structured fields
r = enquire(slug, baner, "anon-priya-0001", "Priya Sharma", "9876500001", "Is this still available?",
            events=["listing_view", "listing_view", "listing_view", "whatsapp_click"],
            bhk=2, budget_min_inr=8000000, budget_max_inr=9000000, timeline="1_3_months", financing="home_loan")
check("stated inquiry accepted", r.status_code == 200, r.text)
# B) buyer only writes a message: requirement must be inferred
r = enquire(slug, wakad, "anon-amit-0002", "Amit Kulkarni", "9876500002", "Looking for 3bhk under 1.3 crore, need it next month, will pay by home loan")
check("message-only inquiry accepted", r.status_code == 200, r.text)
# C) bare inquiry, nothing extra (old-style body)
r = enquire(slug, kharadi, "anon-neha-0003", "Neha Joshi", "9876500003", "Rent details please")
check("old-style inquiry still works", r.status_code == 200, r.text)

leads = c.get(f"{B}/inbox/leads", headers=H).json()["leads"]
by = {l["name"]: l for l in leads}
check("3 leads, hottest first", len(leads) == 3 and leads[0]["name"] == "Priya Sharma", [(l["name"], l["score"]) for l in leads])
check("requirement_line on the list", bool(by["Priya Sharma"].get("requirement_line")), by["Priya Sharma"].get("requirement_line"))

d = c.get(f"{B}/inbox/leads/{by['Priya Sharma']['id']}", headers=H).json()
req = d["requirement"]
check("stated requirement stored", req["bhk"] == 2 and req["budget_max_inr"] == 9000000 and req["timeline"] == "1_3_months" and req["financing"] == "home_loan", req)
check("localities default from the listing", "Baner" in (req.get("localities") or []), req.get("localities"))
check("AI summary is a real sentence", "Baner" in d["ai_summary"] and len(d["ai_summary"]) > 40, d["ai_summary"])
check("next action present", d["next_action"]["type"] in ("call", "whatsapp", "schedule_visit", "follow_up"), d["next_action"])
check("Baner flat is the top match with reasons", d["matches"] and d["matches"][0]["listing_id"] == baner and d["matches"][0]["match_pct"] >= 80 and d["matches"][0]["reasons"], d["matches"][:1])

a = c.get(f"{B}/inbox/leads/{by['Amit Kulkarni']['id']}", headers=H).json()["requirement"]
check("requirement inferred from the message", a["bhk"] == 3 and a["budget_max_inr"] == 13000000 and a["financing"] == "home_loan" and a["source"] in ("inferred", "mixed"), a)

# follow-up draft
dr = c.post(f"{B}/inbox/leads/{by['Priya Sharma']['id']}/followup-draft", headers=H, json={}).json()
check("draft mentions the buyer and the property", "Priya" in dr["message"] and "Baner" in dr["message"], dr["message"])
url = dr["whatsapp_url"]
check("wa.me link carries the text", url.startswith("https://wa.me/919876500001?text=") and urllib.parse.unquote(url.split("text=", 1)[1]) == dr["message"], url[:90])
check("draft explains why", bool(dr["based_on"]), dr["based_on"])
hi = c.post(f"{B}/inbox/leads/{by['Priya Sharma']['id']}/followup-draft", headers=H, json={"language": "hi"}).json()
check("hindi draft returned", bool(hi["message"]) and hi["language"] in ("hi", "en"), hi["language"])

# follow-up scheduling
p = c.patch(f"{B}/inbox/leads/{by['Priya Sharma']['id']}", headers=H, json={"stage": "contacted", "note": "Called, wants a visit"}).json()
check("contacted sets a follow-up due date", p["follow_up"]["due_at"] is not None and p["follow_up"]["overdue"] is False, p["follow_up"])
check("empty patch rejected", c.patch(f"{B}/inbox/leads/{by['Priya Sharma']['id']}", headers=H, json={}).status_code == 422)

# business today
t = c.get(f"{B}/inbox/today", headers=H).json()
cnt = t["counts"]
check("today counts", cnt["new_enquiries_24h"] == 3 and cnt["hot"] >= 1 and cnt["uncontacted"] == 2, cnt)
check("hot buyers list has a top match", t["hot_buyers"] and t["hot_buyers"][0]["top_match"], t["hot_buyers"][:1])
check("headline present", bool(t["headline"]), t["headline"])

# isolation
H2, slug2 = new_agent("Other Agent")
check("other agent sees nothing", c.get(f"{B}/inbox/today", headers=H2).json()["counts"]["new_enquiries_24h"] == 0)
check("other agent cannot read a lead", c.get(f"{B}/inbox/leads/{by['Priya Sharma']['id']}", headers=H2).status_code == 404)
check("other agent cannot draft for a lead", c.post(f"{B}/inbox/leads/{by['Priya Sharma']['id']}/followup-draft", headers=H2, json={}).status_code == 404)

print("\nFAILED:" if fails else "\nALL STEPS PASSED", fails or "")
sys.exit(1 if fails else 0)

"""Sprint 1 end-to-end smoke test against a RUNNING backend on localhost:8010 with a real MongoDB.

Run: docker run -d --name pai-mongo -p 27017:27017 mongo:7
     cd backend && DATABASE_NAME=propertyai_e2e PYTHONPATH=. .venv/Scripts/python.exe -m uvicorn app.main:app --port 8010
     .venv/Scripts/python.exe scripts/e2e_smoke.py
"""
import json, random, sys, httpx

B = "http://localhost:8010/api/v1"
UA = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile Safari/604.1"}
phone = "9" + "".join(random.choice("0123456789") for _ in range(9))
c = httpx.Client(timeout=30)
fails = []


def step(name, r, ok=(200,), show=None):
    good = r.status_code in ok
    print(("PASS" if good else "FAIL"), name, r.status_code, (show(r) if good and show else ("" if good else r.text[:300])))
    if not good:
        fails.append(name)
    return r


r = step("otp request", c.post(f"{B}/join/otp/request", json={"phone": phone}), show=lambda r: "dev_code=" + str(r.json().get("dev_code")))
code = r.json().get("dev_code")
r = step("otp verify", c.post(f"{B}/join/otp/verify", json={"phone": phone, "code": code}),
         show=lambda r: f"new={r.json()['is_new_user']} has_site={r.json()['has_site']}")
tok = r.json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
step("wrong otp rejected", c.post(f"{B}/join/otp/verify", json={"phone": phone, "code": "000000"}), ok=(400, 429))

r = step("create site", c.post(f"{B}/join/site", headers=H, json={"name": "Rahul Sharma", "city": "Pune", "languages": ["English", "Hindi", "Marathi"]}),
         show=lambda r: r.json()["site_url"])
slug = r.json()["slug"]
r2 = step("create site idempotent", c.post(f"{B}/join/site", headers=H, json={"name": "Other", "city": "Pune"}), show=lambda r: f"created={r.json()['created']}")
step("public site data", c.get(f"{B}/agent/public/{slug}"), show=lambda r: r.json().get("agent_name"))

text = "2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, 3rd floor of 12, semi furnished, parking, lift, gym"
r = step("ai draft", c.post(f"{B}/listings/ai/draft", headers=H, data={"text": text, "image_count": "1"}),
         show=lambda r: f"price={r.json()['draft'].get('price_inr')} bhk={r.json()['draft'].get('bhk')} missing={r.json()['missing']}")
draft = r.json()["draft"]
body = {k: v for k, v in draft.items() if v is not None}
body["media"] = [{"url": "https://example.com/flat1.jpg", "kind": "image", "order": 0}]
r = step("create listing (draft)", c.post(f"{B}/listings", headers=H, json=body), ok=(200, 201), show=lambda r: r.json()["status"])
lid = r.json()["id"]
r_inc = step("incomplete draft is created but cannot publish", c.post(f"{B}/listings", headers=H, json={"title": "x"}), ok=(200, 201))
step("publish rejects incomplete (422)", c.post(f"{B}/listings/{r_inc.json()['id']}/publish", headers=H), ok=(422,))
r = step("publish", c.post(f"{B}/listings/{lid}/publish", headers=H), show=lambda r: r.json()["status"])
step("my listings", c.get(f"{B}/listings", headers=H), show=lambda r: f"{len(r.json()['items'])} items")
r = step("public listings by slug", c.get(f"{B}/public/agents/{slug}/listings"), show=lambda r: f"total={r.json()['total']}")
assert r.json()["total"] == 1, "expected exactly one public listing"
step("public listing by id", c.get(f"{B}/public/listings/{lid}"), show=lambda r: r.json()["title"])

anon = "anon-" + "".join(random.choice("abcdef0123456789") for _ in range(12))
ev = {"agent_slug": slug, "anon_id": anon, "listing_id": lid, "source": "instagram", "utm": {"utm_campaign": "baner"}}
step("track listing_view x2", c.post(f"{B}/t/event", headers=UA, json={**ev, "type": "listing_view"}), ok=(202,))
c.post(f"{B}/t/event", headers=UA, json={**ev, "type": "listing_view"})
step("track whatsapp_click", c.post(f"{B}/t/event", headers=UA, json={**ev, "type": "whatsapp_click"}), ok=(202,))
r = step("bot event ignored", c.post(f"{B}/t/event", headers={"User-Agent": "Googlebot/2.1"}, json={**ev, "type": "page_view"}), ok=(202,), show=lambda r: r.text)
step("inquiry without consent rejected", c.post(f"{B}/t/inquiry", json={**ev, "name": "Amit", "phone": "9876543210", "consent": False}), ok=(400,))
step("inquiry", c.post(f"{B}/t/inquiry", json={**ev, "name": "Amit Buyer", "phone": "98765 43210", "message": "Is it available?", "consent": True}),
     show=lambda r: r.text)

r = step("inbox leads", c.get(f"{B}/inbox/leads", headers=H), show=lambda r: json.dumps([(l["name"], l["score"], l["temperature"]) for l in r.json()["leads"]]))
leads = r.json()["leads"]
assert len(leads) == 1 and leads[0]["score"] >= 35, leads
r = step("lead detail timeline", c.get(f"{B}/inbox/leads/{leads[0]['id']}", headers=H), show=lambda r: [t["type"] for t in r.json()["timeline"]])
step("stage update", c.patch(f"{B}/inbox/leads/{leads[0]['id']}", headers=H, json={"stage": "site_visit", "note": "Sat 11am"}), show=lambda r: r.json()["stage"])

# isolation: another agent sees nothing
p2 = "8" + "".join(random.choice("0123456789") for _ in range(9))
d2 = c.post(f"{B}/join/otp/request", json={"phone": p2}).json()["dev_code"]
t2 = c.post(f"{B}/join/otp/verify", json={"phone": p2, "code": d2}).json()["access_token"]
H2 = {"Authorization": f"Bearer {t2}"}
r = step("other agent inbox empty", c.get(f"{B}/inbox/leads", headers=H2), show=lambda r: f"{len(r.json()['leads'])} leads")
assert r.json()["leads"] == []
step("other agent cannot read my listing", c.get(f"{B}/listings/{lid}", headers=H2), ok=(404,))
step("unauthenticated inbox blocked", c.get(f"{B}/inbox/leads"), ok=(401,))

print("\nFAILED:" if fails else "\nALL STEPS PASSED", fails or "")
sys.exit(1 if fails else 0)

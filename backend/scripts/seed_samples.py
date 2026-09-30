"""Seed clearly labelled SAMPLE listings (Kharadi, Upper Kharadi, Wagholi) on an agent's site through the public API.

  python scripts/seed_samples.py --api https://34-180-39-243.sslip.io --phone 9767971656 --code 585040       # live (invite mode)
  python scripts/seed_samples.py --api http://localhost:8000 --phone 9XXXXXXXXX                              # local (dev OTP)
  add --fix-price LISTING_ID=8500000 to correct the price of one of the agent's own listings

Every title starts with "Sample:" - the site, the cards and the captions then label it "SAMPLE LISTING" and say it is not available.
Prices are round, believable figures for illustration only; no RERA numbers are invented (left empty on purpose).
"""
import argparse
import sys

import httpx

SAMPLES = [
    dict(locality="Kharadi", bhk=2, carpet_sqft=1050, price_inr=9_500_000, floor=7, total_floors=22, furnishing="semi", possession="ready",
         amenities=["Parking", "Lift", "Gym", "Security", "Power backup"]),
    dict(locality="Kharadi", bhk=3, carpet_sqft=1450, price_inr=14_500_000, floor=12, total_floors=25, furnishing="furnished", possession="ready",
         amenities=["Parking", "Lift", "Gym", "Swimming pool", "Clubhouse", "Security"]),
    dict(locality="Upper Kharadi", bhk=2, carpet_sqft=980, price_inr=7_800_000, floor=4, total_floors=14, furnishing="unfurnished",
         possession="under_construction", amenities=["Parking", "Lift", "Garden", "Security"]),
    dict(locality="Upper Kharadi", bhk=3, carpet_sqft=1320, price_inr=11_500_000, floor=9, total_floors=18, furnishing="semi", possession="ready",
         amenities=["Parking", "Lift", "Gym", "Garden", "Power backup"]),
    dict(locality="Wagholi", bhk=2, carpet_sqft=850, price_inr=5_800_000, floor=3, total_floors=12, furnishing="unfurnished",
         possession="under_construction", amenities=["Parking", "Lift", "Security", "Garden"]),
    dict(locality="Wagholi", bhk=3, carpet_sqft=1150, price_inr=8_200_000, floor=6, total_floors=15, furnishing="semi", possession="ready",
         amenities=["Parking", "Lift", "Gym", "Clubhouse", "Security"]),
]


def money(n: int) -> str:
    return f"{n / 10_000_000:g} Cr" if n >= 10_000_000 else f"{n / 100_000:g} Lakh"


def body(s: dict) -> dict:
    title = f"Sample: {s['bhk']} BHK apartment for sale in {s['locality']}, Pune"
    desc = (f"SAMPLE LISTING: an illustration of how a listing looks on PUNE Property. This home is not available for sale.\n\n"
            f"{s['bhk']} BHK apartment in {s['locality']}, Pune, {s['carpet_sqft']:,} sq ft carpet area, priced at {money(s['price_inr'])} in this example. "
            f"Real listings show the RERA number, exact possession date and photos provided by the agent.")
    return {"title": title, "transaction": "sale", "property_type": "apartment", "city": "Pune", "visibility": "network",
            "description": {"en": desc}, **s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", required=True)
    ap.add_argument("--phone", required=True)
    ap.add_argument("--code")
    ap.add_argument("--fix-price", help="LISTING_ID=RUPEES")
    a = ap.parse_args()
    api = a.api.rstrip("/") + "/api/v1"
    with httpx.Client(timeout=60) as c:
        req = c.post(f"{api}/join/otp/request", json={"phone": a.phone})
        code = a.code or req.json().get("dev_code")
        if not code:
            sys.exit("no code: pass --code (invite mode) or run against a dev-OTP backend")
        v = c.post(f"{api}/join/otp/verify", json={"phone": a.phone, "code": code})
        if v.status_code != 200:
            sys.exit(f"sign-in failed: HTTP {v.status_code}")
        h = {"Authorization": "Bearer " + v.json()["access_token"]}
        if a.fix_price:
            lid, price = a.fix_price.split("=")
            r = c.patch(f"{api}/listings/{lid}", json={"price_inr": int(price)}, headers=h)
            print("fixed price", lid, r.status_code, r.json().get("price_inr"))
            return
        existing = c.get(f"{api}/listings", headers=h).json()
        items = existing.get("items", existing) if isinstance(existing, dict) else existing
        have = {(i.get("title") or "") for i in items}
        for s in SAMPLES:
            b = body(s)
            if b["title"] in have and False:
                continue
            r = c.post(f"{api}/listings", json=b, headers=h)
            if r.status_code >= 300:
                print("create failed", r.status_code, r.text[:200])
                continue
            lid = r.json()["id"]
            p = c.post(f"{api}/listings/{lid}/publish", json={}, headers=h)
            print(f"{b['title']} -> {p.status_code} {money(s['price_inr'])}")


if __name__ == "__main__":
    main()

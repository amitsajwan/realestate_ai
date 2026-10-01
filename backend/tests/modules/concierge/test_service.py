import re

import pytest
from pydantic import ValidationError

from app.modules.concierge import attribution
from app.modules.concierge.service import CONSENT_TEXT, ConciergeError, mask_phone
from app.modules.listings.schemas import ListingCreate, ListingUpdate
from app.modules.listings.service import ListingError

from .helpers import FULL, PHONE, make, pack

pytestmark = pytest.mark.asyncio
PHONE10 = PHONE[3:]


async def agent(svc, name="Rahul Sharma", reissue=False):
    return await svc.create_agent("OWNER", name, PHONE, "Rahul, Baner", reissue)


async def test_create_agent_returns_code_and_message_and_site():
    svc, db, invites = make()
    out = await agent(svc)
    assert len(out["code"]) == 6 and out["code"].isdigit() and out["created"]
    assert out["code"] in out["whatsapp_message"] and PHONE10 in out["whatsapp_message"]
    assert out["whatsapp_message"].startswith("Hi Rahul")
    a = out["agent"]
    assert a["mobile"] == "98******10" and a["site_url"].startswith("https://pune.test/agent/")
    await invites.verify(PHONE, out["code"])  # the code really works for his login
    # codes are never stored in plain text
    assert out["code"] not in str(db.get_collection("invites").docs)
    assert out["code"] not in str(db.get_collection("concierge_audit").docs)


async def test_existing_agent_is_reused_and_code_only_reissued_on_request():
    svc, db, invites = make()
    first = await agent(svc)
    again = await agent(svc)
    assert again["agent"]["id"] == first["agent"]["id"] and not again["created"] and again["code"] is None
    assert len(db.get_collection("concierge_agents").docs) == 1
    fresh = await agent(svc, reissue=True)
    assert fresh["code"] and fresh["reissued"]
    await invites.verify(PHONE, fresh["code"])


async def test_checklist_progress_grows_with_work():
    svc, db, _ = make()
    a = (await agent(svc))["agent"]
    assert a["progress"] == {"done": 0, "total": 8}
    aid = a["id"]
    await svc.update_branding("OWNER", aid, {"logo": "/uploads/images/logo.png", "photo": "/uploads/images/me.png"})
    for i in range(3):
        l = await svc.create_listing("OWNER", aid, ListingCreate(**{**FULL, "title": f"Home {i}"}))
        await svc.publish_listing("OWNER", aid, l["id"])
    await svc.record_consent("OWNER", aid)
    done = {c["key"] for c in (await svc.list_agents())[0]["checklist"] if c["done"]}
    assert done == {"logo", "photo", "first_listing", "three_listings", "consent"}
    assert (await svc.list_agents())[0]["last_activity"]


async def test_unknown_agent_is_404_everywhere():
    svc, _, _ = make()
    for call in (svc.get_agent("nope"), svc.record_consent("O", "nope"), svc.create_listing("O", "nope", ListingCreate(**FULL)),
                 svc.publish_listing("O", "nope", "x"), svc.update_branding("O", "nope", {}), svc.post_listing("O", "nope", "x", ["instagram"])):
        with pytest.raises(ConciergeError) as e:
            await call
        assert e.value.status_code == 404


async def test_on_behalf_listing_lives_under_the_agent_and_is_validated():
    svc, db, _ = make()
    aid = (await agent(svc))["agent"]["id"]
    l = await svc.create_listing("OWNER", aid, ListingCreate(**FULL))
    assert l["agent_id"] == aid and l["status"] == "draft"
    with pytest.raises(ValidationError):  # Pune only
        ListingCreate(**{**FULL, "city": "Delhi"})
    with pytest.raises(ConciergeError) as e:  # price sanity: a rent figure typed as a sale price
        await svc.create_listing("OWNER", aid, ListingCreate(**{**FULL, "price_inr": 45000}))
    assert e.value.status_code == 422
    with pytest.raises(ConciergeError):
        await svc.patch_listing("OWNER", aid, l["id"], ListingUpdate(price_inr=90_000_000_000))
    patched = await svc.patch_listing("OWNER", aid, l["id"], ListingUpdate(locality="Aundh"))
    assert patched["locality"] == "Aundh"
    pub = await svc.publish_listing("OWNER", aid, l["id"])
    assert pub["status"] == "live"
    with pytest.raises(ListingError) as e2:  # full publish validation still applies
        bare = await svc.create_listing("OWNER", aid, ListingCreate(title="x"))
        await svc.publish_listing("OWNER", aid, bare["id"])
    assert e2.value.status_code == 422


async def test_other_agents_listing_is_not_reachable_through_this_agent():
    svc, db, _ = make()
    a = (await agent(svc))["agent"]["id"]
    other = (await svc.create_agent("OWNER", "Sita Rao", "+919811111111"))["agent"]["id"]
    l = await svc.create_listing("OWNER", other, ListingCreate(**FULL))
    with pytest.raises(ListingError) as e:
        await svc.patch_listing("OWNER", a, l["id"], ListingUpdate(locality="Aundh"))
    assert e.value.status_code == 404


async def test_audit_rows_record_keys_not_values_or_secrets():
    svc, db, _ = make()
    out = await agent(svc)
    aid = out["agent"]["id"]
    l = await svc.create_listing("OWNER", aid, ListingCreate(**FULL))
    await svc.patch_listing("OWNER", aid, l["id"], ListingUpdate(locality="Aundh"))
    await svc.publish_listing("OWNER", aid, l["id"])
    rows = db.get_collection("concierge_audit").docs
    actions = [r["action"] for r in rows]
    assert actions == ["agent.create", "invite.issue", "listing.create", "listing.update", "listing.publish"]
    assert all(r["by"] == "OWNER" and r["at"] and r["agent_id"] == aid for r in rows)
    assert rows[3]["keys"] == ["locality"] and rows[4]["before_status"] == "draft" and rows[4]["after_status"] == "live"
    blob = str(rows)
    assert "Aundh" not in blob and out["code"] not in blob and PHONE10 not in blob


async def test_consent_wording_and_revoke():
    svc, _, _ = make()
    aid = (await agent(svc))["agent"]["id"]
    with pytest.raises(ConciergeError):
        await svc.record_consent("OWNER", aid, text="something else")
    c = await svc.record_consent("OWNER", aid, text=CONSENT_TEXT)
    assert c["given"] and c["recorded_by"] == "OWNER" and c["at"] and c["text"] == CONSENT_TEXT
    assert (await svc.get_agent(aid))["consent"]["given"]
    assert not (await svc.record_consent("OWNER", aid, given=False))["given"]
    assert not await svc.has_consent(aid)


async def post_ready(svc, db):
    aid = (await agent(svc))["agent"]["id"]
    l = await svc.create_listing("OWNER", aid, ListingCreate(**FULL))
    await svc.publish_listing("OWNER", aid, l["id"])
    db.get_collection("marketing_packs").docs.append(pack(aid, l["id"]))
    return aid, l["id"]


async def test_posting_requires_consent_then_posts_with_attribution():
    svc, db, _ = make()
    aid, lid = await post_ready(svc, db)
    with pytest.raises(ConciergeError) as e:
        await svc.post_listing("OWNER", aid, lid, ["facebook_page"])
    assert e.value.status_code == 409 and not db.get_collection("publications").docs
    await svc.record_consent("OWNER", aid)
    pubs = await svc.post_listing("OWNER", aid, lid, ["facebook_page", "instagram"])
    assert [p["status"] for p in pubs] == ["dry_run", "dry_run"]
    fb, ig = (p["payload"]["text"] for p in pubs)
    assert "Listed by Rahul Sharma" in fb and re.search(r"Interested\? https?://\S+/i/\w+", fb)
    assert "Listed by Rahul Sharma" in ig and "Link in our bio" in ig and "http" not in ig
    assert db.get_collection("concierge_audit").docs[-1]["action"] == "listing.post"


async def test_captions_preview_matches_what_is_posted_and_records_nothing():
    svc, db, _ = make()
    aid, lid = await post_ready(svc, db)
    await svc.record_consent("OWNER", aid)
    preview = await svc.captions(aid, lid, ["facebook_page", "instagram"])
    assert not db.get_collection("publications").docs
    pubs = await svc.post_listing("OWNER", aid, lid, ["facebook_page", "instagram"])
    assert [preview["facebook_page"]["text"], preview["instagram"]["text"]] == [p["payload"]["text"] for p in pubs]


async def test_hub_item_added_only_when_instagram_really_published():
    from app.modules.social.config import SocialConfig
    svc, db, _ = make()  # dry run: nothing real posted, so nothing on the public hub
    aid, lid = await post_ready(svc, db)
    await svc.record_consent("OWNER", aid)
    await svc.post_listing("OWNER", aid, lid, ["instagram"])
    assert not db.get_collection("hub_items").docs
    # register directly as a published post would
    listing = await db.get_collection("listings").find_one({"_id": lid})
    await attribution.register_hub_item(db, aid, listing, pack(aid, lid), "https://media.test", "https://ig/p/1")
    item = db.get_collection("hub_items").docs[0]
    assert item["_id"] == f"listing:{lid}" and item["interest_code"] and item["image_url"].startswith("https://media.test/uploads")


async def test_owner_own_listing_gets_no_attribution(monkeypatch):
    svc, db, _ = make()
    aid, lid = await post_ready(svc, db)
    monkeypatch.setenv("CONCIERGE_OWNER_IDS", aid)
    listing = await db.get_collection("listings").find_one({"_id": lid})
    assert await attribution.attribution_text(db, aid, listing, "facebook_page") == ""


async def test_sample_listing_gets_no_attribution():
    svc, db, _ = make()
    aid, lid = await post_ready(svc, db)
    assert await attribution.attribution_text(db, aid, {"_id": "S", "title": "Sample 2 BHK"}, "instagram") == ""


def test_attribution_line_with_and_without_business_name():
    base = {"agent_name": "Rahul Sharma", "branding_data": {}}
    assert attribution.attribution_line(base) == "Listed by Rahul Sharma on Avasetu"
    biz = {**base, "branding_data": {"business_name": "Baner Homes", "rera_agent_no": "A52100012345"}}
    assert attribution.attribution_line(biz) == "Listed by Baner Homes on Avasetu | RERA agent reg: A52100012345"
    assert attribution.attribution_line({"agent_name": "", "branding_data": {}}) == ""


def test_attribution_never_contains_a_phone_number():
    nasty = {"agent_name": "Rahul 98765 43210", "phone": "9876543210",
             "branding_data": {"business_name": "Call +91 9876543210 Homes", "rera_agent_no": "9876543210"}}
    line = attribution.attribution_line(nasty)
    assert not re.search(r"\d{8,}", line.replace(" ", "")) and "9876" not in line


def test_mask_phone():
    assert mask_phone("+919876543210") == "98******10" and mask_phone("") == ""


async def test_branding_update_uses_the_site_update_with_all_branding_fields():
    svc, db, _ = make()
    aid = (await agent(svc))["agent"]["id"]
    out = await svc.update_branding("OWNER", aid, {"logo": "/uploads/images/logo.png", "rera_agent_no": "a52100012345", "preset": "emerald"})
    assert out is not None
    prof = await svc.profiles.find_one({"agent_id": aid})
    assert prof["branding_data"]["logo"] == "/uploads/images/logo.png" and prof["branding_data"]["rera_agent_no"] == "A52100012345"
    with pytest.raises(ConciergeError) as e:
        await svc.update_branding("OWNER", aid, {"logo": "http://evil.example/x.png"})
    assert e.value.status_code == 422


async def test_no_phone_number_in_agent_responses():
    svc, db, _ = make()
    out = await agent(svc)
    aid = out["agent"]["id"]
    await svc.create_listing("OWNER", aid, ListingCreate(**FULL))
    for payload in (out["agent"], await svc.get_agent(aid), (await svc.list_agents())[0], await svc.get_branding(aid)):
        assert PHONE10 not in str(payload)

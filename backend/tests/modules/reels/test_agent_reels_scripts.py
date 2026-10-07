"""The one-off scripts after the sample-data clean-up: new captions for the queued agent reels, and the list of sample posts to delete."""
import asyncio

from app.modules.reels import agent_reels as ar
from scripts import fix_agent_reel_captions as fix
from scripts import list_sample_posts as lsp

OLD = "Still typing?\n\nAvasetu is for Pune property agents: your listings, posts and leads in one place. Screens show sample data."


class Coll:
    def __init__(self, docs):
        self.docs = docs
        self.updates = []

    def find(self, query):
        coll = self

        class Cursor:
            async def to_list(self, _n):
                return list(coll.docs)
        return Cursor()

    async def update_one(self, flt, upd):
        self.updates.append((flt, upd))
        d = next(d for d in self.docs if d["_id"] == flt["_id"])
        d.update(upd.get("$set", {}))
        for k in upd.get("$unset", {}):
            d.pop(k, None)


class Db:
    def __init__(self, docs):
        self.c = Coll(docs)

    def get_collection(self, _name):
        return self.c


def _row(i, code, channel, status="approved", caption=OLD, video=None):
    return {"_id": i, "slug": f"agent-reel-{code.lower()}", "channel": channel, "status": status, "caption": caption, "video": video,
            "creative": {"source": "agent_reels", "reel_code": code, "reel_key": f"agent-{code.lower()}"}}


def test_fix_rewrites_open_agent_reel_captions_and_drops_the_render(tmp_path):
    docs = [_row("1", "B3", "instagram", video="calendar/reels/agent-b3.mp4"), _row("2", "B3", "facebook_page", status="planned"),
            _row("3", "A1", "facebook_page", status="published"),
            {**_row("4", "C2", "instagram"), "creative": {"source": "other", "reel_code": "C2"}}]
    old = tmp_path / "calendar" / "reels"
    old.mkdir(parents=True)
    (old / "agent-b3.mp4").write_bytes(b"x")
    (old / "agent-b3-cover.jpg").write_bytes(b"x")
    db, said = Db(docs), []
    assert asyncio.run(fix.run(db, tmp_path, apply=False, say=said.append)) == 2
    assert db.c.updates == [] and (old / "agent-b3.mp4").is_file()                      # a dry run writes nothing
    assert "BEFORE:" in "\n".join(said) and "Screens show sample data" in "\n".join(said)
    assert asyncio.run(fix.run(db, tmp_path, apply=True, say=said.append)) == 2
    assert docs[0]["caption"] == ar.caption("B3", "instagram") and "video" not in docs[0] and docs[0]["status"] == "approved"
    assert docs[1]["caption"] == ar.caption("B3", "facebook_page") and "/pilot?src=reel_b3_fb" in docs[1]["caption"]
    assert docs[2]["caption"] == OLD and docs[3]["caption"] == OLD                      # history and other rows untouched
    assert not any(old.iterdir())                                                        # the stale render is gone
    assert asyncio.run(fix.run(db, tmp_path, apply=True, say=said.append)) == 0          # idempotent
    assert all("sample" not in d["caption"].lower() for d in docs[:2])


def test_list_sample_posts_finds_published_sample_homes_only():
    docs = [{"_id": "a", "slug": "kharadi-2bhk-ready", "channel": "facebook_page", "status": "published", "kind": "showcase",
             "caption": "2 BHK in Kharadi", "permalink": "https://fb/1", "external_id": "1_2"},
            {"_id": "b", "slug": "agent-reel-a1", "channel": "instagram", "status": "published", "kind": "reel",
             "caption": OLD, "permalink": "https://ig/p/x", "external_id": "179"},
            {"_id": "c", "slug": "hd-compare", "channel": "instagram", "status": "published", "kind": "post", "caption": "Compare five projects"},
            {"_id": "d", "slug": "wagholi-2bhk-ready", "channel": "instagram", "status": "skipped", "kind": "showcase", "caption": "Sample"}]
    said = []
    rows = asyncio.run(lsp.run(Db(docs), say=said.append))
    assert [r["_id"] for r in rows] == ["a", "b"] or sorted(r["_id"] for r in rows) == ["a", "b"]
    out = "\n".join(said)
    assert "https://fb/1" in out and "1_2" in out and "https://ig/p/x" in out and "hd-compare" not in out
    assert "1 on Facebook" in out and "1 on Instagram" in out

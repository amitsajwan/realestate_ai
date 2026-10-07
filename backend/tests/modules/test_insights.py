"""The insights collector (modules/insights): finds working metrics by itself, snapshots at 1h/24h/72h/7d, asks a person only once."""
from datetime import datetime, timedelta, timezone

from app.modules.insights import collector, graph

from .fakes import FakeDb

TOKEN = "EAAsecret123"
PUB = datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)


class FakeGraph:
    """Answers like the Graph API: `good` metric names work, others fail with #100; `denied` makes every call a permission error."""

    def __init__(self, good=("views", "reach", "ig_reels_avg_watch_time"), denied=False):
        self.good, self.denied, self.calls = set(good), denied, []

    async def __call__(self, url, params):
        self.calls.append((url, params.get("metric")))
        if self.denied:
            return 400, {"error": {"code": 10, "message": f"(#10) Application does not have permission, token {TOKEN}"}}
        names = (params.get("metric") or "").split(",")
        bad = [n for n in names if n not in self.good]
        if bad:
            return 400, {"error": {"code": 100, "message": f"(#100) metric[0] must be one of the following values ... {bad[0]}"}}
        return 200, {"data": [{"name": n, "values": [{"value": 10 * (i + 1)}]} for i, n in enumerate(names)]}


async def _setup(graph_fake, now):
    db = FakeDb()
    await db.get_collection("content_calendar").insert_one({
        "_id": "r1", "slug": "reel-w1-tip", "kind": "reel", "channel": "instagram", "status": "published", "external_id": "1789",
        "published_at": PUB, "tags": {"format": "tip", "hook_type": "question"}})
    await db.get_collection("content_calendar").insert_one({
        "_id": "dry", "slug": "x", "kind": "reel", "channel": "instagram", "status": "published", "external_id": "dryrun_ab",
        "published_at": PUB})
    sent = []

    async def notify(db_, owner, kind, summary, ref):
        sent.append((owner, kind, summary))
    clock = {"now": now}
    c = collector.Collector(db, graph_fake, "https://graph", TOKEN, ("owner1",), notify, clock=lambda: clock["now"])
    return db, c, sent, clock


def test_snapshots_are_due_only_inside_their_window():
    row = {"_id": "r", "kind": "reel", "channel": "instagram", "status": "published", "external_id": "1", "published_at": PUB}
    labels = lambda now, taken=set(): [l for _, l, _ in collector.due_snapshots([row], taken, now)]
    assert labels(PUB + timedelta(minutes=30)) == []
    assert labels(PUB + timedelta(hours=1, minutes=5)) == ["1h"]
    assert labels(PUB + timedelta(hours=1, minutes=5), {("r", "1h")}) == []
    assert labels(PUB + timedelta(hours=5)) == []                    # the 1h window closed: never a late, mislabelled number
    assert labels(PUB + timedelta(hours=25)) == ["24h"]
    assert labels(PUB + timedelta(days=7, hours=1)) == ["7d"]


async def test_it_finds_the_working_metrics_itself_and_records_a_tagged_snapshot():
    g = FakeGraph()
    db, c, sent, clock = await _setup(g, PUB + timedelta(hours=1, minutes=10))
    counts = await c.collect_once()
    assert counts["taken"] == 1 and sent == []
    caps = await db.get_collection("insights_capabilities").find_one({"_id": "instagram reel"})
    assert caps["working"] == ["views", "reach", "ig_reels_avg_watch_time"] and "plays" in caps["failed"]
    snap = await db.get_collection("content_metrics").find_one({"post_id": "r1"})
    assert snap["age_label"] == "1h" and snap["metrics"] == {"views": 10, "reach": 20, "ig_reels_avg_watch_time": 30}
    assert snap["tags"]["format"] == "tip"                            # results group by what the post was
    assert all("dryrun" not in u for u, _ in g.calls)                 # a dry-run post is never asked about
    # the next cycle: nothing new is due, and the metric names are not probed again
    n = len(g.calls)
    assert (await c.collect_once())["taken"] == 0 and len(g.calls) == n
    # a day later: one request with the known names, no new probing
    clock["now"] = PUB + timedelta(hours=24, minutes=5)
    assert (await c.collect_once())["taken"] == 1 and len(g.calls) == n + 1


async def test_a_retired_metric_name_is_noticed_and_rechecked_without_a_person():
    g = FakeGraph()
    db, c, sent, clock = await _setup(g, PUB + timedelta(hours=1, minutes=10))
    await c.collect_once()
    g.good.discard("reach")                                           # Meta retires a name
    clock["now"] = PUB + timedelta(hours=24, minutes=5)
    assert (await c.collect_once())["failed"] == 1                    # the known-good request fails ...
    assert (await c.collect_once())["taken"] == 1                     # ... next cycle it checks again and carries on without it
    caps = await db.get_collection("insights_capabilities").find_one({"_id": "instagram reel"})
    assert "reach" not in caps["working"] and sent == []


async def test_a_missing_permission_tells_the_owner_once_and_never_shows_the_token():
    db, c, sent, clock = await _setup(FakeGraph(denied=True), PUB + timedelta(hours=1, minutes=10))
    assert (await c.collect_once())["no_metrics"] == 1
    clock["now"] = PUB + timedelta(hours=1, minutes=40)
    await c.collect_once()
    assert len(sent) == 1 and sent[0][:2] == ("owner1", "content_needs_you")
    assert "permission" in sent[0][2] and TOKEN not in sent[0][2]


def test_off_in_dry_run_or_without_a_token(monkeypatch):
    from app.platform.meta_graph.config import SocialConfig
    monkeypatch.delenv("INSIGHTS_ENABLED", raising=False)
    assert not collector.enabled(SocialConfig(dry_run=True, page_token="t"))
    assert not collector.enabled(SocialConfig(dry_run=False, page_token=""))
    assert collector.enabled(SocialConfig(dry_run=False, page_token="t"))
    monkeypatch.setenv("INSIGHTS_ENABLED", "off")
    assert not collector.enabled(SocialConfig(dry_run=False, page_token="t"))


def test_graph_targets():
    assert graph.target_of({"channel": "facebook_page", "kind": "post", "tags": {"published_as": "reel"}}) == "facebook reel"
    assert graph.target_of({"channel": "instagram", "kind": "showcase"}) == "instagram post"

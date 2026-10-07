"""scripts/insights_check.py (X-1): one request per metric, the token never shown, the right list for each kind of post."""
from scripts import insights_check as ic

TOKEN = "EAAsecret123"


def fake_get(answers):
    calls = []

    async def get(url, params):
        calls.append((url, dict(params)))
        metric = params.get("metric")
        if url.endswith("/debug_token"):
            return 200, {"data": {"scopes": ["pages_read_engagement", "instagram_basic"]}}
        status, body = answers.get(metric, (400, {"error": {"message": f"(#100) {metric} is not valid, token {TOKEN}"}}))
        return status, body
    return get, calls


async def test_each_metric_is_asked_alone_and_errors_never_show_the_token():
    get, calls = fake_get({"views": (200, {"data": [{"name": "views", "values": [{"value": 812}]}]}),
                           "ig_reels_avg_watch_time": (200, {"data": [{"name": "ig_reels_avg_watch_time", "total_value": {"value": 4200}}]})})
    res = await ic.probe(get, "https://graph", "1789", "instagram reel", TOKEN)
    by = {r["metric"]: r for r in res}
    assert len(calls) == len(ic.CANDIDATES["instagram reel"][1]) and all("," not in c[1]["metric"] for c in calls)
    assert by["views"]["ok"] and by["views"]["value"] == 812 and by["ig_reels_avg_watch_time"]["value"] == 4200
    assert not by["plays"]["ok"] and "is not valid" in by["plays"]["reason"]
    assert all(TOKEN not in r["reason"] for r in res)
    text = ic.table({"instagram reel": ({"slug": "reel-w1-tip"}, res)}, await ic.permissions(get, "https://graph", TOKEN))
    assert TOKEN not in text and "| views | yes | 812 |" in text and "instagram_basic" in text
    assert "No published post of this kind" in text   # the kinds with nothing published yet are listed, not hidden


def test_targets_and_latest_published_row_per_kind():
    rows = [{"channel": "instagram", "kind": "reel", "external_id": "1", "published_at": "2026-10-01", "slug": "old"},
            {"channel": "instagram", "kind": "reel", "external_id": "2", "published_at": "2026-10-05", "slug": "new"},
            {"channel": "instagram", "kind": "reel", "external_id": "dryrun_ab", "published_at": "2026-10-06", "slug": "dry"},
            {"channel": "facebook_page", "kind": "post", "external_id": "3", "published_at": "2026-10-04", "slug": "carousel",
             "tags": {"published_as": "reel"}},
            {"channel": "facebook_page", "kind": "post", "external_id": "4", "published_at": "2026-10-03", "slug": "card"}]
    picks = ic.latest_per_target(rows)
    assert picks["instagram reel"]["slug"] == "new"          # the newest real one; a dry-run id is never asked about
    assert picks["facebook reel"]["slug"] == "carousel"       # slides sent as a Reel are measured as a reel
    assert picks["facebook post"]["slug"] == "card" and "instagram post" not in picks

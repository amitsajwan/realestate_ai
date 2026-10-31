"""Plans collected for target projects from the pages that rank for them (app/modules/areastats/planfind.py)."""
import io
from datetime import datetime, timezone

from PIL import Image

from app.modules.areastats import planfind, webfacts

NOW = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)


def plan_png(shade: int) -> bytes:
    out = io.BytesIO()
    im = Image.new("RGB", (800, 600), "white")
    for x in range(0, 800, 40 + shade):
        for y in range(600):
            im.putpixel((x, y), (0, 0, 0))
    im.save(out, "PNG")
    return out.getvalue()


async def test_plan_pictures_of_pages_about_the_project_are_kept_as_web_sources(tmp_path, monkeypatch):
    doc = {"_id": "P52100000001", "regno": "P52100000001", "name": "SUN EMERALD", "pune_place": "kharadi", "promoter": "Sun"}

    async def results(store, d, name, search, now):
        return [{"link": "https://housiey.com/projects/sun-emerald"}, {"link": "https://other.example/x"}]
    monkeypatch.setattr(webfacts, "results_for", results)
    monkeypatch.setattr(webfacts, "sources_for", lambda d, r, n, limit=0: [
        {"url": "https://housiey.com/projects/sun-emerald", "site": "housiey.com", "official": False},
        {"url": "https://other.example/x", "site": "other.example", "official": False}])
    monkeypatch.setattr(webfacts, "about_project", lambda d, n, text, src: (src["site"] == "housiey.com", "page does not name the project"))
    pages = {"https://housiey.com/projects/sun-emerald": '<img src="/img/sun-emerald-2bhk-floor-plan.jpg" alt="2 BHK floor plan">'
             '<img src="/img/clubhouse.jpg" alt="clubhouse">', "https://other.example/x": '<img src="/p/floor-plan.jpg">'}

    async def fetch(url):
        return pages.get(url)

    async def image(url):
        return plan_png(3) if "floor-plan" in url else None
    out = (await planfind.collect(None, doc, NOW, fetch=fetch, image=image, uploads=tmp_path))["plan_sources"]
    [p] = out["plans"]
    assert p["site"] == "housiey.com" and p["source"] == "web" and (tmp_path / p["path"]).is_file()
    assert [r["ok"] for r in out["read"]] == [True, False]

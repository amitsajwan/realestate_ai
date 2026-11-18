"""The deep mind's lookups (docs/plan/buyer-mind.md). Every one only reads, through the owning module's query functions, and
gives the model a short summary, not the whole record: tokens cost money and a long record buries the facts that matter.

A project's counts and dates are the whole project's when its page stands for several MahaRERA registrations
(`areastats.pages.project_scope`, CLAUDE.md rule 11): `project_summary` takes them from the page's `project` scope and says
so, and gives one registration's own figures only under that registration's number.
"""
from typing import Any, Awaitable, Callable, Optional

from app.platform.text import money
from app.platform.toolloop import Tool

ProjectReader = Callable[[str], Awaitable[Optional[dict]]]          # slug -> areastats.pages.project_page
AreaSearch = Callable[[str], Awaitable[list]]                       # question -> knowledge.vectors.search passages

MAX_PRICE_ROWS = 8
MAX_SAME_AREA = 6
MAX_PASSAGES = 4
PASSAGE_CHARS = 600


def _pick(d: Optional[dict], *keys: str) -> dict:
    return {k: d[k] for k in keys if isinstance(d, dict) and d.get(k) not in (None, "", [], {})}


def _inr(v: Any) -> Optional[str]:
    return money(int(v)) if isinstance(v, (int, float)) and v > 0 else None


def _price_row(r: dict) -> dict:
    """A published price as the buyer will read it ("₹68 Lakh"), so a draft's figures can be checked against what was looked up."""
    return {k: v for k, v in {"bhk": r.get("bhk"), "from": _inr(r.get("from_inr")), "to": _inr(r.get("to_inr")),
                              "sqft": r.get("sqft"), "builder_site": bool(r.get("official")) or None,
                              "sources": [s.get("site") for s in r.get("sources") or [] if s.get("site")] or None}.items() if v}


def project_summary(page: dict) -> dict:
    """What the mind needs of a project page: who builds it, where, when it is due, its homes and prices with their dates and
    sources, and the area's other projects (slugs, so it can look them up and suggest them)."""
    scope = page.get("project")
    out: dict[str, Any] = {
        "name": page.get("marketed_name") or page.get("name"),
        "slug": page.get("slug"),
        "area": (page.get("area") or {}).get("name") or (page.get("pune_place") or {}).get("name"),
        "builder": page.get("promoter"),
        "stage": page.get("stage"),
        "sold_out": page.get("sold_out") or None,
        "homes_not_offices": page.get("homes"),
        "maharera_url": page.get("maharera_url"),
    }
    if scope:
        out["whole_project"] = {"registrations": scope.get("registrations"), "regnos": scope.get("regnos"),
                                **_pick(scope, "units_total", "units_booked", "booked_of", "completion_first", "completion_last",
                                        "completion_passed")}
    else:
        out["registration"] = {"regno": page.get("regno"),
                               **_pick(page, "units_total", "units_booked", "completion_now", "completion_at_registration",
                                       "completion_passed")}
    prices = page.get("prices") or {}
    if prices.get("rows"):
        out["prices"] = {"read_at": prices.get("read_at"), "rows": [_price_row(r) for r in prices["rows"][:MAX_PRICE_ROWS]]}
    if page.get("area_rate"):
        out["area_rate"] = page["area_rate"]
    sizes = [_pick(s, "bhk", "low", "high", "kind") for s in page.get("home_sizes") or []]
    if sizes:
        out["home_sizes"] = sizes
    others = [{**_pick(r, "name", "slug", "bhk", "completion_now", "stage"), **({"price_from": _inr(r["price_from"])}
              if isinstance(r.get("price_from"), (int, float)) else _pick(r, "price_from"))} for r in page.get("same_area") or []]
    if others:
        out["same_area"] = others[:MAX_SAME_AREA]
    if page.get("paragraph"):
        out["about"] = page["paragraph"]
    return {k: v for k, v in out.items() if v not in (None, "", [], {})}


def tools(project: ProjectReader, area_search: AreaSearch) -> list[Tool]:
    async def project_facts(slug: str) -> dict:
        page = await project(str(slug).strip().strip("/").split("/")[-1])
        return project_summary(page) if page else {"error": f"no project page for {slug!r}"}

    async def area_question(question: str) -> dict:
        found = await area_search(str(question))
        rows = [{"text": (getattr(p, "text", None) or (p.get("text") if isinstance(p, dict) else "") or "")[:PASSAGE_CHARS],
                 "source": getattr(p, "title", None) or (p.get("title") if isinstance(p, dict) else None)}
                for p in found[:MAX_PASSAGES]]
        rows = [r for r in rows if r["text"]]
        return {"passages": rows} if rows else {"passages": [], "note": "nothing we publish answers this"}

    return [
        Tool("project_facts",
             "A project's facts from our page for it: builder, area, MahaRERA stage and possession dates, homes, published "
             "prices with their date and source, and other projects in the same area (with slugs you can look up).",
             {"type": "object", "properties": {"slug": {"type": "string", "description": "the project page slug, e.g. 'puraniks-abitante-fiore-ravet'"}},
              "required": ["slug"]},
             project_facts),
        Tool("area_question",
             "Search what we publish about Pune areas (schools, metro, roads, offices, water, guides) for a question.",
             {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
             area_question),
    ]

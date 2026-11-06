"""One project on several pages: what the Rankings data means, and the owner's word on it (Studio → SEO → To do).

Two lists said nearly the same thing and neither said what to do: "possibly one project, on separate pages" and "our pages
competing for one search". Most of the second is normal: a project page and its area list both showing for a project's name, or
two list pages for one area. Only searches showing several pages of one project call for a decision, so those join the first
list, as its evidence, and the rest are labelled "nothing to do".

The owner's word goes on the records, never on a project page's text: `owner_group` joins registrations as a confirmed group
(clusters.owner_groups) and `split_apart` takes them off the list and out of the web proof (samegroup.split_candidates). Both
can be undone. A merge 301s pages, so it never crosses two promoters, whoever asks.
"""
from typing import Dict, List

from app.modules.areastats import clusters, pages, samegroup
from app.modules.areastats.text import group_name, promoter_key, words
from app.modules.newsroom.store import Store

SHOWN = 40
MIN_SHARED_WORDS = 2       # "Aldea Annexo C2" and "Aldea Annexo D": one word ("Suyog") is only a builder's name
MIN_SHARED_CHARS = 6
DECISIONS = ("same", "apart", "undo")
TOWNSHIP_WORDS = {"sector", "sectors"}
TOWNSHIP_HINT = "A township: each sector is usually sold as its own project, so they mostly stay separate."


def _regno(d: dict) -> str:
    return str(d.get("regno") or d["_id"])


def _start(name: str) -> List[str]:
    return [w.lower() for w in words(name) if w.lower() != "the"]


def _share_a_name(a: str, b: str) -> bool:
    """The two names start with the same words: at least MIN_SHARED_WORDS of them."""
    shared: List[str] = []
    for x, y in zip(_start(a), _start(b)):
        if x != y:
            break
        shared.append(x)
    return len(shared) >= MIN_SHARED_WORDS and len("".join(shared)) >= MIN_SHARED_CHARS


def _where(d: dict) -> str:
    return str(d.get("pincode") or "").strip() or d.get("pune_place") or d.get("locality") or ""


def one_project(docs: List[dict]) -> bool:
    """Pages that read as one project: names starting alike, one place, at most one promoter, not already kept apart."""
    if len(docs) < 2 or all(d.get("split_apart") for d in docs):
        return False
    first = docs[0]
    return (len({_where(d) for d in docs}) == 1 and len({promoter_key(d.get("promoter")) for d in docs} - {""}) <= 1
            and all(_share_a_name(first.get("name") or "", d.get("name") or "") for d in docs[1:]))


def _slug(path: str) -> str:
    return path.split("/projects/", 1)[1] if path.startswith("/projects/") else ""


def _page(path: str, by_slug: Dict[str, dict]) -> dict:
    doc = by_slug.get(_slug(path))
    if doc:
        return {"path": path, "kind": "project", "label": doc.get("name") or _slug(path)}
    kind = "area" if path.startswith(("/projects/area/", "/localities/")) else "builder" if path.startswith("/builders/") else "other"
    return {"path": path, "kind": kind, "label": path.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").capitalize()}


def explain(conflict: dict, by_slug: Dict[str, dict]) -> dict:
    """A search showing several of our pages, with what it means. kind: "one_project" (a decision), "project_and_list",
    "lists" or "different" (all normal: nothing to do)."""
    shown = [_page(p, by_slug) for p in conflict.get("pages") or []]
    docs = [by_slug[_slug(p["path"])] for p in shown if p["kind"] == "project"]
    if one_project(docs):
        kind = "one_project"
    elif len(docs) >= 2:
        kind = "different"
    else:
        kind = "project_and_list" if docs else "lists"
    return {**conflict, "pages": shown, "kind": kind, "regnos": sorted(_regno(d) for d in docs) if kind == "one_project" else []}


def _state(docs: List[dict], results: Dict[str, List[dict]]) -> str:
    """proved: a page prints two of the numbers, so the pages merge by themselves. waiting: a number is still to be searched.
    no_proof: all searched and no page links them, so only the owner can say."""
    if samegroup.groups(docs, results):
        return "proved"
    return "no_proof" if all(_regno(d) in results for d in docs) else "waiting"


def _row(docs: List[dict], name: str, where: str, why: str, ours: bool, homes: int, results: Dict[str, List[dict]]) -> dict:
    said = {w.lower() for d in docs for w in words(d.get("name") or "")}
    return {
        "name": name, "where": where, "ours": ours, "why": why, "homes": homes, "state": _state(docs, results),
        "hint": TOWNSHIP_HINT if TOWNSHIP_WORDS & said else None, "searches": [],
        "impressions": sum(int(d.get("gsc_impressions") or 0) for d in docs),
        "members": [{"regno": _regno(d), "name": d.get("name") or "", "slug": d.get("page_slug") or "",
                     "impressions": int(d.get("gsc_impressions") or 0), "in_search": pages.ready_for_search(d)} for d in docs],
    }


def view(docs: List[dict], results: Dict[str, List[dict]], conflicts: List[dict]) -> dict:
    """What the To do tab shows: `split` the decisions, those with a search showing their pages first; `competing` every other
    search showing several of our pages, each with what it means."""
    by_slug = {d["page_slug"]: d for d in docs if d.get("page_slug")}
    cands = clusters.split_candidates([d for d in docs if pages.homes(d) and not pages.is_old(d)])
    rows = [_row(c["docs"], c["name"], c["where"], c["why"], c["ours"], c["homes"], results) for c in cands]
    by_reg = {m["regno"]: r for r in rows for m in r["members"]}
    competing = []
    for raw in conflicts:
        c = explain(raw, by_slug)
        if c["kind"] != "one_project":
            competing.append(c)
            continue
        row = next((by_reg[r] for r in c["regnos"] if r in by_reg), None)
        if row is None:
            found = [by_slug[_slug(p["path"])] for p in c["pages"] if p["kind"] == "project"]
            row = _row(found, group_name([d.get("name") or "" for d in found]), _where(found[0]), "same name", False,
                       sum(int(d.get("units_total") or 0) for d in found), results)
            rows.append(row)
            by_reg.update({m["regno"]: row for m in row["members"]})
        row["searches"].append({k: c.get(k) for k in ("phrase", "impressions", "position")})
    rows.sort(key=lambda r: (not r["searches"], not r["ours"], -r["impressions"], -r["homes"], r["name"]))
    count = {s: sum(1 for r in rows if r["state"] == s) for s in ("proved", "waiting", "no_proof")}
    return {"split": {"total": len(rows), **count, "items": rows[:SHOWN], "decided": decided(docs)}, "competing": competing}


def decided(docs: List[dict]) -> List[dict]:
    """The owner's decisions, to see and undo."""
    groups: Dict[tuple, List[dict]] = {}
    for d in docs:
        for field, decision in (("owner_group", "same"), ("split_apart", "apart")):
            if d.get(field):
                groups.setdefault((decision, d[field]), []).append(d)
    return [{"decision": k[0], "name": group_name([d.get("name") or "" for d in ds]), "regnos": sorted(_regno(d) for d in ds)}
            for k, ds in sorted(groups.items())]


async def decide(store: Store, regnos: List[str], decision: str) -> dict:
    """The owner's word on registrations, in force at once: the cluster step runs here rather than at the next refresh, so the
    row leaves the list and the pages move. Raises ValueError on a decision that cannot stand."""
    wanted = sorted(set(regnos))
    if decision not in DECISIONS:
        raise ValueError("Unknown decision")
    if len(wanted) < 2:
        raise ValueError("Choose at least two pages")
    docs = await store.all_projects()
    mine = [d for d in docs if _regno(d) in wanted]
    if len(mine) != len(wanted):
        raise ValueError("A registration is not on the register")
    if decision == "same" and len({promoter_key(d.get("promoter")) for d in mine} - {""}) > 1:
        raise ValueError("Two different promoters are never merged")
    fields = {"owner_group": wanted[0] if decision == "same" else None, "split_apart": wanted[0] if decision == "apart" else None}
    await store.set_projects(wanted, **fields)
    for d in mine:
        d.update(fields)
    await clusters.assign_clusters(store, docs)
    return {"decision": decision, "regnos": wanted}

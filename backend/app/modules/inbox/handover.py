"""The card an agent gets when a buyer is passed to them: everything we know about the lead, in one message.

Owner, 2026-10-26: Saket Shinde enquired on the Mansha Phase-II page (2 BHK, from Google) and was passed to House Deal, but the
message House Deal got said only his name and phone. The old text was built from the chat's state, and a chat started by our
follow-up template has none of it; the lead record has the project, the form answers and where he came from. So the card is built
from the lead first and the chats second, and it says what is still unknown, so the agent asks for it on the first call.

`card` is pure (tests pin it): the caller reads the lead, its chats, its page visits and the project page brief.
`template_params` is the same facts cut to the seven one-line parameters of the agent template (WhatsApp rejects empty or
multi-line parameters).

Owner, 2026-11-07: the agent also gets a link to every page the buyer read and what they wrote, so they can see what the buyer
compared before calling, and the card says the buyer's details are for them only.
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional

from app.core import brand
from app.modules.tracking import origin
from app.modules.tracking.requirement import TIMELINE_LABEL, bhk_text, budget_text

IST = timedelta(hours=5, minutes=30)
AGENT_TEMPLATE = "lead_passed_v2"   # UTILITY template on our WABA; the body below must match Meta's copy
AGENT_BODY = ("New buyer enquiry passed to you by Avasetu.\n\n"
              "Name: {}\nPhone: {}\nProject: {}\nLooking for: {}\nCame from: {}\nPages they read: {}\nThey wrote: {}\n\n"
              "This buyer's details are for you only. Please do not share or forward them.\n\n"
              "Please call them today. Their full details and messages are in Avasetu Studio, Leads.\n\n"
              "Avasetu team")
# An enquiry made on the agent's own site is theirs, not a pass (owner, 2026-10-30): the card names their business and does not
# send them to Studio, since the office phone that reads it (House Deal: the team's WhatsApp) may have no Studio login.
SITE_TEMPLATE = "agent_site_enquiry_v1"   # UTILITY, submitted 2026-10-30; until Meta approves it, AGENT_TEMPLATE goes instead
SITE_BODY = ("New buyer enquiry on your {} website.\n\n"
             "Name: {}\nPhone: {}\nProject: {}\nLooking for: {}\nCame from: {}\n\n"
             "Please call them today.\n\n"
             "Avasetu team")
FINANCING_LABEL = {"home_loan": "Home loan", "own_funds": "Own funds", "undecided": "Not decided"}
SOURCE_LABEL = {"google": "Google search", "bing": "Bing search", "instagram": "Instagram", "facebook": "Facebook",
                "whatsapp": "WhatsApp", "direct": "Opened the link directly", "youtube": "YouTube", **origin.AI_NAMES}
MAX_SAID = 300
MAX_BODY = 1024   # WhatsApp's limit on a template body with its parameters filled in
PRIVATE_LINE = "This buyer's details are for you only. Please do not share or forward them."
# pages an agent reads, not a buyer: a lead who opened them may be an agent trying us out
AGENT_PAGES = ("/agents", "/for-agents", "/trial", "/join", "/studio", "/pilot")
SKIP_PAGES = ("/agent/", "/enquire", "/r/", "/i/", "/go/")   # say nothing about what a buyer wants


def _ist(dt: Optional[datetime]) -> str:
    if not isinstance(dt, datetime):
        return ""
    t = dt + IST
    return f"{t.day} {t:%b}, {t:%I:%M %p}".replace(" 0", " ").replace("AM", "am").replace("PM", "pm") + " IST"


def phone_text(phone: Optional[str]) -> str:
    """'+918975317054' -> '+91 89753 17054'; anything else as given."""
    d = re.sub(r"\D", "", str(phone or ""))
    if len(d) == 12 and d.startswith("91"):
        return f"+91 {d[2:7]} {d[7:]}"
    return str(phone or "").strip()


def ask_of(message: Optional[str]) -> dict:
    """What the form said they want, from the line the site writes: 'About <topic>: <their words>', 'About Site visit: <topic>',
    'Floor plans of <topic>'. -> {want, topic, said}."""
    text = (message or "").strip()
    want = None
    if text.startswith("About "):
        text = text[6:]
    if text.startswith("Floor plans of "):
        want, text = "Floor plans", text[len("Floor plans of "):]
    elif text.startswith("Site visit: "):
        want, text = "A site visit", text[len("Site visit: "):]
    if ")" in text:   # the topic ends with "(MahaRERA P...)"; their own words follow it
        topic, _, said = text.partition(")")
        topic, said = topic + ")", said.lstrip(": ")
    else:
        topic, _, said = text.partition(": ")
    return {"want": want, "topic": topic.strip() or None, "said": said.strip() or None}


def source_text(lead: dict) -> str:
    ft = lead.get("first_touch") or {}
    key = origin.source_key(lead.get("source") or origin.ai_utm(lead.get("utm")) or (lead.get("utm") or {}).get("utm_source")
                            or ft.get("app"), ft.get("referrer"))
    key = "chatgpt" if "chatgpt" in (key or "") else key
    return SOURCE_LABEL.get(key or "", key or "Not known")


def _project_line(project: Optional[dict], topic: Optional[str]) -> Optional[str]:
    if project:
        where = f", {project['area']}" if project.get("area") else ""
        return f"{project['name']}{where} (MahaRERA {project['regno']})"
    return topic


def _contact_line(chats: List[dict], lead: dict) -> str:
    """What has already happened, so the agent does not open with the same question our follow-up asked."""
    out = [m for c in chats for m in c.get("thread") or [] if m.get("from") in ("bot", "you")]
    them = [m for c in chats for m in c.get("thread") or [] if m.get("from") == "them"]
    last_them = max((m.get("at") or "" for m in them), default="")
    bits = []
    if lead.get("auto_followup_at") or out:
        bits.append(f"{brand.NAME} sent them a WhatsApp follow-up")
    if them:
        try:
            at = _ist(datetime.fromisoformat(last_them.rstrip("Z")))
        except ValueError:
            at = ""
        bits.append(f"they replied ({len(them)} message{'s' if len(them) != 1 else ''}{', last ' + at if at else ''})")
    elif bits:
        bits.append("no reply yet")
    calls = lead.get("calls") or []
    if calls:
        bits.append(f"{len(calls)} call{'s' if len(calls) != 1 else ''} logged, last: {calls[-1].get('outcome', '').replace('_', ' ')}")
    line = "; ".join(bits)
    return line[:1].upper() + line[1:] if line else "Nobody has contacted them yet"


def page_links(page: Optional[str], pages: Optional[List[str]], site: str = brand.SITE) -> List[str]:
    """Every page they read that says what they want, as a link, each once, the page they enquired from first."""
    paths = [p.split("?")[0].split("#")[0].rstrip("/") or "/" for p in ([page] if page else []) + list(pages or []) if p]
    return [f"{site}{p}" for p in dict.fromkeys(paths) if not p.startswith(SKIP_PAGES + AGENT_PAGES)]


def card(lead: dict, project: Optional[dict] = None, chats: Optional[List[dict]] = None, pages: Optional[List[str]] = None,
         site: str = brand.SITE) -> dict:
    """{lines: [(label, value)], text, missing}. `chats` are inbox threads (thread() shape), `pages` the paths they opened,
    oldest first. Empty facts are left out of the lines and named in `missing` instead."""
    chats = chats or []
    req = lead.get("requirement") or {}
    ask = ask_of(lead.get("message"))
    ft = lead.get("first_touch") or {}
    page = ft.get("enquiry_page") or ft.get("landing")
    data = next((c.get("data") for c in chats if c.get("data")), {}) or {}
    bhk = bhk_text(req.get("bhk") or data.get("bhk"))
    budget = budget_text(req.get("budget_min_inr"), req.get("budget_max_inr")) or budget_text(data.get("budget_min"), data.get("budget_max"))
    when = TIMELINE_LABEL.get(req.get("timeline") or data.get("timeline") or "")
    money = FINANCING_LABEL.get(req.get("financing") or data.get("financing") or "")
    areas = ", ".join(req.get("localities") or []) or (str(data["locality"]).replace("_", " ").title() if data.get("locality") else "")
    said = [ask["said"]] if ask["said"] else []
    said += [m["text"] for c in chats for m in c.get("thread") or [] if m.get("from") == "them" and m.get("text")][-3:]
    wants = ask["want"] or ("Price sheet and floor plans" if (page or "").startswith("/projects/") else None)
    links = page_links(page, pages, site)
    lines = [
        ("Name", (lead.get("name") or "").strip() or "Not given"),
        ("Phone", phone_text(lead.get("phone")) or "Not given"),
        ("Project", _project_line(project, ask["topic"])),
        ("Wants", wants),
        ("Home", bhk),
        ("Budget", budget),
        ("Buying when", when),
        ("Paying by", money),
        ("Areas", areas or None),
        ("They wrote", " / ".join(f'"{s.strip()[:MAX_SAID]}"' for s in said) or None),
        ("Page", f"{site}{page.split('?')[0]}" if page else None),
        ("Came from", source_text(lead)),
        ("Enquired", _ist(lead.get("created_at"))),
        ("Pages seen", ", ".join(links) if len(links) > 1 else None),
        ("So far", _contact_line(chats, lead)),
        ("Notes", " / ".join(n.get("text", "") for n in lead.get("notes") or [] if n.get("text")) or None),
    ]
    missing = [label for label, v in (("budget", budget), ("BHK", bhk), ("when they want to buy", when),
                                      ("home loan or own funds", money)) if not v]
    lines = [(k, v) for k, v in lines if v]
    head = f"New buyer for you from {brand.NAME}"
    body = [head, ""] + [f"{k}: {v}" for k, v in lines]
    if missing:
        body += ["", "Not known yet, please ask: " + ", ".join(missing)]
    body += ["", PRIVATE_LINE, "", "Please call them today and tell us how it went.", f"{brand.NAME} team"]
    return {"lines": [{"label": k, "value": v} for k, v in lines], "missing": missing, "text": "\n".join(body), "links": links}


def site_params(c: dict, business: str) -> List[str]:
    """The site-enquiry template's six parameters: the agent's business name, then the pass card's five."""
    return [_one_line(business, 60) or "Avasetu"] + template_params(c)[:5]


def _one_line(s: Optional[str], n: int) -> str:
    return re.sub(r"\s+", " ", s or "").strip()[:n]


def template_params(c: dict) -> List[str]:
    """The card cut to the agent template's seven parameters: name, phone, project, what they want, where from and when, the
    links, their own words. Every link goes in while the body stays under WhatsApp's limit; the rest are counted, not cut in half."""
    v = {x["label"]: x["value"] for x in c["lines"]}
    looking = "; ".join(x for x in (v.get("Home"), v.get("Wants"), v.get("Budget") and "budget " + v["Budget"],
                                    v.get("Buying when") and "buying " + v["Buying when"].lower()) if x)
    came = ", ".join(x for x in (v.get("Came from"), v.get("Enquired")) if x)
    params = [_one_line(v.get("Name"), 60) or "A buyer", _one_line(v.get("Phone"), 20) or "not given",
              _one_line(v.get("Project"), 120) or "a home in Pune", _one_line(looking, 160) or "details on the call",
              _one_line(came, 100) or "our website"]
    wrote = _one_line(v.get("They wrote"), 100) or "Nothing in their own words yet"
    room = MAX_BODY - len(AGENT_BODY.replace("{}", "")) - sum(map(len, params)) - len(wrote) - len(", and 99 more in Studio")
    links = c.get("links") or []
    kept: List[str] = []
    for link in links:
        if len(", ".join(kept + [link])) > room:
            break
        kept.append(link)
    pages = ", ".join(kept) or "Not recorded"
    if kept and len(kept) < len(links):
        pages += f", and {len(links) - len(kept)} more in Studio"
    return params + [pages, wrote]

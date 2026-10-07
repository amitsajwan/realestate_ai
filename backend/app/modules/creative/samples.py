"""Sample briefs and the contact-sheet builder used in the design review loop.

    PYTHONPATH=backend python -m app.modules.creative.samples docs/brand/creative-samples
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw

from app.modules.marketing.images import load_font

from .models import Brief
from .pipeline import make

MAHARERA = "Registered projects are listed on the MahaRERA website."


def buyer_briefs() -> List[Brief]:
    return [
        Brief(topic="Site visits before paying a token", short="site visit", stat_value="3",
              stat_label="site visits before you pay a token",
              facts=["Visit at different times of day", "Morning traffic and evening light show different things"],
              tip="Go once on a weekday and once on a weekend.",
              steps=["Visit once in the morning and once in the evening", "Ask for the RERA registration number",
                     "Check carpet area, not just super built-up area", "Walk to the nearest main road and note the traffic",
                     "Ask which approvals are still pending"],
              photo="tower-low", prefer="carousel"),
        Brief(topic="The brochure is not the approval", short="RERA number", myth="The brochure is the approval",
              truth="Check the project's MahaRERA page, not the brochure.", facts=[MAHARERA], tip="Ask for the RERA number before any token.", prefer="myth-vs-fact"),
        Brief(topic="Ready flat or under construction", short="ready flat", question="Ready to move or under construction?",
              options=["Ready to move", "Under construction"], facts=["Both have trade-offs worth weighing."], prefer="poll"),
        Brief(topic="Clean paperwork", short="paperwork", compare=("Messy file", "Clean file"),
              messy=["Papers lost in a WhatsApp chat", "Carpet area not in writing", "Receipts scattered"],
              clean=["One folder, every document", "Carpet area in the agreement", "Every receipt saved"],
              facts=["Keep every document and receipt in one place."], prefer="before-after"),
        Brief(topic="Second visit", short="the second visit", tip="Look at the light, the noise and the lift lobby, not only the flat.",
              facts=["Visit a second time at a different hour."], photo="glass-dusk", prefer="single"),
        Brief(topic="Possession date", short="possession date", tip="Ask for the date in the agreement, in writing.",
              facts=["The agreement should state the possession date."], question="", photo="", prefer="single"),
        Brief(topic="Registration window", short="registration", stat_value="4 months", stat_label="to present your document for registration",
              facts=["A document must be presented for registration within 4 months of signing (Registration Act 1908, Sec 23)."],
              tip="Put the date in your calendar the day you sign.", prefer="stat"),
        Brief(topic="Carpet area", short="carpet area", myth="Bigger super built-up means more space",
              truth="Carpet area is the space you actually walk on.", facts=["Carpet area is the usable floor area inside the walls."],
              steps=["Ask for carpet area in writing", "Compare flats by carpet area", "Check it against the agreement"],
              photo="living-sofa", prefer="carousel"),
    ]


def agent_briefs() -> List[Brief]:
    base = ["Every INTERESTED comment becomes a lead card with BHK, budget and timing", "Buyers are matched to your listings"]
    return [
        Brief(topic="INTERESTED comments become leads", short="buyer comments", facts=base, tip="",
              photo="living-room", stat_value="", stat_label="", prefer="single"),
        Brief(topic="From post to lead", short="lead follow-up", facts=base,
              steps=["Post a listing once", "Buyers comment INTERESTED", "Each comment becomes a lead card", "BHK, budget and timing arrive with it"], prefer="carousel"),
        Brief(topic="A comment is not yet a lead", short="comments", myth="A comment is a lead",
              truth="A comment is a lead once you know budget, BHK and timing.", facts=base, prefer="myth-vs-fact"),
        Brief(topic="Notebook or lead card", short="lead notes", compare=("Notebook chaos", "Ready leads"),
              messy=["Comments copied into a notebook", "Budget asked again and again", "Follow-ups forgotten"],
              clean=["Every comment becomes a lead card", "Budget, BHK and timing on the card", "Follow-ups queued for you"], facts=base, prefer="before-after"),
        Brief(topic="What every lead should arrive with", short="lead details", stat_value="3", stat_label="details on every lead before you reply",
              facts=["Each lead card shows BHK, budget and timing"], tip="Reply with the details already in front of you.", prefer="stat"),
        Brief(topic="Tracking buyer comments", short="buyer comments", question="How do you track buyer comments today?",
              options=["Notebook or memory", "Scrolling WhatsApp"], facts=base,
              steps=["Post a listing once", "Buyers comment INTERESTED", "Each comment becomes a lead card"], prefer="poll"),
    ]


def sample_plan() -> List[Tuple[Brief, str, str, int]]:
    """(brief, audience, channel, seed): 8 buyer and 6 agent posts on Instagram, then Facebook squares."""
    plan = [(b, "buyer", "instagram", i) for i, b in enumerate(buyer_briefs())]
    plan += [(b, "agent", "instagram", 20 + i) for i, b in enumerate(agent_briefs())]
    plan += [(b, "buyer", "facebook", 40 + i) for i, b in enumerate(buyer_briefs()[:4])]
    plan += [(b, "agent", "facebook", 60 + i) for i, b in enumerate(agent_briefs()[:2])]
    return plan


async def render_samples(out: Path, llm=None) -> List:
    out.mkdir(parents=True, exist_ok=True)
    packs, recent = [], []
    for brief, aud, ch, seed in sample_plan():
        pack = await make(brief, aud, ch, llm, seed=seed, recent_layouts=recent[-2:], out_dir=out)
        recent.append(pack.design["layout"])
        packs.append(pack)
    return packs


def contact_sheet(packs: List, path: Path, channel: str, thumb_w: int = 300, per_row: int = 6) -> None:
    """One row per post (carousel slides side by side), wrapped to `per_row` thumbnails per line, with the layout name under each."""
    sel = [p for p in packs if p.channel == channel]
    cells = []
    for p in sel:
        for i, f in enumerate(p.images):
            cells.append((f, p.design["layout"] + (f" {i + 1}/{len(p.images)}" if len(p.images) > 1 else "") + f" [{p.design['palette']}]"))
    if not cells:
        return
    first = Image.open(cells[0][0])
    th = int(thumb_w * first.size[1] / first.size[0])
    pad, label = 16, 26
    rows = (len(cells) + per_row - 1) // per_row
    sheet = Image.new("RGB", (per_row * (thumb_w + pad) + pad, rows * (th + label + pad) + pad), (232, 232, 236))
    d = ImageDraw.Draw(sheet)
    font = load_font(15, "medium")
    for n, (f, cap) in enumerate(cells):
        r, c = divmod(n, per_row)
        x, y = pad + c * (thumb_w + pad), pad + r * (th + label + pad)
        with Image.open(f) as im:
            sheet.paste(im.convert("RGB").resize((thumb_w, th), Image.LANCZOS), (x, y))
        d.text((x, y + th + 4), cap, font=font, fill=(40, 40, 50))
    sheet.save(path, optimize=True)


async def _main(out: Path) -> None:
    packs = await render_samples(out)
    contact_sheet(packs, out / "contact-instagram.png", "instagram")
    contact_sheet(packs, out / "contact-facebook.png", "facebook", thumb_w=340, per_row=6)
    for p in packs:
        print(p.design["layout"], p.design["palette"], p.report["ok"], [q["message"] for q in p.report["problems"]][:3])


if __name__ == "__main__":
    asyncio.run(_main(Path(sys.argv[1] if len(sys.argv) > 1 else "creative-samples")))

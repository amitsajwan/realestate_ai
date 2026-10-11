"""Shared fixtures for the creative tests. No network: the LLM is always a fake."""
from app.modules.creative import strategist, copywriter, art_director
from app.modules.creative.catalog import LAYOUTS
from app.modules.creative.models import Brief, Design, SIZES
from app.modules.creative.samples import agent_briefs, buyer_briefs


class FakeLlm:
    """json() pops queued replies (a dict, None, or an Exception to raise); text() returns `text_reply`."""

    def __init__(self, *json_replies, text_reply="Ek chhota caption. Kharadi mein visit karein."):
        self.replies = list(json_replies)
        self.text_reply = text_reply
        self.calls = []

    async def json(self, system, user):
        self.calls.append(("json", system, user))
        if not self.replies:
            return None
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    async def text(self, system, user, timeout=None):
        self.calls.append(("text", system, user))
        return self.text_reply


# layout id -> (brief, audience, preferred format)
def layout_cases():
    b, a = buyer_briefs(), agent_briefs()
    return {
        "big_number": (b[6], "buyer", "stat"),
        "myth_fact": (b[1], "buyer", "myth-vs-fact"),
        "checklist": (b[0], "buyer", "carousel"),
        "poll": (b[2], "buyer", "poll"),
        "before_after": (b[3], "buyer", "before-after"),
        "photo_led": (b[4], "buyer", "single"),
        "product_showcase": (a[0], "agent", "single"),
        "quote_tip": (b[5], "buyer", "single"),
        "plan_full": (plan_brief(), "buyer", "plan"),
    }


def plan_image() -> str:
    """A floor-plan-like drawing (black lines on white), written once per test run."""
    import tempfile
    from pathlib import Path
    from PIL import Image, ImageDraw
    p = Path(tempfile.gettempdir()) / "creative-test-plan.jpg"
    if not p.is_file():
        im = Image.new("RGB", (1600, 1130), "white")
        d = ImageDraw.Draw(im)
        for box in ((80, 80, 800, 600), (800, 80, 1520, 600), (80, 600, 1100, 1050), (1100, 600, 1520, 1050)):
            d.rectangle(box, outline="black", width=10)
        im.save(p, "JPEG", quality=85)
    return str(p)


def plan_brief(**kw):
    base = dict(topic="Floor plan of a 2 BHK", short="floor plan", facts=["The 2 BHK has a carpet area of 650 sq ft."],
                hooks={}, plan_image=plan_image(), plan_label="Floor plan from the builder's brochure", prefer="plan",
                kicker="GULMOHAR HEIGHTS", tip="Ask for the RERA carpet area of your unit in writing.")
    base.update(kw)
    return Brief(**base)


def build(layout, channel="instagram", palette=None):
    """(copy, design) for one layout, built by the rule path."""
    brief, aud, fmt = layout_cases()[layout]
    brief.prefer = fmt
    angle = strategist.rule_angle(brief, aud, channel, 0, [])
    copy = copywriter.rule_copy(angle, brief)
    design = art_director.choose(copy, angle, [], 0, brief.photo)
    design = Design(layout=layout, palette=palette or design.palette, photo=design.photo or "living-room", emphasis=design.emphasis, size=SIZES[channel])
    return copy, design, brief


def simple_brief(**kw):
    base = dict(topic="Possession date", short="possession date", facts=["The agreement should state the possession date."],
                tip="Ask for the date in the agreement, in writing.")
    base.update(kw)
    return Brief(**base)

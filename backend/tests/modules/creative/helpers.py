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
    }


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

"""Agent-recruitment promo: a 5-slide Instagram carousel, one WhatsApp image and ready-to-paste captions (English, Hinglish).

  cd backend && PYTHONPATH=. python scripts/promo_agents.py [--out uploads/promo]

Needs `segno` for the QR code (pip install segno; a local tool, not a server requirement).
Every slide passes the creative safe-area, contrast and no-truncation checks. The lead card is labelled as sample data.
"""
import argparse
import io
import sys
from pathlib import Path
from typing import List

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from PIL import Image  # noqa: E402

from app.modules.agentprojects.cards import check, save_all  # noqa: E402
from app.modules.creative.layouts.base import Canvas, Rendered  # noqa: E402
from app.modules.creative.layouts.palette import get as palette  # noqa: E402

SIZE = (1080, 1350)
JOIN_URL = "https://avasetu.in/request-invite"
SITE = "avasetu.in"
GREEN = (18, 128, 80)


def _qr(url: str, px: int) -> Image.Image:
    import segno
    buf = io.BytesIO()
    segno.make(url, error="m").save(buf, kind="png", scale=10, border=2, dark="#0f2340", light="#ffffff")
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB").resize((px, px), Image.NEAREST)


def _footer(c: Canvas, n: int, i: int) -> None:
    c.brand_bar(right=SITE, dark_bg=not c.pal.light)
    c.dots(n, i, c.W // 2, c.bottom - 104)


def hook(n: int) -> Rendered:
    c = Canvas(SIZE, palette("navy_gold"), "promo_hook", 0)
    c.chip("Free pilot for Pune agents", c.left, c.top + 10, icon="star", size=28)
    y = 300
    y = c.text("Get more property enquiries.", c.left, y, c.right - c.left, 104, "bold", c.pal.ink, 3, min_size=70, role="headline",
               emph=("enquiries.",)) + 30
    y = c.text("Spend less time chasing them.", c.left, y, c.right - c.left, 72, "bold", c.pal.accent, 2, min_size=50, role="headline") + 50
    c.text("Your own property website, posts and reels made for you, and every enquiry turned into a lead card that says "
           "who to call first.", c.left, y, c.right - c.left, 40, "medium", c.pal.muted, 4, min_size=30, role="support")
    c.text("Swipe", c.left, c.bottom - 190, 200, 34, "semibold", c.pal.accent, 1, role="cue", balance=False)
    c.icon("arrow", (c.left + 150, c.bottom - 178), 34, c.pal.accent)
    _footer(c, n, 0)
    return c.finish()


def problem(n: int) -> Rendered:
    c = Canvas(SIZE, palette("cream"), "promo_problem", 1, pattern=None, glow_at=None)
    y = c.text("SOUND FAMILIAR?", c.left, c.top + 10, c.right - c.left, 28, "bold", c.pal.accent, 1, role="kicker", balance=False) + 34
    y = c.text("Leads slip away while you are busy selling.", c.left, y, c.right - c.left, 72, "bold", c.pal.ink, 3, min_size=52,
               role="headline") + 56
    for title, body in (("“Price?” with no name", "Comments under your post, and no idea who the buyer is."),
                        ("Enquiries everywhere", "Calls, WhatsApp, Instagram, Facebook: the warm buyer gets a late reply."),
                        ("Posts take your evening", "Writing every property up again, in three languages.")):
        c.rrect((c.left, y, c.right, y + 200), 28, c.pal.card, outline=c.pal.edge, width=2)
        c.icon("cross", (c.left + 60, y + 64), 44, (196, 48, 52))
        c.text(title, c.left + 110, y + 36, c.right - c.left - 150, 40, "bold", c.pal.card_ink, 1, min_size=32, role="body",
               balance=False, bg_hint=c.pal.card)
        c.text(body, c.left + 110, y + 96, c.right - c.left - 150, 30, "medium", c.pal.card_muted, 2, min_size=24, role="body",
               bg_hint=c.pal.card)
        y += 228
    _footer(c, n, 1)
    return c.finish()


def offer(n: int) -> Rendered:
    c = Canvas(SIZE, palette("navy_gold"), "promo_offer", 2, pattern=None)
    y = c.text("WHAT AVASETU DOES FOR YOU", c.left, c.top + 10, c.right - c.left, 28, "bold", c.pal.accent, 1, role="kicker",
               balance=False) + 34
    y = c.text("We do the marketing. You do the closing.", c.left, y, c.right - c.left, 68, "bold", c.pal.ink, 3, min_size=50,
               role="headline") + 46
    for icon, title, body in (("home", "Your own property website", "Your homes and builder projects, on one link to share."),
                              ("star", "Posts and reels, made for you", "On your own Instagram and Facebook Page, and on Avasetu's."),
                              ("check", "Projects checked on MahaRERA", "Completion date and homes booked, read from the record."),
                              ("bubble", "Every enquiry, a lead card", "What the buyer wants, and who to call first.")):
        c.circle((c.left + 38, y + 38), 38, c.pal.accent_fill)
        c.icon(icon, (c.left + 38, y + 38), 40, c.pal.accent_ink)
        c.text(title, c.left + 100, y + 6, c.right - c.left - 100, 38, "bold", c.pal.ink, 1, min_size=30, role="body", balance=False)
        c.text(body, c.left + 100, y + 56, c.right - c.left - 100, 28, "medium", c.pal.muted, 2, min_size=22, role="body")
        y += 168
    _footer(c, n, 2)
    return c.finish()


def lead_card(n: int) -> Rendered:
    c = Canvas(SIZE, palette("navy_gold"), "promo_lead", 3)
    y = c.text("THE BEST PART", c.left, c.top + 10, c.right - c.left, 28, "bold", c.pal.accent, 1, role="kicker", balance=False) + 34
    y = c.text("Instead of 50 messages, one clear buyer.", c.left, y, c.right - c.left, 66, "bold", c.pal.ink, 3, min_size=48,
               role="headline") + 40
    x0, x1 = c.left + 20, c.right - 20
    white, ink, grey = (255, 255, 255), (16, 35, 64), (90, 102, 124)
    c.rrect((x0, y, x1, y + 560), 34, white, shadow=True)
    c.text("LEAD CARD · SAMPLE", x0 + 40, y + 40, 520, 24, "bold", grey, 1, role="mock", balance=False, bg_hint=white)
    c.chip("HOT", x1 - 40, y + 30, fill=(196, 48, 52), ink=white, size=26, align_right=True)
    c.text("Sample buyer", x0 + 40, y + 96, x1 - x0 - 80, 46, "bold", ink, 1, role="mock", balance=False, bg_hint=white)
    c.text("Wants a 2 BHK in Kharadi, budget 80 lakh to 1.2 crore, moving in 1 to 3 months, home loan.", x0 + 40, y + 162,
           x1 - x0 - 80, 30, "medium", grey, 3, min_size=24, role="mock", bg_hint=white)
    cx, cy = x0 + 40, y + 290
    for label in ("2 BHK", "₹80 L – 1.2 Cr", "Kharadi", "1–3 months", "Home loan"):
        box = c.chip(label, cx, cy, fill=(230, 244, 241), ink=(11, 63, 58), size=24)
        cx = box[2] + 12
        if cx > x1 - 260:
            cx, cy = x0 + 40, cy + 64
    c.text("Next step: call today and offer a site visit.", x0 + 40, y + 430, x1 - x0 - 80, 28, "semibold", ink, 2, min_size=22,
           role="mock", bg_hint=white)
    bw = (x1 - x0 - 100) // 2
    c.rrect((x0 + 40, y + 478, x0 + 40 + bw, y + 532), 16, ink)
    c.text("Call", x0 + 40, y + 494, bw, 26, "bold", white, 1, align="center", role="mock", balance=False, bg_hint=ink)
    c.rrect((x1 - 40 - bw, y + 478, x1 - 40, y + 532), 16, GREEN)
    c.text("WhatsApp", x1 - 40 - bw, y + 494, bw, 26, "bold", white, 1, align="center", role="mock", balance=False, bg_hint=GREEN)
    _footer(c, n, 3)
    return c.finish()


def join(n: int, qr_px: int = 300) -> Rendered:
    c = Canvas(SIZE, palette("navy_gold"), "promo_join", n - 1)
    y = c.text("JOIN THE FREE PILOT", c.left, c.top + 10, c.right - c.left, 28, "bold", c.pal.accent, 1, role="kicker", balance=False) + 34
    y = c.text("Free during the pilot. Low-cost after.", c.left, y, c.right - c.left, 72, "bold", c.pal.ink, 3, min_size=52,
               role="headline") + 30
    y = c.text("Limited places for agents in Pune. No app to install: it works in your phone's browser.", c.left, y,
               c.right - c.left, 34, "medium", c.pal.muted, 3, min_size=26, role="support") + 46
    box = (c.left, y, c.right, y + qr_px + 80)
    c.rrect(box, 34, c.pal.accent_fill)
    qx, qy = c.left + 40, y + 40
    c.rrect((qx - 10, qy - 10, qx + qr_px + 10, qy + qr_px + 10), 18, (255, 255, 255))
    c.img.paste(_qr(JOIN_URL, qr_px), (qx, qy))
    tx = qx + qr_px + 50
    c.text("Scan, or open", tx, qy + 30, c.right - 40 - tx, 32, "medium", c.pal.accent_ink, 1, min_size=24, role="body",
           balance=False, bg_hint=c.pal.accent_fill)
    c.text(SITE, tx, qy + 90, c.right - 40 - tx, 58, "bold", c.pal.accent_ink, 1, min_size=40, role="body", balance=False,
           bg_hint=c.pal.accent_fill)
    c.text("Tap “Join the free pilot”", tx, qy + 180, c.right - 40 - tx, 30, "semibold", c.pal.accent_ink, 2, min_size=22,
           role="body", bg_hint=c.pal.accent_fill)
    y = box[3] + 50
    for line in ("Your own property website", "Posts and reels made for you", "Every enquiry as a lead card"):
        c.icon("check", (c.left + 20, y + 20), 34, c.pal.accent)
        y = c.text(line, c.left + 60, y, c.right - c.left - 60, 34, "semibold", c.pal.ink, 1, min_size=26, role="body",
                   balance=False) + 26
    _footer(c, n, n - 1)
    return c.finish()


def all_in_one(size=(1080, 1350), url: str = JOIN_URL) -> Rendered:
    """One picture that tells the whole story, for WhatsApp and Facebook groups (4:5) or Status/Stories (9:16)."""
    W, H = size
    tall = H > 1500
    c = Canvas(size, palette("navy_gold"), "promo_single", 0)
    y = c.top + (250 if tall else 10)  # stories: keep clear of the app's top and bottom controls
    c.chip("Free pilot for Pune property agents", c.left, y, icon="star", size=28)
    y += 110 if tall else 90
    y = c.text("Get more property enquiries.", c.left, y, c.right - c.left, 92 if tall else 80, "bold", c.pal.ink, 3,
               min_size=56, role="headline") + 18
    y = c.text("Spend less time chasing them.", c.left, y, c.right - c.left, 60 if tall else 52, "bold", c.pal.accent, 2,
               min_size=40, role="headline") + (70 if tall else 44)
    for icon, line in (("home", "Your own property website"), ("star", "Posts and reels made for you"),
                       ("check", "Projects checked on MahaRERA"), ("bubble", "Every enquiry: who to call first")):
        c.circle((c.left + 30, y + 26), 30, c.pal.accent_fill)
        c.icon(icon, (c.left + 30, y + 26), 32, c.pal.accent_ink)
        c.text(line, c.left + 82, y + 6, c.right - c.left - 82, 38 if tall else 34, "semibold", c.pal.ink, 1, min_size=26,
               role="body", balance=False)
        y += 92 if tall else 78
    y += 30 if tall else 16
    qr = 300 if tall else 240
    c.rrect((c.left, y, c.right, y + qr + 60), 30, c.pal.accent_fill)
    qx, qy = c.left + 30, y + 30
    c.rrect((qx - 8, qy - 8, qx + qr + 8, qy + qr + 8), 16, (255, 255, 255))
    c.img.paste(_qr(url, qr), (qx, qy))
    tx = qx + qr + 40
    c.text("Free during the pilot.", tx, qy + 10, c.right - 30 - tx, 34, "bold", c.pal.accent_ink, 2, min_size=24, role="body",
           bg_hint=c.pal.accent_fill)
    c.text("Low-cost after.", tx, qy + (100 if tall else 90), c.right - 30 - tx, 30, "semibold", c.pal.accent_ink, 1, min_size=22,
           role="body", balance=False, bg_hint=c.pal.accent_fill)
    c.text(SITE, tx, qy + qr - 60, c.right - 30 - tx, 50, "bold", c.pal.accent_ink, 1, min_size=34, role="body", balance=False,
           bg_hint=c.pal.accent_fill)
    c.brand_bar(right="Scan to join")
    r = c.finish()
    check([r])
    return r


def reel(out: Path) -> Path:
    """A 20-second vertical reel with the same story, in our brand (Avasetu end card), generated music, no phone number."""
    from app.modules.reels import music
    from app.modules.reels.compose import Scene, make_reel
    scenes = [
        Scene(kicker="FOR PUNE PROPERTY AGENTS", lines=["Get more property *enquiries*.", "Spend less time chasing them."], seconds=3.6, seed="pa-1"),
        Scene(kicker="SOUND FAMILIAR?", lines=["Leads slip away", "“Price?” with no name", "Enquiries everywhere", "Evenings spent making posts"],
              seconds=4.0, seed="pa-2"),
        Scene(kicker="AVASETU DOES THE MARKETING", lines=["You do the *closing*", "Your own property website", "Posts and reels made for you",
                                                          "Projects checked on MahaRERA"], seconds=4.2, seed="pa-3"),
        Scene(kicker="THE BEST PART", lines=["Every enquiry, a *lead card*", "What the buyer wants", "and who to call *first*"], seconds=3.8, seed="pa-4"),
        Scene(kicker="FREE PILOT · PUNE", lines=["Free during the pilot", "Low-cost after", "Join at *avasetu.in*"], seconds=3.8, seed="pa-5"),
    ]
    tune = music.write(out / "promo-music.wav", seconds=24)
    return make_reel(scenes, out / "agents-reel.mp4", music=tune)


def group_post_lead(url: str = JOIN_URL) -> Rendered:
    """The single group post with the lead card as the hero: what an agent gets, in one look (4:5)."""
    c = Canvas(SIZE, palette("navy_gold"), "promo_group_lead", 0)
    c.chip("Free pilot for Pune property agents", c.left, c.top + 4, icon="star", size=26)
    y = c.text("Stop chasing “Price?” comments.", c.left, c.top + 84, c.right - c.left, 66, "bold", c.pal.ink, 2, min_size=46,
               role="headline") + 14
    y = c.text("Get buyers you can call.", c.left, y, c.right - c.left, 50, "bold", c.pal.accent, 1, min_size=38, role="headline",
               balance=False) + 30
    white, ink, grey = (255, 255, 255), (16, 35, 64), (90, 102, 124)
    x0, x1 = c.left, c.right
    c.rrect((x0, y, x1, y + 380), 30, white, shadow=True)
    c.text("EVERY ENQUIRY BECOMES A LEAD CARD · SAMPLE", x0 + 32, y + 30, x1 - x0 - 200, 20, "bold", grey, 1, min_size=16,
           role="mock", balance=False, bg_hint=white)
    c.chip("HOT", x1 - 32, y + 20, fill=(196, 48, 52), ink=white, size=24, align_right=True)
    c.text("Sample buyer: 2 BHK in Kharadi", x0 + 32, y + 78, x1 - x0 - 64, 38, "bold", ink, 1, min_size=28, role="mock",
           balance=False, bg_hint=white)
    cx, cy = x0 + 32, y + 140
    for label in ("₹80 L – 1.2 Cr", "Moving in 1–3 months", "Home loan"):
        box = c.chip(label, cx, cy, fill=(230, 244, 241), ink=(11, 63, 58), size=24)
        cx = box[2] + 12
    c.text("Next step: call today and offer a site visit.", x0 + 32, y + 228, x1 - x0 - 64, 28, "semibold", ink, 1, min_size=22,
           role="mock", balance=False, bg_hint=white)
    bw = (x1 - x0 - 84) // 2
    c.rrect((x0 + 32, y + 290, x0 + 32 + bw, y + 346), 16, ink)
    c.text("Call", x0 + 32, y + 306, bw, 26, "bold", white, 1, align="center", role="mock", balance=False, bg_hint=ink)
    c.rrect((x1 - 32 - bw, y + 290, x1 - 32, y + 346), 16, GREEN)
    c.text("WhatsApp", x1 - 32 - bw, y + 306, bw, 26, "bold", white, 1, align="center", role="mock", balance=False, bg_hint=GREEN)
    y += 410
    c.text("Plus your own property website, and posts and reels made for you.", c.left, y, c.right - c.left, 30, "semibold",
           c.pal.ink, 2, min_size=24, role="support")
    qr = 190
    qy = c.bottom - 150 - qr
    c.rrect((c.left, qy - 24, c.right, qy + qr + 24), 26, c.pal.accent_fill)
    c.rrect((c.left + 18, qy - 6, c.left + 30 + qr, qy + qr + 6), 12, (255, 255, 255))
    c.img.paste(_qr(url, qr), (c.left + 24, qy))
    tx = c.left + 60 + qr
    c.text("Free during the pilot. Low-cost after.", tx, qy + 14, c.right - 24 - tx, 30, "bold", c.pal.accent_ink, 2, min_size=22,
           role="body", bg_hint=c.pal.accent_fill)
    c.text("Scan or open " + SITE, tx, qy + qr - 54, c.right - 24 - tx, 34, "bold", c.pal.accent_ink, 1, min_size=24, role="body",
           balance=False, bg_hint=c.pal.accent_fill)
    c.brand_bar(right="Pune agents")
    r = c.finish()
    check([r])
    return r


def carousel() -> List[Rendered]:
    n = 5
    slides = [hook(n), problem(n), offer(n), lead_card(n), join(n)]
    check(slides)
    return slides


CAPTION_EN = """Pune property agents: get more enquiries, and spend less time chasing them.

Avasetu gives you:
✅ Your own property website, one link to share
✅ Posts and reels made for you
✅ Builder projects checked on MahaRERA
✅ Every enquiry as a lead card: what the buyer wants and who to call first

Free during the pilot, low-cost after. Limited places for agents in Pune.

Join: https://avasetu.in/request-invite

#PuneRealEstate #PuneProperty #RealEstateAgent #Kharadi #Wagholi #Avasetu"""

WHATSAPP_EN = """Pune property agents 👋

Avasetu gives you your own property website, makes your posts and reels, and turns every enquiry into a lead card that tells you who to call first.

✅ Free during the pilot (low-cost after)
✅ No app to install
✅ Limited places in Pune

See how it works and join: https://avasetu.in"""

WHATSAPP_HINGLISH = """Pune ke property agents 👋

Avasetu aapko deta hai apni property website, aapke liye posts aur reels, aur har enquiry ko ek lead card mein badalta hai: buyer ko kya chahiye aur pehle kise call karna hai.

✅ Pilot ke dauraan free (baad mein bahut kam price)
✅ Koi app install nahi karna
✅ Pune mein limited jagah

Dekhiye aur join kariye: https://avasetu.in"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="uploads/promo")
    ap.add_argument("--reel", action="store_true", help="also render the 20-second promo reel")
    out = Path(ap.parse_args().out)
    files = save_all(carousel(), out, "agents")
    save_all([all_in_one()], out, "group-post")            # WhatsApp / Facebook groups (4:5)
    save_all([group_post_lead()], out, "group-lead")        # the same, with the lead card as the hero
    save_all([all_in_one((1080, 1920))], out, "story")      # WhatsApp Status / Instagram Stories (9:16)
    if "--reel" in sys.argv:
        print("reel:", reel(out))
    # WhatsApp: the hook slide works as a single image; the join slide carries the QR for anyone who wants to scan
    (out / "caption-instagram.txt").write_text(CAPTION_EN, encoding="utf-8")
    (out / "whatsapp-english.txt").write_text(WHATSAPP_EN, encoding="utf-8")
    (out / "whatsapp-hinglish.txt").write_text(WHATSAPP_HINGLISH, encoding="utf-8")
    print("wrote", [f.name for f in files], "and 3 text files to", out)


if __name__ == "__main__":
    main()

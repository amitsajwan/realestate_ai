"""The fixed 'Worth checking' buyer line, the MahaRERA wording audit (T1.1) and the weekly digest hook."""
import re
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.newsroom import captions, cards, codec, digest, policy, roundup
from app.modules.newsroom import presentation as pr
from app.modules.newsroom.samples import SAMPLES, make_doc
from app.modules.newsroom.sources.maharera import to_item
from app.modules.newsroom.stages import check as chk
from app.modules.newsroom.stages.check import check
from app.modules.newsroom.stages.draft import template_draft
from app.modules.newsroom.types import Draft, Fact, Facts, MahaReraProject, Relevance

from .test_check import CLEAN, ITEM, NOW, run

SUNDAY_EVENING = datetime(2026, 10, 4, 12, 30, tzinfo=timezone.utc)


# ---- the buyer line ---------------------------------------------------------------------------------------------------------------------

def _doc(pillar, facts, source="Times of India"):
    return make_doc("x1", facts[0], facts, pillar, ["kharadi"], source)


@pytest.mark.parametrize("pillar,facts,source,key", [
    ("infrastructure", ["Metro corridor 2B to Wagholi is approved."], "The Indian Express", ("infrastructure", "transport")),
    ("infrastructure", ["PMRDA approved a new sewage plant near Kharadi."], "PMC", ("infrastructure", "other")),
    ("new_supply", ["Project Alpha was listed or updated on MahaRERA."], "MahaRERA", ("new_supply", "maharera")),
    ("new_supply", ["A builder has announced a tower near Kharadi."], "Punekar News", ("new_supply", "other")),
    ("rules_money", ["The RBI kept the repo rate unchanged."], "ET Realty", ("rules_money", "loan")),
    ("rules_money", ["Stamp duty in Pune stays the same this year."], "ET Realty", ("rules_money", "cost")),
    ("rules_money", ["MahaRERA issued a new order on complaints."], "ET Realty", ("rules_money", "other")),
    ("locality_life", ["PMC plans new traffic signals near the IT park."], "Punekar News", ("locality_life", "")),
])
def test_line_is_chosen_by_pillar_and_sub_type(pillar, facts, source, key):
    assert pr.buyer_line(_doc(pillar, facts, source)) == policy.BUYER_LINES[key]


def test_no_line_for_education_or_the_digest():
    assert pr.buyer_line(SAMPLES[7]) == ""  # education: already a tip
    assert pr.buyer_line(digest.sample_digest(SAMPLES)) == ""


def test_lines_are_careful_no_prediction_no_will_no_figures_no_advice():
    for line in policy.BUYER_LINES.values():
        assert line.startswith("Worth checking") and len(line) <= 120
        assert not re.search(r"\bwill\b|\d|₹|price|apprecia|invest|return|expected|soon|guarantee", line, re.I), line
        for rx in (policy.BANNED, chk.HYPE, chk.FORWARD, chk.MAHARERA_NEW, *chk.FILLER):
            assert not rx.search(line), line


def test_captions_carry_the_line_after_the_fact_and_before_the_source():
    for d in SAMPLES:
        line = pr.buyer_line(d)
        for ch, text in captions.build(d).items():
            if not line:
                assert "Worth checking" not in text
                continue
            assert line in text, (d["_id"], ch)
            summary = pr.split_text(d["draft"]["text"]).summary
            assert text.index(summary[:40]) < text.index(line) < text.index("Source:") < text.index(captions.footer(ch))


def test_a_long_caption_keeps_the_line_and_stays_under_the_limit():
    d = make_doc("lg", "Big update", ["Fact one is here."], "locality_life", ["kharadi"], "PMC")
    d["draft"]["text"] = ("Sentence number one is quite long and says a lot. " * 30) + "\n\nSource: PMC, as of 29 Sep 2026. https://x.test"
    for ch, text in captions.build(d).items():
        assert len(text) < captions.FB_MAX and pr.buyer_line(d) in text and text.endswith(captions.footer(ch))


async def test_the_line_adds_no_check_problem_to_the_final_captions(monkeypatch):
    for d in SAMPLES:
        with_line = await captions.verify(d, lambda a, b, c: check(a, b, c, now=SUNDAY_EVENING))
        monkeypatch.setattr(pr, "buyer_line", lambda doc: "")
        without = await captions.verify(d, lambda a, b, c: check(a, b, c, now=SUNDAY_EVENING))
        monkeypatch.undo()
        assert with_line == without, d["_id"]


# ---- the check stage's narrow exception ----------------------------------------------------------------------------------------------------

def _with(paragraph):
    return CLEAN.replace("\n\nSource:", f"\n\n{paragraph}\n\nSource:")


def test_check_accepts_every_house_line_even_naming_what_the_source_does_not():
    assert "maharera" not in (ITEM.title + ITEM.text).lower()
    for line in policy.BUYER_LINES.values():
        r = run(_with(line))
        assert r.ok, (line, r.problems)


def test_check_still_rejects_invented_facts_next_to_or_inside_a_house_line():
    line = policy.BUYER_LINES[("new_supply", "maharera")]
    assert not run(_with(line + " Hinjewadi prices will double by 2027.")).ok  # same paragraph, extra claim: checked as usual
    assert not run(_with(line.replace("MahaRERA", "Wakad MahaRERA"))).ok  # an edited house line is ordinary text
    r = run(_with(line) + "\n\nThe Hinjewadi line opens on 5 March.")
    assert not r.ok and any("Hinjewadi" in p for p in r.problems) and any("5 Mar" in p for p in r.problems)
    assert not run(_with("Worth checking: the MahaRERA page.")).ok  # not one of the fixed lines


# ---- the card subtitle ---------------------------------------------------------------------------------------------------------------------

def test_card_uses_the_line_only_when_there_is_no_other_subtitle():
    d = make_doc("c1", "PMC plans new traffic signals near the IT park", ["PMC plans new traffic signals near the IT park."],
                 "locality_life", ["kharadi"], "Punekar News")
    assert pr.support_line(d) == ""
    _, r, _ = cards.render_card(d, "ig")
    assert not cards.problems(r)
    assert [i.text for i in r.items if i.role == "support"] == [pr.buyer_line(d)]
    for s in SAMPLES:  # samples have a second fact: it stays the subtitle
        if pr.support_line(s):
            _, r, _ = cards.render_card(s, "ig")
            assert not any("Worth checking" in i.text for i in r.items)


# ---- T1.1 wording audit: everything the MahaRERA path can produce ------------------------------------------------------------------------

FORBIDDEN = re.compile(r"newly registered|registered (this|last) week|registered with maharera|new launch|\blaunch(ed|es)?\b|"
                       r"just registered|new registration", re.I)


def _texts(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _texts(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _texts(v)


def _maharera_texts():
    now = datetime(2026, 10, 3, 6, 0, tzinfo=timezone.utc)
    p = MahaReraProject("PR1260002601601", "SHANTISHIKHAR", "", "Haveli", "Pune", "411014", "2026-09-27",
                        "https://maharerait.maharashtra.gov.in/public/project/view/1")
    raw = to_item(p, now)
    facts = Facts([Fact(f"Project SHANTISHIKHAR was {policy.MAHARERA_PHRASE}.", raw.text.split(".")[0])], raw.published_at)
    rel = Relevance(True, "new_supply", ["kharadi"])
    drafted = template_draft(raw, facts, rel)
    story = {"_id": "m1", "raw": codec.to_doc(raw), "facts": codec.to_doc(facts), "draft": codec.to_doc(drafted),
             "relevance": codec.to_doc(rel)}
    projects = [{"_id": p.regno, "name": p.name, "locality": "kharadi", "pincode": p.pincode, "last_modified": p.last_modified,
                 "source_url": p.url}]
    rnd = roundup.compose(projects, now, "maharera-x")
    out = [raw.title, raw.text, *_texts(codec.to_doc(drafted)), *_texts(rnd), roundup.TITLE, roundup.CHECK]
    for doc in [story, rnd] + [s for s in SAMPLES if s["raw"]["source"] == "MahaRERA" or pr.pillar(s) == "new_supply"]:
        out += list(captions.build(doc).values()) + [pr.headline(doc), pr.hook(doc), pr.support_line(doc), pr.buyer_line(doc)]
        out += list(_texts(doc.get("draft"))) + list(_texts(doc.get("facts")))
    for doc in [story] + [s for s in SAMPLES if s["raw"]["source"] == "MahaRERA"]:
        _, r, _ = cards.render_card(doc, "ig")
        out += [i.text for i in r.items]
    out += [policy.BUYER_LINES[("new_supply", "maharera")], policy.BUYER_LINES[("new_supply", "other")]]
    return [t for t in out if t]


def test_no_maharera_text_claims_new_registration_or_launch():
    texts = _maharera_texts()
    assert len(texts) > 30 and any(policy.MAHARERA_PHRASE.lower() in t.lower() for t in texts)
    bad = [t for t in texts if FORBIDDEN.search(t)]
    assert not bad, bad


def test_the_sample_maharera_card_says_listed_or_updated():
    s = next(s for s in SAMPLES if s["_id"] == "d4e5f6a7b8")
    assert policy.MAHARERA_PHRASE.lower() in pr.hook(s).lower() and not FORBIDDEN.search(s["draft"]["title"])


# ---- the weekly digest hook ------------------------------------------------------------------------------------------------------------------

def test_digest_caption_opens_with_a_hook_that_says_what_is_inside():
    doc = digest.compose([{**d, "status": "published"} for d in SAMPLES], SUNDAY_EVENING)
    n = len(doc["digest"]["items"])
    for ch, text in captions.build(doc).items():
        first = text.split("\n")[0]
        assert len(first) <= digest.HOOK_MAX_CHARS and first.startswith(f"{n} updates from Kharadi and Wagholi this week"), first
    assert doc["digest"]["cover"] == f"{n} updates from Kharadi and Wagholi this week"
    assert digest.hook(1) == "1 update from Kharadi and Wagholi this week"
    res = check(codec.draft(doc), codec.facts(doc), codec.raw_item(doc), now=SUNDAY_EVENING)
    assert res.ok, res.problems  # the count is backed by the digest's own source text


def test_digest_cover_shows_the_hook_and_every_story_slide_keeps_its_source():
    doc = digest.compose([{**d, "status": "published"} for d in SAMPLES], SUNDAY_EVENING)
    dg = doc["digest"]
    for it in dg["items"]:
        assert f"({it['source']})" in doc["draft"]["text"]
        _, r, _ = cards.render_card(cards._story_doc(it), "ig", "headline", counter="1 of 2")
        metas = [i.text for i in r.items if i.role == "meta"]
        assert any(it["source"] in m for m in metas), (it["id"], metas)
    slides = cards.digest_slides(dg, "fb")
    assert len(slides) == 1
    r = cards._render_headline({"_id": "digest", "relevance": {"pillar": "digest", "areas": []}, "draft": {"format": "digest"}}, "ig",
                               dg["cover"], dg["cover_line"] + ". Swipe.", "", cards._digest_over("NEWS · THIS WEEK"))
    assert not cards.problems(r) and any(i.text == dg["cover"] for i in r.items if i.role == "hook")

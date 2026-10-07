"""PM-1: the system prompts take a voice and a mode. Brand mode must stay byte-identical to what the desk has always sent.
PM-2: every prompt version is pinned by a hash, and a pack records the prompts whose output it kept."""
import hashlib
import json
from pathlib import Path

from app.modules.creative import pipeline, prompts
from app.modules.creative.guards import problems_in, unsupported_orgs
from app.modules.creative.models import Voice

from .helpers import FakeLlm, simple_brief

FIXTURES = Path(__file__).parent / "fixtures"
SNAPSHOT = json.loads((FIXTURES / "brand_prompts.json").read_text(encoding="utf-8"))
PINNED = json.loads((FIXTURES / "prompt_versions.json").read_text(encoding="utf-8"))
STAGES = ("strategist", "copywriter", "translator", "critic")
LISTING_VOICE = Voice(name="House Deal", team="House Deal team", areas="Ranjangaon, Pune")


def test_each_prompt_version_pins_its_text():
    """Changed a prompt? Bump its number in prompts.VERSIONS and add the new hash to fixtures/prompt_versions.json."""
    for stage in STAGES:
        for mode, voice in ((prompts.BRAND, Voice()), (prompts.LISTING, LISTING_VOICE)):
            t = prompts.tag(stage, mode)
            digest = hashlib.sha256(getattr(prompts, stage)(voice, mode).encode()).hexdigest()[:16]
            assert PINNED.get(t) == digest, f"{t}: the text changed; bump prompts.VERSIONS['{stage}']"


async def test_a_pack_records_the_prompts_it_kept(tmp_path):
    clean = {"first_line": "One check before you book.", "question": "What would you add?"}
    pack = await pipeline.make(simple_brief(), "buyer", "instagram", FakeLlm(None, clean), out_dir=tmp_path, reviewer=None)
    assert pack.used_llm and pack.prompts == ["copywriter@2/brand"]   # the strategist reply was None: rules, so no tag
    rules = await pipeline.make(simple_brief(), "buyer", "instagram", None, out_dir=tmp_path / "rules", reviewer=None)
    assert rules.prompts == []


def test_brand_prompts_are_unchanged():
    for stage in STAGES:
        assert getattr(prompts, stage)(Voice(), prompts.BRAND) == SNAPSHOT[stage], stage


def test_listing_prompts_name_the_area_and_allow_the_listed_facts():
    v = Voice(name="House Deal", team="House Deal team", areas="Ranjangaon, Pune")
    for stage in STAGES:
        text = getattr(prompts, stage)(v, prompts.LISTING)
        assert "no prices" not in text and "Kharadi" not in text, stage
    for stage in ("strategist", "copywriter", "critic"):
        assert "Ranjangaon, Pune" in getattr(prompts, stage)(v, prompts.LISTING), stage
    for stage in ("strategist", "copywriter"):
        text = getattr(prompts, stage)(v, prompts.LISTING)
        assert "House Deal" in text and "exactly as the facts state them" in text, stage


def test_a_listing_with_no_area_still_reads_naturally():
    assert "property in Pune." in prompts.copywriter(Voice(), prompts.LISTING)


def test_builder_names_must_come_from_the_facts():
    assert unsupported_orgs("Gulmohar City by Kolte Patil Developers.", "Gulmohar City") == ["Kolte Patil Developers"]
    assert unsupported_orgs("By Kolte Patil Developers.", "Built by Kolte Patil Developers.") == []
    assert unsupported_orgs("Ask the builder. The Builders said so.", "") == []
    assert "name not in facts: Kolte Patil Developers" in problems_in("Kolte Patil Developers project.", "")

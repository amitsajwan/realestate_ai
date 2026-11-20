"""The editor's call (stages/impact.py): what the model is told about a story on one of our tracked topics."""
from datetime import datetime, timezone

from app.modules.newsroom.stages import impact
from app.modules.newsroom.types import RawItem, Relevance

NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)


class Llm:
    def __init__(self, score):
        self.score, self.seen = score, []

    async def json(self, system, user):
        self.seen.append((system, user))
        return {"score": self.score, "who": "buyers", "what_changes": "x", "reason": "y"}


def raw(title):
    return RawItem("i", "Pune Mirror", "https://e.test/a", title, "Land acquisition reached 80%.", NOW, NOW)


async def test_a_tracked_topic_is_named_to_the_editor_so_distance_from_our_areas_is_not_the_reason():
    llm = Llm(7)
    out = await impact.judge(raw("Purandar Airport Tender Nears as Pune Land Acquisition Reaches 80%"),
                             Relevance(True, "infrastructure", [], "tracker: purandar-airport"), llm)
    assert out["keep"] and out["score"] == 7
    system, user = llm.seen[0]
    assert "Tracked topic: purandar-airport" in user
    assert "Which part of Pune it is in is never a reason to score low" in system and "naming" in system


async def test_a_story_on_no_tracked_topic_is_sent_as_before():
    llm = Llm(3)
    out = await impact.judge(raw("Pune Dengue Death: First Fatality of 2026 Reported"), Relevance(True, "locality_life", ["kharadi"], ""), llm)
    assert not out["keep"] and "Tracked topic" not in llm.seen[0][1]

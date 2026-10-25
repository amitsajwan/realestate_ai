"""What the knowledge index cuts into passages from content: the guide topics and our published posts (calendar's, passed in
by app/wiring.py, since conversations never import content)."""
from app.modules.calendar import topics
from app.modules.knowledge import index

CAPTION = "Kharadi metro update 🚇\n\nThe Pune metro line 3 reaches Kharadi by 2027, says Maha-Metro. #Pune #Kharadi"


class Posts:
    """content_calendar, enough for post_chunks: find() over the published posts, async-iterated."""
    def __init__(self, docs):
        self.docs = docs

    def find(self, flt, projection=None):
        docs = [d for d in self.docs if d["status"] == "published" and not d.get("hidden_from_feed") and d.get("caption")]

        async def gen():
            for d in docs:
                yield d
        return gen()


class Db:
    def __init__(self, posts):
        self.content_calendar = Posts(posts)


def test_every_guide_topic_becomes_passages_with_its_guide_link():
    chunks = list(index.topic_chunks())
    for slug in topics.load():
        mine = [c for c in chunks if c["id"].startswith(f"topic:{slug}:")]
        assert mine and all(c["url"] == f"/guides/{slug}" and c["kind"] == "topic" for c in mine)


async def test_published_posts_become_passages_without_hashtags_and_never_a_sample_home():
    db = Db([{"_id": "p1", "status": "published", "caption": CAPTION, "permalink": "https://fb.test/p1", "tags": {"area": "kharadi"}},
             {"_id": "p2", "status": "published", "caption": CAPTION + " sample", "kind": "showcase"},
             {"_id": "p3", "status": "planned", "caption": CAPTION},
             {"_id": "p4", "status": "published", "caption": "Too short"}])
    out = await index.post_chunks(db)
    assert [c["id"] for c in out] == ["post:p1"]
    c = out[0]
    assert c["title"] == "Kharadi metro update 🚇" and "#Pune" not in c["text"] and "line 3 reaches Kharadi by 2027" in c["text"]
    assert c["url"] == "https://fb.test/p1" and c["area"] == "kharadi"


def test_a_topic_passage_reads_every_titled_table_and_drops_the_bold_markers():
    chunks = {c["id"]: c for c in index.topic_chunks()}
    prices = chunks["topic:upper-kharadi:prices"]["text"]
    assert "Locality averages" in prices and "Project specifics" in prices and "Lodha Camelot 3 BHK" in prices
    assert "**" not in chunks["topic:upper-kharadi:where"]["text"]


def test_a_projects_sections_are_indexed_once_and_its_record_paragraph_opens():
    sections = [{"heading": "The project", "text": "Park Eden Phase I is the first phase of Park Eden in Kharadi, Pune."},
                {"heading": "Location", "text": "The project is in Kharadi, on the eastern side of Pune."}]
    doc = {"_id": "P1", "regno": "P1", "name": "Park Eden Phase I", "locality": "kharadi", "page_slug": "park-eden-phase-i-kharadi",
           "page_text": "\n\n".join(s["text"] for s in sections), "page_sections": sections}
    texts = [c["text"] for c in index.project_chunks(doc)]
    assert texts[0].startswith("Park Eden Phase I is a project in Kharadi, Pune, registered with MahaRERA as P1.")
    assert sum(sections[0]["text"] in t for t in texts) == 1
    # an older writer's summary still opens the project's passages
    old = {**doc, "page_text": "Park Eden Phase I is a housing project in Kharadi."}
    assert index.project_chunks(old)[0]["text"].startswith("Park Eden Phase I is a housing project in Kharadi.")

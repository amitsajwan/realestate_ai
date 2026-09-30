"""Shared test helpers for the newsroom plumbing tests."""
from datetime import datetime, timedelta, timezone

from app.modules.newsroom.types import CheckResult, Draft, Fact, Facts, RawItem, Relevance

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def item(n=1, title="Pune ring road land acquisition update"):
    return RawItem(id=f"i{n}", source="test", url=f"https://news.test/{n}", title=title, text="The PMRDA said work will start.",
                   published_at=NOW - timedelta(days=1), fetched_at=NOW)


class FakeSource:
    name = "fake"

    def __init__(self, items, boom=False):
        self.items, self.boom = items, boom

    async def fetch(self, get):
        if self.boom:
            raise RuntimeError("feed down")
        return self.items


def good_stages(fail_on=None, check_ok=True):
    def assess(it, now):
        return Relevance(keep=True, pillar="infrastructure", areas=["kharadi"], reason="ring road")

    async def extract(it, llm):
        if fail_on == it.id:
            raise RuntimeError("boom token=EAABCDEFGHIJKLMNOPQRSTUV")
        return Facts(facts=[Fact(text="Work will start", quote="The PMRDA said work will start.")], as_of=it.published_at)

    async def draft(it, facts, rel, fmt, llm):
        return Draft(format=fmt, text=f"Update: {it.title}. What do you think?", link=it.url, source_names=[it.source])

    def check(d, facts, it):
        return CheckResult(ok=check_ok, problems=[] if check_ok else ["number not in source"])

    return {"filter": assess, "extract": extract, "draft": draft, "check": check}


class FakePublisher:
    def __init__(self, boom=False):
        self.calls, self.boom = [], boom

    async def publish(self, text, link, when):
        if self.boom:
            raise RuntimeError("graph down")
        self.calls.append((text, link, when))
        return f"pid{len(self.calls)}"

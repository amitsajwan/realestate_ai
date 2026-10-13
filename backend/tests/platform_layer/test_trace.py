import logging

from app import readiness
from app.platform import trace


def test_a_line_is_one_greppable_line():
    s = trace.line("reel", "j1", "voice", trace.FAILED, reason='HTTP 403: key "bad"\nnot valid', seconds=12.345, skip=None)
    assert s == 'pipeline=reel ref=j1 step=voice outcome=failed reason="HTTP 403: key "bad" not valid" seconds=12.3'
    assert trace.line("reel", None, "start", trace.OK) == "pipeline=reel ref=- step=start outcome=ok"
    assert len(trace.line("x", "y", "z", trace.OK, reason="a" * 1000)) < 400


def test_levels_follow_the_outcome(caplog):
    log = logging.getLogger("test.trace")
    with caplog.at_level("INFO", logger="test.trace"):
        for outcome in (trace.OK, trace.FALLBACK, trace.SKIPPED, trace.FAILED):
            trace.event(log, "p", "r", "s", outcome)
    assert [r.levelno for r in caplog.records] == [logging.INFO, logging.WARNING, logging.WARNING, logging.ERROR]


def test_readiness_says_why_a_reel_has_no_voice_and_never_logs_a_secret(monkeypatch, caplog):
    monkeypatch.delenv("GOOGLE_TTS_API_KEY", raising=False)
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "secret-token-123")
    monkeypatch.setenv("SOCIAL_DRY_RUN", "false")
    with caplog.at_level("INFO", logger=readiness.log.name):
        readiness.log_readiness("api")
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert 'step=voice outcome=skipped reason="GOOGLE_TTS_API_KEY is not set"' in text
    assert "step=social outcome=failed" in text and "secret-token-123" not in text
    assert {"ffmpeg", "voice", "llm", "music", "social", "calendar"} <= {
        m.split("step=")[1].split()[0] for m in text.splitlines()}


def test_readiness_never_stops_the_start(monkeypatch, caplog):
    def broken():
        raise RuntimeError("boom")
    monkeypatch.setattr(readiness, "checks", broken)
    readiness.log_readiness("worker")   # does not raise
    assert any("readiness checks failed" in r.getMessage() for r in caplog.records)

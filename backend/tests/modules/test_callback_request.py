"""The site's "Call me back" button: a number and consent only, no name. It is a form lead like any other (the agent is told at
once, the follow-up template goes), and the handover and template say the buyer asked for a call back."""
import pytest
from pydantic import ValidationError

from app.modules.inbox import handover
from app.modules.inbox.service import PROJECT_WANT, project_params
from app.modules.tracking import service as tracking_service

from .qual_helpers import inquiry, make

pytestmark = pytest.mark.asyncio


async def test_a_call_back_needs_no_name_and_is_a_new_form_lead(monkeypatch):
    told = []

    async def on_new_lead(db, lead):
        told.append(lead)
    monkeypatch.setattr(tracking_service, "_on_new_lead", on_new_lead)
    svc, db, _ = await make()
    got = await svc.capture_inquiry(inquiry(name="", callback=True, message="Call back: KOLTE PATIL SPRINGSHIRE (MahaRERA P1)"))
    assert got["new_lead"] is True
    lead = db.get_collection("contacts").docs[0]
    assert lead["name"] == "" and lead["channel"] == "form" and lead["consent"]
    assert len(told) == 1


async def test_any_other_form_still_needs_a_name():
    with pytest.raises(ValidationError):
        inquiry(name=" A ")
    with pytest.raises(ValidationError):
        inquiry(name="")


async def test_a_call_back_without_consent_is_refused():
    svc, _, _ = await make()
    with pytest.raises(tracking_service.TrackingError):
        await svc.capture_inquiry(inquiry(name="", callback=True, consent=False))


async def test_the_handover_and_the_template_say_a_call_back_was_asked_for():
    ask = handover.ask_of("Call back: SPRINGSHIRE (MahaRERA P1)")
    assert ask == {"want": "A call back", "topic": "SPRINGSHIRE (MahaRERA P1)", "said": None}
    params = project_params({"name": "", "message": "Call back: SPRINGSHIRE (MahaRERA P1)"}, {"name": "Springshire", "area": "Wagholi"})
    assert params == ["Sir", "Springshire, Wagholi", PROJECT_WANT["A call back"]] and params[2] == "a call back"

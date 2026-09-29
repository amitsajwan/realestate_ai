"""Lead score v1: rule based, explainable. Points per event type, decayed by recency at read time."""
from datetime import datetime, timedelta

POINTS = {
    "page_view": 0,
    "listing_view": 1,
    "share": 3,
    "call_click": 10,
    "whatsapp_click": 10,
    "inquiry": 25,
    "site_visit_booked": 30,
}
LISTING_VIEW_CAP = 5  # views of one listing stop adding after this many
REPEAT_VIEW_BONUS = 2  # extra for coming back to the same listing
HOT_AT = 35  # e.g. an enquiry plus a WhatsApp click or a couple of return visits
WARM_AT = 15


def event_points(event_type: str, prior_views_of_listing: int = 0) -> int:
    if event_type == "listing_view":
        if prior_views_of_listing >= LISTING_VIEW_CAP:
            return 0
        return POINTS["listing_view"] + (REPEAT_VIEW_BONUS if prior_views_of_listing > 0 else 0)
    return POINTS.get(event_type, 0)


def recency_factor(last_activity: datetime, now: datetime) -> float:
    age = now - last_activity
    if age <= timedelta(days=3):
        return 1.0
    if age <= timedelta(days=14):
        return 0.7
    return 0.4


def score(base: int, last_activity: datetime, now: datetime) -> int:
    return round(base * recency_factor(last_activity, now))


def temperature(value: int) -> str:
    if value >= HOT_AT:
        return "hot"
    if value >= WARM_AT:
        return "warm"
    return "cold"

"""Settings of the seo steps that have their own, read at call time."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    review_on: bool   # the daily page check (review.py): SEO_PAGE_REVIEW=off stops it
    site: str         # the live site; empty outside a deployment, where there is no page to read


def load() -> Config:
    site = (os.environ.get("PUBLIC_SITE_URL") or "").strip().rstrip("/")
    return Config(review_on=(os.environ.get("SEO_PAGE_REVIEW") or "on").strip().lower() != "off" and site.startswith("https://"),
                  site=site)

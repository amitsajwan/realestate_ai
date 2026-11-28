"""Neighbourhood research: what is around a place and a project, measured from data and kept fresh by itself
(docs/plan/pune-intelligence.md). Owns the collections `area_research` (one document per kind of fact and place,
_id = "<kind>|<place>"), `schools` (one per school from the official board lists, _id = "<board>|<affiliation>") and
`work_hub_research` (one per work hub, _id = hub slug). Only this module writes them.

How it grows: every kind of fact is one researcher (researchers/<kind>.py) in the registry (researchers/__init__.py). A
researcher says how often it refreshes, gathers its data for one place (or once for the whole city), and turns the stored data
into what a page shows (`present`), hiding itself when it has too little to say. The loop (runner.py) runs whatever is due
within each researcher's budget. Adding a kind of fact is one file and one registry line; pages read everything through
`views`. No model writes a fact here: numbers come from the sources, with their names and dates.
"""
from .store import AREA_RESEARCH, SCHOOLS, WORK_HUB_RESEARCH, Store
from .views import area_view, hub_view, hubs_view, project_view

__all__ = ["AREA_RESEARCH", "SCHOOLS", "WORK_HUB_RESEARCH", "Store", "area_view", "hub_view", "hubs_view", "project_view"]

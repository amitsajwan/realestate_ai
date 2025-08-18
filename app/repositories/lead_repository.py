"""
Lead Repository
===============
Data access layer for lead operations.
"""
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository):
    def __init__(self):
        super().__init__("leads")

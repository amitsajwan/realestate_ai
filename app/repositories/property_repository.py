"""
Property Repository
===================
Data access layer for property operations.
"""
from app.repositories.base import BaseRepository


class PropertyRepository(BaseRepository):
    def __init__(self):
        super().__init__("properties")

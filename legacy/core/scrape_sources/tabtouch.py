"""Tabtouch (Australia) adapter stub.

Implements BookmakerAdapter interface for Tabtouch AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class TabtouchAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for Tabtouch
        return []

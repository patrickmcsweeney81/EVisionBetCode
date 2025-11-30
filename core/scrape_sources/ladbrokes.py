"""Ladbrokes (Australia) adapter stub.

Implements BookmakerAdapter interface for Ladbrokes AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class LadbrokesAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for Ladbrokes
        return []

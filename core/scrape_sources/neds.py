"""Neds (Australia) adapter stub.

Implements BookmakerAdapter interface for Neds AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class NedsAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for Neds
        return []

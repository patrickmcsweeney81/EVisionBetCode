"""PlayUp (Australia) adapter stub.

Implements BookmakerAdapter interface for PlayUp AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class PlayUpAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for PlayUp
        return []

"""BoomBet (Australia) adapter stub.

Implements BookmakerAdapter interface for BoomBet AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class BoomBetAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for BoomBet
        return []

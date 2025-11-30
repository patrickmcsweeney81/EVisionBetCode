"""Bet365 (Australia) adapter stub.

Implements BookmakerAdapter interface for Bet365 AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class Bet365AUAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for Bet365 AU
        return []

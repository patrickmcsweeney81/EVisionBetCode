"""Unibet (Australia) adapter stub.

Implements BookmakerAdapter interface for Unibet AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class UnibetAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for Unibet AU
        return []

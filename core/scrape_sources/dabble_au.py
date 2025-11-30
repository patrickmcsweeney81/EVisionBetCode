"""Dabble (Australia) adapter stub.

Implements BookmakerAdapter interface for Dabble AU. Fill in endpoints and parsing logic.
"""
from .base_adapter import BookmakerAdapter

class DabbleAdapter(BookmakerAdapter):
    def fetch_events(self, sport: str):
        # TODO: Implement scraping logic for Dabble
        return []

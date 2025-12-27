"""
NBA Extractor (V3) - Basketball-specific extraction logic
"""

from typing import Dict, List

from ..base_extractor import BaseExtractor


class NBAExtractor(BaseExtractor):
    """Extract NBA odds from The Odds API."""
    
    def __init__(self):
        super().__init__(
            sport="basketball_nba",
            regions=["au", "us", "eu"],
            markets=["h2h", "spreads", "totals"],
        )
    
    def extract_with_props(self) -> None:
        """Extract NBA with player props (more expensive API calls)."""
        print("\n⚠️  Player props extraction not yet implemented")
        print("Use basic extract() for spreads/totals/h2h only")

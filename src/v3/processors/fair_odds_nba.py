"""
NBA Fair Odds Calculation

Specialization for NBA:
- Aggressive outlier removal (5%) due to sparse props
- Minimum 2 sharps required
- Exclude AU books for player props
- Weight sharps: Pinnacle 50%, DraftKings 30%, FanDuel 20%
"""

import logging
from typing import Dict, List, Tuple
import statistics

logger = logging.getLogger(__name__)


class NBAFairOdds:
    """NBA-specific fair odds calculation"""
    
    SPORT_NAME = "NBA"
    OUTLIER_THRESHOLD = 0.05  # Aggressive
    MIN_SHARP_COUNT = 2
    
    # NBA weight profile (hidden from users)
    WEIGHT_PROFILE = {
        "pinnacle": 0.50,
        "draftkings": 0.30,
        "fanduel": 0.20,
    }
    
    def __init__(self):
        logger.info(f"[Fair Odds] {self.SPORT_NAME} calculator initialized")
    
    def calculate_fair_odds(self, market_data: Dict) -> Tuple[float, float, str]:
        """
        Calculate fair odds for a market.
        
        Returns: (fair_over, fair_under, notes)
        """
        over_odds = market_data.get("over_odds", [])
        under_odds = market_data.get("under_odds", [])
        
        # Separate over/under for weight totals (KEY FIX from v2)
        over_fair, over_notes = self._calculate_side_fair(over_odds, "Over")
        under_fair, under_notes = self._calculate_side_fair(under_odds, "Under")
        
        notes = f"NBA | O:{len(over_odds)} U:{len(under_odds)} | {over_notes} | {under_notes}"
        return over_fair, under_fair, notes
    
    def _calculate_side_fair(self, odds_list: List[Dict], side_name: str) -> Tuple[float, str]:
        """
        Calculate fair odds for one side (Over or Under).
        
        Returns: (fair_odds_decimal, notes)
        """
        if not odds_list:
            return 0.0, f"No {side_name} odds"
        
        if len(odds_list) < self.MIN_SHARP_COUNT:
            return 0.0, f"Insufficient {side_name} sharps"
        
        # Extract decimal odds
        decimals = [float(o["odds"]) for o in odds_list if float(o["odds"]) > 1.01]
        if not decimals:
            return 0.0, f"Invalid {side_name} odds"
        
        # Remove outliers (aggressive: 5%)
        filtered = self._remove_outliers(decimals, self.OUTLIER_THRESHOLD)
        if len(filtered) < self.MIN_SHARP_COUNT:
            return 0.0, f"Insufficient {side_name} after filtering"
        
        # Calculate weighted average using ESPN weight profile
        fair_odds = self._calculate_weighted_fair(filtered, odds_list)
        
        return fair_odds, f"{side_name}:{len(filtered)}"
    
    def _remove_outliers(self, values: List[float], threshold: float) -> List[float]:
        """Remove outliers beyond threshold from median"""
        if len(values) <= 2:
            return values
        
        median = statistics.median(values)
        filtered = []
        
        for val in values:
            pct_diff = abs(val - median) / median
            if pct_diff <= threshold:
                filtered.append(val)
        
        return filtered if filtered else values
    
    def _calculate_weighted_fair(self, odds: List[float], books: List[Dict]) -> float:
        """Calculate weighted average fair odds"""
        if not odds:
            return 0.0
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for book in books:
            book_key = book.get("bookmaker", "").lower()
            weight = self.WEIGHT_PROFILE.get(book_key, 0.0)
            
            if weight > 0:
                try:
                    odds_val = float(book["odds"])
                    weighted_sum += odds_val * weight
                    weight_total += weight
                except (ValueError, KeyError):
                    continue
        
        if weight_total == 0:
            # No weighted books, use simple average
            return statistics.mean(odds) if odds else 0.0
        
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    def calculate_ev(self, fair_odds: float, best_odds: float, selection: str) -> float:
        """
        Calculate EV% for a selection.
        
        EV% = (implied_prob_fair × best_odds - 1) × 100
        """
        if fair_odds <= 1.0 or best_odds <= 1.0:
            return 0.0
        
        fair_prob = 1.0 / fair_odds
        ev = (fair_prob * best_odds - 1) * 100
        
        return round(ev, 2)
    
    def detect_arbitrage(self, over: float, under: float) -> bool:
        """Detect if market has arbitrage (total prob < 1.0)"""
        if over <= 1.0 or under <= 1.0:
            return False
        
        total_prob = (1.0 / over) + (1.0 / under)
        return total_prob < 1.0

"""
Fair Odds Calculator v2 - FIXED version

Key fixes from v1:
- SEPARATE weight totals for Over/Under sides (not shared)
- Per-side outlier detection
- Configurable outlier threshold
- Comprehensive logging

The bug in v1: After filtering outliers, Over side might have 5 books,
Under side might have 3 books. We were using a single weight_total from
the Over side to calculate BOTH sides, giving wrong Under fair odds.

New approach: Calculate weight_total separately for each side.
"""

import logging
from statistics import median
from typing import Dict, List, Optional, Tuple

from src.v3.config import (
    EV_CONFIG,
    SPORT_WEIGHT_PROFILES,
    get_sharp_books,
    get_weight,
)

logger = logging.getLogger(__name__)


class FairOddsCalculatorV2:
    """Calculate fair odds from sharp bookmaker odds using weighted average"""

    def __init__(self):
        """Initialize calculator with config"""
        self.min_sharp_count = EV_CONFIG["min_sharp_count"]
        self.outlier_threshold = EV_CONFIG["outlier_threshold"]

    def calculate_fair_odds(
        self,
        sport_key: str,
        market_data: Dict,
    ) -> Tuple[float, float, int, List[str], int]:
        """
        Calculate fair odds for a market

        Args:
            sport_key: e.g., "basketball_nba"
            market_data: Dict with 'over_odds', 'under_odds', 'over_books', 'under_books'
                        Format: {"over_odds": [1.90, 1.88, 1.92], "over_books": ["DK", "FD", "Pin"]}

        Returns:
            (fair_over, fair_under, sharp_count, books_used, outlier_count)
        """
        over_odds = market_data.get("over_odds", [])
        under_odds = market_data.get("under_odds", [])
        over_books = market_data.get("over_books", [])
        under_books = market_data.get("under_books", [])

        if not over_odds or not under_odds:
            return 0.0, 0.0, 0, [], 0

        # ====================================================================
        # STEP 1: Build weighted lists per side
        # ====================================================================
        over_weighted = []
        under_weighted = []

        for book, odds in zip(over_books, over_odds):
            if self._is_valid_odds(odds):
                weight = get_weight(sport_key, book)
                if weight > 0:
                    over_weighted.append((odds, weight))

        for book, odds in zip(under_books, under_odds):
            if self._is_valid_odds(odds):
                weight = get_weight(sport_key, book)
                if weight > 0:
                    under_weighted.append((odds, weight))

        initial_over_count = len(over_weighted)
        initial_under_count = len(under_weighted)

        # ====================================================================
        # STEP 2: Remove outliers per side
        # ====================================================================
        over_clean, over_outliers = self._remove_outliers(over_weighted)
        under_clean, under_outliers = self._remove_outliers(under_weighted)

        total_outliers = over_outliers + under_outliers

        logger.debug(
            f"Over: {initial_over_count} → {len(over_clean)} "
            f"({over_outliers} outliers removed)"
        )
        logger.debug(
            f"Under: {initial_under_count} → {len(under_clean)} "
            f"({under_outliers} outliers removed)"
        )

        # ====================================================================
        # STEP 3: Check minimum coverage
        # ====================================================================
        if len(over_clean) < self.min_sharp_count or len(under_clean) < self.min_sharp_count:
            logger.debug(
                f"Insufficient coverage: Over={len(over_clean)}, "
                f"Under={len(under_clean)} (min={self.min_sharp_count})"
            )
            return 0.0, 0.0, 0, [], total_outliers

        # ====================================================================
        # STEP 4: Calculate weight totals (SEPARATE FOR EACH SIDE!)
        # ====================================================================
        over_weight_total = sum(w for _, w in over_clean)
        under_weight_total = sum(w for _, w in under_clean)

        # ====================================================================
        # STEP 5: Calculate fair odds (FIXED: separate denominators)
        # ====================================================================
        fair_over = sum(odds * weight for odds, weight in over_clean) / over_weight_total
        fair_under = sum(odds * weight for odds, weight in under_clean) / under_weight_total

        # ====================================================================
        # STEP 6: Determine which books were used
        # ====================================================================
        books_used = []
        for book, odds in zip(over_books, over_odds):
            if any(odds == o and get_weight(sport_key, book) > 0 for o, _ in over_clean):
                books_used.append(book)

        sharp_count = len(over_clean) + len(under_clean)

        logger.debug(
            f"Fair odds: Over={fair_over:.4f}, Under={fair_under:.4f} | "
            f"Books: {books_used} | Sharp count: {sharp_count}"
        )

        return fair_over, fair_under, sharp_count, books_used, total_outliers

    def _is_valid_odds(self, odds: float) -> bool:
        """Validate odds are in reasonable range"""
        return 1.01 <= odds <= 1000.0

    def _remove_outliers(self, weighted_odds: List[Tuple[float, float]]) -> Tuple[List[Tuple], int]:
        """
        Remove outliers using median absolute deviation

        Args:
            weighted_odds: List of (odds, weight) tuples

        Returns:
            (cleaned list, outlier count)
        """
        if len(weighted_odds) < 2:
            return weighted_odds, 0

        # Get odds values (ignore weights for outlier detection)
        odds_values = [o for o, _ in weighted_odds]

        # Calculate median
        med = median(odds_values)

        # Remove odds that deviate >threshold from median
        cleaned = []
        removed_count = 0

        for odds, weight in weighted_odds:
            deviation = abs(odds - med) / med if med > 0 else 0
            if deviation <= self.outlier_threshold:
                cleaned.append((odds, weight))
            else:
                removed_count += 1
                logger.debug(f"Removed outlier: {odds} (deviation: {deviation:.2%})")

        return cleaned, removed_count

    def calculate_implied_probability(self, odds: float) -> float:
        """Convert odds to implied probability"""
        if odds <= 0:
            return 0.0
        return 1.0 / odds

    def calculate_ev(
        self,
        fair_odds: float,
        best_odds: float,
        best_book: str,
    ) -> float:
        """
        Calculate EV percentage

        Formula: EV% = (fair_prob * best_odds - 1) * 100

        Args:
            fair_odds: Fair price (e.g., 1.93)
            best_odds: Best available odds (e.g., 2.05)
            best_book: Bookmaker name (for logging)

        Returns:
            EV percentage (e.g., 6.2 for 6.2%)
        """
        if fair_odds <= 0 or best_odds <= 0:
            return 0.0

        fair_prob = self.calculate_implied_probability(fair_odds)
        ev = (fair_prob * best_odds - 1.0) * 100

        return ev

    def detect_arbs(self, over_best: float, under_best: float) -> bool:
        """
        Detect if there's an arbitrage (can win both sides)

        Arb exists if: (1/over_best + 1/under_best) < 1

        Args:
            over_best: Best available Over odds
            under_best: Best available Under odds

        Returns:
            True if arbitrage exists
        """
        if over_best <= 0 or under_best <= 0:
            return False

        sum_implied = (1.0 / over_best) + (1.0 / under_best)
        return sum_implied < 1.0


def main():
    """Test fair odds calculator"""
    calculator = FairOddsCalculatorV2()

    # Test case: NBA totals
    # Sharp books: Pinnacle 1.90, DraftKings 1.88, FanDuel 1.92 (Over)
    # Sharp books: Pinnacle 1.77, DraftKings 1.75, FanDuel 1.74 (Under)
    market = {
        "over_odds": [1.90, 1.88, 1.92],
        "under_odds": [1.77, 1.75, 1.74],
        "over_books": ["pinnacle", "draftkings", "fanduel"],
        "under_books": ["pinnacle", "draftkings", "fanduel"],
    }

    fair_over, fair_under, sharp_count, books, outliers = calculator.calculate_fair_odds(
        "basketball_nba", market
    )

    print(f"Fair Over: {fair_over:.4f}")
    print(f"Fair Under: {fair_under:.4f}")
    print(f"Sharp Count: {sharp_count}")
    print(f"Books Used: {books}")
    print(f"Outliers Removed: {outliers}")

    # Test EV calculation
    ev = calculator.calculate_ev(fair_under, 1.93, "sportsbet")
    print(f"EV% (Under 1.93): {ev:.2f}%")


if __name__ == "__main__":
    main()

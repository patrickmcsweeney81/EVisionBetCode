"""
Bookmaker Ratings & Weighting System

Each bookmaker gets a 1-4 star rating (reliability/sharpness).
Users can customize weights per rating tier via environment or code.
"""

import os
from typing import Dict, Optional

# ============================================================================
# BOOKMAKER RATINGS (1-4 stars)
# ============================================================================
# 4⭐ = Industry standard, fast lines, sharp pricing
# 3⭐ = Major player, solid pricing, good coverage
# 2⭐ = Secondary source, some lag, limited lines
# 1⭐ = Backup only, occasional use, limited reliability

BOOKMAKER_RATINGS = {
    # 4⭐ - GOLD STANDARD (Industry leaders)
    "Pinnacle": 4,  # No limits, fastest line mover
    "Betfair_EU": 4,  # Exchange = market consensus
    "Draftkings": 4,  # Huge US volume, sharp
    "Fanduel": 4,  # Major US player
    # 3⭐ - MAJOR SHARPS (Reliable sources)
    "Betfair_AU": 3,  # Local AU exchange
    "Betfair_UK": 3,  # UK exchange data
    "Betmgm": 3,  # Quality US depth
    "Betrivers": 3,  # US market depth
    "Betsson": 3,  # European reliability
    "Marathonbet": 3,  # European alternative
    "Lowvig": 3,  # Specialty: low margins
    # 2⭐ - SECONDARY SOURCES (Good but slower)
    "Nordicbet": 2,  # Nordic niche
    "Mybookie": 2,  # Offshore, solid
    "Betonline": 2,  # Offshore backup
    "Bovada": 2,  # Offshore backup
    # 1⭐ - TERTIARY (Use with caution)
    "Sportsbet": 1,  # AU corporate (target, not sharp)
    "Pointsbet": 1,  # AU corporate (target, not sharp)
    "Tab": 1,  # AU corporate (target, not sharp)
    "Tabtouch": 1,  # AU corporate (target, not sharp)
    "Unibet_AU": 1,  # AU (target, not sharp)
    "Ladbrokes_AU": 1,  # AU corporate (target, not sharp)
    "Neds": 1,  # AU corporate (target, not sharp)
    "Betr": 1,  # AU startup (target, not sharp)
    "Boombet": 1,  # AU niche (target, not sharp)
    "Williamhill_US": 1,  # US secondary
    "Sbk": 1,  # US secondary
    "Fanatics": 1,  # US secondary
    "Ballybet": 1,  # US secondary
    "Betparx": 1,  # US secondary
    "Espnbet": 1,  # US secondary
    "Fliff": 1,  # US secondary
    "Hardrockbet": 1,  # US secondary
    "Rebet": 1,  # US secondary
    "Williamhill_UK": 1,  # UK secondary
    "Betvictor": 1,  # UK secondary
    "Bwin": 1,  # EU secondary
    "Coral": 1,  # UK secondary
    "Skybet": 1,  # UK secondary
    "Paddypower": 1,  # UK secondary
    "Boylesports": 1,  # UK secondary
    "Betfred": 1,  # UK secondary
    "Williamhill_EU": 1,  # EU secondary
    "Codere": 1,  # EU secondary
    "Tipico": 1,  # EU secondary
    "Leovegas": 1,  # EU secondary
    "Parionssport": 1,  # EU secondary
    "Winamax_FR": 1,  # EU secondary
    "Winamax_DE": 1,  # EU secondary
    "Unibet_FR": 1,  # EU secondary
    "Unibet_NL": 1,  # EU secondary
    "Unibet_SE": 1,  # EU secondary
    "Betclic": 1,  # EU secondary
}

# ============================================================================
# SPORT-SPECIFIC WEIGHT PROFILES
# ============================================================================
# Different sports have different sharp coverage depth.
# Define weight distributions for each sport.

SPORT_WEIGHT_PROFILES = {
    # Standard profile: balanced multi-source (8+ sharps available)
    "basketball_nba": {
        4: 0.35,  # 4⭐ books
        3: 0.40,  # 3⭐ books
        2: 0.15,  # 2⭐ books
        1: 0.10,  # 1⭐ targets
    },
    "americanfootball_nfl": {
        4: 0.35,
        3: 0.40,
        2: 0.15,
        1: 0.10,
    },
    "soccer_epl": {
        4: 0.35,
        3: 0.40,
        2: 0.15,
        1: 0.10,
    },
    # Pinnacle-heavy: limited sharp coverage (2-4 sharps)
    "icehockey_nhl": {
        4: 0.50,  # Pinnacle + DK/FD if present
        3: 0.30,  # Secondary sharps (Betfair, Betsson)
        2: 0.10,  # Rare
        1: 0.10,  # Targets
    },
    # Betfair-dominated: exchange leads price discovery (1-2 sharps)
    "cricket_big_bash": {
        4: 0.70,  # Betfair (exchange = market)
        3: 0.20,  # Pinnacle backup
        2: 0.05,  # Rare
        1: 0.05,  # Targets
    },
    "cricket_ipl": {
        4: 0.75,
        3: 0.15,
        2: 0.05,
        1: 0.05,
    },
    "tennis_atp": {
        4: 0.65,  # Betfair + Pinnacle lead
        3: 0.25,  # Secondary sharps
        2: 0.05,
        1: 0.05,
    },
    "tennis_wta": {
        4: 0.65,
        3: 0.25,
        2: 0.05,
        1: 0.05,
    },
    # Default for unknown/generic sports
    "default": {
        4: 0.40,  # Conservative: weight 4⭐ more
        3: 0.35,
        2: 0.15,
        1: 0.10,
    },
}

# ============================================================================
# DEFAULT WEIGHTS BY RATING
# ============================================================================
# Can override via environment variables or code
# Format: WEIGHT_STAR_<N> = decimal weight for N-star books

DEFAULT_WEIGHTS = {
    4: 0.35,  # 4⭐ books split 35% total
    3: 0.40,  # 3⭐ books split 40% total
    2: 0.15,  # 2⭐ books split 15% total
    1: 0.10,  # 1⭐ books split 10% total (targets + secondaries)
}


def get_sport_weight(sport: Optional[str]) -> float:
    """
    Lightweight sport scaler for sharp weighting.

    Currently defaults to 1.0 for all sports but supports per-sport overrides
    via env vars named SPORT_WEIGHT_<SPORT_KEY> (uppercased).
    """

    if not sport:
        return 1.0

    env_key = f"SPORT_WEIGHT_{sport.upper()}"
    env_val = os.getenv(env_key)
    if env_val:
        try:
            return float(env_val)
        except ValueError:
            print(f"[!] Invalid {env_key}={env_val}, using default 1.0")

    return 1.0


def load_weight_config(sport: Optional[str] = None) -> Dict[int, float]:
    """Load weight configuration from environment or defaults.

    Args:
        sport: Sport key (e.g., 'basketball_nba', 'icehockey_nhl').
               If provided, uses sport-specific profile.
               Falls back to 'default' if sport not found.

    Environment variables (override sport profile):
    - WEIGHT_STAR_4=0.35  (4-star books)
    - WEIGHT_STAR_3=0.40  (3-star books)
    - WEIGHT_STAR_2=0.15  (2-star books)
    - WEIGHT_STAR_1=0.10  (1-star books)

    Example:
        weights = load_weight_config('icehockey_nhl')  # NHL-specific
        weights = load_weight_config()  # Default profile
    """
    # Get sport-specific profile or fall back to default
    if sport and sport in SPORT_WEIGHT_PROFILES:
        weights = SPORT_WEIGHT_PROFILES[sport].copy()
    else:
        weights = SPORT_WEIGHT_PROFILES["default"].copy()

    # Environment variables override sport profile
    for star in [4, 3, 2, 1]:
        env_key = f"WEIGHT_STAR_{star}"
        env_val = os.getenv(env_key)
        if env_val:
            try:
                weights[star] = float(env_val)
            except ValueError:
                print(f"[!] Invalid {env_key}={env_val}, using default {weights[star]}")

    # Validate sum is approximately 1.0
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        print(f"[WARN] Weight sum={total:.2%} (should be 100%) for sport={sport}")

    return weights


def calculate_book_weight(book_name: str, weights: Dict[int, float]) -> float:
    """Get individual weight for a bookmaker.

    Distributes the star-tier weight equally among books in that tier.

    Args:
        book_name: Bookmaker name
        weights: Star-tier weights from load_weight_config()

    Returns:
        Individual weight for this book (0.0-1.0)
    """
    rating = BOOKMAKER_RATINGS.get(book_name, 1)
    tier_weight = weights.get(rating, weights[1])

    # Count how many books have this rating
    books_in_tier = sum(1 for r in BOOKMAKER_RATINGS.values() if r == rating)

    if books_in_tier == 0:
        return 0.0

    # Equal split within tier
    return tier_weight / books_in_tier


def get_sharp_books_only(weights: Optional[Dict[int, float]] = None) -> Dict[str, float]:
    """Return only sharp books (3⭐ and 4⭐) with weights.

    Use this for fair odds calculation.
    """
    if weights is None:
        weights = load_weight_config()

    sharps = {}
    for book, rating in BOOKMAKER_RATINGS.items():
        if rating >= 3:  # Only 3⭐ and 4⭐
            sharps[book] = calculate_book_weight(book, weights)

    return sharps


AU_TARGET_BOOKS = [
    # AU corporates (primary targets)
    "Sportsbet",
    "Pointsbet",
    "Tab",
    "Tabtouch",
    "Unibet_AU",
    "Ladbrokes_AU",
    "Neds",
    "Betr",
    "Boombet",
    # Include local exchange as a target for availability/visibility
    "Betfair_AU",
]


def get_target_books_only() -> list:
    """Return AU target books only (plus Betfair_AU).

    These are the books where we surface EV opportunities for the frontend.
    """
    return AU_TARGET_BOOKS.copy()


def print_rating_summary():
    """Print bookmaker ratings and weight distribution."""
    weights = load_weight_config()

    print("=" * 70)
    print("BOOKMAKER RATINGS & WEIGHTS")
    print("=" * 70)

    for star in [4, 3, 2, 1]:
        books = [b for b, r in BOOKMAKER_RATINGS.items() if r == star]
        tier_weight = weights[star]
        per_book = calculate_book_weight(books[0], weights) if books else 0

        print(f"\n{'⭐' * star} ({star}-STAR) - Tier Weight: {tier_weight:.1%}")
        print(f"   Count: {len(books)} books × {per_book:.2%} each = {tier_weight:.1%}")
        print(
            f"   Books: {', '.join(books[:5])}"
            + (f" ... +{len(books)-5} more" if len(books) > 5 else "")
        )

    print("\n" + "=" * 70)
    print(f"Total Sharps (3⭐+4⭐): {len(get_sharp_books_only(weights))} books")
    print(f"Total Targets (1⭐): {len(get_target_books_only())} books")
    print("=" * 70)


if __name__ == "__main__":
    print_rating_summary()

    print("\n=== SHARP BOOKS WITH DEFAULT WEIGHTS ===\n")
    sharps = get_sharp_books_only()
    for book, weight in sorted(sharps.items(), key=lambda x: x[1], reverse=True):
        print(f"{book:20} {weight:.3f} ({weight:.1%})")

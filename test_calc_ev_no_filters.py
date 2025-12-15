"""
TEST: Calculate EV with NO FILTERS
Shows all rows from raw_odds_pure.csv without any filtering.
This helps debug what data flows through the pipeline.

Key differences from normal calculate_opportunities.py:
- EV_MIN_EDGE = 0 (no minimum EV threshold)
- EXCLUDE_MARKETS = {} (no market exclusions)
- sharp_count >= 0 (accept zero sharp books)
- No outlier removal
- Output ALL opportunities found
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Dict, List, Tuple

import pandas as pd
from dotenv import load_dotenv

# Add src directory to path
SCRIPT_DIR = Path(__file__).parent
src_dir = SCRIPT_DIR / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from pipeline_v2.ratings import BOOKMAKER_RATINGS, get_sport_weight
from pipeline_v2.calculate_opportunities import (
    build_headers as build_ev_headers,
    format_sport_abbrev,
    format_market_name,
    format_commence_time,
)

# Load environment
env_path = SCRIPT_DIR / ".env"
load_dotenv(dotenv_path=env_path)


def get_data_dir():
    """Find data directory."""
    cwd = Path.cwd()
    data_path = cwd / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    if data_path.exists():
        return data_path
    
    script_parent = Path(__file__).parent
    data_path = script_parent / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


DATA_DIR = get_data_dir()
RAW_ODDS_FILE = DATA_DIR / "raw_odds_pure.csv"
# Normalized output to match ev_hits.csv schema
OUTPUT_FILE = DATA_DIR / "ev_all.csv"

# TEST CONFIG: NO FILTERS
EV_MIN_EDGE = 0.0  # Accept ALL EV values (even negative)
EXCLUDE_MARKETS = set()  # No market exclusions
MIN_SHARP_COUNT = 0  # Accept even zero sharp books

# Kelly betting config
BANKROLL = float(os.getenv("BANKROLL", "1000"))
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.25"))

# Target books (1⭐) - Australian bookmakers (matching ratings.py AU_TARGET_BOOKS)
TARGET_BOOKS = [
    "Sportsbet",
    "Pointsbet",
    "Tab",
    "Tabtouch",
    "Unibet_AU",
    "Ladbrokes_AU",
    "Neds",
    "Betr",
    "Boombet",
    "Betfair_AU",  # AU exchange included as target
    "Betright",    # Also in CSV
    "Dabble_Au",   # Also in CSV
    "Playup",      # Also in CSV
]


def normalize_book_name(name: str) -> str:
    """Normalize bookmaker names for matching (lowercase, no underscores)."""
    return name.lower().replace("_", "").replace(" ", "")


def parse_float(s: str | float) -> float:
    """Parse string/float to float, return 0 on error."""
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return float(str(s).strip())
    except (ValueError, AttributeError):
        return 0.0


def kelly_stake(bankroll: float, fair_odds: float, best_odds: float, frac: float) -> float:
    """Calculate Kelly stake."""
    if fair_odds <= 1.0 or best_odds <= 1.0:
        return 0.0
    p = 1.0 / fair_odds
    b = best_odds - 1.0
    q = 1.0 - p
    kelly_pct = max(0, (b * p - q) / b)
    return bankroll * kelly_pct * frac


def extract_sides(rows: List[Dict]) -> Tuple[Dict | None, Dict | None]:
    """Extract side A and side B from grouped rows."""
    if len(rows) == 1:
        return rows[0], None
    if len(rows) >= 2:
        return rows[0], rows[1]
    return None, None


def fair_from_sharps(
    side_a: Dict,
    side_b: Dict,
    bookie_cols: List[str],
    sport_key: str | None = None,
) -> Tuple[float, float, int]:
    """
    TEST VERSION: Compute fair odds using sharp (3⭐/4⭐) books.
    Returns (fair_a, fair_b, sharp_count).
    If no sharp books, returns 0.0, 0.0, 0
    """

    def collect(side: Dict) -> List[Tuple[str, float, int]]:
        bucket: List[Tuple[str, float, int]] = []
        for bk in bookie_cols:
            rating = BOOKMAKER_RATINGS.get(bk, 0)
            if rating < 3:
                continue
            price = parse_float(side.get(bk, "0"))
            if price <= 1:
                continue
            bucket.append((bk, price, rating))
        return bucket

    sport_key = sport_key or side_a.get("sport") or side_b.get("sport") or ""
    sport_weight = get_sport_weight(str(sport_key)) if sport_key else 1.0

    sharp_a = collect(side_a)
    sharp_b = collect(side_b)

    def fair(bucket: List[Tuple[str, float, int]]) -> float:
        # TEST: Accept even single sharp book
        if len(bucket) < 1:
            return 0.0
        total_weight = sum(rating * sport_weight for _, _, rating in bucket)
        weighted_sum = sum((1.0 / price) * (rating * sport_weight) for _, price, rating in bucket)
        if total_weight == 0 or weighted_sum <= 0:
            return 0.0
        return 1.0 / (weighted_sum / total_weight)

    fair_a = fair(sharp_a)
    fair_b = fair(sharp_b)
    sharp_count = min(len(sharp_a), len(sharp_b)) if sharp_a or sharp_b else 0

    return fair_a, fair_b, sharp_count


def process_two_way_markets(
    grouped: Dict, bookie_cols: List[str], verbose: bool = False
) -> List[Dict]:
    """TEST VERSION: Process markets with NO FILTERS."""
    opportunities: List[Dict] = []

    stats = {
        "total_buckets": len(grouped),
        "missing_sides": 0,
        "no_sharps": 0,
        "checked_opportunities": 0,
        "found_ev": 0,
    }

    # Map CSV column names to target books (case-insensitive, flexible matching)
    target_books = []
    target_normalized = {normalize_book_name(b): b for b in TARGET_BOOKS}
    
    for col in bookie_cols:
        col_norm = normalize_book_name(col)
        if col_norm in target_normalized:
            target_books.append(col)
    
    if verbose:
        print(f"\n[TEST MODE] Processing with NO FILTERS")
        print(f"   Target AU bookmakers: {len(target_books)}")
        print(f"   {', '.join(target_books)}")

    for (sport, event_id, market, point, player_name), rows in grouped.items():
        # TEST: No market exclusions
        
        side_a, side_b = extract_sides(rows)
        if not side_a:
            stats["missing_sides"] += 1
            continue

        # TEST: Accept even if only one side or no sharps
        fair_a, fair_b, sharp_count = fair_from_sharps(
            side_a, side_b or {}, bookie_cols, sport
        )
        
        # Track but don't skip
        if fair_a <= 1 and fair_b <= 1:
            stats["no_sharps"] += 1

        sel_a = side_a.get("selection", "")
        sel_b = side_b.get("selection", "") if side_b else ""

        away = side_a.get("away_team", "")
        home = side_a.get("home_team", "")
        teams = f"{away} V {home}" if away and home else ""

        base_meta = {
            "timestamp": side_a.get("timestamp", ""),
            "sport": sport,
            "event_id": event_id,
            "commence_time": side_a.get("commence_time", ""),
            "teams": teams,
            "market": market,
            "line": point,
            "sharp_book_count": sharp_count,
        }

        def maybe_player(selection: str) -> str:
            s = selection.replace("Over", "").replace("Under", "").replace("+", "").strip()
            return s

        # Evaluate all opportunities (no EV minimum)
        for side, fair, sel in [(side_a, fair_a, sel_a)]:
            if side_b:
                sides_to_check = [(side_a, fair_a, sel_a), (side_b, fair_b, sel_b)]
            else:
                sides_to_check = [(side_a, fair_a, sel_a)]
            
            for side, fair, sel in sides_to_check:
                for book in target_books:
                    odds = parse_float(side.get(book, "0"))
                    if odds <= 1:
                        continue

                    stats["checked_opportunities"] += 1
                    
                    # TEST: Calculate EV even if fair is invalid
                    ev = (odds / fair) - 1.0 if fair > 1 else 0.0
                    
                    # TEST: No minimum threshold - accept ALL
                    stats["found_ev"] += 1
                    
                    prob = 1.0 / fair if fair > 1 else 0.0
                    stake = kelly_stake(BANKROLL, fair, odds, KELLY_FRACTION) if fair > 1 else 0.0

                    opp = {
                        **base_meta,
                        "player": maybe_player(sel),
                        "selection": sel,
                        "best_book": book,
                        "odds_decimal": odds,
                        "fair_odds": fair,
                        "ev_percent": ev * 100,
                        "implied_prob": prob * 100,
                        "stake": stake,
                    }

                    for bk in bookie_cols:
                        val = parse_float(side.get(bk, "0"))
                        opp[bk] = val if val > 0 else 0

                    opportunities.append(opp)

    if verbose:
        print(f"\n[TEST] Processing Stats:")
        print(f"   Total market buckets: {stats['total_buckets']}")
        print(f"   Missing sides: {stats['missing_sides']}")
        print(f"   No sharp coverage: {stats['no_sharps']}")
        print(f"   Book/side combos checked: {stats['checked_opportunities']}")
        print(f"   Total opportunities found: {stats['found_ev']}")

    return opportunities


def build_headers(bookie_cols: List[str]) -> List[str]:
    """Build header identical to pipeline ev_hits schema.

    Uses pipeline's build_headers to ensure same ordering and formatting,
    including the special placement of Playup, Betright, Dabble_Au after Boombet.
    """
    return build_ev_headers(bookie_cols)


def pretty_float(x, decimals=2):
    """Format float for display."""
    if x == 0:
        return "0"
    return f"{x:.{decimals}f}"


def main():
    print("[TEST] Calculate EV with NO FILTERS")
    print("=" * 70)
    
    if not RAW_ODDS_FILE.exists():
        print(f"❌ Raw odds file not found: {RAW_ODDS_FILE}")
        print("   Run extract_odds.py first")
        sys.exit(1)

    print(f"[OK] Reading {RAW_ODDS_FILE}")
    df = pd.read_csv(RAW_ODDS_FILE)
    print(f"[OK] Loaded {len(df)} rows")

    if df.empty:
        print("⚠️ No data in raw_odds_pure.csv")
        sys.exit(0)

    # Identify bookmaker columns
    meta_cols = {
        "timestamp",
        "sport",
        "event_id",
        "away_team",
        "home_team",
        "commence_time",
        "market",
        "point",
        "selection",
    }
    bookie_cols = [c for c in df.columns if c not in meta_cols]
    print(f"[OK] Found {len(bookie_cols)} bookmaker columns")

    # Group by (sport, event_id, market, point)
    # Player name is embedded in selection for player props
    df["point"] = df["point"].fillna(0.0).astype(float)

    grouped = {}
    for _, row in df.iterrows():
        # Extract player from selection if it's a player prop
        selection = str(row.get("selection", ""))
        player_name = ""
        if "Over" in selection or "Under" in selection:
            # Player prop: extract player name
            player_name = selection.replace("Over", "").replace("Under", "").replace("+", "").strip()
        
        key = (
            row["sport"],
            row["event_id"],
            row["market"],
            row["point"],
            player_name,
        )
        grouped.setdefault(key, []).append(row.to_dict())

    print(f"[OK] Grouped into {len(grouped)} market buckets")

    # Process
    opportunities = process_two_way_markets(grouped, bookie_cols, verbose=True)
    print(f"\n[OK] Found {len(opportunities)} opportunities (NO FILTERS)")

    # Write CSV
    if not opportunities:
        print("⚠️ No opportunities to write")
        sys.exit(0)

    headers = build_headers(bookie_cols)

    # Map internal fields to ev_hits display headers
    field_map = {
        "Start Time": "commence_time",
        "Sport": "sport",
        "Teams": "teams",
        "Market": "market",
        "Line": "line",
        "Selection": "selection",
        "Sharps": "sharp_book_count",
        "Book": "best_book",
        "Odds": "odds_decimal",
        "Fair": "fair_odds",
        "EV%": "ev_percent",
        "Prob": "implied_prob",
        "Stake": "stake",
    }

    def format_row(opp: Dict) -> Dict:
        row: Dict[str, str] = {}
        for col in headers:
            internal = field_map.get(col, col)
            val = opp.get(internal, "")

            if col == "Start Time" and val:
                row[col] = format_commence_time(val)
            elif col == "Sport" and val:
                row[col] = format_sport_abbrev(val)
            elif col == "Market" and val:
                row[col] = format_market_name(val)
            elif col == "EV%" and isinstance(val, (int, float)):
                row[col] = f"{val:.2f}%"
            elif col == "Prob" and isinstance(val, (int, float)):
                row[col] = f"{val:.2f}%"
            elif col == "Stake" and isinstance(val, (int, float)):
                row[col] = f"${int(val)}"
            elif col in ["Odds", "Fair"] and isinstance(val, (int, float)):
                row[col] = f"{val:.4f}"
            elif isinstance(val, float):
                row[col] = f"{val:.4f}" if val > 0 else ""
            else:
                row[col] = val if val != 0 else ""
        return row

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for opp in opportunities:
            writer.writerow(format_row(opp))

    print(f"✅ Wrote {len(opportunities)} rows to {OUTPUT_FILE}")
    print("[DONE] Test complete - review output CSV")


if __name__ == "__main__":
    main()

"""
Calculate EV opportunities from all_raw_odds.csv
Reads the merged raw odds file, calculates fair odds from sharp books,
and outputs EV-positive opportunities to all_ev_hits.csv.
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Dict, List, Tuple, Optional

import config

# Data paths
DATA_DIR = Path(__file__).parent / "data"
INPUT_FILE = DATA_DIR / config.MERGED_RAW_ODDS
OUTPUT_FILE = DATA_DIR / config.EV_HITS_FILE


def parse_float(val: str) -> float:
    """Parse string to float, return 0 on error."""
    try:
        return float(val) if val else 0.0
    except:
        return 0.0


def normalize_bookmaker_key(key: str) -> str:
    """Normalize bookmaker key to match config (lowercase, no special chars)."""
    return key.lower().replace("_", "").replace("-", "")


def is_over_selection(selection: str) -> bool:
    """Check if selection is an Over outcome."""
    s = selection.lower()
    return s.startswith("over") or s.endswith(" over")


def is_under_selection(selection: str) -> bool:
    """Check if selection is an Under outcome."""
    s = selection.lower()
    return s.startswith("under") or s.endswith(" under")


def extract_player_name(selection: str) -> str:
    """Extract player name from selection (removes Over/Under suffix)."""
    parts = selection.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].lower() in {"over", "under"}:
        return parts[0]
    return selection


def group_markets(rows: List[Dict]) -> Dict[Tuple, List[Dict]]:
    """
    Group rows by (sport, event_id, market, line, player).
    Each group should contain exactly 2 rows (Over/Under or Home/Away).
    """
    groups = defaultdict(list)
    
    for row in rows:
        market = row.get("market", "")
        selection = row.get("selection", "")
        
        # For player props, include player name in grouping
        player = ""
        if market.startswith(("player_", "batter_", "pitcher_", "goalie_")):
            player = extract_player_name(selection)
        
        key = (
            row.get("sport", ""),
            row.get("event_id", ""),
            market,
            row.get("line", ""),
            player,
        )
        groups[key].append(row)
    
    return groups


def extract_two_sides(rows: List[Dict]) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Extract exactly 2 sides from grouped rows (Over/Under or Team A/Team B).
    Returns (side1, side2) or (None, None) if not valid 2-way market.
    """
    if len(rows) != 2:
        return None, None
    
    # Check for exactly 2 unique selections
    selections = set(r.get("selection", "") for r in rows)
    if len(selections) != 2:
        return None, None
    
    # Identify Over/Under sides
    over_row = next((r for r in rows if is_over_selection(r.get("selection", ""))), None)
    under_row = next((r for r in rows if is_under_selection(r.get("selection", ""))), None)
    
    if over_row and under_row:
        return over_row, under_row
    
    # For h2h/spreads (not Over/Under), just return the two rows
    return rows[0], rows[1]


def calculate_fair_odds(side1: Dict, side2: Dict, bookmaker_columns: List[str]) -> Tuple[float, float, int]:
    """
    Calculate fair odds from sharp bookmakers using median.
    Returns (fair_odds_side1, fair_odds_side2, sharp_count).
    """
    sharp_odds_1 = []
    sharp_odds_2 = []
    
    for col in bookmaker_columns:
        if not config.is_sharp_book(col):
            continue
        
        odds1 = parse_float(side1.get(col, ""))
        odds2 = parse_float(side2.get(col, ""))
        
        if odds1 > 1.0:
            sharp_odds_1.append(odds1)
        if odds2 > 1.0:
            sharp_odds_2.append(odds2)
    
    # Require minimum sharp book coverage
    sharp_count = min(len(sharp_odds_1), len(sharp_odds_2))
    if sharp_count < config.MIN_SHARP_BOOKS:
        return 0.0, 0.0, 0
    
    # Use median for fair odds
    fair_1 = median(sharp_odds_1) if sharp_odds_1 else 0.0
    fair_2 = median(sharp_odds_2) if sharp_odds_2 else 0.0
    
    return fair_1, fair_2, sharp_count


def find_ev_opportunities(side: Dict, fair_odds: float, bookmaker_columns: List[str]) -> List[Dict]:
    """
    Find EV-positive opportunities for one side of a market.
    Returns list of EV hits (one per target bookmaker with positive EV).
    """
    if fair_odds <= 1.0:
        return []
    
    opportunities = []
    fair_prob = 1.0 / fair_odds
    
    for col in bookmaker_columns:
        if not config.is_target_book(col):
            continue
        
        target_odds = parse_float(side.get(col, ""))
        if target_odds <= 1.0:
            continue
        
        # Calculate EV
        ev_decimal = (target_odds * fair_prob) - 1.0
        
        if ev_decimal >= config.EV_MIN_EDGE:
            # Kelly Criterion stake
            edge = ev_decimal
            kelly_full = edge / (target_odds - 1)
            stake = config.DEFAULT_BANKROLL * kelly_full * config.DEFAULT_KELLY_FRACTION
            stake = max(0, min(stake, config.DEFAULT_BANKROLL * 0.1))  # Cap at 10%
            
            opportunities.append({
                "timestamp": datetime.now().isoformat(),
                "sport": side.get("sport", ""),
                "event_id": side.get("event_id", ""),
                "commence_time": side.get("commence_time", ""),
                "teams": side.get("teams", ""),
                "market": side.get("market", ""),
                "line": side.get("line", ""),
                "selection": side.get("selection", ""),
                "player": side.get("player", ""),
                "bookmaker": col,
                "odds": f"{target_odds:.2f}",
                "fair_odds": f"{fair_odds:.2f}",
                "ev_percent": f"{ev_decimal * 100:.2f}",
                "implied_prob": f"{fair_prob * 100:.2f}",
                "stake": f"{stake:.2f}",
            })
    
    return opportunities


def calculate_ev():
    """Main EV calculation workflow."""
    print("[EV CALC] Calculate EV opportunities from all_raw_odds.csv")
    print("=" * 70)
    
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        print("   Run merge_raw_odds.py first to create all_raw_odds.csv")
        return
    
    # Read all raw odds
    print(f"[READ] Loading {INPUT_FILE.name}...")
    rows = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        bookmaker_columns = [
            col for col in reader.fieldnames
            if col not in config.METADATA_COLUMNS
        ]
        for row in reader:
            rows.append(row)
    
    print(f"✓ Loaded {len(rows)} rows")
    print(f"✓ Found {len(bookmaker_columns)} bookmaker columns")
    
    # Group by market
    print(f"\n[GROUP] Grouping rows by market...")
    groups = group_markets(rows)
    print(f"✓ Found {len(groups)} unique markets")
    
    # Calculate EV for each market
    print(f"\n[CALC] Calculating EV opportunities...")
    all_opportunities = []
    market_count = 0
    skip_count = 0
    
    for key, market_rows in groups.items():
        market_count += 1
        
        # Extract two sides
        side1, side2 = extract_two_sides(market_rows)
        if not side1 or not side2:
            skip_count += 1
            continue
        
        # Skip excluded markets
        market_type = side1.get("market", "")
        if market_type in config.EXCLUDE_MARKETS:
            skip_count += 1
            continue
        
        # Calculate fair odds
        fair_1, fair_2, sharp_count = calculate_fair_odds(side1, side2, bookmaker_columns)
        
        if fair_1 <= 1.0 or fair_2 <= 1.0:
            skip_count += 1
            continue
        
        # Find EV opportunities for both sides
        opps_1 = find_ev_opportunities(side1, fair_1, bookmaker_columns)
        opps_2 = find_ev_opportunities(side2, fair_2, bookmaker_columns)
        
        all_opportunities.extend(opps_1)
        all_opportunities.extend(opps_2)
    
    print(f"✓ Processed {market_count} markets")
    print(f"  Skipped: {skip_count} (invalid or excluded)")
    print(f"  Found: {len(all_opportunities)} EV opportunities")
    
    # Write EV opportunities to CSV
    if not all_opportunities:
        print("\n⚠️  No EV opportunities found")
        return
    
    print(f"\n[WRITE] Writing {len(all_opportunities)} opportunities to {OUTPUT_FILE.name}...")
    
    headers = [
        "timestamp", "sport", "event_id", "commence_time", "teams",
        "market", "line", "selection", "player", "bookmaker",
        "odds", "fair_odds", "ev_percent", "implied_prob", "stake"
    ]
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for opp in all_opportunities:
            writer.writerow(opp)
    
    print(f"✅ Wrote {OUTPUT_FILE}")
    
    # Summary by sport
    print(f"\n[SUMMARY]")
    by_sport = defaultdict(int)
    for opp in all_opportunities:
        by_sport[opp["sport"]] += 1
    
    for sport in sorted(by_sport.keys()):
        print(f"  {sport}: {by_sport[sport]} opportunities")
    
    print("\n[DONE]")


def main():
    calculate_ev()


if __name__ == "__main__":
    main()

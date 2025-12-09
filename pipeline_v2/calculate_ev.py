"""
CALCULATE EV FROM RAW ODDS (wide format)
Reads the wide raw CSV (one row per outcome with all bookmaker columns),
computes fair odds from sharp books (DK/FD/Betfair when present), then
writes EV-positive opportunities to CSV and PostgreSQL database.
"""
import csv
import sys
import os
from pathlib import Path
from statistics import median
from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import database models (adjust path to EV_Finder)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "EV_Finder" / "src"))
from database import Base, OddsSnapshot

# File locations
RAW_CSV = Path(__file__).parent.parent / "data" / "raw_odds_pure.csv"
EV_CSV = Path(__file__).parent.parent / "data" / "ev_opportunities.csv"

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. Please set it in your environment (e.g., in .env file)."
    )
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# EV settings
EV_MIN_EDGE = 0.01  # 1%
BANKROLL = 1000
KELLY_FRACTION = 0.25

# Metadata columns present in raw CSV
META_COLS = {
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

# Treat these as sharp sources (must have BOTH sides to be used)
# Expanded: All major sharp bookmakers across regions
SHARP_COLS = [
    "Pinnacle",
    "Draftkings",
    "Fanduel",
    "Betmgm",
    "Betonline",
    "Bovada",
    "Lowvig",
    "Mybookie",
    "Betrivers",
    "Betfair_AU",
    "Betfair_EU",
    "Betfair_UK",
    "Marathonbet",
    "Betsson",
    "Nordicbet",
]

# Limit EV targets to AU books present in this dataset
AU_TARGET_BOOKS = {
    "Sportsbet",
    "Pointsbet",
    "Tab",
    "Tabtouch",
    "Unibet_AU",
    "Ladbrokes_AU",
    "Neds",
    "Betr",
    "Boombet",
    "Betfair_AU",  # include exchange if present
}

# Skip these markets (exchange-only, invalid for sharp pricing)
EXCLUDE_MARKETS = {"spreads_lay", "totals_lay"}

# Minimum bookmakers required to establish fair odds
MIN_BOOKMAKER_COVERAGE = 2


def devig_two_way(over_odds: float, under_odds: float) -> Tuple[float, float]:
    """
    Devig two-way odds (Over/Under, Spread sides, etc.)
    Returns: (prob_over, prob_under) - probabilities that sum to ~1.0
    """
    if over_odds <= 1 or under_odds <= 1:
        return 0.0, 0.0
    
    over_prob = 1.0 / over_odds
    under_prob = 1.0 / under_odds
    total = over_prob + under_prob
    
    if total == 0:
        return 0.0, 0.0
    
    # Devig: proportional scaling
    over_devig = over_prob / total
    under_devig = under_prob / total
    
    return over_devig, under_devig


def calculate_fair_odds_two_way(
    sharps_over: List[float],
    sharps_under: List[float]
) -> Tuple[float, float]:
    """
    Calculate fair odds from sharp bookmaker odds using median.
    """
    if not sharps_over or not sharps_under:
        return 0.0, 0.0
    
    # Use median of sharp odds
    fair_over = sorted(sharps_over)[len(sharps_over) // 2]
    fair_under = sorted(sharps_under)[len(sharps_under) // 2]
    
    return fair_over, fair_under


def kelly_stake(bankroll: float, fair_odds: float, bet_odds: float, kelly_frac: float) -> float:
    """Calculate Kelly Criterion stake."""
    if bet_odds <= 1 or fair_odds <= 1:
        return 0.0
    
    prob = 1.0 / fair_odds
    edge = (bet_odds * prob) - (1 - prob)
    
    if edge <= 0:
        return 0.0
    
    kelly_full = edge / (bet_odds - 1)
    stake = bankroll * kelly_full * kelly_frac
    
    return max(0, min(stake, bankroll * 0.1))  # Cap at 10% of bankroll


def read_raw_odds() -> List[Dict]:
    """Read raw odds CSV."""
    if not RAW_CSV.exists():
        print(f"[!] {RAW_CSV} not found")
        return []

    rows = []
    try:
        with open(RAW_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        print(f"[OK] Read {len(rows)} rows from {RAW_CSV}")
        return rows
    except Exception as e:
        print(f"[!] Error reading CSV: {e}")
        return []


def parse_float(val: str) -> float:
    try:
        return float(val)
    except Exception:
        return 0.0


def _player_key(selection: str) -> str:
    """Extract player identifier (drop trailing Over/Under)."""
    if not selection:
        return ""
    parts = selection.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].lower() in {"over", "under"}:
        return parts[0]
    return selection


def group_rows_wide(rows: List[Dict]) -> Dict[Tuple[str, str, str, str, str], List[Dict]]:
    """Group rows by (sport, event_id, market, point, player_name).

    Player props get their own bucket per player to avoid mixing multiple players
    in one market/line (e.g., Donte DiVincenzo Over grouped separately from others).
    Non-player markets keep player_name empty so grouping behavior is unchanged.
    """
    grouped: Dict[Tuple[str, str, str, str, str], List[Dict]] = {}
    for row in rows:
        market = row.get("market", "")
        selection = row.get("selection", "")
        player_name = _player_key(selection) if market.startswith("player_") else ""

        key = (
            row.get("sport", ""),
            row.get("event_id", ""),
            market,
            row.get("point", ""),
            player_name,
        )
        grouped.setdefault(key, []).append(row)
    return grouped


def extract_sides(rows: List[Dict]) -> Tuple[Dict, Dict]:
    """Return two sides (A, B) from the grouped rows."""
    def is_over(sel: str) -> bool:
        s = sel.lower()
        return s.startswith("over") or s.endswith(" over")

    def is_under(sel: str) -> bool:
        s = sel.lower()
        return s.startswith("under") or s.endswith(" under")

    over_row = next((r for r in rows if is_over(r.get("selection", ""))), None)
    under_row = next((r for r in rows if is_under(r.get("selection", ""))), None)

    if over_row and under_row:
        return over_row, under_row

    # Fallback: take first two distinct selections
    if len(rows) >= 2:
        return rows[0], rows[1]

    return None, None


def get_bookie_columns(rows: List[Dict]) -> List[str]:
    if not rows:
        return []
    return [c for c in rows[0].keys() if c not in META_COLS]


def fair_from_sharps(side_a: Dict, side_b: Dict, bookie_cols: List[str]) -> Tuple[float, float, int]:
    """Compute fair odds from sharp books present on both sides.
    Returns (fair_a, fair_b, sharp_count) where sharp_count indicates confidence.
    Requires at least 2 different bookmakers with full coverage of both sides.
    """
    sharp_pairs = []
    for col in SHARP_COLS:
        if col not in bookie_cols:
            continue
        a = parse_float(side_a.get(col, "0"))
        b = parse_float(side_b.get(col, "0"))
        if a > 1 and b > 1:
            pa, pb = devig_two_way(a, b)
            if pa > 0 and pb > 0:
                sharp_pairs.append((1 / pa, 1 / pb))

    if not sharp_pairs or len(sharp_pairs) < MIN_BOOKMAKER_COVERAGE:
        return 0.0, 0.0, 0

    fair_a = median([p[0] for p in sharp_pairs])
    fair_b = median([p[1] for p in sharp_pairs])
    return fair_a, fair_b, len(sharp_pairs)


def process_two_way_markets(grouped: Dict, bookie_cols: List[str], verbose: bool = False) -> List[Dict]:
    opportunities: List[Dict] = []
    
    # Diagnostic counters
    stats = {
        'total_buckets': len(grouped),
        'missing_sides': 0,
        'no_sharps': 0,
        'checked_opportunities': 0,
        'below_threshold': 0,
        'found_ev': 0
    }

    # Limit EV targets to AU books present in this dataset
    target_books = [b for b in bookie_cols if b in AU_TARGET_BOOKS]
    
    if verbose:
        print(f"\n[EV DETAIL] Target AU bookmakers detected: {len(target_books)}")
        print(f"   {', '.join(target_books)}")

    for (sport, event_id, market, point, player_name), rows in grouped.items():
        # Skip exchange-only markets
        if market in EXCLUDE_MARKETS:
            stats['no_sharps'] += 1
            continue
        
        side_a, side_b = extract_sides(rows)
        if not side_a or not side_b:
            stats['missing_sides'] += 1
            continue

        fair_a, fair_b, sharp_count = fair_from_sharps(side_a, side_b, bookie_cols)
        if fair_a <= 1 or fair_b <= 1 or sharp_count == 0:
            stats['no_sharps'] += 1
            continue

        sel_a = side_a.get("selection", "")
        sel_b = side_b.get("selection", "")

        base_meta = {
            "timestamp": side_a.get("timestamp", ""),
            "sport": sport,
            "event_id": event_id,
            "away_team": side_a.get("away_team", ""),
            "home_team": side_a.get("home_team", ""),
            "commence_time": side_a.get("commence_time", ""),
            "market": market,
            "line": point,
            "sharp_book_count": sharp_count,
        }

        def maybe_player(selection: str) -> str:
            # For props selection contains player + Over/Under
            s = selection.replace("Over", "").replace("Under", "").replace("+", "").strip()
            return s

        # Evaluate opportunities for both sides, AU books only
        for side, fair, sel in [(side_a, fair_a, sel_a), (side_b, fair_b, sel_b)]:
            for book in target_books:
                odds = parse_float(side.get(book, "0"))
                if odds <= 1:
                    continue

                stats['checked_opportunities'] += 1
                ev = (odds / fair) - 1.0
                if ev < EV_MIN_EDGE:
                    stats['below_threshold'] += 1
                    continue

                stats['found_ev'] += 1
                prob = 1.0 / fair
                stake = kelly_stake(BANKROLL, fair, odds, KELLY_FRACTION)

                # Store raw numbers (will format for CSV later)
                opp = {
                    **base_meta,
                    "player": maybe_player(sel),
                    "selection": sel,
                    "best_book": book,
                    "odds_decimal": odds,
                    "fair_odds": fair,
                    "ev_percent": ev * 100,  # Store as percentage number
                    "implied_prob": prob * 100,  # Store as percentage number
                    "stake": stake,
                }

                for bk in bookie_cols:
                    val = parse_float(side.get(bk, "0"))
                    opp[bk] = val if val > 0 else 0

                opportunities.append(opp)
    
    if verbose:
        print(f"\n[EV DETAIL] EV Calculation Breakdown:")
        print(f"   Total market buckets: {stats['total_buckets']}")
        print(f"   Missing both sides: {stats['missing_sides']}")
        print(f"   No sharp coverage: {stats['no_sharps']}")
        print(f"   Valid buckets checked: {stats['total_buckets'] - stats['missing_sides'] - stats['no_sharps']}")
        print(f"   Book/side combos checked: {stats['checked_opportunities']}")
        print(f"   Below {EV_MIN_EDGE*100:.1f}% threshold: {stats['below_threshold']}")
        print(f"   Found EV opportunities: {stats['found_ev']}")

    return opportunities


def build_headers(bookie_cols: List[str]) -> List[str]:
    # Ensure Pinnacle column is present even if empty
    if "Pinnacle" not in bookie_cols:
        bookie_cols = ["Pinnacle"] + bookie_cols
    base = [
        "timestamp",
        "sport",
        "event_id",
        "away_team",
        "home_team",
        "commence_time",
        "market",
        "player",
        "line",
        "selection",
        "sharp_book_count",
        "best_book",
        "odds_decimal",
        "fair_odds",
        "ev_percent",
        "implied_prob",
        "stake",
    ]
    return base + bookie_cols


def write_opportunities(opportunities: List[Dict], headers: List[str]):
    """Write EV opportunities to CSV and database."""
    if not opportunities:
        print("[!] No opportunities to write")
        return

    # Write to CSV (backup) - format numbers for human readability
    try:
        with open(EV_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for opp in opportunities:
                # Format row for CSV display
                row = {}
                for col in headers:
                    val = opp.get(col, "")
                    if col == "ev_percent" and isinstance(val, (int, float)):
                        row[col] = f"{val:.2f}%"
                    elif col == "implied_prob" and isinstance(val, (int, float)):
                        row[col] = f"{val:.2f}%"
                    elif col == "stake" and isinstance(val, (int, float)):
                        row[col] = f"${int(val)}"
                    elif col in ["odds_decimal", "fair_odds"] and isinstance(val, (int, float)):
                        row[col] = f"{val:.4f}"
                    elif isinstance(val, float):
                        row[col] = f"{val:.4f}" if val > 0 else ""
                    else:
                        row[col] = val if val else ""
                writer.writerow(row)

        print(f"[OK] Wrote {len(opportunities)} opportunities to {EV_CSV}")
    except Exception as e:
        print(f"[!] Error writing CSV: {e}")

    # Write to database - use raw numeric values
    try:
        # Create tables if not exist
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # Clear old records (optional - could keep history)
            db.query(OddsSnapshot).delete()
            
            # Insert new records - data is already in correct format
            for opp in opportunities:
                record = OddsSnapshot(
                    timestamp=datetime.utcnow(),
                    sport=opp.get("sport"),
                    event_id=opp.get("event_id"),
                    away_team=opp.get("away_team"),
                    home_team=opp.get("home_team"),
                    commence_time=datetime.fromisoformat(opp["commence_time"].replace("Z", "+00:00")) if opp.get("commence_time") else None,
                    market=opp.get("market"),
                    player=opp.get("player") if opp.get("player") else None,
                    line=float(opp["point"]) if opp.get("point") else None,
                    selection=opp.get("selection"),
                    bookmaker=opp.get("best_book"),
                    odds_decimal=opp.get("odds_decimal"),
                    fair_odds=opp.get("fair_odds"),
                    ev_percent=opp.get("ev_percent"),
                    implied_prob=opp.get("implied_prob"),
                    sharp_book_count=int(opp.get("sharp_book_count", 0)),
                    stake=opp.get("stake")
                )
                db.add(record)
            
            db.commit()
            print(f"[OK] Wrote {len(opportunities)} opportunities to database")
        finally:
            db.close()
    except Exception as e:
        print(f"[!] Error writing to database: {e}")


def main():
    print("=== EV CALCULATOR (wide) ===\n")

    raw_rows = read_raw_odds()
    if not raw_rows:
        sys.exit(1)

    bookie_cols = get_bookie_columns(raw_rows)
    print(f"[OK] Detected {len(bookie_cols)} bookmaker columns")

    grouped = group_rows_wide(raw_rows)
    print(f"[PROC] Grouped into {len(grouped)} market/line buckets")

    opportunities = process_two_way_markets(grouped, bookie_cols, verbose=True)
    print(f"[OK] Found {len(opportunities)} EV opportunities")

    headers = build_headers(bookie_cols)
    write_opportunities(opportunities, headers)

    print("\n[DONE] Complete")


if __name__ == "__main__":
    main()

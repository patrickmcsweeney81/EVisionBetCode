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
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Import bookmaker ratings & weighting
from ratings import (
    BOOKMAKER_RATINGS,
    load_weight_config,
    calculate_book_weight,
    get_sharp_books_only,
    get_target_books_only,
)

# Database imports (conditional)
Base = declarative_base()


class EVOpportunity(Base):
    __tablename__ = "ev_opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sport = Column(String(50), nullable=False)
    event_id = Column(String(100), nullable=False)
    away_team = Column(String(100))
    home_team = Column(String(100))
    commence_time = Column(DateTime)
    market = Column(String(50), nullable=False)
    point = Column(Float)
    selection = Column(String(200), nullable=False)
    player = Column(String(200))
    fair_odds = Column(Float)
    best_book = Column(String(50), nullable=False)
    best_odds = Column(Float, nullable=False)
    ev_percent = Column(Float, nullable=False)
    sharp_book_count = Column(Integer)
    implied_prob = Column(Float)
    stake = Column(Float)
    kelly_fraction = Column(Float, default=0.25)
    created_at = Column(DateTime, default=datetime.utcnow)

# Load environment - look for .env in parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# File locations - use absolute paths for reliability
# Try multiple locations to support both local and Render deployments
def get_data_dir():
    """Find data directory - supports local and Render deployments"""
    # Option 1: Relative to script location (most common)
    script_parent = Path(__file__).parent.parent
    if (script_parent / "data").exists():
        return script_parent / "data"
    
    # Option 2: Current working directory (Render cron jobs)
    cwd = Path.cwd()
    if (cwd / "data").exists():
        return cwd / "data"
    
    # Option 3: Check if we're in /src subdirectory
    if "src" in str(cwd):
        parent = cwd.parent
        if (parent / "data").exists():
            return parent / "data"
    
    # Default fallback
    return script_parent / "data"

DATA_DIR = get_data_dir()
RAW_CSV = DATA_DIR / "raw_odds_pure.csv"
EV_CSV = DATA_DIR / "ev_opportunities.csv"

# Database connection (optional - only if DATABASE_URL is set)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = None
SessionLocal = None
if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   Continuing with CSV output only...")
        engine = None
        SessionLocal = None

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

# Load bookmaker weights from ratings system
WEIGHT_CONFIG = load_weight_config()
SHARP_WEIGHTS = get_sharp_books_only(WEIGHT_CONFIG)
TARGET_BOOKS = get_target_books_only()

# For backwards compatibility
SHARP_COLS = list(SHARP_WEIGHTS.keys())
AU_TARGET_BOOKS = set(TARGET_BOOKS)  # Will include all 1⭐ books

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
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not RAW_CSV.exists():
        print(f"[!] {RAW_CSV} not found")
        print(f"[!] Looking in: {DATA_DIR}")
        print(f"[!] Data directory exists: {DATA_DIR.exists()}")
        print(f"[!] Contents of {DATA_DIR}:")
        try:
            for item in DATA_DIR.iterdir():
                print(f"    - {item.name}")
        except Exception as e:
            print(f"    (error listing: {e})")
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
    """Return two sides (A, B) from the grouped rows.
    
    If multiple rows exist for same side (different timestamps), 
    prefer the one with most bookmaker coverage.
    """
    def is_over(sel: str) -> bool:
        s = sel.lower()
        return s.startswith("over") or s.endswith(" over")

    def is_under(sel: str) -> bool:
        s = sel.lower()
        return s.startswith("under") or s.endswith(" under")
    
    def count_bookmaker_odds(row: Dict) -> int:
        """Count non-zero bookmaker odds in this row."""
        count = 0
        for key, val in row.items():
            if key not in META_COLS and val:
                try:
                    if float(val) > 1:
                        count += 1
                except:
                    pass
        return count

    # Get all over/under rows
    over_rows = [r for r in rows if is_over(r.get("selection", ""))]
    under_rows = [r for r in rows if is_under(r.get("selection", ""))]
    
    # Pick the row with most bookmaker coverage (handles duplicate timestamps)
    over_row = max(over_rows, key=count_bookmaker_odds) if over_rows else None
    under_row = max(under_rows, key=count_bookmaker_odds) if under_rows else None

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


def remove_outliers_relative(odds_list: List[float], tolerance: float = 0.05) -> List[float]:
    """Remove odds >tolerance% away from median.
    
    Args:
        odds_list: List of decimal odds
        tolerance: Acceptable deviation (default 5%)
    
    Returns:
        Filtered odds list
    """
    if len(odds_list) < 2:
        return odds_list
    
    med = median(odds_list)
    return [o for o in odds_list if abs(o - med) / med <= tolerance]


def fair_from_sharps(side_a: Dict, side_b: Dict, bookie_cols: List[str]) -> Tuple[float, float, int]:
    """Compute weighted fair odds from sharp books (with outlier removal).
    
    Process:
    1. Collect devigged odds from sharp books (3⭐ and 4⭐)
    2. Remove outliers (5% tolerance from median)
    3. Calculate weighted average using SHARP_WEIGHTS
    
    Returns (fair_a, fair_b, sharp_count) where sharp_count = books used.
    Requires at least MIN_BOOKMAKER_COVERAGE weight in result.
    """
    over_odds = []
    under_odds = []
    over_weighted = []
    under_weighted = []
    total_weight = 0.0
    
    for col, weight in SHARP_WEIGHTS.items():
        if col not in bookie_cols:
            continue
        
        a = parse_float(side_a.get(col, "0"))
        b = parse_float(side_b.get(col, "0"))
        
        # Both sides required
        if a <= 1 or b <= 1:
            continue
        
        # Devig
        pa, pb = devig_two_way(a, b)
        if pa > 0 and pb > 0:
            fair_a = 1 / pa
            fair_b = 1 / pb
            
            over_odds.append(fair_a)
            under_odds.append(fair_b)
            over_weighted.append((fair_a, weight))
            under_weighted.append((fair_b, weight))
            total_weight += weight
    
    # Remove outliers before weighting
    over_odds_clean = remove_outliers_relative(over_odds, tolerance=0.05)
    under_odds_clean = remove_outliers_relative(under_odds, tolerance=0.05)
    
    # Recalculate weights for non-outlier books only
    over_weighted = [(o, w) for o, w in over_weighted if o in over_odds_clean]
    under_weighted = [(o, w) for o, w in under_weighted if o in under_odds_clean]
    
    # Calculate separate totals for each side
    over_weight_total = sum(w for _, w in over_weighted)
    under_weight_total = sum(w for _, w in under_weighted)
    
    # Need minimum weight coverage
    if over_weight_total < 0.10 or under_weight_total < 0.10:
        return 0.0, 0.0, 0
    
    # Calculate weighted averages with individual weight totals
    fair_a = sum(odds * weight for odds, weight in over_weighted) / over_weight_total
    fair_b = sum(odds * weight for odds, weight in under_weighted) / under_weight_total
    
    sharp_count = len(over_weighted)  # Use over side count (should equal under count)
    
    return fair_a, fair_b, sharp_count


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

    # Use target books (1⭐) present in this dataset
    target_books = [b for b in bookie_cols if b in TARGET_BOOKS]
    
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

    # Write to database (optional - only if connected)
    if SessionLocal and engine:
        try:
            db = SessionLocal()
            try:
                # Clear old records (optional - could keep history)
                db.query(EVOpportunity).delete()
                
                # Insert new records - data is already in correct format
                for opp in opportunities:
                    commence_ts = None
                    if opp.get("commence_time"):
                        try:
                            commence_ts = datetime.fromisoformat(opp["commence_time"].replace("Z", "+00:00"))
                        except Exception:
                            commence_ts = None

                    record = EVOpportunity(
                        detected_at=datetime.utcnow(),
                        sport=opp.get("sport"),
                        event_id=opp.get("event_id"),
                        away_team=opp.get("away_team"),
                        home_team=opp.get("home_team"),
                        commence_time=commence_ts,
                        market=opp.get("market"),
                        player=opp.get("player") if opp.get("player") else None,
                        point=float(opp["line"]) if opp.get("line") else None,
                        selection=opp.get("selection"),
                        best_book=opp.get("best_book"),
                        best_odds=opp.get("odds_decimal"),
                        fair_odds=opp.get("fair_odds"),
                        ev_percent=opp.get("ev_percent"),
                        implied_prob=opp.get("implied_prob"),
                        sharp_book_count=int(opp.get("sharp_book_count", 0)),
                        stake=opp.get("stake"),
                        kelly_fraction=KELLY_FRACTION,
                    )
                    db.add(record)
                
                db.commit()
                print(f"[OK] Wrote {len(opportunities)} opportunities to database")
            finally:
                db.close()
        except Exception as e:
            print(f"[!] Error writing to database: {e}")
    else:
        print("[OK] Database not connected - skipping database write (CSV output saved)")



def main():
    print("=== EV CALCULATOR (weighted by bookmaker rating & sport) ===\n")
    
    # Debug: Show file paths
    print(f"[DEBUG] Script location: {Path(__file__).resolve()}")
    print(f"[DEBUG] Working directory: {Path.cwd()}")
    print(f"[DEBUG] Data directory: {DATA_DIR}")
    print(f"[DEBUG] Raw CSV path: {RAW_CSV}")
    print(f"[DEBUG] Data dir exists: {DATA_DIR.exists()}")
    print(f"[DEBUG] Raw CSV exists: {RAW_CSV.exists()}")
    print()

    raw_rows = read_raw_odds()
    if not raw_rows:
        sys.exit(1)

    bookie_cols = get_bookie_columns(raw_rows)
    print(f"[OK] Detected {len(bookie_cols)} bookmaker columns")

    # Detect sports in data
    sports_in_data = set(row.get("sport", "unknown") for row in raw_rows)
    print(f"[OK] Detected sports: {', '.join(sorted(sports_in_data))}")

    # Process each sport with its own weight profile
    all_opportunities = []
    
    for sport in sorted(sports_in_data):
        print(f"\n{'='*70}")
        print(f"Processing: {sport}")
        print(f"{'='*70}")
        
        # Load sport-specific weights
        weights = load_weight_config(sport)
        print(f"[CONFIG] Weight profile for {sport}:")
        print(f"  4*: {weights[4]:.1%}  3*: {weights[3]:.1%}  2*: {weights[2]:.1%}  1*: {weights[1]:.1%}")
        
        # Update global weights for this sport
        global SHARP_WEIGHTS, TARGET_BOOKS
        SHARP_WEIGHTS = get_sharp_books_only(weights)
        TARGET_BOOKS = get_target_books_only()
        
        # Filter rows for this sport
        sport_rows = [r for r in raw_rows if r.get("sport") == sport]
        
        # Group and calculate EV
        grouped = group_rows_wide(sport_rows)
        print(f"[PROC] Grouped into {len(grouped)} market/line buckets")

        opportunities = process_two_way_markets(grouped, bookie_cols, verbose=True)
        print(f"[OK] Found {len(opportunities)} EV opportunities")
        
        all_opportunities.extend(opportunities)
    
    print(f"\n{'='*70}")
    print(f"FINAL RESULTS")
    print(f"{'='*70}")
    print(f"Total opportunities across all sports: {len(all_opportunities)}")
    
    # Build headers from first opportunity
    if all_opportunities:
        headers = build_headers(bookie_cols)
        write_opportunities(all_opportunities, headers)
    else:
        print("[!] No opportunities found")

    print("\n[DONE] Complete")


if __name__ == "__main__":
    main()

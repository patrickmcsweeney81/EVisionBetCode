#!/usr/bin/env python3
import os, csv, json, time, statistics, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple

import requests
from dateutil import parser as dateparser
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If python-dotenv isn't installed that's fine; env vars can still come
    # from OS / .bat
    pass

# ---------------------------------------------------------------------
# Paths / files
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

EV_CSV     = DATA_DIR / "hits_ev.csv"     # EV hits only
DEDUP_FILE = DATA_DIR / "seen_hits.json"  # dedupe storage
API_USAGE_FILE = DATA_DIR / "api_usage.json"  # API credits tracking
ALL_ODDS_CSV = DATA_DIR / "all_odds.csv"  # All markets/odds regardless of EV


# ---------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------
def load_env(key: str, default: str = "") -> str:
    v = os.getenv(key)
    return v if v is not None else default

def _strip_inline_comment(val: str) -> str:
    """Return value with any inline '#' comment removed and trimmed.
    Handles cases like "0.03   # comment" from .env files.
    """
    try:
        return val.split("#", 1)[0].strip()
    except Exception:
        return val

def load_env_float(key: str, default: str) -> float:
    try:
        raw = load_env(key, default)
        cleaned = _strip_inline_comment(raw)
        return float(cleaned)
    except Exception:
        return float(default)

def load_env_int(key: str, default: str) -> int:
    try:
        raw = load_env(key, default)
        cleaned = _strip_inline_comment(raw)
        return int(cleaned)
    except Exception:
        return int(default)

ODDS_API_KEY   = load_env("ODDS_API_KEY")
ODDS_API_BASE  = load_env("ODDS_API_BASE", "https://api.the-odds-api.com/v4")
REGIONS        = load_env("REGIONS", "au")
MARKETS        = load_env("MARKETS", "h2h")
# SPORTS: Use specific sports for all future games, or "upcoming" for games starting very soon
# Popular: americanfootball_nfl,basketball_ncaab,basketball_nba,icehockey_nhl,baseball_mlb,soccer_epl
SPORTS         = load_env("SPORTS", "americanfootball_nfl,basketball_ncaab,icehockey_nhl")

# Optional: restrict which sports will request player_props. Comma-separated sport keys.
# Example: "basketball_nba,americanfootball_nfl,icehockey_nhl"
PLAYER_PROPS_SPORTS = [s.strip() for s in load_env("PLAYER_PROPS_SPORTS", "").split(",") if s.strip()]

EV_MIN_EDGE    = load_env_float("EV_MIN_EDGE", "0.03")  # 3%
MIN_PROB       = load_env_float("MIN_PROB", "0.25")  # Minimum win probability (25% = avoid long shots)
MIN_BOOKMAKERS_FOR_FAIR = load_env_int("MIN_BOOKMAKERS_FOR_FAIR", "1")  # Minimum bookmakers needed for reliable fair price (Pinnacle alone is sufficient)

# Line matching tolerance for spreads/totals (allows sharp books with slightly different lines)
# IMPORTANT: 0.5 points is a significant edge in betting! Use 0.25 to avoid mismatched comparisons
# Example: +3.5 vs +3.0 are DIFFERENT bets (push vs loss), so tolerance must be strict
# 0.25 allows matching lines that differ by rounding (e.g., 232.25 vs 232.0) but not half-points
LINE_TOLERANCE = load_env_float("LINE_TOLERANCE", "0.5")  # +/- points allowed when matching lines (use 0.5 for half-point snapping)

# Time filters for game selection (0 = no filter)
MIN_TIME_TO_START_MINUTES = load_env_int("MIN_TIME_TO_START_MINUTES", "5")  # Skip games starting within X minutes
MAX_TIME_TO_START_HOURS = load_env_int("MAX_TIME_TO_START_HOURS", "168")  # Only include games within X hours (168 = 7 days, 0 = no limit)

BETFAIR_COMMISSION = load_env_float("BETFAIR_COMMISSION", "0.06")  # 6%

# Notifications / staking
TELEGRAM_BOT_TOKEN = load_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = load_env("TELEGRAM_CHAT_ID")
TELEGRAM_ENABLED = load_env("TELEGRAM_ENABLED", "1")  # set to "0" to disable
BOTS_TELEGRAM_DEBUG = load_env("TELEGRAM_DEBUG", "0")
BANKROLL = load_env_float("BANKROLL", "1000")
KELLY_FRACTION = load_env_float("KELLY_FRACTION", "0.25")
STAKE_FALLBACK = load_env_float("STAKE_FALLBACK", "10")
SUMMARY_ENABLED = load_env("SUMMARY_ENABLED", "0")  # 1=send run summary telegram
TEST_ALLOW_DUPES = load_env("TEST_ALLOW_DUPES", "0")  # 1=ignore dedupe for testing
FILTER_BOOKS = [b.strip() for b in load_env("FILTER_BOOKS", "").split(",") if b.strip()]
FILTER_SPORTS = [s.strip() for s in load_env("FILTER_SPORTS", "").split(",") if s.strip()]
EV_MAX_ALERTS = load_env_int("EV_MAX_ALERTS", "0")   # 0 = unlimited

# Fair price weighting (combine sharp sources by weighted probabilities)
# Pinnacle (50%): Tier 1 sharp, industry standard
# Betfair (30%): Tier 2 exchange with deep liquidity (commission-adjusted)
# Median of other sharps (20%): Includes Matchbook + all US books for consensus
# Default weights: prioritize Pinnacle, include Betfair and a small median-of-sharps
# Recommended starting weights (can be overridden via env):
#   Pinnacle: 70%, Betfair: 20%, other sharps (median): 10%
FAIR_WEIGHT_PINNACLE = load_env_float("FAIR_WEIGHT_PINNACLE", "0.7")
FAIR_WEIGHT_BETFAIR  = load_env_float("FAIR_WEIGHT_BETFAIR", "0.2")
FAIR_WEIGHT_SHARPS   = load_env_float("FAIR_WEIGHT_SHARPS", "0.1")

# Pinnacle-priority options: when enabled, prefer Pinnacle as canonical line/source-of-truth
PINNACLE_PRIORITY = load_env("PINNACLE_PRIORITY", "1")  # 1=enable pinnacle-priority canonicalization
PINNACLE_WEIGHT = load_env_float("PINNACLE_WEIGHT", str(FAIR_WEIGHT_PINNACLE))
PINNACLE_RELAX_MIN_SHARPS = load_env("PINNACLE_RELAX_MIN_SHARPS", "1")  # 1=relax MIN_SHARP_BOOKIES when Pinnacle present
PINNACLE_SYNTH_METHOD = load_env("PINNACLE_SYNTH_METHOD", "complement")  # complement|mirror

# Explicit list of other sharp bookmakers to use for the 'median' component.
# Comma-separated env var. Default includes 4 known sharps.
SHARP_BOOKIES = [b.strip() for b in load_env("SHARP_BOOKIES", "matchbook,lowvig,unibet,williamhill_us").split(",") if b.strip()]
# Minimum number of sharp book samples required (per side) to consider the median-of-sharps
MIN_SHARP_BOOKIES = load_env_int("MIN_SHARP_BOOKIES", "4")

# Maximum allowable odds to consider for EV alerts (skip extremely longshots or very large prices)
# BonusBank example: user set max allowable odds to 3.0 (decimal). Set via env MAX_ALLOWED_ODDS.
MAX_ALLOWED_ODDS = load_env_float("MAX_ALLOWED_ODDS", "10.0")

# Minimum stake filter (skip opportunities below this amount)
MIN_STAKE = load_env_float("MIN_STAKE", "5.0")

# Maximum bookmaker decimal odds to consider for EV alerts (helps avoid very longshots)
# Set to 3.0 to mirror user preference (only consider odds <= 3.0)
MAX_ALLOWED_ODDS = load_env_float("MAX_ALLOWED_ODDS", "3.0")

# Debug flag for bookmaker data collection
EV_DEBUG_BOOKS = load_env("EV_DEBUG_BOOKS", "0")  # 1=print book details per event

# Outlier detection and data quality filters
OUTLIER_DETECTION_ENABLED = load_env("OUTLIER_DETECTION_ENABLED", "1")  # 1=remove outliers from median calculation
MAX_MARGIN_PERCENT = load_env_float("MAX_MARGIN_PERCENT", "15.0")  # Skip bookmakers with margins > 15% (likely stale/suspicious)
MIN_BOOKMAKERS_AFTER_OUTLIERS = load_env_int("MIN_BOOKMAKERS_AFTER_OUTLIERS", "5")  # Minimum books required after outlier removal

# Interpolation to synthesize fair at target line when no exact sharp match
ENABLE_INTERPOLATION = load_env("ENABLE_INTERPOLATION", "1")
# Defaults tuned: widen neighbor window and reduce min samples to improve coverage on AU-heavy markets
INTERP_MAX_GAP = float(load_env("INTERP_MAX_GAP", "1.5"))  # Max distance to use neighbors (e.g., 1.5 points)
INTERP_MIN_SAMPLES = load_env_int("INTERP_MIN_SAMPLES", "3")  # Min samples per neighbor line for interpolation
# When neighbor interpolation fails, allow a single-nearest-line fallback if at least
# this many samples exist on that single line (set to 1 to be permissive).
INTERP_MIN_SAMPLES_SINGLE = load_env_int("INTERP_MIN_SAMPLES_SINGLE", "2")

# In-memory audit of interpolation decisions. Each entry is a dict and will be
# flushed to data/interp_audit.csv at the end of the run when present.
INTERP_AUDIT: List[Dict[str, Any]] = []

def _record_interp_audit(entry: Dict[str, Any]) -> None:
    """Append an interpolation audit entry to the in-memory list.

    Expected keys: timestamp, event_id, sport, market, side, method,
    target_line, neighbors (string), neighbor_counts (string), result_prob
    """
    try:
        INTERP_AUDIT.append(entry)
    except Exception:
        pass

def _flush_interp_audit_csv() -> None:
    """Write any collected interpolation audit entries to data/interp_audit.csv.

    This is intentionally lightweight: if the file doesn't exist it is created,
    otherwise entries are appended. Quiet on failure.
    """
    try:
        if not INTERP_AUDIT:
            return
        out_path = DATA_DIR / "interp_audit.csv"
        write_header = not out_path.exists()
        with out_path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp","event_id","sport","market","side","method","target_line","neighbors","neighbor_counts","result_prob"])
            for e in INTERP_AUDIT:
                writer.writerow([
                    e.get("timestamp",""),
                    e.get("event_id",""),
                    e.get("sport",""),
                    e.get("market",""),
                    e.get("side",""),
                    e.get("method",""),
                    e.get("target_line",""),
                    e.get("neighbors",""),
                    e.get("neighbor_counts",""),
                    e.get("result_prob",""),
                ])
        # Clear after flush to avoid duplicate writes across runs in same session
        INTERP_AUDIT.clear()
    except Exception:
        # Don't crash the run for audit failures
        try:
            if EV_DEBUG_BOOKS == "1":
                import traceback
                traceback.print_exc()
        except Exception:
            pass

# Pinnacle zero-fair diagnostics: collect spread/totals lines where Pinnacle
# was available but the master fair odds calculated to 0.0. This helps target
# cases where we failed to synthesize a fair despite Pinnacle being present.
DIAG_PINNACLE_ISSUES: List[Dict[str, Any]] = []

def _record_pinnacle_issue(entry: Dict[str, Any]) -> None:
    try:
        DIAG_PINNACLE_ISSUES.append(entry)
    except Exception:
        pass

def _flush_pinnacle_issues_csv() -> None:
    try:
        if not DIAG_PINNACLE_ISSUES:
            return
        out_path = DATA_DIR / "pinnacle_zero_fair.csv"
        write_header = not out_path.exists()
        with out_path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp","event_id","sport","market","line",
                    "key_A","key_B","pinnacle_found","fair_master_A","fair_master_B","pinnacle_keys"
                ])
            for e in DIAG_PINNACLE_ISSUES:
                writer.writerow([
                    e.get("timestamp", ""),
                    e.get("event_id", ""),
                    e.get("sport", ""),
                    e.get("market", ""),
                    e.get("line", ""),
                    e.get("key_A", ""),
                    e.get("key_B", ""),
                    e.get("pinnacle_found", ""),
                    e.get("fair_master_A", ""),
                    e.get("fair_master_B", ""),
                    ";".join(e.get("pinnacle_keys", [])),
                ])
        DIAG_PINNACLE_ISSUES.clear()
    except Exception:
        try:
            if EV_DEBUG_BOOKS == "1":
                import traceback
                traceback.print_exc()
        except Exception:
            pass

# Temporary holder populated by build_fair_prices so callers can correlate
# the last build call with diagnostic checks immediately after.
LAST_BUILD_FAIR_DIAG: Dict[str, Any] = {}

# Diagnostic: sharp presence per event/line
DIAG_SHARP_PRESENCE: List[Dict[str, Any]] = []

def _record_sharp_presence(entry: Dict[str, Any]) -> None:
    try:
        DIAG_SHARP_PRESENCE.append(entry)
    except Exception:
        pass

def _flush_sharp_presence_csv() -> None:
    try:
        if not DIAG_SHARP_PRESENCE:
            return
        out_path = DATA_DIR / "sharp_presence.csv"
        write_header = not out_path.exists()
        with out_path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp","event_id","sport","market","line","key_A","key_B",
                    "pinnacle_present","betfair_present","sharp_count_A","sharp_count_B",
                    "sharps_A","sharps_B"
                ])
            for e in DIAG_SHARP_PRESENCE:
                writer.writerow([
                    e.get("timestamp",""),
                    e.get("event_id",""),
                    e.get("sport",""),
                    e.get("market",""),
                    e.get("line",""),
                    e.get("key_A",""),
                    e.get("key_B",""),
                    e.get("pinnacle_present",""),
                    e.get("betfair_present",""),
                    e.get("sharp_count_A",""),
                    e.get("sharp_count_B",""),
                    e.get("sharps_A",""),
                    e.get("sharps_B",""),
                ])
        DIAG_SHARP_PRESENCE.clear()
    except Exception:
        try:
            if EV_DEBUG_BOOKS == "1":
                import traceback
                traceback.print_exc()
        except Exception:
            pass

# AU soft books – tweak as you like
# Note: Keys must match The Odds API's exact bookmaker keys
AU_BOOKIES = [
    "sportsbet",
    "pointsbetau",
    "ladbrokes_au",    # API uses ladbrokes_au, not ladbrokes
    "neds",
    "tab",
    "tabtouch",        # Available for NBA/NHL, not NFL
    "unibet",
    "betr_au",         # API uses betr_au, not betr
    "bet365_au",       # API uses bet365_au for Australian region
    "dabble_au",       # API uses dabble_au; available for NBA
    "boombet",         # Available for most AU sports
    "playup",
    "betright",
    "betfair_ex_au",
]

# Sharp books for fair price (preferred sources)
# Tier 1: Pinnacle (sharpest)
# Tier 2: Betfair (commission-adjusted, liquid exchange)
# Tier 4: Matchbook (secondary exchange)
SHARP_BOOKIES = [
    "pinnacle",        # Tier 1: Industry standard for sharp pricing
    "betfair_ex_au",   # Tier 2: Betfair Australia (use only one Betfair region to save API calls)
    "matchbook",       # Tier 4: Secondary exchange with decent liquidity
]

# US books - use for fair price calculation but not for betting opportunities
US_BOOKIES = [
    "draftkings",
    "fanduel",
    "betmgm",
    "williamhill_us",
    "bovada",
    "mybookieag",
    "betrivers",
    "espnbet",
    "caesars",
    "wynnbet",
    "sisportsbook",
    "fliff",
    "fanatics",
]


# ---------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------
def _sport_emoji(sport_key: str, sport_title: str) -> Tuple[str, str]:
    key = (sport_key or "").lower()
    title = sport_title or ""
    mapping = {
        "basketball": ("🏀", "Basketball"),
        "soccer": ("⚽", "Soccer"),
        "tennis": ("🎾", "Tennis"),
        "baseball": ("⚾", "Baseball"),
        "americanfootball": ("🏈", "American Football"),
        "icehockey": ("🏒", "Ice Hockey"),
        "mma": ("🥊", "MMA"),
        "boxing": ("🥊", "Boxing"),
        "cricket": ("🏏", "Cricket"),
        "rugby": ("🏉", "Rugby"),
    }
    for k, v in mapping.items():
        if k in key:
            return v
    # fallback to provided title
    return "🎯", (title or "Sport").title()


def _book_pretty(book_key: str) -> str:
    pretty = {
        "unibet": "Unibet",
        "sportsbet": "Sportsbet",
        "bet365": "bet365",
        "ladbrokes": "Ladbrokes",
        "neds": "Neds",
        "tab": "TAB",
        "tabtouch": "TABtouch",
        "pointsbetau": "PointsBet AU",
        "betr": "Betr",
        "playup": "PlayUp",
        "betright": "BetRight",
    }
    return pretty.get((book_key or "").lower(), (book_key or "").title())


def _local_time_str(commence_iso: str) -> str:
    try:
        dt = dateparser.isoparse(commence_iso)
        dt_local = dt.astimezone()  # convert to local tz
        return dt_local.strftime("%a %b %d, %I:%M%p")
    except Exception:
        return commence_iso or ""


def _kelly_stake(prob: float, odds: float) -> float:
    try:
        b = max(0.0, odds - 1.0)
        p = max(0.0, min(1.0, prob))
        q = 1.0 - p
        f_star = 0.0 if b <= 0 else (p * b - q) / b
        f_star = max(0.0, f_star) * KELLY_FRACTION
        stake = BANKROLL * f_star
        if stake <= 0:
            return STAKE_FALLBACK
        return round(stake, 2)
    except Exception:
        return STAKE_FALLBACK


def _format_telegram_message(
    event: Dict[str, Any],
    selection: str,
    book_key: str,
    odds: float,
    fair_odds: float,
    edge_pct: float,
    prob: float,
) -> str:
    home = event.get("home_team", "Home")
    away = event.get("away_team", "Away")
    sport_key = event.get("sport_key", "")
    sport_title = event.get("sport_title", "")
    emoji, sport_name = _sport_emoji(sport_key, sport_title)
    when_local = _local_time_str(event.get("commence_time"))
    book_name = _book_pretty(book_key)
    stake = _kelly_stake(prob, odds)
    
    # Calculate urgency warning
    urgency = ""
    commence_time_str = event.get("commence_time", "")
    if commence_time_str:
        try:
            commence_dt = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            minutes_to_start = (commence_dt - now_utc).total_seconds() / 60
            if 0 < minutes_to_start < 60:
                urgency = f"⚠️ HURRY! Starts in {minutes_to_start:.0f} minutes!"
        except:
            pass

    lines = [
        f"🔥 Pats EV Bot 🔥 EV +{edge_pct * 100:.1f}%",
        f"{home} V {away}",
        f"{emoji} {sport_name}    H2H",
        f"{when_local} (local time)",
    ]
    if urgency:
        lines.append(urgency)
    lines.extend([
        "H2H",
        f"{selection} • {book_name} ${odds:.2f}",
        f"Stake = ${stake:.2f}",
        f"Fair = ${fair_odds:.2f}     Prob {prob * 100:.1f}%",
    ])
    return "\n".join(lines)


def _send_telegram(text: str, debug: bool = False) -> None:
    if TELEGRAM_ENABLED == "0":
        return
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        if debug or BOTS_TELEGRAM_DEBUG == "1" or r.status_code != 200:
            try:
                print(f"[telegram] status={r.status_code} ok={r.ok}")
                # Print a small snippet (avoid flooding logs)
                body = r.text
                if len(body) > 500:
                    body = body[:500] + "..."
                print(f"[telegram] response: {body}")
            except Exception:
                pass
    except Exception:
        # fail silently; logging continues to CSV
        if debug or BOTS_TELEGRAM_DEBUG == "1":
            import traceback
            print("[telegram] exception raised while sending:")
            traceback.print_exc()
        pass


## NOTE: Arbitrage functionality removed – legacy helper deleted.


# ---------------------------------------------------------------------
# Dedupe & CSV
# ---------------------------------------------------------------------
def load_dedupe() -> Dict[str, bool]:
    if not DEDUP_FILE.exists():
        return {}
    try:
        with DEDUP_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_dedupe(seen: Dict[str, bool]) -> None:
    with DEDUP_FILE.open("w", encoding="utf-8") as f:
        json.dump(seen, f)

def load_api_usage() -> Dict[str, Any]:
    """Load API usage tracking data."""
    if not API_USAGE_FILE.exists():
        return {"monthly_usage": {}, "total_credits": 0}
    try:
        with API_USAGE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"monthly_usage": {}, "total_credits": 0}

def save_api_usage(usage_data: Dict[str, Any]) -> None:
    """Save API usage tracking data."""
    with API_USAGE_FILE.open("w", encoding="utf-8") as f:
        json.dump(usage_data, f, indent=2)

def log_api_usage(sports_count: int) -> None:
    """Log API credits used for this run (10 credits per sport)."""
    credits_used = sports_count * 10
    usage_data = load_api_usage()
    
    # Get current month key (YYYY-MM)
    now = datetime.now()
    month_key = now.strftime("%Y-%m")
    
    # Initialize month if not exists
    if month_key not in usage_data.get("monthly_usage", {}):
        usage_data["monthly_usage"] = usage_data.get("monthly_usage", {})
        usage_data["monthly_usage"][month_key] = {"credits": 0, "runs": 0, "first_run": now.isoformat(), "last_run": now.isoformat()}
    
    # Update usage
    usage_data["monthly_usage"][month_key]["credits"] += credits_used
    usage_data["monthly_usage"][month_key]["runs"] += 1
    usage_data["monthly_usage"][month_key]["last_run"] = now.isoformat()
    usage_data["total_credits"] = usage_data.get("total_credits", 0) + credits_used
    
    save_api_usage(usage_data)
    
    # Display usage info
    month_usage = usage_data["monthly_usage"][month_key]
    print(f"[api] Credits used this run: {credits_used} ({sports_count} sports × 10)")
    print(f"[api] Month {month_key}: {month_usage['credits']}/20000 credits used ({month_usage['runs']} runs)")
    remaining = 20000 - month_usage['credits']
    if remaining > 0:
        runs_remaining = remaining // (sports_count * 10)
        print(f"[api] Remaining: {remaining} credits (~{runs_remaining} more runs this month)")
    else:
        print(f"[api] ⚠️  WARNING: Monthly limit exceeded by {abs(remaining)} credits!")

def _expected_ev_header() -> List[str]:
    """Return the expected EV CSV header columns in required order."""
    return [
        "game_start_perth",  # Game start time in Perth local time (UTC+8)
        "sport",
        "EV",
        "event",
        "market",
        "line",
        "side",
        "stake",
        "book",
        "price",
        "Prob",
        "Fair",
        # Bookmaker columns in requested order
        "Pinnacle",
        "Betfair",
        "Sportsbet",
        "Bet365",
        "Pointsbet",
        "Dabble",
        "Ladbrokes",
        "Unibet",
        "Neds",
        "TAB",
        "TABtouch",
        "Betr",
        "PlayUp",
        "BetRight",
    ]

def _write_ev_csv_header(path: Path) -> None:
    """Write custom EV CSV header with individual AU bookmaker columns."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(_expected_ev_header())

def ensure_hits_csv() -> None:
    expected = _expected_ev_header()
    # Create or repair EV CSV header
    if not EV_CSV.exists():
        _write_ev_csv_header(EV_CSV)
    else:
        try:
            with EV_CSV.open("r", encoding="utf-8") as f:
                first = f.readline().strip()
            # Parse header as CSV to compare robustly
            reader = csv.reader([first])
            current_header = next(reader, [])
            if current_header != expected:
                # Rewrite header (truncate file)
                _write_ev_csv_header(EV_CSV)
        except Exception:
            # If anything goes wrong, at least ensure header exists
            _write_ev_csv_header(EV_CSV)


# ---------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------
def implied_prob_from_decimal(odds: float) -> float:
    if odds <= 1.0:
        return 0.0
    return 1.0 / odds

def devig_two_way(o1: float, o2: float) -> Tuple[float, float]:
    """
    Strip margin from a 2-way market for one book.
    Returns (p_home, p_away) that sum to 1.
    """
    p1 = implied_prob_from_decimal(o1)
    p2 = implied_prob_from_decimal(o2)
    s = p1 + p2
    if s <= 0:
        return 0.0, 0.0
    return p1 / s, p2 / s

def effective_back_odds_betfair(raw_odds: float, commission: float) -> float:
    """
    Adjust Betfair back odds for commission on net winnings.
    Effective odds = 1 + (O - 1) * (1 - commission)
    """
    if raw_odds <= 1.0:
        return raw_odds
    profit = (raw_odds - 1.0) * (1.0 - commission)
    return 1.0 + profit

def remove_outliers_iqr(probabilities: List[float]) -> List[float]:
    """
    Remove outliers using Interquartile Range (IQR) method.
    
    This filters out bookmakers with suspiciously high/low probabilities that could be:
    - Stale odds (not updated)
    - Data errors
    - Promotional/limited lines
    - Books with poor price models
    
    IQR method:
    1. Calculate Q1 (25th percentile) and Q3 (75th percentile)
    2. IQR = Q3 - Q1
    3. Remove values outside [Q1 - 1.5×IQR, Q3 + 1.5×IQR]
    
    Returns filtered list of probabilities. Returns original if too few samples.
    """
    if len(probabilities) < 5:  # Need at least 5 samples for meaningful outlier detection
        return probabilities
    
    sorted_probs = sorted(probabilities)
    n = len(sorted_probs)
    
    # Calculate Q1 and Q3
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_probs[q1_idx]
    q3 = sorted_probs[q3_idx]
    
    iqr = q3 - q1
    if iqr <= 0:  # All values are the same
        return probabilities
    
    # Calculate bounds (1.5×IQR is standard for outlier detection)
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Filter outliers
    filtered = [p for p in probabilities if lower_bound <= p <= upper_bound]
    
    # Ensure we still have enough samples after filtering
    if len(filtered) < MIN_BOOKMAKERS_AFTER_OUTLIERS:
        return probabilities  # Not enough data after filtering, use original
    
    return filtered


def snap_to_half(val: float) -> float:
    """Snap a numeric line to the nearest 0.5 increment.

    E.g., 3.26 -> 3.5, 3.24 -> 3.0, -3.26 -> -3.5
    """
    try:
        return round(float(val) * 2.0) / 2.0
    except Exception:
        return val

def calculate_margin(odds1: float, odds2: float) -> float:
    """
    Calculate bookmaker margin (overround) for a 2-way market.
    
    Margin = (1/odds1 + 1/odds2 - 1) × 100
    
    Typical margins:
    - Sharp books (Pinnacle): 2-3%
    - Exchanges (Betfair): ~2% (via commission)
    - Recreational books: 5-10%
    - Suspicious/stale odds: >15%
    
    Returns margin as percentage.
    """
    if odds1 <= 0 or odds2 <= 0:
        return 100.0  # Invalid odds
    
    p1 = 1.0 / odds1
    p2 = 1.0 / odds2
    margin = (p1 + p2 - 1.0) * 100.0
    
    return margin


# ---------------------------------------------------------------------
# API fetch
# ---------------------------------------------------------------------
def fetch_h2h_events(sport_key: str) -> List[Dict[str, Any]]:
    if not ODDS_API_KEY:
        raise SystemExit("Set ODDS_API_KEY first.")
    url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "decimal",
    }
    print(f"[API] Fetching {sport_key} with regions={REGIONS}, markets={MARKETS}")
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()


def _compute_spreads_totals_ev(event: Dict[str, Any], seen: Dict[str, bool]) -> Tuple[int, int]:
    """Process spreads and totals markets for EV only (no ARB yet).
    Returns (hits, ev_hits) added.
    """
    hits = 0
    ev_hits = 0

    market_keys = [m.strip() for m in MARKETS.split(",") if m.strip()]
    # Support spreads, totals and player_props (player prop markets like "player points over/under")
    market_keys = [m for m in market_keys if m in ("spreads", "totals", "player_props")]
    if not market_keys:
        return 0, 0
    
    if EV_DEBUG_BOOKS == "1":
        print(f"[DEBUG] Scanning spreads/totals for: {event.get('home_team')} vs {event.get('away_team')}")

    home = event.get("home_team")
    away = event.get("away_team")

    # Build fair prices per market and line using sharp books
    for mkey in market_keys:
        # Build a mapping of line -> fair dict per outcome
        # Approach: iterate lines observed across all bookmakers by reading outcomes
        lines_seen = set()
        for bk in event.get("bookmakers", []):
            bk_key = bk.get("key")
            markets = bk.get("markets", [])
            m = next((mm for mm in markets if mm.get("key") == mkey), None)
            if not m:
                continue
            outs = m.get("outcomes", [])
            if len(outs) != 2:
                continue
            # For spreads: outcomes have opposite points (e.g., -8.5 and 8.5)
            # For totals: outcomes have same point (e.g., 243.5 and 243.5)
            pt = outs[0].get("point")
            if pt is None:
                continue
            pt2 = outs[1].get("point")
            if pt2 is None:
                continue
            
            # For spreads, check if points are opposites (abs values match)
            # For totals and player_props, check if points are the same
            # Use snapped lines (nearest 0.5) to canonicalize bookmaker-provided lines
            try:
                spt = snap_to_half(float(pt))
                spt2 = snap_to_half(float(pt2))
            except Exception:
                continue

            if mkey == "spreads":
                if abs(abs(spt) - abs(spt2)) > 1e-9:
                    continue
                # For spreads, use ABSOLUTE value as the line identifier
                # (we'll process both positive and negative sides together)
                lines_seen.add(abs(spt))
            elif mkey == "totals" or mkey == "player_props":
                if abs(spt - spt2) > 1e-9:
                    continue
                lines_seen.add(spt)


        # If Pinnacle priority is enabled, prefer Pinnacle-reported lines as the
        # canonical set to evaluate. This will restrict evaluation to Pinnacle's
        # lines when available and avoid missing Pinnacle-only spreads.
        if PINNACLE_PRIORITY == "1":
            try:
                pin_lines = set()
                for bk in event.get("bookmakers", []):
                    if bk.get("key") != "pinnacle":
                        continue
                    m = next((mm for mm in bk.get("markets", []) if mm.get("key") == mkey), None)
                    if not m:
                        continue
                    outs = m.get("outcomes", [])
                    if len(outs) != 2:
                        continue
                    for o in outs:
                        pt = o.get("point")
                        if pt is None:
                            continue
                        try:
                            # For spreads, use absolute value
                            snapped = snap_to_half(float(pt))
                            if mkey == "spreads":
                                pin_lines.add(abs(snapped))
                            else:
                                pin_lines.add(snapped)
                        except Exception:
                            continue
                if pin_lines:
                    lines_seen = pin_lines
            except Exception:
                pass

        for line_val in sorted(lines_seen):
            if EV_DEBUG_BOOKS == "1":
                print(f"[DEBUG]   {mkey} line {line_val}")
            fair = build_fair_prices(event, market_key=mkey, line=line_val)
            out_keys = list(fair.keys())
            
            # For EV hit detection, we need fair prices. But for all_odds.csv logging,
            # we want to log ALL markets even without fair prices. So continue processing.
            has_fair_prices = len(out_keys) == 2
            if not has_fair_prices:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG]     No fair prices: outcomes={len(out_keys)} (will log to all_odds.csv without fair)")
                    print(f"[DEBUG]     Outcome keys: {out_keys}")

            # Prepare per-outcome master fair odds (if available)
            fair_master: Dict[str, float] = {}
            if has_fair_prices:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[FAIR-LOOKUP] out_keys={out_keys}")
                    print(f"[FAIR-LOOKUP] fair.keys()={list(fair.keys())}")
                for ok in out_keys:
                    fair_row = fair.get(ok, {})
                    if EV_DEBUG_BOOKS == "1":
                        print(f"[FAIR-LOOKUP] Lookup ok={ok}, got fair_row={fair_row}")
                    fair_master[ok] = master_fair_odds(fair_row)

            # Diagnostic: if Pinnacle was present for this target but the
            # computed master fair odds are zero for both sides, record a
            # targeted debug row to help root-cause spread coverage issues.
            try:
                diag = LAST_BUILD_FAIR_DIAG if isinstance(LAST_BUILD_FAIR_DIAG, dict) else None
                if diag and diag.get("event_id") == event.get("id") and diag.get("market") == mkey and float(diag.get("line") or 0) == float(line_val):
                    pinn_found = int(bool(diag.get("pinnacle_found")))
                    # Only consider spreads/totals/player_props
                    if mkey in ("spreads", "totals", "player_props") and pinn_found:
                        a_master = fair_master.get(out_keys[0], 0.0) if out_keys and has_fair_prices else 0.0
                        b_master = fair_master.get(out_keys[1], 0.0) if out_keys and has_fair_prices else 0.0
                        if (not a_master or a_master <= 0.0) and (not b_master or b_master <= 0.0):
                            _record_pinnacle_issue({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "event_id": event.get("id", ""),
                                "sport": event.get("sport_key", ""),
                                "market": mkey,
                                "line": float(line_val),
                                "key_A": diag.get("key_A", ""),
                                "key_B": diag.get("key_B", ""),
                                "pinnacle_found": pinn_found,
                                "fair_master_A": a_master,
                                "fair_master_B": b_master,
                                "pinnacle_keys": diag.get("pinnacle_keys", []),
                            })
            except Exception:
                pass

            # Build per-outcome bookmaker odds dict for this line (for EV CSV columns)
            # This will be populated as we collect odds from bookmakers
            all_odds_by_outcome: Dict[str, Dict[str, float]] = {}

            # Collect ALL bookmaker odds at this line for all outcomes (including Pinnacle)
            for bk in event.get("bookmakers", []):
                bkey = bk.get("key")
                # Collect from ALL bookmakers for CSV display, not just AU_BOOKIES
                markets = bk.get("markets", [])
                m = next((mm for mm in markets if mm.get("key") == mkey), None)
                if not m:
                    continue
                outs = m.get("outcomes", [])
                if len(outs) != 2:
                    continue
                pt = outs[0].get("point")
                try:
                    # Allow lines within LINE_TOLERANCE (e.g., -7.5 matches -7.0 or -8.0 with tolerance=0.5)
                    if abs(float(pt) - float(line_val)) > LINE_TOLERANCE:
                        continue
                except Exception:
                    continue

                # Store RAW odds for each outcome using composite key format
                # IMPORTANT: For spreads/totals, normalize keys to the target line_val
                # so they align with build_fair_prices() which also keys by the target line.
                for o in outs:
                    outcome_name = o.get("name")
                    outcome_point = o.get("point")
                    # When a bookmaker line is within tolerance of our target line, snap it to the
                    # canonical target. This ensures consistent keys like 'Over_46.5' even if the
                    # book reported 46.499 or 46.75.
                    if mkey in ("spreads", "totals", "player_props") and outcome_point is not None:
                        try:
                            # If this is a strict market (spreads/totals), require exact snapped equality
                            if mkey in ("spreads", "totals"):
                                if abs(snap_to_half(float(outcome_point)) - snap_to_half(float(line_val))) > 1e-9:
                                    # Throw away bookmaker outcome that snaps to a different half-point
                                    continue
                                point_key = float(line_val)
                            else:
                                # For other markets (like player_props) allow snapping-within-tolerance
                                if abs(snap_to_half(float(outcome_point)) - float(line_val)) <= LINE_TOLERANCE:
                                    point_key = float(line_val)
                                else:
                                    point_key = snap_to_half(float(outcome_point))
                        except Exception:
                            point_key = outcome_point
                    else:
                        point_key = outcome_point

                    if mkey == "spreads":
                        nm = f"{outcome_name}_{point_key}"
                    elif mkey == "totals" or mkey == "player_props":
                        # For totals and player_props normalize to the computed point_key
                        nm = f"{outcome_name}_{point_key}"
                    else:
                        nm = outcome_name
                    try:
                        price = float(o.get("price"))
                        if nm not in all_odds_by_outcome:
                            all_odds_by_outcome[nm] = {}
                        all_odds_by_outcome[nm][bkey] = price
                    except Exception:
                        pass

            # Loop AU books to find EV opportunities at this line
            for bk in event.get("bookmakers", []):
                bkey = bk.get("key")
                if FILTER_BOOKS and bkey not in FILTER_BOOKS:
                    continue
                if bkey not in AU_BOOKIES:
                    continue
                markets = bk.get("markets", [])
                m = next((mm for mm in markets if mm.get("key") == mkey), None)
                if not m:
                    continue
                outs = m.get("outcomes", [])
                if len(outs) != 2:
                    continue
                # Ensure line matches (within tolerance)
                pt = outs[0].get("point")
                try:
                    # Allow lines within LINE_TOLERANCE (e.g., -7.5 matches -7.0 or -8.0 with tolerance=0.5)
                    if abs(float(pt) - float(line_val)) > LINE_TOLERANCE:
                        continue
                except Exception:
                    continue

                # Build name->price map for this book at this line
                # For spreads/totals, normalize keys to the target line (line_val)
                name_price = {}
                for o in outs:
                    outcome_name = o.get("name")
                    outcome_point = o.get("point")
                    if mkey == "spreads":
                        nm = f"{outcome_name}_{line_val}"
                    elif mkey == "totals" or mkey == "player_props":
                        nm = f"{outcome_name}_{line_val}"
                    else:
                        nm = outcome_name
                    try:
                        name_price[nm] = float(o.get("price"))
                    except Exception:
                        pass

                # Evaluate EV for each outcome if fair is available
                if EV_DEBUG_BOOKS == "1" and name_price:
                    print(f"[DEBUG]     {bkey} at line {line_val}: {len(name_price)} prices, keys={list(name_price.keys())}")
                for nm, price in name_price.items():
                    # Log ALL spreads/totals to all_odds.csv FIRST (even without fair price)
                    fm = fair_master.get(nm)
                    edge = None
                    if fm and fm > 0:
                        p_true = 1.0 / fm
                        edge = price * p_true - 1.0
                    
                    # Pass the full fair dictionary with ALL outcomes for this line
                    # This allows flush_all_odds to look up either side's fair price
                    fair_dict_full = {ok: fair_master.get(ok, 0.0) for ok in out_keys} if has_fair_prices else {nm: 0.0}
                    
                    log_all_odds(
                        event, nm, line_val, bkey, price,
                        fair_dict_full, fair_dict_full,  # Pass full fair dict with both outcomes
                        edge if edge is not None else 0.0,  # Use 0 edge if no fair price
                        all_book_odds=all_odds_by_outcome.get(nm, {}),
                        market_key=mkey,
                    )
                    
                    # Now check if we have fair price for EV hit detection
                    if not fm or fm <= 0:
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[DEBUG]       {nm}: no fair price (fm={fm}), logged to all_odds but skipping EV check")
                        continue
                    # Enforce user's max allowed odds cutoff
                    if price > MAX_ALLOWED_ODDS:
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[DEBUG]       {nm} @ ${price:.2f}: price > MAX_ALLOWED_ODDS (${MAX_ALLOWED_ODDS:.2f}), skipping")
                        continue
                    p_true = 1.0 / fm
                    edge = price * p_true - 1.0
                    
                    # Now apply filters for hits_ev.csv
                    if p_true < MIN_PROB:
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[DEBUG]       {nm} @ ${price:.2f}: prob={p_true*100:.1f}% < {MIN_PROB*100:.1f}% threshold, skipping")
                        continue
                    # Skip extremely large bookmaker odds beyond MAX_ALLOWED_ODDS
                    if price > MAX_ALLOWED_ODDS:
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[DEBUG]       {nm} @ ${price:.2f}: price > MAX_ALLOWED_ODDS ({MAX_ALLOWED_ODDS}), skipping")
                        continue
                    # Strict filter: only log if bookmaker price >= fair price
                    if price < fm:
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[DEBUG]       {nm} @ ${price:.2f}: price < fair (${fm:.2f}), skipping")
                        continue
                    if EV_DEBUG_BOOKS == "1":
                        print(f"[DEBUG]       {nm} @ ${price:.2f}: edge={edge*100:.1f}% (fair=${fm:.2f})")
                    if edge >= EV_MIN_EDGE:
                        # Check minimum stake filter
                        stake = _kelly_stake(p_true, price)
                        if stake < MIN_STAKE:
                            if EV_DEBUG_BOOKS == "1":
                                print(f"[DEBUG]       Skipped: stake ${stake:.2f} < ${MIN_STAKE:.2f} minimum")
                            continue
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[DEBUG]       EV HIT!")
                        k = hit_key(event, nm, bkey, price)
                        if TEST_ALLOW_DUPES == "1" or not seen.get(k):
                            if TEST_ALLOW_DUPES != "1":
                                seen[k] = True
                            # Pass the correct fair dict for this specific outcome
                            log_hit(
                                event, nm, float(line_val), bkey, price,
                                fair.get(nm, {}), fair.get(nm, {}),  # Same dict for both params (ignored for non-h2h)
                                edge,
                                f"EV {mkey} line={line_val}",
                                all_book_odds=all_odds_by_outcome.get(nm),
                                market_key=mkey,
                            )
                            try:
                                msg = _format_telegram_message(
                                    event, nm, bkey, price, fm, edge, p_true
                                )
                                _send_telegram(msg)
                            except Exception:
                                pass
                            hits += 1
                            ev_hits += 1

    return hits, ev_hits


# ---------------------------------------------------------------------
# Fair prices from Pinnacle, Betfair (commission), median sharp
# ---------------------------------------------------------------------
def build_fair_prices(event: Dict[str, Any], market_key: str = "h2h", line: float = None) -> Dict[str, Dict[str, float]]:
    """
    Return per-outcome fair odds dict for a given market.
    
    For h2h: outcomes are home/away
    For spreads/totals: outcomes are indexed by line (e.g., "home_-3.5", "over_231.5")
    
    Returns:
    {
      "outcome1": {"pinnacle": 2.01, "betfair": 1.95, "median": 1.98},
      "outcome2": {...}
    }
    """
    home_name = event.get("home_team")
    away_name = event.get("away_team")

    sharp_probs = {}
    # Keep mapping of outcome -> list of (book_key, prob) for sharp book filtering
    sharp_probs_bybook: Dict[str, List[Tuple[str, float]]] = {}
    pin_odds = {}
    bf_odds = {}

    # For interpolation: collect per-actual-line devig probabilities near target
    # We keep separate maps for the two outcome names (e.g., home vs away or Over vs Under)
    line_probs_A: Dict[float, List[float]] = {}
    line_probs_B: Dict[float, List[float]] = {}

    # Determine canonical outcome names for A and B
    # For totals and player_props we treat outcomes as Over/Under
    if market_key == "spreads":
        name_A = home_name
        name_B = away_name
    elif market_key in ("totals", "player_props"):
        name_A = "Over"
        name_B = "Under"
    else:
        name_A = home_name
        name_B = away_name
    # outcome_map may be referenced later; initialize to avoid UnboundLocalError
    outcome_map = {}

    # Pre-scan Pinnacle reported points for this market so we can treat
    # Pinnacle's snapped line as canonical when PINNACLE_PRIORITY is enabled.
    pinnacle_points: Dict[str, float] = {}
    try:
        for _bk in event.get("bookmakers", []):
            if _bk.get("key") != "pinnacle":
                continue
            mkt = next((mm for mm in _bk.get("markets", []) if mm.get("key") == market_key), None)
            if not mkt:
                continue
            for out in mkt.get("outcomes", []):
                try:
                    nm = out.get("name")
                    pt = out.get("point")
                    if pt is None:
                        continue
                    pinnacle_points[nm] = snap_to_half(float(pt))
                except Exception:
                    continue
            # Found Pinnacle market, no need to keep scanning other pinnacle entries
            break
    except Exception:
        pass

    for bk in event.get("bookmakers", []):
        bkey = bk.get("key")
        
        # Debug: Check what Pinnacle actually has
        if EV_DEBUG_BOOKS == "1" and bkey == "pinnacle":
            markets = bk.get("markets", [])
            print(f"[DEBUG] Pinnacle has {len(markets)} markets: {[m.get('key') for m in markets]}")
            print(f"[DEBUG] Looking for market_key={market_key}")
            for m in markets:
                mkey = m.get("key")
                print(f"[DEBUG] Checking market {mkey} == {market_key}? {mkey == market_key}")
                if mkey == market_key:
                    outs = m.get("outcomes", [])
                    print(f"[DEBUG] Pinnacle {market_key} has {len(outs)} outcomes")
                    for out in outs:
                        print(f"[DEBUG]   {out.get('name')} point={out.get('point')} price={out.get('price')}")
        
        # CRITICAL: Exclude AU bookmakers from fair price calculation to avoid circular logic
        # (We'll compare AU odds against this fair price, so AU odds can't influence it)
        if bkey in AU_BOOKIES:
            continue
        
        markets = bk.get("markets", [])
        target_market = next((m for m in markets if m.get("key") == market_key), None)
        if not target_market:
            continue

        outs = target_market.get("outcomes", [])
        if len(outs) != 2:
            continue

        # Build outcome keys based on market type
        outcome_map = {}
        for out in outs:
            name = out.get("name")
            point = out.get("point")

            # Normalize bookmaker point to nearest half and snap to target 'line' when
            # within LINE_TOLERANCE so outcome keys align across books.
            point_key = None
            if market_key in ("spreads", "totals", "player_props") and point is not None:
                try:
                    sp = snap_to_half(float(point))
                    if line is not None and abs(sp - float(line)) <= LINE_TOLERANCE:
                        point_key = float(line)
                    else:
                        point_key = sp
                except Exception:
                    point_key = point
            else:
                point_key = point

            # Create unique key for this outcome
            if market_key == "h2h":
                out_key = name  # "home_team" or "away_team"
            elif market_key in ("spreads", "totals", "player_props"):
                if point_key is not None:
                    out_key = f"{name}_{point_key}"
                else:
                    out_key = name
            else:
                out_key = name

            outcome_map[out_key] = out

            # If filtering by line for spreads/totals, check match with tolerance
            add_to_sharp = True
            eligible_for_interp = False
        if line is not None and market_key in ("spreads", "totals", "player_props"):
            # Allow lines within LINE_TOLERANCE for exact-line sharp aggregation
            # But also allow a wider INTERP_MAX_GAP window to gather neighbors for interpolation
            closest_line = None
            min_diff = float('inf')
            for out in outs:
                pt = out.get("point")
                if pt is not None:
                    diff = abs(pt - line)
                    if diff < min_diff:
                        min_diff = diff
                        closest_line = pt
                        # remember which outcome name produced the closest line
                        try:
                            closest_out_name = out.get("name")
                        except Exception:
                            closest_out_name = None
            # Enforce strict snapping rules for spreads/totals where line differences change probability
            strict_markets = ("spreads", "totals", "asian_handicap", "alternate_lines")
            if market_key in strict_markets:
                # If after snapping the book's closest line does not equal the target snapped line, normally throw it away
                if closest_line is None:
                    add_to_sharp = False
                    eligible_for_interp = False
                else:
                    book_snap = snap_to_half(closest_line)
                    target_snap = snap_to_half(line)
                    # Identify which outcome this closest_line belonged to (if available)
                    # (closest_out_name set in the loop above when computing closest_line)
                    try:
                        out_name_for_closest = closest_out_name
                    except NameError:
                        out_name_for_closest = None

                    if abs(book_snap - target_snap) <= 1e-9:
                        add_to_sharp = True
                        eligible_for_interp = False
                    else:
                        # Relax snapping when Pinnacle priority is enabled: accept this book
                        # if its closest_line matches Pinnacle's snapped point for the same outcome
                        if PINNACLE_PRIORITY == "1" and out_name_for_closest and out_name_for_closest in pinnacle_points:
                            pin_pt = pinnacle_points.get(out_name_for_closest)
                            if pin_pt is not None and abs(book_snap - pin_pt) <= LINE_TOLERANCE:
                                add_to_sharp = True
                                eligible_for_interp = False
                            else:
                                add_to_sharp = False
                                eligible_for_interp = False
                        else:
                            add_to_sharp = False
                            eligible_for_interp = False
            else:
                add_to_sharp = closest_line is not None and min_diff <= LINE_TOLERANCE
                eligible_for_interp = (ENABLE_INTERPOLATION == "1" and closest_line is not None and min_diff <= INTERP_MAX_GAP)
            # Skip entirely if outside both exact/on-neighbor allowed behavior
            if not add_to_sharp and not eligible_for_interp:
                continue

        # Extract odds for each outcome (process this bookmaker's outcomes now)
        for out_key, out in outcome_map.items():
            try:
                odds = float(out.get("price"))
            except Exception:
                continue

            if out_key not in sharp_probs:
                sharp_probs[out_key] = []

            # Keep raw Pinnacle odds (capture regardless of add_to_sharp so Pinnacle can
            # act as canonical source-of-truth even when other books don't exactly match)
            if bkey == "pinnacle":
                pin_odds[out_key] = odds

            # Betfair: adjust for commission (capture regardless of add_to_sharp)
            if (bkey == "betfair_ex_au" or bkey == "betfair_ex_uk"):
                bf_odds[out_key] = effective_back_odds_betfair(odds, BETFAIR_COMMISSION)

        # After processing all outcomes for this bookmaker, collect devigged probabilities
        # This allows fair price calculation using ALL bookmakers (not just sharp)
        if len(outcome_map) == 2:
            out_keys = list(outcome_map.keys())
            try:
                o1 = float(outcome_map[out_keys[0]].get("price"))
                o2 = float(outcome_map[out_keys[1]].get("price"))

                # Calculate and check margin (skip if suspiciously high)
                margin = calculate_margin(o1, o2)
                if margin > MAX_MARGIN_PERCENT:
                    if EV_DEBUG_BOOKS == "1":
                        print(f"[DEBUG]     Skipping {bkey}: margin {margin:.1f}% exceeds {MAX_MARGIN_PERCENT}% threshold")
                    # skip this bookmaker's contribution
                    continue

                p1, p2 = devig_two_way(o1, o2)
                # Initialize lists if needed
                if add_to_sharp:
                    if out_keys[0] not in sharp_probs:
                        sharp_probs[out_keys[0]] = []
                    if out_keys[1] not in sharp_probs:
                        sharp_probs[out_keys[1]] = []
                    sharp_probs[out_keys[0]].append(p1)
                    sharp_probs[out_keys[1]].append(p2)
                    # also preserve which book contributed each prob for filtered medians
                    sharp_probs_bybook.setdefault(out_keys[0], []).append((bkey, p1))
                    sharp_probs_bybook.setdefault(out_keys[1], []).append((bkey, p2))

                # Also collect per-actual-line probabilities for interpolation (near target line)
                if line is not None and market_key in ("spreads", "totals", "player_props") and ENABLE_INTERPOLATION == "1":
                    # Map outcomes back to their names/points
                    # Build a temporary name->(price, point) mapping for this book
                    name_point_map: Dict[str, Tuple[float, float]] = {}
                    for o in outs:
                        try:
                            nm = o.get("name")
                            pt = float(o.get("point")) if o.get("point") is not None else None
                            pr = float(o.get("price"))
                            name_point_map[nm] = (pr, pt)
                        except Exception:
                            pass
                    if name_A in name_point_map and name_B in name_point_map:
                        prA, ptA = name_point_map[name_A]
                        prB, ptB = name_point_map[name_B]
                        # Use devigged probs already computed (p1,p2) aligned to out_keys order.
                        # Align p1/p2 to A/B by matching out_keys names
                        # out_keys contain normalized keys like "Name_line"; extract base names to compare
                        base1 = out_keys[0].split("_")[0]
                        base2 = out_keys[1].split("_")[0]
                        pA = p1 if base1 == name_A else p2
                        pB = p2 if base1 == name_A else p1
                        # Record if within interpolation window
                        try:
                            if ptA is not None and abs(ptA - float(line)) <= INTERP_MAX_GAP:
                                line_probs_A.setdefault(ptA, []).append(pA)
                            if ptB is not None and abs(ptB - float(line)) <= INTERP_MAX_GAP:
                                line_probs_B.setdefault(ptB, []).append(pB)
                        except Exception:
                            pass
            except Exception:
                pass

    # Check if we have enough bookmakers for reliable fair price calculation
    # Count unique bookmakers that contributed probabilities
    out_keys = list(sharp_probs.keys())
    insufficient_samples = False
    if out_keys:
        # Get the number of prob samples for first outcome as proxy for bookmaker count
        num_bookmakers = len(sharp_probs[out_keys[0]]) if sharp_probs.get(out_keys[0]) else 0
        if num_bookmakers < MIN_BOOKMAKERS_FOR_FAIR:
            # For spreads/totals with interpolation enabled, allow fallback later.
            if not (ENABLE_INTERPOLATION == "1" and market_key in ("spreads", "totals", "player_props") and line is not None):
                return {}
            insufficient_samples = True

    # Build fair prices for each outcome using all known outcome keys as a pair
    out_keys = list(sharp_probs.keys())

    # If no sharp_probs were collected but Pinnacle or Betfair provided odds,
    # ensure we still construct canonical outcome keys for the target line so
    # Pinnacle/Betfair contributions are not silently dropped.
    # For spreads: use Pinnacle's actual keys (which have correct +/- signs)
    if not out_keys and (pin_odds or bf_odds):
        try:
            if EV_DEBUG_BOOKS == "1":
                print(f"[DEBUG] No sharp_probs for {market_key} line={line}; pin_odds keys={list(pin_odds.keys()) if pin_odds else []}, bf_odds keys={list(bf_odds.keys()) if bf_odds else []}")
            if market_key == "spreads" and pin_odds and len(pin_odds) == 2:
                # For spreads, use Pinnacle's keys directly (they have correct signs)
                out_keys = list(pin_odds.keys())
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG] Using Pinnacle keys as canonical for spreads: {out_keys}")
            elif market_key in ("spreads", "totals", "player_props") and line is not None:
                kA = f"{name_A}_{line}"
                kB = f"{name_B}_{line}"
                out_keys = [kA, kB]
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG] Created synthetic keys for {market_key}: {out_keys}")
            else:
                kA = name_A
                kB = name_B
                out_keys = [kA, kB]
            # Initialize empty lists so downstream code can append or set components
            for k in out_keys:
                sharp_probs.setdefault(k, [])
        except Exception:
            pass
    
    # CRITICAL DEDUPLICATION: For spreads, out_keys may contain duplicate
    # team keys with opposite signs (e.g., "Team_6.5" AND "Team_-6.5" from different books).
    # Merge them BEFORE initializing fair dict to ensure exactly 2 keys.
    if EV_DEBUG_BOOKS == "1" and market_key == "spreads":
        print(f"[KEY-DEDUP-CHECK] out_keys={out_keys}, len={len(out_keys)}, pin_odds keys={list(pin_odds.keys())}")
    
    if market_key == "spreads" and len(out_keys) > 2:
        from collections import defaultdict
        if EV_DEBUG_BOOKS == "1":
            print(f"[KEY-DEDUP] BEFORE: pin_odds has {len(pin_odds)} keys: {list(pin_odds.keys())}")
        
        # Group pin_odds by team name (ignore sign)
        by_team = defaultdict(list)
        for key in list(pin_odds.keys()):
            if "_" in key:
                team = key.rsplit("_", 1)[0]
                by_team[team].append(key)
        
        # For each team with multiple keys, keep the one with Pinnacle data (source of truth)
        canonical_keys = []
        for team, keys in by_team.items():
            if len(keys) == 1:
                canonical_keys.append(keys[0])
            else:
                # Multiple keys for same team - find which one Pinnacle uses
                pin_key = None
                for k in keys:
                    if k in pin_odds and pin_odds[k]:
                        pin_key = k
                        break
                if pin_key:
                    canonical_keys.append(pin_key)
                    # Merge other keys' data into canonical key
                    for k in keys:
                        if k != pin_key:
                            # Merge sharp_probs
                            if k in sharp_probs:
                                if pin_key not in sharp_probs:
                                    sharp_probs[pin_key] = []
                                sharp_probs[pin_key].extend(sharp_probs[k])
                                del sharp_probs[k]
                            # Remove duplicate from pin_odds/bf_odds
                            if k in pin_odds:
                                del pin_odds[k]
                            if k in bf_odds:
                                del bf_odds[k]
                            if EV_DEBUG_BOOKS == "1":
                                print(f"[KEY-DEDUP] Merged {k} into canonical {pin_key}")
                else:
                    # No Pinnacle data; keep first key arbitrarily
                    canonical_keys.append(keys[0])
        
        # Update out_keys to canonical set
        out_keys = canonical_keys
        if EV_DEBUG_BOOKS == "1":
            print(f"[KEY-DEDUP] AFTER: out_keys={out_keys}")
    
    # Now initialize fair dict with final deduplicated out_keys
    fair: Dict[str, Dict[str, float]] = {}
    for k in out_keys:
        fair[k] = {"pinnacle": None, "betfair": None, "median": None}

    if len(out_keys) == 2:
        k1, k2 = out_keys[0], out_keys[1]

        # For spreads, Pinnacle reports opposite-signed points. Before checking pin_odds,
        # try to populate missing keys by finding opposite-sign matches.
        if market_key == "spreads" and line is not None:
            if EV_DEBUG_BOOKS == "1":
                print(f"[OPP-SIGN] Checking opposite signs for k1={k1}, k2={k2}")
                print(f"[OPP-SIGN] pin_odds keys: {list(pin_odds.keys())}")
            try:
                # Try to find opposite-sign matches for each canonical key
                if k1 not in pin_odds:
                    # Extract name and line from k1 (format: "Name_line")
                    parts1 = k1.rsplit("_", 1)
                    if len(parts1) == 2:
                        name1, line1 = parts1[0], float(parts1[1])
                        # Look for opposite-sign match
                        opp_key = f"{name1}_{-line1}"
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[OPP-SIGN] k1={k1} not in pin_odds, trying opp_key={opp_key}")
                        if opp_key in pin_odds:
                            pin_odds[k1] = pin_odds[opp_key]
                            if EV_DEBUG_BOOKS == "1":
                                print(f"[OPP-SIGN] SUCCESS: Copied {opp_key} -> {k1}")
                if k2 not in pin_odds:
                    parts2 = k2.rsplit("_", 1)
                    if len(parts2) == 2:
                        name2, line2 = parts2[0], float(parts2[1])
                        opp_key = f"{name2}_{-line2}"
                        if EV_DEBUG_BOOKS == "1":
                            print(f"[OPP-SIGN] k2={k2} not in pin_odds, trying opp_key={opp_key}")
                        if opp_key in pin_odds:
                            pin_odds[k2] = pin_odds[opp_key]
                            if EV_DEBUG_BOOKS == "1":
                                print(f"[OPP-SIGN] SUCCESS: Copied {opp_key} -> {k2}")
            except Exception as e:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[OPP-SIGN] ERROR: {e}")

        # Pinnacle fair
        if k1 in pin_odds and k2 in pin_odds:
            if EV_DEBUG_BOOKS == "1":
                print(f"[PIN-DEVIG] k1={k1} odds={pin_odds[k1]}, k2={k2} odds={pin_odds[k2]}")
            try:
                p1, p2 = devig_two_way(pin_odds[k1], pin_odds[k2])
                fair[k1]["pinnacle"] = 1.0 / p1 if p1 > 0 else None
                fair[k2]["pinnacle"] = 1.0 / p2 if p2 > 0 else None
                if EV_DEBUG_BOOKS == "1":
                    print(f"[PIN-DEVIG] SUCCESS: fair[{k1}]={fair[k1]['pinnacle']:.3f}, fair[{k2}]={fair[k2]['pinnacle']:.3f}")
            except Exception as e:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[PIN-DEVIG] ERROR: {e}")

        # Betfair fair
        if k1 in bf_odds and k2 in bf_odds:
            try:
                p1, p2 = devig_two_way(bf_odds[k1], bf_odds[k2])
                fair[k1]["betfair"] = 1.0 / p1 if p1 > 0 else None
                fair[k2]["betfair"] = 1.0 / p2 if p2 > 0 else None
            except Exception:
                pass

        # Median of sharp probabilities (per outcome) with optional outlier removal
        # Calculate median probabilities and ensure they're complementary (sum to 1.0)
        probs_k1 = sharp_probs.get(k1, [])
        probs_k2 = sharp_probs.get(k2, [])

        # Build lists of probabilities coming only from configured sharp bookies
        probs_k1_sharp = [p for (bk, p) in sharp_probs_bybook.get(k1, []) if bk in SHARP_BOOKIES]
        probs_k2_sharp = [p for (bk, p) in sharp_probs_bybook.get(k2, []) if bk in SHARP_BOOKIES]

        if OUTLIER_DETECTION_ENABLED == "1":
            if probs_k1:
                probs_k1_filtered = remove_outliers_iqr(probs_k1)
                if EV_DEBUG_BOOKS == "1" and len(probs_k1_filtered) < len(probs_k1):
                    print(f"[DEBUG]   Outliers removed for {k1}: {len(probs_k1)} -> {len(probs_k1_filtered)} bookmakers")
                probs_k1 = probs_k1_filtered
            if probs_k2:
                probs_k2_filtered = remove_outliers_iqr(probs_k2)
                if EV_DEBUG_BOOKS == "1" and len(probs_k2_filtered) < len(probs_k2):
                    print(f"[DEBUG]   Outliers removed for {k2}: {len(probs_k2)} -> {len(probs_k2_filtered)} bookmakers")
                probs_k2 = probs_k2_filtered
            # also filter the sharp-only lists
            if probs_k1_sharp:
                probs_k1_sharp = remove_outliers_iqr(probs_k1_sharp)
            if probs_k2_sharp:
                probs_k2_sharp = remove_outliers_iqr(probs_k2_sharp)

        # Calculate median for both sides using configured sharp bookies only if we have enough sharp samples
        if len(probs_k1_sharp) >= MIN_SHARP_BOOKIES and len(probs_k2_sharp) >= MIN_SHARP_BOOKIES:
            p_med1 = statistics.median(probs_k1_sharp)
            p_med2 = statistics.median(probs_k2_sharp)
            # Normalize so probabilities sum to 1.0 (like devig_two_way)
            total = p_med1 + p_med2
            if total > 0:
                p_med1_norm = p_med1 / total
                p_med2_norm = p_med2 / total
                fair[k1]["median"] = 1.0 / p_med1_norm if p_med1_norm > 0 else None
                fair[k2]["median"] = 1.0 / p_med2_norm if p_med2_norm > 0 else None
        else:
            # Not enough configured sharps; do not set median component (rely on Pinnacle/Betfair)
            pass

        # -----------------------------------------------------------------
        # Pinnacle single-side handling (canonicalization)
        # If Pinnacle provided a price for at least one side, populate the
        # pinnacle component even when the opposite side is missing. When both
        # sides exist we prefer a devig_two_way; when only one side exists we
        # synthesize the complement probability (conservative fallback).
        # -----------------------------------------------------------------
        try:
            pinA = pin_odds.get(k1)
            pinB = pin_odds.get(k2)
            # Fallback: if Pinnacle didn't register under the canonical key, try
            # to find any Pinnacle entry for the same outcome name with a nearby
            # point (e.g., snapped differences). This helps when Pinnacle's
            # reported point differs slightly from our target line.
            # CRITICAL FIX: For spreads, Pinnacle reports opposite-signed points
            # (e.g., Team A: -6.0, Team B: +6.0). We need to check both same-sign
            # AND opposite-sign matches.
            def _find_pin_for_name(name_base: str, target_line: float):
                best_val = None
                bestd = float('inf')
                for kk, vv in pin_odds.items():
                    try:
                        parts = kk.rsplit("_", 1)
                        if len(parts) == 2 and parts[0] == name_base:
                            pt = float(parts[1])
                            # For spreads, check both same-sign and opposite-sign matches
                            # (Pinnacle uses opposite signs for the two teams)
                            d1 = abs(pt - float(target_line))  # same sign
                            d2 = abs(pt + float(target_line))  # opposite sign
                            d = min(d1, d2)
                            if d < bestd:
                                bestd = d
                                best_val = vv
                    except Exception:
                        continue
                return best_val
            if (not pinA) and k1 and name_A and line is not None:
                pinA = _find_pin_for_name(name_A, line)
            if (not pinB) and k2 and name_B and line is not None:
                pinB = _find_pin_for_name(name_B, line)
            if pinA or pinB:
                # both sides available at Pinnacle: devig and set pinnacle component
                if pinA and pinB and (not fair[k1].get("pinnacle") or not fair[k2].get("pinnacle")):
                    try:
                        p1, p2 = devig_two_way(float(pinA), float(pinB))
                        fair[k1]["pinnacle"] = 1.0 / p1 if p1 > 0 else None
                        fair[k2]["pinnacle"] = 1.0 / p2 if p2 > 0 else None
                    except Exception:
                        pass
                # single-side Pinnacle: use implied probability and synthesize complement
                elif pinA and not pinB:
                    try:
                        pA = 1.0 / float(pinA)
                        pA = max(0.0001, min(0.9999, pA))
                        pB = max(0.0001, 1.0 - pA)
                        fair[k1]["pinnacle"] = 1.0 / pA
                        fair[k2]["pinnacle"] = 1.0 / pB
                    except Exception:
                        pass
                elif pinB and not pinA:
                    try:
                        pB = 1.0 / float(pinB)
                        pB = max(0.0001, min(0.9999, pB))
                        pA = max(0.0001, 1.0 - pB)
                        fair[k2]["pinnacle"] = 1.0 / pB
                        fair[k1]["pinnacle"] = 1.0 / pA
                    except Exception:
                        pass
        except Exception:
            pass

        # Additional Pinnacle fallback: some Pinnacle keys may include
        # variations of outcome names (abbreviations, punctuation). If we
        # still don't have any pinnacle component set for the canonical
        # keys, attempt a relaxed substring-based lookup against collected
        # pin_odds and pick the nearest-point match. This is conservative
        # — we only use it when PINNACLE_PRIORITY is enabled so it doesn't
        # affect normal median-of-sharps behaviour.
        try:
            if PINNACLE_PRIORITY == "1":
                # canonical names
                if len(out_keys) == 2:
                    ka, kb = out_keys[0], out_keys[1]
                    need_ka = not fair.get(ka, {}).get("pinnacle")
                    need_kb = not fair.get(kb, {}).get("pinnacle")
                    # Helper: find any pin_odds key that contains the base name
                    # CRITICAL: For spreads, check both same-sign and opposite-sign matches
                    def _find_pin_contains(name_base: str, target_line: float):
                        best_val = None
                        bestd = float('inf')
                        low = name_base.lower() if name_base else ""
                        for kk, vv in pin_odds.items():
                            try:
                                k_low = kk.lower()
                                if low in k_low:
                                    # Try to parse point from key suffix if available
                                    parts = kk.rsplit("_", 1)
                                    if len(parts) == 2:
                                        pt = float(parts[1])
                                    else:
                                        # Unknown point, treat as very close
                                        pt = target_line
                                    # For spreads, check both same-sign and opposite-sign
                                    d1 = abs(pt - float(target_line))
                                    d2 = abs(pt + float(target_line))
                                    d = min(d1, d2)
                                    if d < bestd:
                                        bestd = d
                                        best_val = vv
                            except Exception:
                                continue
                        return best_val

                    # Attempt relaxed lookups
                    if need_ka and name_A and line is not None:
                        v = _find_pin_contains(name_A, line)
                        if v:
                            try:
                                pA = 1.0 / float(v)
                                pA = max(0.0001, min(0.9999, pA))
                                pB = max(0.0001, 1.0 - pA)
                                fair[ka]["pinnacle"] = 1.0 / pA
                                fair[kb]["pinnacle"] = 1.0 / pB
                            except Exception:
                                pass
                    if need_kb and name_B and line is not None:
                        v = _find_pin_contains(name_B, line)
                        if v:
                            try:
                                pB = 1.0 / float(v)
                                pB = max(0.0001, min(0.9999, pB))
                                pA = max(0.0001, 1.0 - pB)
                                fair[kb]["pinnacle"] = 1.0 / pB
                                fair[ka]["pinnacle"] = 1.0 / pA
                            except Exception:
                                pass
        except Exception:
            pass

    # If configured to prioritize Pinnacle and we lack a median component,
    # optionally relax the MIN_SHARP_BOOKIES requirement by using Pinnacle as
    # the median surrogate. This helps ensure spreads with only Pinnacle data
    # still produce a master fair price.
    try:
        if PINNACLE_PRIORITY == "1" and (str(PINNACLE_RELAX_MIN_SHARPS) == "1"):
            # canonical keys
            if len(out_keys) == 2:
                ka, kb = out_keys[0], out_keys[1]
                if (not fair.get(ka, {}).get("median")) and fair.get(ka, {}).get("pinnacle"):
                    fair[ka]["median"] = fair[ka]["pinnacle"]
                if (not fair.get(kb, {}).get("median")) and fair.get(kb, {}).get("pinnacle"):
                    fair[kb]["median"] = fair[kb]["pinnacle"]
    except Exception:
        pass

    # Interpolate median probabilities when exact-line data is insufficient
    if ENABLE_INTERPOLATION == "1" and market_key in ("spreads", "totals", "player_props") and line is not None:
        # If median not set for this target, attempt interpolation using nearest neighbor lines
        # Determine the canonical fair keys for this target
        key_A = f"{name_A}_{line}"
        key_B = f"{name_B}_{line}"

        # If fair dict is empty (no out_keys) initialize entries
        if key_A not in fair:
            fair[key_A] = {"pinnacle": None, "betfair": None, "median": None}
        if key_B not in fair:
            fair[key_B] = {"pinnacle": None, "betfair": None, "median": None}

        need_A = not fair[key_A].get("median")
        need_B = not fair[key_B].get("median")

        # Try interpolate A and derive B via complement if needed
        if need_A:
            pA = neighbor_interp(line_probs_A, float(line))
            if pA > 0.0:
                fair[key_A]["median"] = 1.0 / pA
                fair[key_B]["median"] = 1.0 / (1.0 - pA)
                # Audit: record neighbor interpolation usage
                try:
                    keys = sorted(line_probs_A.keys())
                    lower = max([k for k in keys if k <= float(line)], default=None)
                    upper = min([k for k in keys if k >= float(line)], default=None)
                    neigh_desc = f"{lower}:{upper}"
                    counts = f"{len(line_probs_A.get(lower, []))}:{len(line_probs_A.get(upper, []))}"
                except Exception:
                    neigh_desc = ""
                    counts = ""
                _record_interp_audit({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_id": event.get("id", ""),
                    "sport": event.get("sport_key", ""),
                    "market": market_key,
                    "side": name_A,
                    "method": "two-sided",
                    "target_line": float(line),
                    "neighbors": neigh_desc,
                    "neighbor_counts": counts,
                    "result_prob": pA,
                })

        # Or try interpolate B and derive A
        if (not fair[key_A].get("median")) and need_B:
            pB = neighbor_interp(line_probs_B, float(line))
            if pB > 0.0:
                fair[key_B]["median"] = 1.0 / pB
                fair[key_A]["median"] = 1.0 / (1.0 - pB)
                # Audit: record neighbor interpolation usage for B
                try:
                    keys = sorted(line_probs_B.keys())
                    lower = max([k for k in keys if k <= float(line)], default=None)
                    upper = min([k for k in keys if k >= float(line)], default=None)
                    neigh_desc = f"{lower}:{upper}"
                    counts = f"{len(line_probs_B.get(lower, []))}:{len(line_probs_B.get(upper, []))}"
                except Exception:
                    neigh_desc = ""
                    counts = ""
                _record_interp_audit({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_id": event.get("id", ""),
                    "sport": event.get("sport_key", ""),
                    "market": market_key,
                    "side": name_B,
                    "method": "two-sided",
                    "target_line": float(line),
                    "neighbors": neigh_desc,
                    "neighbor_counts": counts,
                    "result_prob": pB,
                })

        # Conservative fallback: if full interpolation failed, try single-nearest-line median
        # This helps when one nearby line has samples but the opposite neighbor is missing.
        if (not fair[key_A].get("median")):
            pA_near = nearest_single_side_prob(line_probs_A, float(line), INTERP_MAX_GAP)
            if pA_near > 0.0:
                fair[key_A]["median"] = 1.0 / pA_near
                # Derive complement for other side
                if 1.0 - pA_near > 0:
                    fair[key_B]["median"] = 1.0 / (1.0 - pA_near)
                # Audit single-nearest fallback usage
                try:
                    # find nearest key and its distance
                    keys = sorted(line_probs_A.keys())
                    best = None
                    bestd = float('inf')
                    for k in keys:
                        d = abs(k - float(line))
                        if d < bestd:
                            bestd = d
                            best = k
                    neigh_desc = f"nearest={best}"
                    counts = f"{len(line_probs_A.get(best, [])) if best is not None else 0}"
                except Exception:
                    neigh_desc = ""
                    counts = ""
                _record_interp_audit({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_id": event.get("id", ""),
                    "sport": event.get("sport_key", ""),
                    "market": market_key,
                    "side": name_A,
                    "method": "single-nearest",
                    "target_line": float(line),
                    "neighbors": neigh_desc,
                    "neighbor_counts": counts,
                    "result_prob": pA_near,
                })
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG]   Single-nearest fallback A: line={line} used neighbor dist <= {INTERP_MAX_GAP}")

        if (not fair[key_B].get("median")):
            pB_near = nearest_single_side_prob(line_probs_B, float(line), INTERP_MAX_GAP)
            if pB_near > 0.0:
                fair[key_B]["median"] = 1.0 / pB_near
                if 1.0 - pB_near > 0:
                    fair[key_A]["median"] = 1.0 / (1.0 - pB_near)
                # Audit single-nearest fallback usage for B
                try:
                    keys = sorted(line_probs_B.keys())
                    best = None
                    bestd = float('inf')
                    for k in keys:
                        d = abs(k - float(line))
                        if d < bestd:
                            bestd = d
                            best = k
                    neigh_desc = f"nearest={best}"
                    counts = f"{len(line_probs_B.get(best, [])) if best is not None else 0}"
                except Exception:
                    neigh_desc = ""
                    counts = ""
                _record_interp_audit({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_id": event.get("id", ""),
                    "sport": event.get("sport_key", ""),
                    "market": market_key,
                    "side": name_B,
                    "method": "single-nearest",
                    "target_line": float(line),
                    "neighbors": neigh_desc,
                    "neighbor_counts": counts,
                    "result_prob": pB_near,
                })
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG]   Single-nearest fallback B: line={line} used neighbor dist <= {INTERP_MAX_GAP}")

    # Diagnostic: record which sharp sources were available for this target
    try:
        # Determine canonical target keys for A/B
        if market_key in ("spreads", "totals", "player_props") and line is not None:
            key_A = f"{name_A}_{line}"
            key_B = f"{name_B}_{line}"
        else:
            key_A = name_A
            key_B = name_B

        pin_present_A = key_A in pin_odds
        pin_present_B = key_B in pin_odds
        bf_present_A = key_A in bf_odds
        bf_present_B = key_B in bf_odds

        sharps_A = [bk for (bk, p) in sharp_probs_bybook.get(key_A, []) if bk in SHARP_BOOKIES]
        sharps_B = [bk for (bk, p) in sharp_probs_bybook.get(key_B, []) if bk in SHARP_BOOKIES]

        _record_sharp_presence({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": event.get("id", ""),
            "sport": event.get("sport_key", ""),
            "market": market_key,
            "line": float(line) if line is not None else "",
            "key_A": key_A,
            "key_B": key_B,
            "pinnacle_present": int(pin_present_A) + int(pin_present_B),
            "betfair_present": int(bf_present_A) + int(bf_present_B),
            "sharp_count_A": len(sharps_A),
            "sharp_count_B": len(sharps_B),
            "sharps_A": ",".join(sorted(set(sharps_A))),
            "sharps_B": ",".join(sorted(set(sharps_B))),
        })
    except Exception:
        pass

    # Populate LAST_BUILD_FAIR_DIAG so the caller can detect cases where
    # Pinnacle was present yet master_fair_odds later resolves to 0.0.
    try:
        if market_key in ("spreads", "totals", "player_props") and line is not None and len(out_keys) == 2:
            key_A = f"{name_A}_{line}"
            key_B = f"{name_B}_{line}"
        else:
            key_A = name_A
            key_B = name_B
        pinnacle_keys = list(pin_odds.keys())
        LAST_BUILD_FAIR_DIAG.clear()
        LAST_BUILD_FAIR_DIAG.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": event.get("id", ""),
            "sport": event.get("sport_key", ""),
            "market": market_key,
            "line": float(line) if line is not None else "",
            "key_A": key_A,
            "key_B": key_B,
            "pinnacle_keys": pinnacle_keys,
            "pinnacle_found": int(bool(pinnacle_keys)),
        })
    except Exception:
        pass

    if EV_DEBUG_BOOKS == "1" and market_key == "spreads":
        print(f"[BUILD-RETURN] Returning fair dict with {len(fair)} keys: {list(fair.keys())}")
        for k, v in fair.items():
            print(f"  {k}: pinnacle={v.get('pinnacle')}, betfair={v.get('betfair')}, median={v.get('median')}")
    
    return fair


def master_fair_odds(fair_row: Dict[str, float]) -> float:
    """
    Combine Pinnacle, Betfair (commission-adjusted), and 'median' of other sharps
    into a single fair price using WEIGHTED probabilities. Missing components are
    ignored and weights are re-normalized over those present.

    Steps:
      - Convert each available fair odds O_i to probability p_i = 1 / O_i
      - Assign weights: pinnacle -> FAIR_WEIGHT_PINNACLE,
                        betfair  -> FAIR_WEIGHT_BETFAIR,
                        median   -> FAIR_WEIGHT_SHARPS
      - Normalize weights to sum to 1 over available sources
      - p* = sum_i (w_i * p_i)
      - Return fair odds = 1 / p* (or 0.0 if p* <= 0)
    """
    if EV_DEBUG_BOOKS == "1":
        pinnacle_val = fair_row.get("pinnacle", "None")
        betfair_val = fair_row.get("betfair", "None")
        median_val = fair_row.get("median", "None")
        print(f"[MASTER-FAIR] Input: pinnacle={pinnacle_val}, betfair={betfair_val}, median={median_val}")
    
    components = []
    # Map key -> (odds, weight)
    # Use Pinnacle, Betfair (commission-adjusted) and median-of-sharps when available
    if fair_row.get("pinnacle") and fair_row["pinnacle"] > 0:
        components.append((fair_row["pinnacle"], FAIR_WEIGHT_PINNACLE))
    if fair_row.get("betfair") and fair_row["betfair"] > 0:
        components.append((fair_row["betfair"], FAIR_WEIGHT_BETFAIR))
    if fair_row.get("median") and fair_row["median"] > 0:
        components.append((fair_row["median"], FAIR_WEIGHT_SHARPS))

    if not components:
        if EV_DEBUG_BOOKS == "1":
            print(f"[MASTER-FAIR] No components! Returning 0.0")
        return 0.0

    # Normalize weights over available components
    w_sum = sum(w for _, w in components)
    if w_sum <= 0:
        # fallback to simple average if weights are degenerate
        probs = [1.0 / o for (o, _) in components if o > 0]
        if not probs:
            return 0.0
        p_star = sum(probs) / len(probs)
        return (1.0 / p_star) if p_star > 0 else 0.0

    p_star = 0.0
    for odds_i, w_i in components:
        if odds_i <= 0:
            continue
        p_i = 1.0 / odds_i
        p_star += p_i * (w_i / w_sum)

    return (1.0 / p_star) if p_star > 0 else 0.0


def neighbor_interp(line_map: Dict[float, List[float]], target: float) -> float:
    """Interpolate median probability for target line using nearest lower/upper neighbors.

    Returns a probability in (0,1) or 0.0 if interpolation not possible.
    """
    if not line_map:
        return 0.0
    keys = sorted(line_map.keys())
    lower = max([k for k in keys if k <= target], default=None)
    upper = min([k for k in keys if k >= target], default=None)
    # Ensure distinct neighbors
    if lower is None or upper is None or lower == upper:
        return 0.0
    low_vals = line_map.get(lower, [])
    up_vals = line_map.get(upper, [])
    if len(low_vals) < INTERP_MIN_SAMPLES or len(up_vals) < INTERP_MIN_SAMPLES:
        return 0.0
    m_low = statistics.median(low_vals)
    m_up = statistics.median(up_vals)
    try:
        t = (target - lower) / (upper - lower)
    except Exception:
        return 0.0
    p = (1.0 - t) * m_low + t * m_up
    # Clip to (0,1)
    if p <= 0.0:
        p = 0.0001
    if p >= 1.0:
        p = 0.9999
    return p


def nearest_single_side_prob(line_map: Dict[float, List[float]], target: float, max_gap: float) -> float:
    """Return the median probability from the single nearest line within max_gap

    Respects INTERP_MIN_SAMPLES_SINGLE as the minimum samples required on that line.
    Returns 0.0 if no suitable neighbor found.
    """
    if not line_map:
        return 0.0
    keys = sorted(line_map.keys())
    best = None
    bestd = float('inf')
    for k in keys:
        d = abs(k - target)
        if d < bestd:
            bestd = d
            best = k
    if best is None:
        return 0.0
    if bestd > max_gap:
        return 0.0
    vals = line_map.get(best, [])
    if not vals or len(vals) < INTERP_MIN_SAMPLES_SINGLE:
        return 0.0
    return statistics.median(vals)


# ---------------------------------------------------------------------
# Dedupe key + logging
# ---------------------------------------------------------------------
def hit_key(event: Dict[str, Any], selection: str, book: str, odds: float) -> str:
    parts = [
        event.get("id", ""),
        event.get("sport_key", ""),
        selection,
        book,
        f"{odds:.3f}",
    ]
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()

# Track best EV per game+market+side for all_odds.csv (deduplicated logging)
_all_odds_tracker: Dict[str, Dict[str, Any]] = {}

def log_all_odds(
    event: Dict[str, Any],
    selection: str,
    line: float,
    book: str,
    book_odds: float,
    fair_home: Dict[str, float],
    fair_away: Dict[str, float],
    edge_pct: float,
    all_book_odds: Dict[str, float] = None,
    market_key: str = "h2h",
) -> None:
    """Track best EV for each game+market+side combination. Actual logging happens in flush_all_odds()."""
    global _all_odds_tracker
    
    sport   = event.get("sport_key")
    home    = event.get("home_team")
    away    = event.get("away_team")
    event_id = event.get("id")
    
    # Create unique key for game+market+side
    key = f"{event_id}|{market_key}|{selection}"
    
    # Keep only the best EV for this combination
    if key not in _all_odds_tracker or edge_pct > _all_odds_tracker[key]['edge_pct']:
        _all_odds_tracker[key] = {
            'event': event,
            'selection': selection,
            'line': line,
            'book': book,
            'book_odds': book_odds,
            'fair_home': fair_home,
            'fair_away': fair_away,
            'edge_pct': edge_pct,
            'all_book_odds': all_book_odds,
            'market_key': market_key
        }

def flush_all_odds() -> None:
    """Write all tracked best EV opportunities to all_odds.csv."""
    global _all_odds_tracker
    
    if not _all_odds_tracker:
        return
    
    # Ensure CSV exists with headers
    if not ALL_ODDS_CSV.exists():
        with ALL_ODDS_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "game_start_perth", "sport", "EV", "event", "market", "line", "side",
                "stake", "book", "price", "Prob", "Fair",
                "Pinnacle", "Betfair", "Sportsbet", "Bet365", "Pointsbet", "Dabble",
                "Ladbrokes", "Unibet", "Neds", "TAB", "TABtouch", "Betr", "PlayUp", "BetRight"
            ])
    
    # Write all tracked opportunities
    rows = []
    for key, data in _all_odds_tracker.items():
        event = data['event']
        selection = data['selection']
        line = data['line']
        book = data['book']
        book_odds = data['book_odds']
        fair_home = data['fair_home']
        fair_away = data['fair_away']
        edge_pct = data['edge_pct']
        all_book_odds = data['all_book_odds']
        market_key = data['market_key']
        
        sport = event.get("sport_key")
        home = event.get("home_team")
        away = event.get("away_team")
        commence = event.get("commence_time")
        
        # For spreads/totals, selection includes line (e.g., "Brooklyn Nets_10.5").
        # For h2h, selection is just the team name. The structure of fair_* differs:
        #  - h2h: fair_home/fair_away are component dicts {pinnacle, betfair, median}
        #  - spreads/totals: we pass a dict mapping selection->master fair (float)
        # Handle these cases explicitly and compute fair_master accordingly.
        fair_master = 0.0
        if market_key == "h2h":
            # Determine which side this selection refers to and compute master fair from components
            home = event.get("home_team")
            away = event.get("away_team")
            if selection == home and isinstance(fair_home, dict):
                fair_master = master_fair_odds(fair_home)
            elif selection == away and isinstance(fair_away, dict):
                fair_master = master_fair_odds(fair_away)
            if os.getenv("EV_DEBUG_BOOKS") == "1":
                try:
                    dbg_home = master_fair_odds(fair_home) if isinstance(fair_home, dict) else 0.0
                    dbg_away = master_fair_odds(fair_away) if isinstance(fair_away, dict) else 0.0
                    print(f"[DEBUG CSV] H2H fair: home={home} ${dbg_home:.2f} | away={away} ${dbg_away:.2f} | sel={selection} => ${fair_master:.2f}")
                except Exception:
                    pass
        else:
            # spreads/totals path: fair dicts are passed as selection->float
            fair_dict = fair_home if isinstance(fair_home, dict) and selection in fair_home else fair_away
            if isinstance(fair_dict, dict) and selection in fair_dict:
                fair_val = fair_dict[selection]
                # If it's a float, use it directly; if it's a dict, process it
                if isinstance(fair_val, (int, float)):
                    fair_master = float(fair_val)
                    if os.getenv("EV_DEBUG_BOOKS") == "1" and market_key in ("spreads", "totals"):
                        print(f"[DEBUG CSV] Found fair for '{selection}': ${fair_master:.2f}")
                else:
                    # It's a dict with pinnacle/betfair/median keys
                    fair_master = master_fair_odds(fair_val)
        
        try:
            # Convert game start time to Perth time
            perth_tz = timezone(timedelta(hours=8))
            if commence:
                commence_dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                game_start_perth = commence_dt.astimezone(perth_tz).strftime("%Y-%m-%d %H:%M:%S")
            else:
                game_start_perth = "Unknown"

            prob = (1.0 / fair_master) if fair_master > 0 else 0.0
            stake = _kelly_stake(prob, book_odds)
            event_name = f"{home} V {away}"
            
            # Extract clean side name
            side_display = selection
            # For spreads, totals and player_props remove the trailing _line suffix
            if market_key in ("spreads", "totals", "player_props") and "_" in selection:
                side_display = selection.rsplit("_", 1)[0]
            
            # Build bookmaker odds columns
            book_order = [
                "pinnacle", "betfair_ex_au", "sportsbet", "bet365_au", "pointsbetau", "dabble_au",
                "ladbrokes_au", "unibet", "neds", "tab", "tabtouch", "betr_au", "playup", "betright"
            ]
            book_odds_cols = []
            if all_book_odds:
                for bk in book_order:
                    # Use key membership to decide if we have a value for this book.
                    # Previously this checked truthiness which left blanks when the
                    # book was absent or had a 0.0 value. We want to show 0.00
                    # when the key exists and a numeric value is present, and
                    # otherwise leave the column empty.
                    if bk in all_book_odds and all_book_odds.get(bk) is not None:
                        try:
                            book_odds_cols.append(f"{float(all_book_odds.get(bk)):.2f}")
                        except Exception:
                            book_odds_cols.append("")
                    else:
                        book_odds_cols.append("")
            else:
                book_odds_cols = [""] * len(book_order)
            
            row = [
                game_start_perth, sport, f"{edge_pct * 100:.2f}%", event_name, market_key,
                f"{line:.1f}" if line else "", side_display, f"${stake:.2f}", book,
                f"${book_odds:.2f}", f"{prob * 100:.1f}%", f"${fair_master:.2f}"
            ] + book_odds_cols
            rows.append(row)
        except Exception as e:
            print(f"[ERROR] Failed to build CSV row: {e}")
            import traceback
            traceback.print_exc()
    
    # Write all rows
    if rows:
        with ALL_ODDS_CSV.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerows(rows)
    
    # Clear tracker for next run
    _all_odds_tracker.clear()


def report_data_quality() -> None:
    """Print simple data-quality counters from the generated all_odds.csv.
    Reports total rows and how many have Fair == $0.00 grouped by market.
    Safe to call even if the file doesn't exist yet.
    """
    try:
        if not ALL_ODDS_CSV.exists():
            return
        totals = {"h2h": [0, 0], "spreads": [0, 0], "totals": [0, 0], "other": [0, 0]}
        with ALL_ODDS_CSV.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                m = (row.get("market") or "").lower()
                key = m if m in totals else "other"
                totals[key][0] += 1
                if (row.get("Fair") or "").strip() == "$0.00":
                    totals[key][1] += 1
        # Emit compact summary lines
        for k, (total, zeros) in totals.items():
            if total > 0:
                pct = (zeros / total) * 100.0
                print(f"[dq] {k:7s}: rows={total} zero-fair={zeros} ({pct:.1f}%)")
    except Exception as e:
        print(f"[dq] Failed to compute data quality: {e}")


def log_hit(
    event: Dict[str, Any],
    selection: str,
    line: float,
    book: str,
    book_odds: float,
    fair_home: Dict[str, float],
    fair_away: Dict[str, float],
    edge_pct: float,
    notes: str = "",
    all_book_odds: Dict[str, float] = None,
    market_key: str = "h2h",
) -> None:
    ensure_hits_csv()
    ts_utc = datetime.now(timezone.utc).isoformat()
    sport   = event.get("sport_key")
    league  = event.get("sport_title")
    event_id = event.get("id")
    home    = event.get("home_team")
    away    = event.get("away_team")
    commence = event.get("commence_time")

    fair_dict = fair_home if selection == home else fair_away
    
    # EV CSV: custom format with individual AU bookmaker columns
    try:
        # Convert game start time to Perth time (UTC+8, no DST in Western Australia)
        perth_tz = timezone(timedelta(hours=8))
        if commence:
            # Parse ISO format: "2025-11-11T03:30:00Z" or with timezone
            commence_dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
            game_start_perth = commence_dt.astimezone(perth_tz).strftime("%Y-%m-%d %H:%M:%S")
        else:
            game_start_perth = "N/A"
        
        fair_master = master_fair_odds(fair_dict)
        prob = (1.0 / fair_master) if fair_master > 0 else 0.0
        stake = _kelly_stake(prob, book_odds)
        event_name = f"{home} V {away}"
        
        # For spreads/totals/player_props, extract outcome name without the _point suffix
        # e.g., "Over_6.0" -> "Over", "Home_-3.5" -> "Home"
        side_display = selection
        if market_key in ("spreads", "totals", "player_props") and "_" in selection:
            side_display = selection.rsplit("_", 1)[0]
        
        # Build ordered bookmaker odds columns (matching header order)
        # NOTE: Keys must match the API's actual bookmaker identifiers
        book_order = [
            "pinnacle",       # Pinnacle (sharp book, no commission adjustment)
            "betfair_ex_au",  # Betfair (RAW odds, no commission adjustment for display)
            "sportsbet",      # Sportsbet
            "bet365_au",      # Bet365 AU (API uses bet365_au)
            "pointsbetau",    # Pointsbet
            "dabble_au",      # Dabble (API uses dabble_au)
            "ladbrokes_au",   # Ladbrokes (API uses ladbrokes_au)
            "unibet",         # Unibet
            "neds",           # Neds
            "tab",            # TAB
            "tabtouch",       # TABtouch
            "betr_au",        # Betr (API uses betr_au)
            "playup",         # PlayUp
            "betright",       # BetRight
        ]
        book_odds_cols = []
        if all_book_odds:
            for bk in book_order:
                if bk in all_book_odds and all_book_odds.get(bk) is not None:
                    try:
                        book_odds_cols.append(f"{float(all_book_odds.get(bk)):.2f}")
                    except Exception:
                        book_odds_cols.append("")
                else:
                    book_odds_cols.append("")
        else:
            book_odds_cols = [""] * len(book_order)
        
        ev_row = [
            game_start_perth,  # Game start time in Perth local time
            sport,
            f"{edge_pct * 100:.2f}%",
            event_name,
            market_key,
            f"{line:.1f}" if line else "",
            side_display,
            f"${stake:.2f}",
            book,
            f"${book_odds:.2f}",
            f"{prob * 100:.1f}%",
            f"${fair_master:.2f}",
        ] + book_odds_cols
        
        with EV_CSV.open("a", newline="", encoding="utf-8") as f2:
            w2 = csv.writer(f2)
            w2.writerow(ev_row)
    except Exception:
        pass


# ---------------------------------------------------------------------
# Core scan
# ---------------------------------------------------------------------
def scan_sport(sport_key: str, seen: Dict[str, bool]) -> Dict[str, int]:
    # Robust fetch: try requested MARKETS, but if the API rejects player_props (422)
    # retry without it so other markets (spreads/totals/h2h) still return.
    def _fetch_with_markets(markets_str: str):
        url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": REGIONS,
            "markets": markets_str,
            "oddsFormat": "decimal",
        }
        print(f"[API] GET {sport_key}: regions={REGIONS}, markets={markets_str}")
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        return r.json()

    markets_env = [m.strip() for m in MARKETS.split(",") if m.strip()]
    # If player_props is requested globally, allow per-sport opt-in via PLAYER_PROPS_SPORTS
    if "player_props" in markets_env and PLAYER_PROPS_SPORTS:
        # sport_key can be sport_key or sport title; prefer exact sport_key match
        if sport_key not in PLAYER_PROPS_SPORTS:
            # Remove player_props for this sport to avoid extra API calls
            markets_env = [m for m in markets_env if m != "player_props"]
            if EV_DEBUG_BOOKS == "1":
                print(f"[scan] player_props disabled for sport={sport_key} (not in PLAYER_PROPS_SPORTS)")
    markets_str = ",".join(markets_env)
    events = []
    try:
        events = _fetch_with_markets(markets_str)
    except requests.exceptions.HTTPError as he:
        # If the API doesn't accept player_props for this sport, retry without it
        try:
            code = he.response.status_code if he.response is not None else None
        except Exception:
            code = None
        if code == 422 and "player_props" in markets_env:
            reduced = [m for m in markets_env if m != "player_props"]
            if reduced:
                try:
                    print(f"[scan] Server rejected markets='{markets_str}'; retrying without player_props")
                    events = _fetch_with_markets(",".join(reduced))
                except Exception as e:
                    # Fall back to original error handling below
                    raise
            else:
                raise
        else:
            raise
    hits = 0
    ev_hits = 0
    arb_hits = 0  # ARB disabled
    ev_alerts_sent = 0
    
    print(f"[scan] Processing {len(events)} events")

    filtered_count = 0
    filtered_events = []  # Track filtered events with reasons
    for ev in events:
        # Filter by event start time (if filters are enabled)
        if MIN_TIME_TO_START_MINUTES > 0 or MAX_TIME_TO_START_HOURS > 0:
            commence_time = ev.get("commence_time")
            if commence_time:
                try:
                    commence_dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                    now_utc = datetime.now(timezone.utc)
                    time_to_start = commence_dt - now_utc
                    minutes_to_start = time_to_start.total_seconds() / 60
                    
                    # Skip games starting too soon (if MIN filter enabled)
                    if MIN_TIME_TO_START_MINUTES > 0 and minutes_to_start < MIN_TIME_TO_START_MINUTES:
                        filtered_count += 1
                        filtered_events.append({
                            'event': f"{ev.get('home_team')} vs {ev.get('away_team')}",
                            'sport': ev.get('sport_key'),
                            'minutes_to_start': minutes_to_start,
                            'reason': f'Too soon (< {MIN_TIME_TO_START_MINUTES}m)'
                        })
                        continue
                    
                    # Skip games too far in future (if MAX filter enabled)
                    if MAX_TIME_TO_START_HOURS > 0 and minutes_to_start > MAX_TIME_TO_START_HOURS * 60:
                        filtered_count += 1
                        filtered_events.append({
                            'event': f"{ev.get('home_team')} vs {ev.get('away_team')}",
                            'sport': ev.get('sport_key'),
                            'minutes_to_start': minutes_to_start,
                            'reason': f'Too far (> {MAX_TIME_TO_START_HOURS}h)'
                        })
                        continue
                except Exception as e:
                    pass  # If we can't parse time, include the event
        
        # H2H market processing
        fair = build_fair_prices(ev, market_key="h2h")
        home = ev.get("home_team")
        away = ev.get("away_team")
        
        # Calculate master fair odds for home and away
        fair_home_master = master_fair_odds(fair.get(home, {}))
        fair_away_master = master_fair_odds(fair.get(away, {}))

        # Collect ALL bookmaker odds for EV CSV columns (first pass)
        # This includes sharp books like Pinnacle for display purposes
        all_home_odds: Dict[str, float] = {}
        all_away_odds: Dict[str, float] = {}
        
        if EV_DEBUG_BOOKS == "1":
            print(f"\n[DEBUG] Event: {home} vs {away}")
            print(f"[DEBUG] Bookmakers in API response:")
            for bk in ev.get("bookmakers", []):
                print(f"  - {bk.get('key')}")
        
        for bk in ev.get("bookmakers", []):
            bkey = bk.get("key")
            if FILTER_BOOKS and bkey not in FILTER_BOOKS:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG] Skipped {bkey} (FILTER_BOOKS)")
                continue
            # Collect ALL bookmakers for CSV display (not just AU_BOOKIES)
            # But we'll only scan AU_BOOKIES for EV opportunities in the second pass
            markets = bk.get("markets", [])
            h2h = next((m for m in markets if m.get("key") == "h2h"), None)
            if not h2h:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG] {bkey}: no h2h market")
                continue
            outs = h2h.get("outcomes", [])
            if len(outs) != 2:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG] {bkey}: outcomes != 2 ({len(outs)})")
                continue
            o_home = next((o for o in outs if o.get("name") == home), None)
            o_away = next((o for o in outs if o.get("name") == away), None)
            if not o_home or not o_away:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG] {bkey}: missing home/away outcomes")
                continue
            try:
                oh = float(o_home.get("price"))
                oa = float(o_away.get("price"))
            except Exception as e:
                if EV_DEBUG_BOOKS == "1":
                    print(f"[DEBUG] {bkey}: price parsing error: {e}")
                continue
            # Store RAW odds (no commission adjustment for Betfair here)
            all_home_odds[bkey] = oh
            all_away_odds[bkey] = oa
            if EV_DEBUG_BOOKS == "1":
                print(f"[DEBUG] OK {bkey}: home={oh}, away={oa}")
            
            # Log ALL odds to all_odds.csv for ALL bookmakers (not just AU)
            ev_edge_home = oh * (1.0 / fair_home_master) - 1.0 if fair_home_master > 0 else 0.0
            ev_edge_away = oa * (1.0 / fair_away_master) - 1.0 if fair_away_master > 0 else 0.0
            
            log_all_odds(
                ev, home, 0.0, bkey, oh,
                fair.get(home, {}), fair.get(away, {}),
                ev_edge_home,
                all_book_odds=all_home_odds,
                market_key="h2h",
            )
            
            log_all_odds(
                ev, away, 0.0, bkey, oa,
                fair.get(home, {}), fair.get(away, {}),
                ev_edge_away,
                all_book_odds=all_away_odds,
                market_key="h2h",
            )
        
        if EV_DEBUG_BOOKS == "1":
            print(f"[DEBUG] Collected {len(all_home_odds)} bookmakers for CSV columns")
            print(f"[DEBUG] Keys: {list(all_home_odds.keys())}")

        # ---- EV hits vs master fair (second pass - only AU bookmakers for EV detection) ----
        for bk in ev.get("bookmakers", []):
            bkey = bk.get("key")
            if FILTER_BOOKS and bkey not in FILTER_BOOKS:
                continue
            if bkey not in AU_BOOKIES:
                continue
            markets = bk.get("markets", [])
            h2h = next((m for m in markets if m.get("key") == "h2h"), None)
            if not h2h:
                continue
            outs = h2h.get("outcomes", [])
            if len(outs) != 2:
                continue
            o_home = next((o for o in outs if o.get("name") == home), None)
            o_away = next((o for o in outs if o.get("name") == away), None)
            if not o_home or not o_away:
                continue
            try:
                oh = float(o_home.get("price"))
                oa = float(o_away.get("price"))
            except Exception:
                continue
            
            # Debug mode: log all games with fair odds
            if os.getenv("LOG_ALL_GAMES") == "1":
                print(f"\n[GAME] {home} vs {away}")
                print(f"  Fair odds: {home}=${fair_home_master:.2f} | {away}=${fair_away_master:.2f}")
                print(f"  {bkey}: {home}=${oh:.2f} (EV={(oh/fair_home_master-1)*100:.2f}%) | {away}=${oa:.2f} (EV={(oa/fair_away_master-1)*100:.2f}%)")
            
            if fair_home_master > 0:
                p_true_home = 1.0 / fair_home_master
                if p_true_home < MIN_PROB:
                    continue
                ev_edge_home = oh * p_true_home - 1.0
                # Skip bookmaker odds above configured maximum allowed odds
                if oh > MAX_ALLOWED_ODDS:
                    if EV_DEBUG_BOOKS == "1":
                        print(f"[DEBUG]       {bkey} {home} @ ${oh:.2f}: price > MAX_ALLOWED_ODDS (${MAX_ALLOWED_ODDS:.2f}), skipping")
                    continue
                # Enforce max odds limit for h2h checks as well
                if oh > MAX_ALLOWED_ODDS:
                    continue
                if ev_edge_home >= EV_MIN_EDGE and (EV_MAX_ALERTS == 0 or ev_alerts_sent < EV_MAX_ALERTS):
                    # Check minimum stake filter
                    stake = _kelly_stake(p_true_home, oh)
                    if stake < MIN_STAKE:
                        continue
                    k = hit_key(ev, home, bkey, oh)
                    if TEST_ALLOW_DUPES == "1" or not seen.get(k):
                        if TEST_ALLOW_DUPES != "1":
                            seen[k] = True
                        log_hit(
                            ev, home, 0.0, bkey, oh,
                            fair.get(home, {}), fair.get(away, {}),
                            ev_edge_home,
                            "EV edge >= threshold",
                            all_book_odds=all_home_odds,
                            market_key="h2h",
                        )
                        try:
                            msg = _format_telegram_message(
                                ev, home, bkey, oh, fair_home_master, ev_edge_home, p_true_home
                            )
                            _send_telegram(msg)
                        except Exception:
                            pass
                        hits += 1
                        ev_hits += 1
                        ev_alerts_sent += 1

            if fair_away_master > 0:
                p_true_away = 1.0 / fair_away_master
                if p_true_away < MIN_PROB:
                    continue
                ev_edge_away = oa * p_true_away - 1.0
                # Skip bookmaker odds above configured maximum allowed odds
                if oa > MAX_ALLOWED_ODDS:
                    if EV_DEBUG_BOOKS == "1":
                        print(f"[DEBUG]       {bkey} {away} @ ${oa:.2f}: price > MAX_ALLOWED_ODDS (${MAX_ALLOWED_ODDS:.2f}), skipping")
                    continue
                if oa > MAX_ALLOWED_ODDS:
                    continue
                if ev_edge_away >= EV_MIN_EDGE and (EV_MAX_ALERTS == 0 or ev_alerts_sent < EV_MAX_ALERTS):
                    # Check minimum stake filter
                    stake = _kelly_stake(p_true_away, oa)
                    if stake < MIN_STAKE:
                        continue
                    k = hit_key(ev, away, bkey, oa)
                    if TEST_ALLOW_DUPES == "1" or not seen.get(k):
                        if TEST_ALLOW_DUPES != "1":
                            seen[k] = True
                        log_hit(
                            ev, away, 0.0, bkey, oa,
                            fair.get(home, {}), fair.get(away, {}),
                            ev_edge_away,
                            "EV edge >= threshold",
                            all_book_odds=all_away_odds,
                            market_key="h2h",
                        )
                        try:
                            msg = _format_telegram_message(
                                ev, away, bkey, oa, fair_away_master, ev_edge_away, p_true_away
                            )
                            _send_telegram(msg)
                        except Exception:
                            pass
                        hits += 1
                        ev_hits += 1
                        ev_alerts_sent += 1
        
        # Spreads & Totals EV (ARB disabled)
        added_hits, added_ev = _compute_spreads_totals_ev(ev, seen)
        hits += added_hits
        ev_hits += added_ev

    if filtered_count > 0:
        print(f"[scan] Filtered {filtered_count} events by time constraints (min={MIN_TIME_TO_START_MINUTES}m, max={MAX_TIME_TO_START_HOURS}h)")

    return {"total": hits, "ev": ev_hits, "arb": arb_hits, "filtered": filtered_events}


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
def main() -> int:
    # One-off test message path
    if "--test-telegram" in sys.argv[1:]:
        try:
            if not TELEGRAM_BOT_TOKEN:
                print("[test] TELEGRAM_BOT_TOKEN missing. Set it in .env.")
            if not TELEGRAM_CHAT_ID:
                print("[test] TELEGRAM_CHAT_ID missing. Set it in .env.")
            print(f"[test] TELEGRAM_ENABLED={TELEGRAM_ENABLED}")
            print(f"[test] chat_id={TELEGRAM_CHAT_ID}")
            ts = datetime.now().astimezone().strftime("%a %b %d, %I:%M%p")
            _send_telegram(f"🔥 Pats EV Bot 🔥 Test message\nSent: {ts} (local time)", debug=True)
            print("[test] Telegram test attempted (see logs above for API response).")
            return 0
        except Exception as e:
            print(f"[test] Telegram test failed: {e}")
            return 1
    if not ODDS_API_KEY:
        print("[X] ODDS_API_KEY missing.")
        return 1

    seen = load_dedupe()
    # Determine which sports to scan
    sports_env = [s.strip() for s in SPORTS.split(",") if s.strip()]
    sports = FILTER_SPORTS if FILTER_SPORTS else sports_env
    
    # Log API usage before scanning
    log_api_usage(len(sports))
    
    total_hits = 0
    total_ev = 0
    all_filtered_events = []  # Collect all filtered events across sports

    for sp in sports:
        print(f"[scan] sport={sp}")
        try:
            stats = scan_sport(sp, seen)
            total_hits += stats["total"]
            total_ev += stats["ev"]
            all_filtered_events.extend(stats.get("filtered", []))
            # ARB disabled; ignore stats["arb"] if present
            time.sleep(0.25)
        except Exception as e:
            print(f"[!] Error scanning {sp}: {e}")

    save_dedupe(seen)
    # Flush any diagnostic CSVs we've collected during the run so they're
    # available immediately for inspection.
    try:
        _flush_interp_audit_csv()
    except Exception:
        pass
    try:
        _flush_sharp_presence_csv()
    except Exception:
        pass
    try:
        _flush_pinnacle_issues_csv()
    except Exception:
        pass
    
    # Flush interpolation audit CSV (if any) and all_odds tracker to CSV
    _flush_interp_audit_csv()
    _flush_sharp_presence_csv()
    flush_all_odds()
    # Print simple data-quality counters for quick visibility
    report_data_quality()
    
    # Display filtered events if any
    if all_filtered_events:
        print(f"\n{'='*100}")
        print(f"FILTERED EVENTS ({len(all_filtered_events)} total)")
        print(f"{'='*100}\n")
        for fe in all_filtered_events:
            mins = fe['minutes_to_start']
            print(f"  {fe['event']:<50} {fe['reason']:<25} ({mins:.1f}m to start)")
        print(f"\n{'='*100}\n")
    print(f"[done] Hits logged this run: {total_hits} (EV={total_ev})")
    print(f"[info] EV CSV=> {EV_CSV}")
    print(f"[info] Dedupe=> {DEDUP_FILE}")
    if SUMMARY_ENABLED == "1":
        try:
            msg = (
                "Run summary\n"
                f"Sports: {', '.join(sports)}\n"
                f"EV hits: {total_ev}\n"
                f"Total: {total_hits}"
            )
            _send_telegram(msg)
        except Exception:
            pass
    
    # Run analysis script if hits were found
    if total_ev > 0:
        try:
            import subprocess
            analyze_script = Path(__file__).parent / "analyze_ev.py"
            if analyze_script.exists():
                print(f"\n[analysis] Running {analyze_script.name}...")
                subprocess.run([sys.executable, str(analyze_script)], check=False)
        except Exception as e:
            print(f"[!] Error running analysis: {e}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

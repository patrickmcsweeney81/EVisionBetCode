# Standardized CSV header order for all logging scripts
CSV_HEADERS = [
    "Start Time", "Sport", "Event", "Market", "Selection", "O/U + Y/N", "Book", "Price",
    "Fair", "EV%", "Prob", "Stake", "NumSharps",
    "Pinnacle", "Betfair", "Sportsbet", "Bet365", "Pointsbet", "Betright", "Tab", "Dabble", "Unibet",
    "Ladbrokes", "Playup", "Tabtouch", "Betr", "Neds", "Draftkings", "Fanduel", "Betmgm", "Betonline",
    "Bovada", "Boombet"
]

"""
Centralized configuration for bookmakers and API settings.
Edit bookmaker lists here to add/remove books from analysis.

NOTE (v2.0): book_weights.py module provides flexible 0-4 weight system.
The lists below are maintained for backward compatibility but new code
should use book_weights.get_book_weight() for dynamic weight lookup.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Optional external enrichment integrations:
# - BALLDONTLIE (NBA player context): set BALLDONTLIE_ENABLED=1 to attach recent form/minutes
#   to each NBA player prop record (adds player_context field). Safe, low-latency.


# ============================================================================
# SHARP BOOKMAKERS (used for fair price calculation)
# DEPRECATED v2.0: All handlers now use book_weights.py for dynamic weight lookup.
# This list is retained only for legacy compatibility with old monolithic bot.
# New code: use book_weights.list_books_by_weight(market_type, min_weight=3)
# ============================================================================
SHARP_BOOKIES = [
    "pinnacle",          # Primary sharp (weight 4)
    "betfair_ex_eu",     # Betfair Europe (weight 3)
    "betfair_ex_au",     # Betfair Australia (weight 3)
    "draftkings",        # DraftKings (best for player props)
    "fanduel",           # FanDuel (best for player props)
    "betmgm",            # BetMGM (good for player props)
    "betonlineag",       # BetOnline
    "bovada",            # Bovada
    "betus",             # BetUS
    "lowvig",            # LowVig
    "mybookieag",        # MyBookie
    "marathonbet",       # Marathon Bet
    "matchbook",         # Matchbook
]

# ============================================================================
# AUSTRALIAN BOOKMAKERS (target books for EV opportunities)
# ============================================================================
AU_BOOKIES = [
    "sportsbet",         # SportsBet
    "tab",               # TAB
    "neds",              # Neds
    "ladbrokes_au",      # Ladbrokes
    "pointsbetau",       # PointsBet (AU)
    "boombet",           # BoomBet
    "betright",          # Bet Right
    "playup",            # PlayUp
    "unibet",            # Unibet
    "tabtouch",          # TABtouch
    "dabble_au",         # Dabble AU
    "betr_au",           # Betr
    "bet365_au",         # Bet365 AU
]

# ============================================================================
# U.S. MASS-MARKET BOOKMAKERS (optional inclusion for EV opportunities)
# These are widely used, not necessarily sharp. Controlled via INCLUDE_US_BOOKS env.
# Odds API keys chosen for breadth of availability.
# ============================================================================
US_BOOKIES = [
    "draftkings",       # DraftKings
    "fanduel",          # FanDuel
    "betmgm",           # BetMGM
    "caesars",          # Caesars
    "betrivers",        # BetRivers
    "sugarhouse",       # SugarHouse
    "superbook",        # SuperBook
    "twinspires",       # TwinSpires
    "wynnbet",          # WynnBet
    "williamhill_us",   # William Hill US
    "bovada",           # Bovada
    "betonlineag",      # BetOnline
    "betus",            # BetUS
    "lowvig",           # LowVig
    "mybookieag",       # MyBookie
]

# ============================================================================
# OTHER BOOKMAKERS (logged for comparison, not used in fair calc)
# ============================================================================
OTHER_BOOKIES = [
    "draftkings",        # DraftKings
    "fanduel",           # FanDuel
    "betmgm",            # BetMGM
]

# ============================================================================
# ALL BOOKMAKERS FOR CSV COLUMNS (order matters for CSV output)
# ============================================================================
ALL_BOOKIES_ORDERED = [
    "pinnacle",
    "betfair",
    # AU books (primary targets - from Odds API widget list)
    "sportsbet",
    "tab",
    "neds",
    "ladbrokes_au",
    "pointsbetau",
    "boombet",
    "betright",
    "playup",
    "unibet",
    "tabtouch",
    "dabble_au",
    "betr_au",
    "bet365_au",
    # US/International books (extended list)
    "draftkings",
    "fanduel",
    "betmgm",
    "caesars",
    "betrivers",
    "sugarhouse",
    "superbook",
    "twinspires",
    "wynnbet",
    "williamhill_us",
    "bovada",
    "betonlineag",
    "betus",
    "lowvig",
    "mybookieag",
    "marathonbet",
    "matchbook",
]

# ============================================================================
# FAIR PRICE WEIGHTS
# DEPRECATED: Use book_weights.py 0-4 scale system instead.
# These percentage weights are kept for legacy code compatibility only.
# ============================================================================
WEIGHT_PINNACLE = 0.75       # Pinnacle gets 75% weight
WEIGHT_BETFAIR = 0.0         # Betfair excluded from fair calculation
WEIGHT_OTHER_SHARPS = 0.25   # Other sharp books get 25% weight (median)

# ============================================================================
# PLAYER PROPS MARKETS BY SPORT
# ============================================================================

# NBA Basketball Props
NBA_PROP_MARKETS = [
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_threes",
    "player_blocks",
    "player_steals",
    "player_blocks_steals",
    "player_turnovers",
    "player_points_rebounds_assists",
    "player_points_rebounds",
    "player_points_assists",
    "player_rebounds_assists",
    "player_double_double",
    "player_triple_double",
    "player_first_basket",
]

# NFL American Football Props - High liquidity markets only
# Removed: longest_completion, rush_longest, reception_longest, solo_tackles, 
# defensive_interceptions, pats (low availability)
NFL_PROP_MARKETS = [
    # Passing (high liquidity)
    "player_pass_yds",
    "player_pass_tds",
    "player_pass_completions",
    "player_pass_attempts",
    "player_pass_interceptions",
    # Rushing (high liquidity)
    "player_rush_yds",
    "player_rush_tds",
    "player_rush_attempts",
    # Receiving (high liquidity)
    "player_receptions",
    "player_reception_yds",
    "player_reception_tds",
    # Combo stats (medium liquidity)
    "player_rush_reception_yds",
    "player_rush_reception_tds",
    # Defense/Special teams (high liquidity)
    "player_tackles_assists",
    "player_sacks",
    "player_kicking_points",
    "player_field_goals",
    # Touchdown scorers (Yes/No - high liquidity)
    "player_1st_td",
    "player_anytime_td",
    "player_last_td",
    # Alternate markets (high value when available)
    "player_pass_yds_alternate",
    "player_pass_tds_alternate",
    "player_rush_yds_alternate",
    "player_rush_tds_alternate",
    "player_receptions_alternate",
    "player_reception_yds_alternate",
    "player_reception_tds_alternate",
]

# AFL Australian Rules Props
AFL_PROP_MARKETS = [
    "player_disposals",
    "player_goals",
    "player_kicks",
    "player_handballs",
    "player_marks",
    "player_tackles",
]

# NRL Rugby League Props
NRL_PROP_MARKETS = [
    "player_tries",
    "player_anytime_tryscorer",
    "player_first_tryscorer",
]

# Soccer Props
SOCCER_PROP_MARKETS = [
    "player_shots",
    "player_shots_on_target",
    "player_anytime_goalscorer",
    "player_first_goalscorer",
]

# Map sport keys to their prop markets
SPORT_PROP_MARKETS = {
    "basketball_nba": NBA_PROP_MARKETS,
    "americanfootball_nfl": NFL_PROP_MARKETS,
    "aussierules_afl": AFL_PROP_MARKETS,
    "rugbyleague_nrl": NRL_PROP_MARKETS,
    "soccer_epl": SOCCER_PROP_MARKETS,
    "soccer_uefa_champs_league": SOCCER_PROP_MARKETS,
}

# ============================================================================
# BETFAIR CONFIGURATION
# ============================================================================

BETFAIR_BOOKIES = ["betfair_ex_eu", "betfair_ex_au"]  # Betfair exchanges to exclude
BETFAIR_COMMISSION = float(os.getenv("BETFAIR_COMMISSION", 0.06))    # 6% commission rate (override with .env)

# Betfair API keys (active and testing)
BETFAIR_API_KEY_ACTIVE = os.getenv("BETFAIR_API_KEY_ACTIVE", "")
BETFAIR_API_KEY_TESTING = os.getenv("BETFAIR_API_KEY_TESTING", "")

# ============================================================================
# THRESHOLDS & FILTERS
# ============================================================================
EV_MIN_EDGE = 0.02           # Minimum EV threshold (2%)
MIN_PROB = 0.20              # Minimum probability threshold (20%)
MIN_STAKE = 5.0              # Minimum Kelly stake to log ($5)
MAX_MARGIN_PERCENT = 15.0    # Skip books with margin >15%
MIN_BOOKMAKERS_AFTER_OUTLIERS = 5  # Minimum sharp books needed
LINE_TOLERANCE = 0.25        # Spreads/totals line matching tolerance

# Enable/disable filters (set to False to disable)
ENABLE_EV_FILTER = True      # Set False to log all opportunities regardless of edge
ENABLE_PROB_FILTER = True    # Set False to log all probabilities

# ============================================================================
# BANKROLL & KELLY
# ============================================================================
BANKROLL = 1000.0            # Default bankroll ($1000)
KELLY_FRACTION = 0.25        # Kelly fraction for stake sizing (25%)

# ============================================================================
# TIME FILTERS
# ============================================================================
MIN_TIME_TO_START_MINUTES = 0   # Skip events starting too soon (minutes)
MAX_TIME_TO_START_HOURS = 999   # Skip events too far out (hours)

# ============================================================================
# DATA QUALITY
# ============================================================================
OUTLIER_DETECTION_ENABLED = True  # Enable outlier removal from median calculation

# ============================================================================
# FILE PATHS
# ============================================================================
DATA_DIR_NAME = "data"
DEDUP_FILE_NAME = "seen_hits.json"
# Deprecated: EV_CSV_NAME removed (policy: only all_odds_analysis.csv + all_odds.csv retained)
ALL_ODDS_CSV_NAME = "all_odds_analysis.csv"

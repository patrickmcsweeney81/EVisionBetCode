"""
EVisionBet Bookmaker Ratings (52 books, 0-4⭐)

Classification:
- 4⭐ MAIN SHARPS (4): pinnacle, fanduel, draftkings, betfair_ex_eu
  → Used for fair odds calculation (primary)
  
- 3⭐ SHARPS (2): betonlineag, lowvig
  → Used for fair odds calculation (secondary)
  
- 2⭐ MEDIUM (9): matchbook, betrivers, williamhill_us, williamhill, fanatics, 
                   hardrockbet, ballybet, bovada, betmgm
  → Not used for fair odds, tracked for EV opportunities
  
- 1⭐ SOFT/NOVELTY (23): betanysports, betclic_fr, betparx, betsson, betus, 
                         codere_it, coolbet, espnbet, fliff, gtbets, leovegas_se,
                         marathonbet, mybookieag, nordicbet, onexbet, parionssport_fr,
                         rebet, sport888, tipico_de, winamax_de, unibet_fr, unibet_nl, unibet_se
  → Low priority longtail books
  
- 0⭐ WEIGHT 0 (13): ALL AU books + unibet
  → Not used in fair odds, AU local market exclusions
"""

BOOKMAKER_RATINGS = {
    # ========================================================================
    # 4⭐ MAIN SHARPS - Primary fair odds contributors
    # ========================================================================
    "pinnacle": {
        "stars": 4,
        "category": "sharp",
        "region": "us",
        "title": "Pinnacle",
        "weight_nba": 0.35,
        "weight_nfl": 0.35,
    },
    "fanduel": {
        "stars": 4,
        "category": "sharp",
        "region": "us",
        "title": "FanDuel",
        "weight_nba": 0.30,
        "weight_nfl": 0.30,
    },
    "draftkings": {
        "stars": 4,
        "category": "sharp",
        "region": "us",
        "title": "DraftKings",
        "weight_nba": 0.30,
        "weight_nfl": 0.30,
    },
    "betfair_ex_eu": {
        "stars": 4,
        "category": "sharp",
        "region": "eu",
        "title": "Betfair (EU)",
        "weight_nba": 0.05,
        "weight_nfl": 0.05,
    },

    # ========================================================================
    # 3⭐ SHARPS - Secondary fair odds contributors
    # ========================================================================
    "betonlineag": {
        "stars": 3,
        "category": "sharp",
        "region": "us",
        "title": "BetOnline",
        "weight_nba": 0.10,
        "weight_nfl": 0.10,
    },
    "lowvig": {
        "stars": 3,
        "category": "sharp",
        "region": "us",
        "title": "LowVig",
        "weight_nba": 0.10,
        "weight_nfl": 0.10,
    },

    # ========================================================================
    # 2⭐ MEDIUM - Not used for fair odds, tracked for EV
    # ========================================================================
    "matchbook": {
        "stars": 2,
        "category": "medium",
        "region": "eu",
        "title": "Matchbook",
    },
    "betrivers": {
        "stars": 2,
        "category": "medium",
        "region": "us",
        "title": "BetRivers",
    },
    "williamhill_us": {
        "stars": 2,
        "category": "medium",
        "region": "us",
        "title": "William Hill (US)",
    },
    "williamhill": {
        "stars": 2,
        "category": "medium",
        "region": "eu",
        "title": "William Hill",
    },
    "fanatics": {
        "stars": 2,
        "category": "medium",
        "region": "us",
        "title": "Fanatics",
    },
    "hardrockbet": {
        "stars": 2,
        "category": "medium",
        "region": "us",
        "title": "Hard Rock Bet",
    },
    "ballybet": {
        "stars": 2,
        "category": "medium",
        "region": "us",
        "title": "Bally Bet",
    },
    "bovada": {
        "stars": 2,
        "category": "medium",
        "region": "us",
        "title": "Bovada",
    },
    "betmgm": {
        "stars": 2,
        "category": "medium",
        "region": "us",
        "title": "BetMGM",
    },

    # ========================================================================
    # 1⭐ SOFT/NOVELTY/LONGTAIL - Low priority books
    # ========================================================================
    "betanysports": {
        "stars": 1,
        "category": "soft",
        "region": "us",
        "title": "BetAnySports",
    },
    "betclic_fr": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Betclic (FR)",
    },
    "betparx": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Betparx",
    },
    "betsson": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Betsson",
    },
    "betus": {
        "stars": 1,
        "category": "soft",
        "region": "us",
        "title": "BetUS",
    },
    "codere_it": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Codere (IT)",
    },
    "coolbet": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "CoolBet",
    },
    "espnbet": {
        "stars": 1,
        "category": "soft",
        "region": "us",
        "title": "ESPN Bet",
    },
    "fliff": {
        "stars": 1,
        "category": "soft",
        "region": "us",
        "title": "Fliff",
    },
    "gtbets": {
        "stars": 1,
        "category": "soft",
        "region": "us",
        "title": "GTBets",
    },
    "leovegas_se": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "LeoVegas (SE)",
    },
    "marathonbet": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "MarathonBet",
    },
    "mybookieag": {
        "stars": 1,
        "category": "soft",
        "region": "us",
        "title": "MyBookie",
    },
    "nordicbet": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "NordicBet",
    },
    "onexbet": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "OneXBet",
    },
    "parionssport_fr": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Parions Sport (FR)",
    },
    "rebet": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Rebet",
    },
    "sport888": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Sport888",
    },
    "tipico_de": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Tipico (DE)",
    },
    "winamax_de": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Winamax (DE)",
    },
    "winamax_fr": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Winamax (FR)",
    },
    "unibet_fr": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Unibet (FR)",
    },
    "unibet_nl": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Unibet (NL)",
    },
    "unibet_se": {
        "stars": 1,
        "category": "soft",
        "region": "eu",
        "title": "Unibet (SE)",
    },

    # ========================================================================
    # 0⭐ WEIGHT 0 - AU local & exclusions (not used in fair odds)
    # ========================================================================
    "betfair_ex_au": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Betfair (AU)",
    },
    "sportsbet": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Sportsbet",
    },
    "tab": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "TAB",
    },
    "tabtouch": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "TAB Touch",
    },
    "pointsbetau": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "PointsBet (AU)",
    },
    "ladbrokes_au": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Ladbrokes (AU)",
    },
    "neds": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Neds",
    },
    "betr_au": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Betr (AU)",
    },
    "betright": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "BetRight",
    },
    "dabble_au": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Dabble",
    },
    "playup": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "PlayUp",
    },
    "boombet": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Boombet",
    },
    "unibet": {
        "stars": 0,
        "category": "local_au",
        "region": "au",
        "title": "Unibet",
    },
}


def get_sharp_books():
    """Get all books rated 3⭐ or 4⭐ (used for fair odds)"""
    return {
        k: v for k, v in BOOKMAKER_RATINGS.items()
        if v["stars"] >= 3
    }


def get_target_books():
    """Get all books rated 1-2⭐ (for EV detection)"""
    return {
        k: v for k, v in BOOKMAKER_RATINGS.items()
        if v["stars"] in [1, 2]
    }


def get_books_by_region(region):
    """Get books available in region"""
    return {
        k: v for k, v in BOOKMAKER_RATINGS.items()
        if v["region"] == region
    }


def get_books_by_stars(min_stars, max_stars=4):
    """Get books within star range"""
    return {
        k: v for k, v in BOOKMAKER_RATINGS.items()
        if min_stars <= v["stars"] <= max_stars
    }


def get_weight_for_sport(bookmaker: str, sport_key: str) -> float:
    """Get weight contribution for bookmaker in specific sport"""
    book_info = BOOKMAKER_RATINGS.get(bookmaker.lower(), {})
    
    # Map sport keys to weight keys
    if "basketball" in sport_key:
        return book_info.get("weight_nba", 0.0)
    elif "americanfootball" in sport_key:
        return book_info.get("weight_nfl", 0.0)
    
    return 0.0

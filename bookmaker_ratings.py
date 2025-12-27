"""
BOOKMAKER RATINGS - Final Locked Configuration
All 54 bookmakers mapped to star ratings (4⭐, 3⭐, 2⭐, 1⭐, 0⭐)

Column Order Rule (LOCKED FOR ALL FUTURE CSVs):
  1. 4⭐ sharps (6 books) - Fair odds calculation
  2. 0⭐ AU targets (14 books) - EV opportunity surface
  3. 3⭐ sharps (4 books) - Sharp coverage depth
  4. 2⭐ decent (6 books) - Secondary market depth
  5. 1⭐ soft (24 books) - Regional/soft books

This column order NEVER CHANGES - applies to NBA, NFL, NHL, all sports.

Last Updated: December 28, 2025
Status: FINAL - LOCKED FOR ALL FUTURE EXTRACTIONS
"""

# All 54 bookmakers with their star ratings - FINAL LOCKED ORDER
BOOKMAKER_RATINGS = {
    # 4⭐ SHARPS - Fair Odds Calculation (6 books)
    "pinnacle": 4,
    "betfair_ex_eu": 4,
    "matchbook": 4,
    "draftkings": 4,
    "fanduel": 4,
    "lowvig": 4,
    
    # 0⭐ AU TARGETS - Surface EV Opportunities (14 books)
    "bet365": 0,
    "betfair_ex_au": 0,
    "sportsbet": 0,
    "dabble_au": 0,
    "pointsbetau": 0,
    "neds": 0,
    "ladbrokes_au": 0,
    "unibet": 0,
    "betright": 0,
    "betr_au": 0,
    "boombet": 0,
    "playup": 0,
    "tab": 0,
    "tabtouch": 0,
    
    # 3⭐ SHARPS - Sharp Coverage Depth (4 books)
    "betonlineag": 3,
    "betmgm": 3,
    "betrivers": 3,
    "fanatics": 3,
    
    # 2⭐ DECENT - Secondary Market Depth (6 books)
    "hardrockbet": 2,
    "williamhill": 2,
    "williamhill_us": 2,
    "bovada": 2,
    "betanysports": 2,
    "espnbet": 2,
    
    # 1⭐ SOFT - Regional/Soft/Promotional Books (24 books)
    "betclic_fr": 1,
    "betsson": 1,
    "betus": 1,
    "coolbet": 1,
    "codere_it": 1,
    "everygame": 1,
    "fliff": 1,
    "gtbets": 1,
    "leovegas_se": 1,
    "marathonbet": 1,
    "mybookieag": 1,
    "nordicbet": 1,
    "onexbet": 1,
    "parionssport_fr": 1,
    "rebet": 1,
    "sport888": 1,
    "tipico_de": 1,
    "unibet_fr": 1,
    "unibet_nl": 1,
    "unibet_se": 1,
    "winamax_de": 1,
    "winamax_fr": 1,
    "ballybet": 1,
    "betparx": 1,
}

# Final column order (LOCKED) - used in ALL future CSVs
FINAL_COLUMN_ORDER = [
    # 4⭐ Sharps (Fair Odds) - 6 books
    "pinnacle",
    "betfair_ex_eu",
    "matchbook",
    "draftkings",
    "fanduel",
    "lowvig",
    
    # 0⭐ AU Targets (EV Surface) - 14 books
    "bet365",
    "betfair_ex_au",
    "sportsbet",
    "dabble_au",
    "pointsbetau",
    "neds",
    "ladbrokes_au",
    "unibet",
    "betright",
    "betr_au",
    "boombet",
    "playup",
    "tab",
    "tabtouch",
    
    # 3⭐ Sharps (Coverage Depth) - 4 books
    "betonlineag",
    "betmgm",
    "betrivers",
    "fanatics",
    
    # 2⭐ Decent (Secondary Depth) - 6 books
    "hardrockbet",
    "williamhill",
    "williamhill_us",
    "bovada",
    "betanysports",
    "espnbet",
    
    # 1⭐ Soft (Regional/Soft) - 24 books
    "betclic_fr",
    "betsson",
    "betus",
    "coolbet",
    "codere_it",
    "everygame",
    "fliff",
    "gtbets",
    "leovegas_se",
    "marathonbet",
    "mybookieag",
    "nordicbet",
    "onexbet",
    "parionssport_fr",
    "rebet",
    "sport888",
    "tipico_de",
    "unibet_fr",
    "unibet_nl",
    "unibet_se",
    "winamax_de",
    "winamax_fr",
    "ballybet",
    "betparx",
]

# Helper functions
def get_rating(book_key: str) -> int:
    """Get star rating for a bookmaker."""
    return BOOKMAKER_RATINGS.get(book_key, 1)

def get_sharp_books() -> dict:
    """Get only sharp books (3⭐ and 4⭐) for fair odds calculation."""
    return {k: v for k, v in BOOKMAKER_RATINGS.items() if v >= 3}

def get_target_books() -> dict:
    """Get only target books (0⭐ - AU target sportsbooks for EV surface)."""
    return {k: v for k, v in BOOKMAKER_RATINGS.items() if v == 0}

def get_books_by_rating(rating: int) -> list:
    """Get all books with a specific rating."""
    return [k for k, v in BOOKMAKER_RATINGS.items() if v == rating]

# Stats
TOTAL_BOOKS = len(BOOKMAKER_RATINGS)
SHARPS_4_STAR = len(get_books_by_rating(4))
SHARPS_3_STAR = len(get_books_by_rating(3))
DECENT_2_STAR = len(get_books_by_rating(2))
SOFT_1_STAR = len(get_books_by_rating(1))
TARGETS_0_STAR = len(get_books_by_rating(0))

if __name__ == "__main__":
    print(f"Bookmaker Ratings Summary (FINAL - LOCKED)")
    print(f"=" * 60)
    print(f"4⭐ Sharps (Fair Odds):     {SHARPS_4_STAR} books")
    print(f"0⭐ Targets (AU EV):        {TARGETS_0_STAR} books")
    print(f"3⭐ Sharps (Coverage):      {SHARPS_3_STAR} books")
    print(f"2⭐ Decent (Depth):         {DECENT_2_STAR} books")
    print(f"1⭐ Soft (Regional):        {SOFT_1_STAR} books")
    print(f"-" * 60)
    print(f"TOTAL:                      {TOTAL_BOOKS} books")
    print()
    print(f"Column order (locked): {len(FINAL_COLUMN_ORDER)} columns")
    print(f"Order: 4⭐ → 0⭐ → 3⭐ → 2⭐ → 1⭐")
    print(f"Status: FINAL - LOCKED FOR ALL FUTURE CSVs")

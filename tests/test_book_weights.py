"""
Tests for the book_weights module.
"""

import sys
from pathlib import Path

import pytest

from core.book_weights import (
    MAIN_MARKET_WEIGHTS,
    PLAYER_PROP_WEIGHTS,
    SPORT_OVERRIDES,
    get_book_display_name,
    get_book_weight,
    list_books_by_weight,
)

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline_v2.ratings import BOOKMAKER_RATINGS, get_sport_weight


def test_main_market_weights():
    assert MAIN_MARKET_WEIGHTS.get("pinnacle") == 4
    assert MAIN_MARKET_WEIGHTS.get("circa") == 4
    assert MAIN_MARKET_WEIGHTS.get("bookmaker") == 4
    assert MAIN_MARKET_WEIGHTS.get("betonline") == 3
    assert MAIN_MARKET_WEIGHTS.get("draftkings") == 3
    assert MAIN_MARKET_WEIGHTS.get("bovada") == 1


def test_player_prop_weights():
    assert PLAYER_PROP_WEIGHTS.get("pinnacle") == 4
    assert PLAYER_PROP_WEIGHTS.get("draftkings") == 4
    assert PLAYER_PROP_WEIGHTS.get("fanduel") == 4
    assert PLAYER_PROP_WEIGHTS.get("betmgm") == 3
    assert PLAYER_PROP_WEIGHTS.get("bovada") == 1


def test_sport_overrides_exist():
    assert "MMA" in SPORT_OVERRIDES
    assert "NBA" in SPORT_OVERRIDES
    assert "NFL" in SPORT_OVERRIDES
    assert "main" in SPORT_OVERRIDES["MMA"]
    assert "props" in SPORT_OVERRIDES["MMA"]
    assert "props" in SPORT_OVERRIDES["NBA"]
    assert "props" in SPORT_OVERRIDES["NFL"]


def test_get_book_weight_basic():
    assert get_book_weight("pinnacle", "main") == 4
    assert get_book_weight("pinnacle", "h2h") == 4
    assert get_book_weight("pinnacle", "spreads") == 4
    assert get_book_weight("draftkings", "props") == 4
    assert get_book_weight("unknown_book", "main") == 0
    assert get_book_weight("nonexistent", "props") == 0


def test_get_book_weight_normalization():
    assert get_book_weight("PINNACLE", "main") == 4
    assert get_book_weight("Pinnacle", "MAIN") == 4
    assert get_book_weight("  pinnacle  ", "  main  ") == 4
    assert get_book_weight("pinnacle", "h2h") == 4
    assert get_book_weight("pinnacle", "spread") == 4
    assert get_book_weight("pinnacle", "spreads") == 4
    assert get_book_weight("pinnacle", "total") == 4
    assert get_book_weight("pinnacle", "totals") == 4
    assert get_book_weight("pinnacle", "moneyline") == 4


def test_get_book_weight_sport_override():
    assert get_book_weight("betonline", "main") == 3
    assert get_book_weight("betonline", "main", "MMA") == 4
    assert get_book_weight("bet365", "props") == 2
    assert get_book_weight("bet365", "props", "NBA") == 3
    assert get_book_weight("draftkings", "props", "BASKETBALL_NBA") == get_book_weight(
        "draftkings", "props", "NBA"
    )
    assert get_book_weight("betonline", "main", "UFC") == get_book_weight(
        "betonline", "main", "MMA"
    )


def test_get_book_weight_fallback():
    assert get_book_weight("marathonbet", "props") == 1
    assert get_book_weight("marathonbet", "props", "NBA") == 1


def test_get_book_display_name():
    assert get_book_display_name("pinnacle") == "Pinnacle"
    assert get_book_display_name("draftkings") == "DraftKings"
    assert get_book_display_name("bet365_au") == "Bet365 AU"
    assert get_book_display_name("unknown_book") == "Unknown Book"


def test_list_books_by_weight():
    main_books = list_books_by_weight("main")
    assert "pinnacle" in main_books
    assert main_books["pinnacle"] == 4
    prop_books_3 = list_books_by_weight("props", min_weight=3)
    assert "pinnacle" in prop_books_3
    assert "draftkings" in prop_books_3
    assert "fanduel" in prop_books_3
    assert "bovada" not in prop_books_3
    nba_props = list_books_by_weight("props", sport="NBA", min_weight=3)
    assert "bet365" in nba_props


def test_weight_scale_consistency():
    for book, weight in MAIN_MARKET_WEIGHTS.items():
        assert 0 <= weight <= 4
    for book, weight in PLAYER_PROP_WEIGHTS.items():
        assert 0 <= weight <= 4
    for sport, overrides in SPORT_OVERRIDES.items():
        for market_type, weights in overrides.items():
            for book, weight in weights.items():
                assert 0 <= weight <= 4


def test_bookmaker_ratings():
    assert BOOKMAKER_RATINGS["pinnacle"] == 4
    assert BOOKMAKER_RATINGS["circa"] == 4
    assert BOOKMAKER_RATINGS["draftkings"] == 3
    assert BOOKMAKER_RATINGS["fanduel"] == 3


def test_sport_weight_default():
    assert get_sport_weight("basketball_nba") == 1.0

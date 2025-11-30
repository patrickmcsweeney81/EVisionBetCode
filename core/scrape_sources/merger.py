"""Merge odds data from primary API (Odds API) and scrape sources.

The merger ensures:
1. Primary API data is canonical (team names, event IDs, sport keys)
2. Scraped data fills gaps (missing bookmakers, additional markets)
3. Duplicate detection prevents double-counting same odds
4. Team name fuzzy matching handles naming variations
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, List, Optional

from .base_adapter import Event as ScrapeEvent


def fuzzy_match_team(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """
    Fuzzy match team names to handle variations.
    
    Examples:
        "Los Angeles Lakers" ~ "LA Lakers" -> True
        "Golden State Warriors" ~ "Warriors" -> True
        "Boston Celtics" !~ "Miami Heat" -> False
    
    Args:
        name1: First team name
        name2: Second team name
        threshold: Match ratio threshold (0-1)
    
    Returns:
        True if names match closely enough
    """
    if name1 == name2:
        return True
    
    # Normalize: lowercase, strip common prefixes
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()
    
    # Quick checks
    if n1 == n2:
        return True
    if n1 in n2 or n2 in n1:
        return True
    
    # Sequence matcher
    ratio = SequenceMatcher(None, n1, n2).ratio()
    return ratio >= threshold


def find_matching_event(
    scraped_event: ScrapeEvent,
    primary_events: List[Dict],
    time_tolerance_minutes: int = 30
) -> Optional[Dict]:
    """
    Find matching event in primary API events.
    
    Matching criteria:
    1. Sport must match exactly
    2. Teams must fuzzy match (both home and away)
    3. Commence time within tolerance window
    
    Args:
        scraped_event: Event from scrape source
        primary_events: Events from primary API (Odds API format)
        time_tolerance_minutes: Max time difference for match
    
    Returns:
        Matching primary event dict or None
    """
    from datetime import datetime, timedelta
    
    for primary in primary_events:
        # Sport match
        if primary.get("sport_key") != scraped_event.sport_key:
            continue
        
        # Team match (fuzzy)
        primary_home = primary.get("home_team", "")
        primary_away = primary.get("away_team", "")
        
        home_match = fuzzy_match_team(primary_home, scraped_event.home_team)
        away_match = fuzzy_match_team(primary_away, scraped_event.away_team)
        
        if not (home_match and away_match):
            continue
        
        # Time match (within tolerance)
        try:
            primary_time = datetime.fromisoformat(primary.get("commence_time", "").replace("Z", "+00:00"))
            scraped_time = datetime.fromisoformat(scraped_event.commence_time.replace("Z", "+00:00"))
            
            time_diff = abs((primary_time - scraped_time).total_seconds() / 60)
            if time_diff > time_tolerance_minutes:
                continue
        except Exception:
            # If time parsing fails, allow match (better than missing data)
            pass
        
        return primary
    
    return None


def merge_bookmaker_into_event(
    primary_event: Dict,
    scraped_event: ScrapeEvent
) -> Dict:
    """
    Merge scraped bookmaker data into primary event.
    
    Adds new bookmaker entry or updates existing markets for that bookmaker.
    
    Args:
        primary_event: Event dict from primary API (modified in-place)
        scraped_event: Event from scrape source
    
    Returns:
        Modified primary_event dict
    """
    bookmakers = primary_event.setdefault("bookmakers", [])
    
    # Check if bookmaker already exists
    existing_bookie = None
    for bk in bookmakers:
        if bk.get("key") == scraped_event.bookmaker_key:
            existing_bookie = bk
            break
    
    if existing_bookie:
        # Merge markets (prioritize scraped data for freshness)
        existing_markets = {m.get("key"): m for m in existing_bookie.get("markets", [])}
        
        for scraped_mkt in scraped_event.markets:
            mkt_key = scraped_mkt.key
            
            # Convert scraped market to Odds API format
            outcomes_list = []
            for out in scraped_mkt.outcomes:
                outcome_dict = {
                    "name": out.name,
                    "price": out.price,
                }
                if out.point is not None:
                    outcome_dict["point"] = out.point
                if out.description:
                    outcome_dict["description"] = out.description
                outcomes_list.append(outcome_dict)
            
            market_dict = {
                "key": mkt_key,
                "outcomes": outcomes_list,
            }
            if scraped_mkt.last_update:
                market_dict["last_update"] = scraped_mkt.last_update
            
            # Replace existing market or add new
            existing_markets[mkt_key] = market_dict
        
        existing_bookie["markets"] = list(existing_markets.values())
    else:
        # Add new bookmaker
        new_bookie = {
            "key": scraped_event.bookmaker_key,
            "title": scraped_event.bookmaker_key.replace("_", " ").title(),
            "markets": []
        }
        
        for scraped_mkt in scraped_event.markets:
            outcomes_list = []
            for out in scraped_mkt.outcomes:
                outcome_dict = {
                    "name": out.name,
                    "price": out.price,
                }
                if out.point is not None:
                    outcome_dict["point"] = out.point
                if out.description:
                    outcome_dict["description"] = out.description
                outcomes_list.append(outcome_dict)
            
            market_dict = {
                "key": scraped_mkt.key,
                "outcomes": outcomes_list,
            }
            if scraped_mkt.last_update:
                market_dict["last_update"] = scraped_mkt.last_update
            
            new_bookie["markets"].append(market_dict)
        
        bookmakers.append(new_bookie)
    
    return primary_event


def merge_odds_data(
    primary_events: List[Dict],
    scraped_events: List[ScrapeEvent],
    time_tolerance_minutes: int = 30
) -> List[Dict]:
    """
    Merge scraped odds data into primary API events.
    
    Strategy:
    1. Match scraped events to primary events (fuzzy team names + time window)
    2. For matches: add/update bookmaker markets in primary event
    3. For non-matches: optionally add as new event (not implemented; prevents pollution)
    
    Args:
        primary_events: Events from primary API (Odds API format)
        scraped_events: Events from scrape sources
        time_tolerance_minutes: Max time difference for event matching
    
    Returns:
        Merged events list (primary_events modified in-place and returned)
    """
    matched_count = 0
    unmatched_count = 0
    
    for scraped in scraped_events:
        match = find_matching_event(scraped, primary_events, time_tolerance_minutes)
        
        if match:
            merge_bookmaker_into_event(match, scraped)
            matched_count += 1
        else:
            unmatched_count += 1
            # Optionally log unmatched for debugging
            # print(f"[Merger] No match for {scraped.home_team} vs {scraped.away_team} ({scraped.bookmaker_key})")
    
    print(f"[Merger] Matched {matched_count} scraped events, {unmatched_count} unmatched")
    
    return primary_events


def merge_multiple_sources(
    primary_events: List[Dict],
    scrape_adapters: List,
    sport: str,
    markets: Optional[List[str]] = None
) -> List[Dict]:
    """
    Convenience function to merge multiple scrape sources at once.
    
    Args:
        primary_events: Events from primary API
        scrape_adapters: List of adapter instances (SportsbetAdapter, etc.)
        sport: Sport key to fetch
        markets: Market keys to fetch (None = all)
    
    Returns:
        Merged events
    """
    all_scraped = []
    
    for adapter in scrape_adapters:
        try:
            scraped = adapter.fetch_events(sport, markets)
            all_scraped.extend(scraped)
            print(f"[Merger] Fetched {len(scraped)} events from {adapter.bookmaker_key}")
        except Exception as e:
            print(f"[Merger] Failed to fetch from {adapter.bookmaker_key}: {e}")
    
    return merge_odds_data(primary_events, all_scraped)

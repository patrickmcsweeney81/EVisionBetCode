"""
V3 Base Extractor - Parent class for all sport extractors
Handles common logic: API calls, CSV writing, data transformation
"""

import csv
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

from .config import (
    ODDS_API_HOST,
    API_KEY,
    BOOKMAKERS,
    BOOK_ABBREVIATIONS,
    CSV_COLUMNS,
    DATA_DIR,
    EVENT_MIN_MINUTES,
    EVENT_MAX_HOURS,
    EXCLUDE_MARKETS,
    MIN_BOOK_COUNT,
    REQUIRE_TWO_WAY,
    NORMALIZE_MARKETS,
    NORMALIZE_AMOUNT,
    BOOKS_TO_NORMALIZE,
)


class BaseExtractor:
    """Base extractor for all sports. Override in subclasses for sport-specific logic."""

    def __init__(self, sport: str, regions: List[str], markets: List[str]):
        self.sport = sport
        self.regions = regions
        self.markets = markets
        self.api_key = API_KEY
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
    def extract(self) -> pd.DataFrame:
        """Main extraction flow. Override _fetch_events in subclass."""
        print(f"\n{'='*60}")
        print(f"Extracting {self.sport.upper()}")
        print(f"{'='*60}")
        
        # Fetch events from API
        events = self._fetch_events()
        if not events:
            print(f"No events found for {self.sport}")
            return pd.DataFrame()
        
        print(f"Found {len(events)} events")
        
        # Extract odds for each event
        rows = []
        for event in events:
            event_rows = self._process_event(event)
            rows.extend(event_rows)
        
        if not rows:
            print("No valid odds found")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        
        # Normalize lines (whole numbers → .5)
        df = self._normalize_lines(df)
        
        print(f"Extracted {len(df)} odds rows")
        return df
    
    def _fetch_events(self) -> List[Dict]:
        """Fetch events from Odds API. Override in subclass if needed."""
        url = f"{ODDS_API_HOST}/v4/sports/{self.sport}/events"
        
        # Time window
        now = datetime.now(timezone.utc)
        min_commence = (now + timedelta(minutes=EVENT_MIN_MINUTES)).isoformat()
        max_commence = (now + timedelta(hours=EVENT_MAX_HOURS)).isoformat()
        
        params = {
            "apiKey": self.api_key,
            "regions": ",".join(self.regions),
        }
        
        try:
            print(f"Fetching events from {url}")
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # API returns list directly or dict with 'data' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("data", [])
            return []
        except Exception as e:
            print(f"Error fetching events: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _process_event(self, event: Dict) -> List[Dict]:
        """Process single event: fetch odds, structure rows."""
        event_id = event.get("id")
        away_team = event.get("away_team", "")
        home_team = event.get("home_team", "")
        commence_time = event.get("commence_time", "")
        
        # Fetch odds for this event
        odds_resp = self._fetch_odds(event_id)
        if not odds_resp:
            return []
        
        # API structure: bookmakers array, each has markets
        bookmakers = odds_resp.get("bookmakers", [])
        if not bookmakers:
            return []
        
        rows = []
        
        # For each market, collect all bookmaker odds
        markets_by_key = {}  # market_key -> {outcome_name -> {book: price}}
        
        for bookmaker in bookmakers:
            book_key = bookmaker.get("key")
            book_name = BOOK_ABBREVIATIONS.get(book_key, book_key.title())
            
            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                
                if market_key not in self.markets:
                    continue
                
                if market_key not in markets_by_key:
                    markets_by_key[market_key] = {}
                
                for outcome in market.get("outcomes", []):
                    outcome_name = outcome.get("name")
                    point = outcome.get("point", "")
                    price = outcome.get("price")
                    
                    outcome_key = f"{outcome_name}|{point}"
                    
                    if outcome_key not in markets_by_key[market_key]:
                        markets_by_key[market_key][outcome_key] = {
                            "name": outcome_name,
                            "point": point,
                            "market": market_key,
                            "books": {},
                        }
                    
                    markets_by_key[market_key][outcome_key]["books"][book_name] = price
        
        # Now convert to rows
        for market_key, outcomes in markets_by_key.items():
            for outcome_key, outcome_data in outcomes.items():
                row = {
                    "timestamp": self.timestamp,
                    "sport": self.sport,
                    "event_id": event_id,
                    "away_team": away_team,
                    "home_team": home_team,
                    "commence_time": commence_time,
                    "market": market_key,
                    "point": outcome_data["point"],
                    "selection": outcome_data["name"],
                }
                
                # Add all bookmaker odds
                for book_col in BOOK_ABBREVIATIONS.values():
                    row[book_col] = outcome_data["books"].get(book_col, "")
                
                rows.append(row)
        
        return rows
    
    def _fetch_odds(self, event_id: str) -> Dict:
        """Fetch odds for single event."""
        url = f"{ODDS_API_HOST}/v4/sports/{self.sport}/events/{event_id}/odds"
        
        params = {
            "apiKey": self.api_key,
            "regions": ",".join(self.regions),
            "markets": ",".join(self.markets),
            "oddsFormat": "decimal",
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # API returns dict directly
            if isinstance(data, dict) and "bookmakers" in data:
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"Error fetching odds for {event_id}: {e}")
            return {}
    
    def _normalize_lines(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize whole-number lines to .5 (e.g., 10 → 10.5)."""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Only normalize spreads and totals
        mask = df["market"].isin(NORMALIZE_MARKETS)
        
        if not mask.any():
            return df
        
        # Convert point to float, normalize if needed
        def normalize_point(point_val, book_col):
            if pd.isna(point_val) or point_val == "":
                return point_val
            
            try:
                point_float = float(point_val)
                # Check if it's a whole number (ends in .0)
                if point_float == int(point_float):
                    # Check if this book should be normalized
                    if book_col in BOOKS_TO_NORMALIZE:
                        return point_float + NORMALIZE_AMOUNT
                return point_float
            except (ValueError, TypeError):
                return point_val
        
        # Apply normalization to each bookmaker column
        for book_col in BOOK_ABBREVIATIONS.values():
            if book_col in df.columns:
                df.loc[mask, "point"] = df.loc[mask, "point"].apply(
                    lambda p: normalize_point(p, book_col)
                )
        
        return df
    
    def save_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Save DataFrame to CSV."""
        if df.empty:
            print("No data to save")
            return None
        
        # Ensure all columns exist
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        
        # Reorder columns
        df = df[CSV_COLUMNS]
        
        # Save
        output_path = Path(DATA_DIR) / "v3" / "extracts" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"Saved: {output_path}")
        print(f"Rows: {len(df)}")
        
        return output_path

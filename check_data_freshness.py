"""
Check how fresh The Odds API data is by examining last_update timestamps.
"""
import os
import requests
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check_api_freshness(sport_key="basketball_nba"):
    """
    Check how old the odds data is from The Odds API.
    
    Returns dict with:
    - current_time: Current UTC time
    - bookmaker_updates: {bookmaker: {last_update, age_seconds}}
    """
    api_key = os.getenv("ODDS_API_KEY")
    
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": "au,us",
        "markets": "h2h"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    events = response.json()
    
    if not events:
        return {"error": "No events found"}
    
    # Use first event as sample
    event = events[0]
    current_time = datetime.now(timezone.utc)
    
    bookmaker_freshness = {}
    
    for bk in event.get("bookmakers", []):
        bkey = bk.get("key", "")
        last_update_str = bk.get("last_update")
        
        if last_update_str:
            # Parse ISO format timestamp
            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            age_seconds = (current_time - last_update).total_seconds()
            age_minutes = age_seconds / 60
            
            bookmaker_freshness[bkey] = {
                "last_update": last_update_str,
                "age_seconds": int(age_seconds),
                "age_minutes": round(age_minutes, 1),
                "is_fresh": age_seconds < 300  # Fresh if < 5 minutes old
            }
    
    return {
        "event": f"{event.get('away_team')} @ {event.get('home_team')}",
        "sport": sport_key,
        "current_time": current_time.isoformat(),
        "bookmakers": bookmaker_freshness
    }


def display_freshness(sport_key="basketball_nba"):
    """Display data freshness in a readable format."""
    result = check_api_freshness(sport_key)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\n{'='*80}")
    print(f"Data Freshness Check - {sport_key}")
    print(f"{'='*80}")
    print(f"Event: {result['event']}")
    print(f"Current Time: {result['current_time']}")
    print(f"\n{'Bookmaker':<20} {'Last Update':<30} {'Age (min)':<12} {'Fresh?'}")
    print(f"{'-'*80}")
    
    # Sort by age (oldest first)
    sorted_books = sorted(
        result['bookmakers'].items(),
        key=lambda x: x[1]['age_seconds'],
        reverse=True
    )
    
    for bkey, info in sorted_books:
        age_str = f"{info['age_minutes']} min"
        fresh_str = "✓ Fresh" if info['is_fresh'] else "✗ Stale"
        
        print(f"{bkey:<20} {info['last_update']:<30} {age_str:<12} {fresh_str}")
    
    # Summary
    fresh_count = sum(1 for info in result['bookmakers'].values() if info['is_fresh'])
    total_count = len(result['bookmakers'])
    avg_age = sum(info['age_minutes'] for info in result['bookmakers'].values()) / total_count
    
    print(f"\n{'='*80}")
    print(f"Summary: {fresh_count}/{total_count} bookmakers have fresh data (< 5 min old)")
    print(f"Average data age: {avg_age:.1f} minutes")
    print(f"{'='*80}\n")


def check_specific_bookmaker(sport_key="basketball_nba", bookmaker="ladbrokes_au"):
    """Check freshness of specific bookmaker."""
    result = check_api_freshness(sport_key)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return None
    
    if bookmaker in result['bookmakers']:
        info = result['bookmakers'][bookmaker]
        print(f"\n{bookmaker} Data Freshness:")
        print(f"  Last Update: {info['last_update']}")
        print(f"  Age: {info['age_minutes']} minutes ({info['age_seconds']} seconds)")
        print(f"  Status: {'Fresh ✓' if info['is_fresh'] else 'Stale ✗'}")
        return info
    else:
        print(f"{bookmaker} not found in data")
        return None


def check_player_props_freshness(sport_key="americanfootball_nfl"):
    """Check freshness of player props data."""
    api_key = os.getenv("ODDS_API_KEY")
    
    # Get events first
    events_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "h2h"
    }
    
    response = requests.get(events_url, params=params)
    response.raise_for_status()
    events = response.json()
    
    if not events:
        return {"error": "No events found"}
    
    # Get props for first event
    event = events[0]
    event_id = event['id']
    
    props_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
    props_params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "player_pass_yds,player_rush_yds"
    }
    
    response = requests.get(props_url, params=props_params)
    response.raise_for_status()
    props_event = response.json()
    
    current_time = datetime.now(timezone.utc)
    bookmaker_freshness = {}
    
    for bk in props_event.get("bookmakers", []):
        bkey = bk.get("key", "")
        last_update_str = bk.get("last_update")
        
        if last_update_str:
            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            age_seconds = (current_time - last_update).total_seconds()
            age_minutes = age_seconds / 60
            
            bookmaker_freshness[bkey] = {
                "last_update": last_update_str,
                "age_seconds": int(age_seconds),
                "age_minutes": round(age_minutes, 1),
                "is_fresh": age_seconds < 300
            }
    
    return {
        "event": f"{props_event.get('away_team')} @ {props_event.get('home_team')}",
        "sport": sport_key,
        "current_time": current_time.isoformat(),
        "bookmakers": bookmaker_freshness
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        sport = sys.argv[1]
    else:
        sport = "basketball_nba"
    
    print(f"\nChecking {sport} data freshness...\n")
    
    # Main markets
    display_freshness(sport)
    
    # Props if NFL
    if sport == "americanfootball_nfl":
        print("\nChecking NFL player props data freshness...\n")
        result = check_player_props_freshness(sport)
        if "error" not in result:
            print(f"Event: {result['event']}")
            print(f"\nPlayer Props Bookmakers:")
            for bkey, info in result['bookmakers'].items():
                print(f"  {bkey}: {info['age_minutes']} min old")
    
    # Check specific bookmaker
    print("\n" + "="*80)
    check_specific_bookmaker(sport, "ladbrokes_au")
    print("="*80)

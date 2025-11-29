"""
Check all available markets for NBA from The Odds API
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ODDS_API_KEY')

# First, get all available markets for basketball_nba
url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/odds'
params = {
    'apiKey': api_key,
    'regions': 'au,us',
    'markets': 'h2h',  # Start with h2h to see what's available
    'oddsFormat': 'decimal'
}

print("Fetching available markets for NBA from The Odds API...")
print("=" * 80)

# Get one event to see structure
response = requests.get(url, params=params)
events = response.json()

if events and len(events) > 0:
    event = events[0]
    print(f"\nSample Event: {event.get('away_team')} @ {event.get('home_team')}")
    print(f"Event ID: {event.get('id')}")
    
    # Check available markets by trying different market keys
    all_markets = [
        # Main markets
        'h2h', 'spreads', 'totals',
        
        # Player props - Points
        'player_points', 'player_points_over_under', 'player_points_alternate',
        
        # Player props - Rebounds
        'player_rebounds', 'player_rebounds_over_under', 'player_rebounds_alternate',
        
        # Player props - Assists
        'player_assists', 'player_assists_over_under', 'player_assists_alternate',
        
        # Player props - Threes
        'player_threes', 'player_threes_over_under', 'player_three_point_field_goals_made',
        
        # Player props - Blocks/Steals
        'player_blocks', 'player_steals', 'player_blocks_steals',
        
        # Player props - Combos
        'player_points_rebounds_assists', 'player_points_rebounds',
        'player_points_assists', 'player_rebounds_assists',
        
        # Player props - Special
        'player_double_double', 'player_triple_double',
        'player_first_basket', 'player_first_field_goal',
        'anytime_first_basket',
        
        # Team props
        'team_totals', 'team_points',
        
        # Quarters/Halves
        'h2h_q1', 'h2h_q2', 'h2h_q3', 'h2h_q4',
        'h2h_h1', 'h2h_h2',
        'totals_q1', 'totals_q2', 'totals_q3', 'totals_q4',
        'totals_h1', 'totals_h2',
        'spreads_q1', 'spreads_q2', 'spreads_q3', 'spreads_q4',
        'spreads_h1', 'spreads_h2'
    ]
    
    print(f"\n\nChecking {len(all_markets)} possible markets...")
    print("=" * 80)
    
    available_markets = []
    
    for market in all_markets:
        test_params = {
            'apiKey': api_key,
            'regions': 'au,us',
            'markets': market,
            'oddsFormat': 'decimal'
        }
        
        test_response = requests.get(url, params=test_params)
        
        if test_response.status_code == 200:
            test_data = test_response.json()
            
            # Check if market has data
            if test_data and len(test_data) > 0:
                first_event = test_data[0]
                bookmakers = first_event.get('bookmakers', [])
                
                if bookmakers and len(bookmakers) > 0:
                    markets_data = bookmakers[0].get('markets', [])
                    
                    if markets_data and len(markets_data) > 0:
                        available_markets.append(market)
                        num_bookmakers = len(bookmakers)
                        num_outcomes = len(markets_data[0].get('outcomes', []))
                        print(f"✓ {market:40s} - {num_bookmakers} bookmakers, {num_outcomes} outcomes")
                        continue
        
        # If we get here, market not available
        # print(f"✗ {market:40s} - Not available")
    
    print("\n" + "=" * 80)
    print(f"\nAVAILABLE MARKETS ({len(available_markets)}):")
    print("=" * 80)
    for market in available_markets:
        print(f"  - {market}")
    
    print(f"\n\nAPI Requests remaining: {response.headers.get('x-requests-remaining', 'Unknown')}")
    print(f"Note: We used ~{len(all_markets)} requests to check all markets")

else:
    print("No events found!")

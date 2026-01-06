import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

# Get one event to see what bookmakers are available
url = "https://api.the-odds-api.com/v4/sports/basketball_nba/events"
params = {
    'apiKey': ODDS_API_KEY,
    'regions': 'au,us,us2,eu'
}

response = requests.get(url, params=params)
data = response.json()

if data and len(data) > 0:
    event = data[0]
    print(f"Event: {event['home_team']} @ {event['away_team']}\n")
    print("Available Bookmakers:")
    
    bookmakers = event.get('bookmakers', [])
    for bm in bookmakers:
        print(f"  - {bm['key']}")

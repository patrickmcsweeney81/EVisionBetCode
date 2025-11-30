#!/usr/bin/env python3

import requests
import os
import csv

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# AU bookies to check
AU_BOOKIES = [
    "sportsbet", "tab", "neds", "ladbrokes_au", "pointsbetau", "boombet", "betright", "playup", "unibet", "tabtouch", "dabble_au", "betr_au", "bet365_au"
]

# Markets to check
MARKETS = ["spreads", "totals"]

# Sports to check
SPORTS = ['americanfootball_nfl', 'basketball_nba', 'icehockey_nhl']

def check_coverage():
    with open("data/missing_bookies_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sport", "event", "market", "missing_bookies"])
        for sport in SPORTS:
            print(f"\n{'='*60}")
            print(f"Sport: {sport}")
            print(f"{'='*60}")
            resp = requests.get(
                f'https://api.the-odds-api.com/v4/sports/{sport}/odds',
                params={
                    'apiKey': ODDS_API_KEY,
                    'regions': 'au',
                    'markets': ','.join(MARKETS),
                    'oddsFormat': 'decimal'
                },
                timeout=15
            )
            events = resp.json()
            if not events or len(events) == 0:
                print("No events found")
                continue
            for e in events:
                event_name = e.get('home_team', '') + ' vs ' + e.get('away_team', '')
                for market in e.get('bookmakers', []):
                    present = [b['key'] for b in e.get('bookmakers', [])]
                    missing = [b for b in AU_BOOKIES if b not in present]
                    if missing:
                        writer.writerow([sport, event_name, market.get('key', ''), ','.join(missing)])
            print(f"Checked {len(events)} events for {sport}.")
    print("\nCoverage check complete. See data/missing_bookies_log.csv.")

if __name__ == "__main__":
    check_coverage()

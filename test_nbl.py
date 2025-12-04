import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ODDS_API_KEY')
url = 'https://api.the-odds-api.com/v4/sports'
params = {'apiKey': api_key}
r = requests.get(url, params=params).json()

print("Available sports with 'basketball' in key:")
for sport in r:
    if 'basketball' in sport['key']:
        print(f"  {sport['key']} - Active: {sport['active']}")

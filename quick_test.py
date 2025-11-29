from ev_arb_bot import fetch_h2h_events

e = fetch_h2h_events('americanfootball_nfl')[0]
print(f"Event: {e['home_team']} vs {e['away_team']}")
print(f"Bookmakers: {len(e['bookmakers'])}\n")

bk = e['bookmakers'][0]
print(f"First bookmaker: {bk['key']}")

h2h = next((m for m in bk['markets'] if m['key']=='h2h'), None)
if h2h:
    print(f"H2H outcomes: {len(h2h['outcomes'])}")
    for o in h2h['outcomes']:
        print(f"  {o['name']}: ${o['price']}")

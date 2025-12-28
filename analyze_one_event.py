import pandas as pd

csv = 'data/v3/extracts/basketball_nba_raw_20251228_110850.csv'
df = pd.read_csv(csv)

# Get first event
first_event_id = df['event_id'].iloc[0]
first_event = df[df['event_id'] == first_event_id].copy()

print(f"EVENT: {first_event['event_name'].iloc[0]}")
print(f"Event ID: {first_event_id}")
print(f"Start Time: {first_event['commence_time'].iloc[0]}")
print(f"\n{'='*100}")

# Show spreads
spreads = first_event[first_event['market_type'] == 'spread']
print(f"\nSPREADS ({len(spreads)} rows):")
print("-" * 100)
for idx, row in spreads.iterrows():
    selection = row['selection']
    point = row['point']
    print(f"\n{selection.upper()} @ {point}")
    # Show first 5 bookmakers
    bookmakers = df.columns[8:]
    odds_sample = []
    for book in list(bookmakers)[:10]:
        odd = row[book]
        if pd.notna(odd):
            odds_sample.append(f"{book}: {odd}")
    print("  " + " | ".join(odds_sample))

# Show totals
totals = first_event[first_event['market_type'] == 'totals']
print(f"\n{'='*100}\nTOTALS ({len(totals)} rows):")
print("-" * 100)
for idx, row in totals.iterrows():
    selection = row['selection']
    point = row['point']
    print(f"\n{selection.upper()} @ {point}")
    # Show first 5 bookmakers
    bookmakers = df.columns[8:]
    odds_sample = []
    for book in list(bookmakers)[:10]:
        odd = row[book]
        if pd.notna(odd):
            odds_sample.append(f"{book}: {odd}")
    print("  " + " | ".join(odds_sample))

# Show h2h
h2h = first_event[first_event['market_type'] == 'h2h']
print(f"\n{'='*100}\nH2H ({len(h2h)} rows):")
print("-" * 100)
for idx, row in h2h.iterrows():
    selection = row['selection']
    print(f"\n{selection.upper()}")
    # Show first 5 bookmakers
    bookmakers = df.columns[8:]
    odds_sample = []
    for book in list(bookmakers)[:10]:
        odd = row[book]
        if pd.notna(odd):
            odds_sample.append(f"{book}: {odd}")
    print("  " + " | ".join(odds_sample))

print(f"\n{'='*100}")
print("\nKEY OBSERVATIONS:")
print("1. Each (market, selection, point) is a separate row")
print("2. Same bookmakers across all rows (allows direct comparison)")
print("3. NaN values where book doesn't offer that line")
print("4. Odds are in decimal format (need conversion for US display)")

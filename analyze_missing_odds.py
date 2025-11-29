import csv
from pathlib import Path

csv_path = Path("data/all_odds_analysis.csv")

if not csv_path.exists():
    print("all_odds_analysis.csv not found")
    exit(1)

rows = list(csv.DictReader(open(csv_path)))
print(f"Total rows analyzed: {len(rows)}\n")

# Bookmaker columns to analyze
au_books = ['pinnacle', 'betfair', 'sportsbet', 'tab', 'neds', 'ladbrokes_au', 
            'pointsbetau', 'boombet', 'betright', 'playup', 'unibet', 'tabtouch', 
            'dabble_au', 'betr_au', 'bet365_au']

print("=" * 70)
print("BOOKMAKER COVERAGE ANALYSIS")
print("=" * 70)

coverage_data = []
for book in au_books:
    filled = sum(1 for r in rows if r.get(book, '').strip())
    empty = len(rows) - filled
    pct = (filled / len(rows) * 100) if len(rows) > 0 else 0
    coverage_data.append((book, filled, empty, pct))
    print(f"{book:15} {filled:3}/{len(rows)} ({pct:5.1f}%) | Missing: {empty:3} rows")

print("\n" + "=" * 70)
print("MISSING VALUE PATTERNS BY MARKET")
print("=" * 70)

# Analyze by market type
markets = {}
for row in rows:
    market = row.get('market', 'unknown')
    if market not in markets:
        markets[market] = []
    markets[market].append(row)

for market, market_rows in markets.items():
    print(f"\n{market.upper()} ({len(market_rows)} rows):")
    for book in ['pinnacle', 'betfair', 'sportsbet', 'tab']:  # Sample books
        filled = sum(1 for r in market_rows if r.get(book, '').strip())
        pct = (filled / len(market_rows) * 100) if len(market_rows) > 0 else 0
        print(f"  {book:15} {filled:3}/{len(market_rows)} ({pct:5.1f}%)")

print("\n" + "=" * 70)
print("SAMPLE ROWS WITH MISSING ODDS")
print("=" * 70)

# Find rows where multiple bookmakers are missing
for i, row in enumerate(rows[:10]):
    missing_books = [book for book in au_books if not row.get(book, '').strip()]
    if len(missing_books) > 5:
        print(f"\nRow {i+1}: {row['event']} - {row['market']} - {row['selection']}")
        print(f"  Bookmaker: {row['bookmaker']}")
        print(f"  Missing {len(missing_books)} books: {', '.join(missing_books[:5])}...")
        print(f"  Fair: {row.get('Fair', 'N/A')}, Book: {row.get('Book', 'N/A')}")

print("\n" + "=" * 70)
print("ROOT CAUSE ANALYSIS")
print("=" * 70)

# Check if rows where bookmaker == column name have odds
print("\nChecking if bookmaker column contains its own odds:")
for book in ['sportsbet', 'tab', 'neds', 'pointsbetau']:
    matching_rows = [r for r in rows if r.get('bookmaker') == book]
    if matching_rows:
        has_own_odds = sum(1 for r in matching_rows if r.get(book, '').strip())
        print(f"  {book:15} {has_own_odds:3}/{len(matching_rows)} rows have odds in their own column")

# Check for spreads/totals with different points
print("\nChecking market-specific patterns:")
spreads = [r for r in rows if 'spreads' in r.get('market', '')]
totals = [r for r in rows if 'totals' in r.get('market', '')]
h2h = [r for r in rows if r.get('market') == 'h2h']

print(f"  h2h markets: {len(h2h)} rows")
print(f"  spreads markets: {len(spreads)} rows")
print(f"  totals markets: {len(totals)} rows")

if spreads:
    unique_spreads = set(r.get('market') for r in spreads)
    print(f"  Unique spread lines: {len(unique_spreads)} ({', '.join(list(unique_spreads)[:3])}...)")
    
if totals:
    unique_totals = set(r.get('market') for r in totals)
    print(f"  Unique total lines: {len(unique_totals)} ({', '.join(list(unique_totals)[:3])}...)")

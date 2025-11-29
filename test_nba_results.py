import csv
from pathlib import Path

csv_path = Path("data/all_odds_analysis.csv")
rows = list(csv.DictReader(open(csv_path)))

print("=" * 70)
print("NBA H2H TEST RESULTS")
print("=" * 70)

print(f"\nTotal rows: {len(rows)}")
print(f"Columns: {len(rows[0].keys())}")

# Check for NumSharps column
has_numsharps = 'NumSharps' in rows[0].keys()
print(f"\nNumSharps column exists: {has_numsharps}")

if has_numsharps:
    numsharps_populated = sum(1 for r in rows if r.get('NumSharps', '').strip())
    print(f"NumSharps populated: {numsharps_populated}/{len(rows)} ({numsharps_populated/len(rows)*100:.1f}%)")
    
    # Show distribution
    ns_values = [r.get('NumSharps', '').strip() for r in rows if r.get('NumSharps', '').strip()]
    if ns_values:
        from collections import Counter
        counts = Counter(ns_values)
        print(f"\nNumSharps distribution:")
        for val in sorted(counts.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            print(f"  {val} sharps: {counts[val]} rows")

# Check Betfair coverage
betfair_populated = sum(1 for r in rows if r.get('betfair', '').strip())
print(f"\nBetfair coverage: {betfair_populated}/{len(rows)} ({betfair_populated/len(rows)*100:.1f}%)")

# Check Pinnacle coverage
pinnacle_populated = sum(1 for r in rows if r.get('pinnacle', '').strip())
print(f"Pinnacle coverage: {pinnacle_populated}/{len(rows)} ({pinnacle_populated/len(rows)*100:.1f}%)")

# Sample rows
print("\n" + "=" * 70)
print("SAMPLE ROWS")
print("=" * 70)

# Row with Betfair
print("\nRow WITH Betfair:")
sample = next((r for r in rows if r.get('betfair', '').strip()), None)
if sample:
    print(f"  Event: {sample['event']}")
    print(f"  Market: {sample['market']}")
    print(f"  Selection: {sample['selection']}")
    print(f"  Bookmaker: {sample['bookmaker']}")
    print(f"  Book odds: {sample['Book']}")
    print(f"  Fair odds: {sample['Fair']}")
    print(f"  EV%: {sample['EV%']}")
    print(f"  Pinnacle: {sample.get('pinnacle', 'N/A')}")
    print(f"  Betfair: {sample.get('betfair', 'N/A')}")
    print(f"  NumSharps: {sample.get('NumSharps', 'N/A')}")
else:
    print("  No rows with Betfair found")

# Row without Betfair
print("\nRow WITHOUT Betfair:")
sample2 = next((r for r in rows if not r.get('betfair', '').strip()), None)
if sample2:
    print(f"  Event: {sample2['event']}")
    print(f"  Market: {sample2['market']}")
    print(f"  Selection: {sample2['selection']}")
    print(f"  Bookmaker: {sample2['bookmaker']}")
    print(f"  Book odds: {sample2['Book']}")
    print(f"  Fair odds: {sample2['Fair']}")
    print(f"  EV%: {sample2['EV%']}")
    print(f"  Pinnacle: {sample2.get('pinnacle', 'N/A')}")
    print(f"  Betfair: {sample2.get('betfair', 'N/A')}")
    print(f"  NumSharps: {sample2.get('NumSharps', 'N/A')}")

# Check h2h market coverage
h2h_rows = [r for r in rows if r.get('market') == 'h2h']
print(f"\n" + "=" * 70)
print(f"H2H MARKET COVERAGE (Total: {len(h2h_rows)} rows)")
print("=" * 70)

if h2h_rows:
    h2h_betfair = sum(1 for r in h2h_rows if r.get('betfair', '').strip())
    h2h_pinnacle = sum(1 for r in h2h_rows if r.get('pinnacle', '').strip())
    h2h_fair = sum(1 for r in h2h_rows if r.get('Fair', '').strip())
    
    print(f"Pinnacle: {h2h_pinnacle}/{len(h2h_rows)} ({h2h_pinnacle/len(h2h_rows)*100:.1f}%)")
    print(f"Betfair: {h2h_betfair}/{len(h2h_rows)} ({h2h_betfair/len(h2h_rows)*100:.1f}%)")
    print(f"Fair price calculated: {h2h_fair}/{len(h2h_rows)} ({h2h_fair/len(h2h_rows)*100:.1f}%)")

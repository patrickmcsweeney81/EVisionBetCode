import csv

# Read filtered hits
filtered = list(csv.DictReader(open('data/hits_ev_filtered.csv')))

print("=" * 80)
print("COMPARISON: Console EV Output vs Filtered Hits")
print("=" * 80)

print("\n=== CONSOLE OUTPUT FROM BOT (last run) ===")
console_hits = [
    "sportsbet, unibet    Josh Giddey          U 1.5 1.800 (fair=1.711, edge=5.2%, stake=$15)",
    "betright            Cooper Flagg         O 4.5 2.400 (fair=2.309, edge=3.9%, stake=$5)",
    "tab                 Vincent Williams Jr  U 6.5 1.850 (fair=1.722, edge=7.4%, stake=$20)",
    "dabble_au           Naji Marshall        U 4.5 2.050 (fair=1.979, edge=3.6%, stake=$10)",
    "betright            Nikola Jokic         U10.5 1.950 (fair=1.871, edge=4.2%, stake=$10)",
    "ladbrokes_au        Peyton Watson        U12.5 1.900 (fair=1.730, edge=9.8%, stake=$25)"
]

for hit in console_hits:
    print(f"  {hit}")

print("\n=== FILTERED HITS (from filter_ev_hits.py) ===")
print(f"Total: {len(filtered)} hits")
print()

for r in filtered:
    print(f"  {r['bookmaker']:20} {r['selection']:30} {r['market']:15} Book:{r['Book']:7} Fair:{r['Fair']:7} EV:{r['EV%']:7} Prob:{r['Prob']:7}")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

console_count = len(console_hits)
filter_count = len(filtered)

print(f"\nConsole hits: {console_count}")
print(f"Filtered hits: {filter_count}")
print(f"Difference: {console_count - filter_count}")

if console_count != filter_count:
    print("\n⚠️  MISMATCH - Console output shows MORE hits than filter!")
    print("\nPossible reasons:")
    print("  1. Console uses old EV calculation (book odds based)")
    print("  2. Console uses different thresholds")
    print("  3. Console doesn't apply max-edge or bookmaker combining")
    print("  4. Some console hits below 3% EV or 40% prob threshold")
    
    # Check which console hits might be filtered out
    print("\nChecking console hits:")
    for hit in console_hits:
        # Extract edge from console output
        if "edge=" in hit:
            edge_str = hit.split("edge=")[1].split("%")[0]
            edge = float(edge_str)
            player = hit.split("(")[0].strip().split()[-1]
            
            if edge < 3.0:
                print(f"  ❌ {player}: {edge:.1f}% edge < 3% threshold")
            else:
                print(f"  ✅ {player}: {edge:.1f}% edge >= 3% threshold")
else:
    print("\n✅ MATCH - Console and filtered counts are equal")

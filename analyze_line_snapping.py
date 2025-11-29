import csv
from pathlib import Path
from collections import defaultdict

csv_path = Path("data/all_odds_analysis.csv")
rows = list(csv.DictReader(open(csv_path)))

print("=" * 80)
print("SPREAD/TOTAL LINE SNAPPING SAFETY ANALYSIS")
print("=" * 80)

# Analyze spreads
spreads = [r for r in rows if 'spreads' in r.get('market', '')]
totals = [r for r in rows if 'totals' in r.get('market', '')]

# Group by event and extract lines
spread_lines_by_event = defaultdict(set)
total_lines_by_event = defaultdict(set)

for row in spreads:
    event = row['event']
    market = row['market']
    line = float(market.split('_')[1]) if '_' in market else 0
    spread_lines_by_event[event].add(line)

for row in totals:
    event = row['event']
    market = row['market']
    line = float(market.split('_')[1]) if '_' in market else 0
    total_lines_by_event[event].add(line)

print("\nSPREAD LINE ANALYSIS")
print("=" * 80)

spread_gaps = []
for event, lines in spread_lines_by_event.items():
    sorted_lines = sorted(lines)
    if len(sorted_lines) > 1:
        for i in range(len(sorted_lines) - 1):
            gap = sorted_lines[i+1] - sorted_lines[i]
            spread_gaps.append(gap)
            if gap <= 1.0:  # Show small gaps
                print(f"{event[:50]:50} | Lines: {sorted_lines} | Gap: {gap}")

if spread_gaps:
    print(f"\nSpread gap statistics:")
    print(f"  Min gap: {min(spread_gaps):.1f}")
    print(f"  Max gap: {max(spread_gaps):.1f}")
    print(f"  Average gap: {sum(spread_gaps)/len(spread_gaps):.2f}")
    print(f"  Gaps <= 0.5: {sum(1 for g in spread_gaps if g <= 0.5)} / {len(spread_gaps)}")
    print(f"  Gaps == 0.5: {sum(1 for g in spread_gaps if g == 0.5)} / {len(spread_gaps)}")
    print(f"  Gaps == 1.0: {sum(1 for g in spread_gaps if g == 1.0)} / {len(spread_gaps)}")

print("\n" + "=" * 80)
print("TOTAL LINE ANALYSIS")
print("=" * 80)

total_gaps = []
for event, lines in total_lines_by_event.items():
    sorted_lines = sorted(lines)
    if len(sorted_lines) > 1:
        for i in range(len(sorted_lines) - 1):
            gap = sorted_lines[i+1] - sorted_lines[i]
            total_gaps.append(gap)
            if gap <= 2.0:  # Show small gaps
                print(f"{event[:50]:50} | Lines: {sorted_lines} | Gap: {gap}")

if total_gaps:
    print(f"\nTotal gap statistics:")
    print(f"  Min gap: {min(total_gaps):.1f}")
    print(f"  Max gap: {max(total_gaps):.1f}")
    print(f"  Average gap: {sum(total_gaps)/len(total_gaps):.2f}")
    print(f"  Gaps <= 0.5: {sum(1 for g in total_gaps if g <= 0.5)} / {len(total_gaps)}")
    print(f"  Gaps == 0.5: {sum(1 for g in total_gaps if g == 0.5)} / {len(total_gaps)}")
    print(f"  Gaps == 1.0: {sum(1 for g in total_gaps if g == 1.0)} / {len(total_gaps)}")

print("\n" + "=" * 80)
print("ODDS DEVIATION ANALYSIS (Same Event, Different Lines)")
print("=" * 80)

# For spreads: Compare odds when lines differ by 0.5
print("\nSPREADS - Odds change when line differs by 0.5:")
for event, lines in spread_lines_by_event.items():
    sorted_lines = sorted(lines)
    for i in range(len(sorted_lines) - 1):
        line1, line2 = sorted_lines[i], sorted_lines[i+1]
        if abs(line2 - line1) == 0.5:
            # Get odds for both lines
            rows1 = [r for r in spreads if r['event'] == event and f'_{line1}' in r['market']]
            rows2 = [r for r in spreads if r['event'] == event and f'_{line2}' in r['market']]
            
            if rows1 and rows2:
                # Get average odds for each line
                odds1 = [float(r['Book']) for r in rows1 if r['Book']]
                odds2 = [float(r['Book']) for r in rows2 if r['Book']]
                
                if odds1 and odds2:
                    avg1 = sum(odds1) / len(odds1)
                    avg2 = sum(odds2) / len(odds2)
                    diff = abs(avg1 - avg2)
                    pct_diff = (diff / avg1) * 100
                    
                    print(f"{event[:40]:40} | {line1:4.1f} → {line2:4.1f} | "
                          f"Odds: {avg1:.3f} → {avg2:.3f} | "
                          f"Diff: {diff:.3f} ({pct_diff:.1f}%)")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

# Calculate safety metrics
safe_spread_snap = all(g >= 0.5 for g in spread_gaps) if spread_gaps else True
safe_total_snap = all(g >= 0.5 for g in total_gaps) if total_gaps else True

print("\nSnapping to nearest 0.5 safety:")
print(f"  Spreads: {'✅ SAFE' if safe_spread_snap else '⚠️ RISKY'}")
print(f"  Totals: {'✅ SAFE' if safe_total_snap else '⚠️ RISKY'}")

if spread_gaps:
    min_spread_gap = min(spread_gaps)
    if min_spread_gap >= 1.0:
        print(f"\n✅ SPREADS: Min gap is {min_spread_gap:.1f} - safe to snap ±0.5")
    elif min_spread_gap >= 0.5:
        print(f"\n⚠️ SPREADS: Min gap is {min_spread_gap:.1f} - snapping ±0.5 may collide")
    else:
        print(f"\n❌ SPREADS: Min gap is {min_spread_gap:.1f} - DO NOT snap ±0.5")

if total_gaps:
    min_total_gap = min(total_gaps)
    if min_total_gap >= 1.0:
        print(f"\n✅ TOTALS: Min gap is {min_total_gap:.1f} - safe to snap ±0.5")
    elif min_total_gap >= 0.5:
        print(f"\n⚠️ TOTALS: Min gap is {min_total_gap:.1f} - snapping ±0.5 may collide")
    else:
        print(f"\n❌ TOTALS: Min gap is {min_total_gap:.1f} - DO NOT snap ±0.5")

import csv
from pathlib import Path

csv_path = Path("data/all_odds_analysis.csv")
rows = list(csv.DictReader(open(csv_path)))

spreads = [r for r in rows if 'spreads' in r.get('market', '')]
totals = [r for r in rows if 'totals' in r.get('market', '')]

# Extract line values
spread_lines = [float(s['market'].split('_')[1]) for s in spreads if '_' in s['market']]
total_lines = [float(t['market'].split('_')[1]) for t in totals if '_' in t['market']]

# Categorize
spread_whole = [l for l in spread_lines if l % 1 == 0]  # X.0
spread_half = [l for l in spread_lines if l % 1 == 0.5]  # X.5
total_whole = [l for l in total_lines if l % 1 == 0]  # X.0
total_half = [l for l in total_lines if l % 1 == 0.5]  # X.5

print("=" * 70)
print("WHOLE NUMBER vs HALF POINT ANALYSIS")
print("=" * 70)

print("\nSPREADS:")
print(f"  Whole numbers (X.0): {len(spread_whole):3}/{len(spread_lines)} ({len(spread_whole)/len(spread_lines)*100:5.1f}%)")
print(f"  Half points (X.5):   {len(spread_half):3}/{len(spread_lines)} ({len(spread_half)/len(spread_lines)*100:5.1f}%)")
print(f"  Unique whole spreads: {sorted(set([l for l in spread_lines if l % 1 == 0]))}")
print(f"  Unique half spreads:  {sorted(set([l for l in spread_lines if l % 1 == 0.5]))}")

print("\nTOTALS:")
print(f"  Whole numbers (X.0): {len(total_whole):3}/{len(total_lines)} ({len(total_whole)/len(total_lines)*100:5.1f}%)")
print(f"  Half points (X.5):   {len(total_half):3}/{len(total_lines)} ({len(total_half)/len(total_lines)*100:5.1f}%)")
print(f"  Unique whole totals: {sorted(set([l for l in total_lines if l % 1 == 0]))}")
print(f"  Unique half totals:  {sorted(set([l for l in total_lines if l % 1 == 0.5]))}")

print("\n" + "=" * 70)
print("SNAPPING TO WHOLE NUMBERS - COLLISION ANALYSIS")
print("=" * 70)

# Check if snapping to whole numbers would cause collisions
unique_spreads = sorted(set(spread_lines))
unique_totals = sorted(set(total_lines))

print("\nSPREADS - Would snapping X.5 UP to (X+1).0 cause collisions?")
collisions = 0
for line in unique_spreads:
    if line % 1 == 0.5:  # Half point
        target = int(line) + 1  # Round up to next whole
        if target in unique_spreads:
            print(f"  COLLISION: {line} would snap to {target}.0, but {target}.0 already exists!")
            collisions += 1
        else:
            print(f"  SAFE: {line} -> {target}.0 (no existing line)")

if collisions == 0:
    print("  No collisions detected for spreads!")

print("\nTOTALS - Would snapping X.5 UP to (X+1).0 cause collisions?")
collisions = 0
for line in unique_totals:
    if line % 1 == 0.5:  # Half point
        target = int(line) + 1  # Round up to next whole
        if target in unique_totals:
            print(f"  COLLISION: {line} would snap to {target}.0, but {target}.0 already exists!")
            collisions += 1
        else:
            print(f"  SAFE: {line} -> {target}.0 (no existing line)")

if collisions == 0:
    print("  No collisions detected for totals!")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)

print("\nSnapping X.5 UP to next whole number (X+1).0:")

# Check if any whole numbers would be affected
spread_wholes = set([l for l in unique_spreads if l % 1 == 0])
total_wholes = set([l for l in unique_totals if l % 1 == 0])

spread_safe = True
for half in unique_spreads:
    if half % 1 == 0.5:
        if (int(half) + 1) in spread_wholes:
            spread_safe = False
            break

total_safe = True  
for half in unique_totals:
    if half % 1 == 0.5:
        if (int(half) + 1) in total_wholes:
            total_safe = False
            break

if spread_safe:
    print("  SPREADS: SAFE - no collisions")
else:
    print("  SPREADS: UNSAFE - would cause collisions")
    
if total_safe:
    print("  TOTALS: SAFE - no collisions")
else:
    print("  TOTALS: UNSAFE - would cause collisions")

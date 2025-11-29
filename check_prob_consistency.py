import csv
from pathlib import Path

csv_path = Path("data/all_odds_analysis.csv")
rows = list(csv.DictReader(open(csv_path)))

# Find Orlando Magic h2h bets
orlando = [r for r in rows if 'Orlando' in r.get('event', '') and r.get('market') == 'h2h' and 'Orlando' in r.get('selection', '')]

print("=" * 80)
print("ORLANDO MAGIC H2H - PROBABILITY CONSISTENCY CHECK")
print("=" * 80)
print(f"\nBookmaker         Book    Fair    EV%      Prob     NumSharps")
print("-" * 80)

for r in orlando[:15]:
    print(f"{r['bookmaker']:15} {r['Book']:7} {r['Fair']:7} {r['EV%']:8} {r['Prob']:8} {r.get('NumSharps', 'N/A'):^10}")

# Check if all probs are the same
probs = [r['Prob'] for r in orlando if r['Prob']]
unique_probs = set(probs)

print("\n" + "=" * 80)
print("RESULT:")
print("=" * 80)
if len(unique_probs) == 1:
    print(f"✓ ALL PROBABILITIES ARE CONSISTENT: {list(unique_probs)[0]}")
else:
    print(f"✗ INCONSISTENT PROBABILITIES FOUND: {unique_probs}")
    print(f"  This is WRONG - all should show the same prob based on fair odds!")

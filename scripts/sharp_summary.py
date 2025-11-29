import csv
from collections import Counter, defaultdict
from pathlib import Path

CSV = Path(r"c:\EV_ARB Bot VSCode\data\sharp_presence.csv")
if not CSV.exists():
    print("ERROR: sharp_presence.csv not found at", CSV)
    raise SystemExit(1)

min_sharp_required = 4

rows = []
with CSV.open('r', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for r in reader:
        # normalize numeric fields
        try:
            r['pinnacle_present'] = int(r.get('pinnacle_present') or 0)
        except:
            r['pinnacle_present'] = 0
        try:
            r['betfair_present'] = int(r.get('betfair_present') or 0)
        except:
            r['betfair_present'] = 0
        try:
            r['sharp_count_A'] = int(r.get('sharp_count_A') or 0)
        except:
            r['sharp_count_A'] = 0
        try:
            r['sharp_count_B'] = int(r.get('sharp_count_B') or 0)
        except:
            r['sharp_count_B'] = 0
        rows.append(r)

total = len(rows)
if total == 0:
    print('No rows in sharp_presence.csv')
    raise SystemExit(0)

pinnacle_rows = sum(1 for r in rows if r['pinnacle_present']>0)
betfair_rows = sum(1 for r in rows if r['betfair_present']>0)

sharpA_counts = Counter(r['sharp_count_A'] for r in rows)
sharpB_counts = Counter(r['sharp_count_B'] for r in rows)

sharpA_ge_min = sum(1 for r in rows if r['sharp_count_A'] >= min_sharp_required)
sharpB_ge_min = sum(1 for r in rows if r['sharp_count_B'] >= min_sharp_required)

either_sharp = sum(1 for r in rows if (r['sharp_count_A']>0 or r['sharp_count_B']>0))

print(f"Total target lines in sharp_presence.csv: {total}")
print(f"Pinnacle present on line (either side): {pinnacle_rows} ({pinnacle_rows/total:.1%})")
print(f"Betfair present on line (either side):   {betfair_rows} ({betfair_rows/total:.1%})")
print()
print(f"Sharp book counts (A side): {dict(sharpA_counts)}")
print(f"Sharp book counts (B side): {dict(sharpB_counts)}")
print()
print(f"Lines with >= {min_sharp_required} sharps on A side: {sharpA_ge_min} ({sharpA_ge_min/total:.1%})")
print(f"Lines with >= {min_sharp_required} sharps on B side: {sharpB_ge_min} ({sharpB_ge_min/total:.1%})")
print(f"Lines with any sharp on either side: {either_sharp} ({either_sharp/total:.1%})")

# Top 10 lines with no pinnacles and no sharps
no_pin_no_sharp = [r for r in rows if r['pinnacle_present']==0 and r['sharp_count_A']==0 and r['sharp_count_B']==0]
print('\nExamples (up to 10) of lines with NO Pinnacle and NO Sharps:')
for r in no_pin_no_sharp[:10]:
    print(f" - {r['sport']} | {r['market']} | {r.get('line','')} | {r.get('key_A','')} vs {r.get('key_B','')}")

# Save a lightweight summary to disk next to CSV
out = Path(r"c:\EV_ARB Bot VSCode\data\sharp_presence_summary.txt")
with out.open('w', encoding='utf-8') as fh:
    fh.write(f"Total lines: {total}\n")
    fh.write(f"Pinnacle present (either side): {pinnacle_rows} ({pinnacle_rows/total:.3%})\n")
    fh.write(f"Betfair present (either side): {betfair_rows} ({betfair_rows/total:.3%})\n")
    fh.write(f"Lines with >= {min_sharp_required} sharps on A side: {sharpA_ge_min} ({sharpA_ge_min/total:.3%})\n")
    fh.write(f"Lines with >= {min_sharp_required} sharps on B side: {sharpB_ge_min} ({sharpB_ge_min/total:.3%})\n")
    fh.write(f"Lines with any sharp on either side: {either_sharp} ({either_sharp/total:.3%})\n")

print(f"\nSummary written to: {out}")

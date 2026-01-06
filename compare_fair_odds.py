import numpy as np

# De-vigged probabilities from all 3 sharp books
probs = [0.537234, 0.539683, 0.543767]

print("WITHOUT 20% TRIM (keep all 3 books)")
print("="*60)
print(f"De-vigged probabilities: {probs}")
print(f"Median of all 3: {np.median(probs):.6f}")
print(f"Fair Odds: 1 / {np.median(probs):.6f} = {1/np.median(probs):.4f}")
print(f"Rounded: {round(1/np.median(probs), 2)}")
print()

print("WITH 20% TRIM (current logic)")
print("="*60)
trim_count = max(1, int(len(probs) * 0.2))
trimmed = probs[trim_count:-trim_count] if trim_count > 0 else probs
print(f"Trim count: {trim_count}")
print(f"Trimmed probs: {trimmed}")
print(f"Median of trimmed: {np.median(trimmed):.6f}")
print(f"Fair Odds: 1 / {np.median(trimmed):.6f} = {1/np.median(trimmed):.4f}")
print(f"Rounded: {round(1/np.median(trimmed), 2)}")
print()

# Also show if we only used DraftKings + FanDuel
print("IF WE ONLY USED DRAFTKINGS + FANDUEL (remove BetOnlineAG)")
print("="*60)
two_books = [0.537234, 0.543767]
print(f"Probabilities: {two_books}")
print(f"Median: {np.median(two_books):.6f}")
print(f"Fair Odds: 1 / {np.median(two_books):.6f} = {1/np.median(two_books):.4f}")
print(f"Rounded: {round(1/np.median(two_books), 2)}")

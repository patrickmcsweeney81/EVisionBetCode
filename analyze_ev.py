"""
EV Analysis Script
Reads hits_ev.csv and performs various analysis tasks
"""

import csv
from pathlib import Path
from typing import List, Dict

# Path to CSV files
INPUT_CSV = Path(__file__).parent / "data" / "hits_ev.csv"
OUTPUT_CSV = Path(__file__).parent / "data" / "analysis_output.csv"


def load_ev_data() -> List[Dict[str, str]]:
    """Load all rows from the EV CSV file."""
    if not INPUT_CSV.exists():
        print(f"Error: CSV file not found at {INPUT_CSV}")
        return []
    
    rows = []
    with INPUT_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def sort_by_ev(rows: List[Dict[str, str]], descending: bool = True) -> List[Dict[str, str]]:
    """Sort rows by EV percentage (highest to lowest by default)."""
    def get_ev_value(row: Dict[str, str]) -> float:
        """Extract numeric EV value from percentage string like '3.69%'"""
        ev_str = row.get("EV", "0%")
        try:
            # Remove '%' and convert to float
            return float(ev_str.rstrip('%'))
        except (ValueError, AttributeError):
            return 0.0
    
    return sorted(rows, key=get_ev_value, reverse=descending)


def group_by_best_ev(rows: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """
    Group rows by game+side+line, keeping only the best EV for each.
    If multiple bookmakers offer the same best EV, combine them.
    
    Returns list of grouped entries with format:
    {
        'ev': '9.05%',
        'sport': 'icehockey_nhl',
        'event': 'Colorado Avalanche V Anaheim Ducks',
        'market': 'totals',
        'line': '6.5',
        'side': 'Over',
        'bookmakers': ['unibet', 'tabtouch'],  # All books at best EV
        'prices': ['$2.05', '$2.04'],  # Corresponding prices
        'stake': '$21.55',  # Highest stake
        'game_start_perth': '2025-11-12 10:40:00'
    }
    """
    from collections import defaultdict
    
    # Group by: event + market + line + side
    groups = defaultdict(list)
    
    for row in rows:
        # Create unique key for this bet opportunity
        key = (
            row.get('event', ''),
            row.get('market', ''),
            row.get('line', ''),
            row.get('side', '')
        )
        groups[key].append(row)
    
    # For each group, find the best EV and collect all bookmakers at that EV
    result = []
    for key, group_rows in groups.items():
        # Sort by EV to find best
        sorted_group = sort_by_ev(group_rows, descending=True)
        best_row = sorted_group[0]
        best_ev_value = float(best_row.get('EV', '0%').rstrip('%'))
        
        # Collect all bookmakers with the same best EV (within 0.01% tolerance)
        best_bookmakers = []
        best_prices = []
        best_stake = 0.0
        
        for row in sorted_group:
            ev_value = float(row.get('EV', '0%').rstrip('%'))
            if abs(ev_value - best_ev_value) < 0.01:  # Same EV (tolerance for rounding)
                best_bookmakers.append(row.get('book', 'N/A'))
                best_prices.append(row.get('price', 'N/A'))
                # Track highest stake
                try:
                    stake_val = float(row.get('stake', '$0').lstrip('$'))
                    if stake_val > best_stake:
                        best_stake = stake_val
                except (ValueError, AttributeError):
                    pass
        
        result.append({
            'ev': best_row.get('EV', 'N/A'),
            'sport': best_row.get('sport', 'N/A'),
            'event': best_row.get('event', 'N/A'),
            'market': best_row.get('market', 'N/A'),
            'line': best_row.get('line', ''),
            'side': best_row.get('side', 'N/A'),
            'bookmakers': best_bookmakers,
            'prices': best_prices,
            'stake': f"${best_stake:.2f}" if best_stake > 0 else 'N/A',
            'game_start_perth': best_row.get('game_start_perth', 'N/A')
        })
    
    # Sort result by EV
    return sorted(result, key=lambda x: float(x['ev'].rstrip('%')), reverse=True)


def save_deduplicated_csv(rows: List[Dict[str, str]]):
    """Keep only the best EV per game+side, remove bookmaker columns M-Z, add profit column."""
    if not rows:
        return
    
    # Group by best EV per game+side
    grouped = group_by_best_ev(rows)
    
    # Extract the original rows (first entry from each group has the best EV)
    best_rows = []
    for entry in grouped:
        # Find the original row from rows that matches this entry
        for row in rows:
            if (row['event'] == entry['event'] and 
                row['side'] == entry['side'] and 
                row['EV'] == entry['ev'] and
                row['book'] == entry['bookmakers'][0]):
                
                # Calculate profit: stake × price - stake
                stake_val = float(row['stake'].lstrip('$'))
                price_val = float(row['price'].lstrip('$'))
                profit = stake_val * price_val - stake_val
                
                # Keep only columns up to Fair (remove individual bookmaker columns)
                filtered_row = {
                    'game_start_perth': row['game_start_perth'],
                    'sport': row['sport'],
                    'EV': row['EV'],
                    'event': row['event'],
                    'market': row['market'],
                    'line': row['line'],
                    'side': row['side'],
                    'stake': row['stake'],
                    'book': row['book'],
                    'price': row['price'],
                    'Prob': row['Prob'],
                    'Fair': row['Fair'],
                    'profit': f"${profit:.2f}"
                }
                best_rows.append(filtered_row)
                break
    
    # Save deduplicated data
    if best_rows:
        with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=best_rows[0].keys())
            writer.writeheader()
            writer.writerows(best_rows)
    
    print(f"[info] Analysis output saved: {OUTPUT_CSV}")
    print(f"[info] {len(best_rows)} unique opportunities (from {len(rows)} total hits)")


def display_sorted_ev(limit: int = None):
    """Display EV hits sorted by EV value (highest to lowest), grouped by game."""
    rows = load_ev_data()
    
    if not rows:
        print("No data found.")
        return
    
    # Save deduplicated CSV file
    save_deduplicated_csv(rows)
    
    # Group by best EV per game+side (for display)
    grouped = group_by_best_ev(rows)
    
    # Apply limit if specified
    if limit:
        grouped = grouped[:limit]
    
    print(f"\n{'='*130}")
    print(f"EV HITS SORTED BY VALUE (Highest to Lowest) - Best EV Only Per Game")
    print(f"{'='*130}\n")
    
    # Print header
    print(f"{'EV':<8} {'Sport':<20} {'Event':<45} {'Side':<20} {'Bookmakers':<30}")
    print(f"{'-'*130}")
    
    # Print each grouped entry
    for entry in grouped:
        ev = entry['ev']
        sport = entry['sport'][:19]
        event = entry['event'][:44]
        side = entry['side'][:19]
        
        # Combine bookmakers and prices
        book_info = []
        for book, price in zip(entry['bookmakers'], entry['prices']):
            book_info.append(f"{book}({price})")
        bookmakers_str = ", ".join(book_info)[:29]
        
        print(f"{ev:<8} {sport:<20} {event:<45} {side:<20} {bookmakers_str:<30}")
    
    print(f"\n{'='*130}")
    print(f"Total unique opportunities: {len(grouped)} (from {len(rows)} total hits)")
    print(f"{'='*130}\n")
    
    # Calculate and display summary statistics
    if grouped:
        # Total stake required
        total_stake = sum(float(entry['stake'].lstrip('$')) for entry in grouped if entry['stake'] != 'N/A')
        
        # Average EV
        ev_values = [float(entry['ev'].rstrip('%')) for entry in grouped]
        avg_ev = sum(ev_values) / len(ev_values) if ev_values else 0
        
        # Best bookmaker distribution
        bookmaker_counts = {}
        for entry in grouped:
            for book in entry['bookmakers']:
                bookmaker_counts[book] = bookmaker_counts.get(book, 0) + 1
        
        # Sort bookmakers by count
        top_books = sorted(bookmaker_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"{'='*130}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*130}")
        print(f"Total stake required: ${total_stake:.2f}")
        print(f"Average EV: {avg_ev:.2f}%")
        print(f"Highest EV: {max(ev_values):.2f}%")
        print(f"Lowest EV: {min(ev_values):.2f}%")
        print(f"\nTop Bookmakers:")
        for book, count in top_books[:5]:
            print(f"  {book}: {count} opportunities")
        print(f"{'='*130}\n")


if __name__ == "__main__":
    # Display all hits sorted by EV
    display_sorted_ev()
    
    # Uncomment to show only top 10
    # display_sorted_ev(limit=10)

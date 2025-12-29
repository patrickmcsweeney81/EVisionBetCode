"""
SPREADS/TOTALS: MARKET GROUPING & FAIR ODDS CALCULATION
Correct approach: Each unique (market_type, point, selection) analyzed independently
Based on SPREADS_TOTALS_CORRECT_STRUCTURE.md
"""

import pandas as pd
import statistics
import glob
from pathlib import Path

# Sharp books (3⭐ - 4⭐ rating)
SHARP_BOOKS = ['pinnacle', 'betfair_ex_eu', 'betfair_ex_int']
TARGET_BOOKS = ['fanduel', 'mybookieag', 'matchbook']

def get_latest_csv():
    """Find latest CSV file"""
    files = sorted(glob.glob(r"data/v3/extracts/*.csv"))
    return files[-1] if files else None

def get_bookmaker_columns(df):
    """Get list of all bookmaker columns"""
    metadata = ['event_id', 'extracted_at', 'commence_time', 'league', 'event_name', 'market_type', 'point', 'selection']
    return [col for col in df.columns if col not in metadata]

def process_all_markets(csv_path):
    """
    Load CSV and process each market point independently
    """
    
    df = pd.read_csv(csv_path)
    
    # Filter to spreads and totals
    markets_df = df[df['market_type'].isin(['spreads', 'totals'])].copy()
    
    # Convert point to numeric
    markets_df['point'] = pd.to_numeric(markets_df['point'], errors='coerce')
    
    print(f"\n{'='*80}")
    print(f"MARKET GROUPING & FAIR ODDS CALCULATION")
    print(f"{'='*80}\n")
    
    bookmaker_cols = get_bookmaker_columns(df)
    results = []
    
    # Process each unique market
    for (event_id, market_type, point, selection), group in markets_df.groupby(
        ['event_id', 'market_type', 'point', 'selection']
    ):
        row = group.iloc[0]
        event_name = row['event_name']
        
        # Get all bookmaker odds for this market
        book_odds = []
        for book in bookmaker_cols:
            if book in group.columns:
                odds = group[book].iloc[0]
                if pd.notna(odds) and odds > 0:
                    book_odds.append({'book': book, 'odds': odds})
        
        # Filter to sharp books
        sharp_odds = [bo for bo in book_odds if bo['book'] in SHARP_BOOKS]
        
        # Calculate fair odds only if we have sharp books
        fair_odds = None
        sharp_count = len(sharp_odds)
        
        if sharp_count >= 1:
            odds_values = [bo['odds'] for bo in sharp_odds]
            fair_odds = statistics.mean(odds_values)
        
        # Check target books for value
        for target_book in TARGET_BOOKS:
            target_odds = None
            for bo in book_odds:
                if bo['book'] == target_book:
                    target_odds = bo['odds']
                    break
            
            if target_odds and fair_odds:
                ev_pct = (target_odds / fair_odds) - 1
                
                results.append({
                    'event_name': event_name,
                    'market_type': market_type,
                    'point': point,
                    'selection': selection,
                    'target_book': target_book,
                    'target_odds': target_odds,
                    'fair_odds': fair_odds,
                    'sharp_count': sharp_count,
                    'ev_pct': ev_pct,
                    'total_books': len(book_odds)
                })
    
    # Create results dataframe
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        print("No data to process")
        return
    
    # Summary statistics
    print(f"Total markets analyzed: {len(markets_df)}")
    print(f"Markets with sharp books: {len(results_df['market_type'].unique())}")
    print(f"Opportunities found: {len(results_df)}\n")
    
    # Show by event
    for event_name in results_df['event_name'].unique():
        event_data = results_df[results_df['event_name'] == event_name]
        
        print(f"\n{'─'*80}")
        print(f"📍 {event_name}")
        print(f"{'─'*80}\n")
        
        # Group by market
        for (market_type, point, selection) in event_data[['market_type', 'point', 'selection']].drop_duplicates().values:
            market_data = event_data[
                (event_data['market_type'] == market_type) &
                (event_data['point'] == point) &
                (event_data['selection'] == selection)
            ]
            
            if len(market_data) == 0:
                continue
            
            # Get market details
            first = market_data.iloc[0]
            fair_odds = first['fair_odds']
            sharp_count = first['sharp_count']
            total_books = first['total_books']
            
            print(f"  {market_type.upper():8} {selection:20} @ {point:6.1f}")
            print(f"    Fair odds: {fair_odds:.3f} ({sharp_count} sharp book(s), {total_books} total)")
            
            # Show target books with EV
            for _, row in market_data.iterrows():
                ev_pct = row['ev_pct']
                ev_color = "✅" if ev_pct > 0.03 else "❌" if ev_pct < -0.03 else "⚪"
                print(f"      {ev_color} {row['target_book']:15} @ {row['target_odds']:.3f}  EV: {ev_pct:+6.1%}")
            print()
    
    # Summary by bookmaker
    print(f"\n{'='*80}")
    print(f"BOOKMAKER VALUE SUMMARY")
    print(f"{'='*80}\n")
    
    for book in TARGET_BOOKS:
        book_data = results_df[results_df['target_book'] == book]
        
        if len(book_data) == 0:
            continue
        
        positive_ev = (book_data['ev_pct'] > 0.03).sum()
        negative_ev = (book_data['ev_pct'] < -0.03).sum()
        avg_ev = book_data['ev_pct'].mean()
        
        print(f"{book:15} Positive EV: {positive_ev:2}  Negative EV: {negative_ev:2}  Avg EV: {avg_ev:+6.1%}")
    
    print(f"\n{'='*80}\n")
    
    return results_df

if __name__ == "__main__":
    csv_path = get_latest_csv()
    
    if not csv_path:
        print("❌ No CSV found in data/v3/extracts/")
        exit(1)
    
    print(f"\n📂 Loading: {Path(csv_path).name}")
    
    results = process_all_markets(csv_path)

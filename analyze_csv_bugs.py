"""
CSV Data Quality Analyzer
Identifies bugs and data quality issues in all_odds_analysis.csv
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

def analyze_csv_bugs(csv_path):
    """Comprehensive analysis of CSV data quality issues"""
    
    print("=" * 80)
    print("CSV DATA QUALITY ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing: {csv_path}\n")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    print(f"Total Rows: {len(df):,}")
    print(f"Total Columns: {len(df.columns)}")
    print(f"\nDate Range: {df['Time'].min()} to {df['Time'].max()}")
    print("\n" + "=" * 80)
    
    # Bug 1: Missing Fair Prices
    print("\n🔍 BUG 1: MISSING FAIR PRICES")
    print("-" * 80)
    missing_fair = df[df['Fair'].isna()]
    print(f"Rows with missing Fair price: {len(missing_fair):,} ({len(missing_fair)/len(df)*100:.1f}%)")
    
    if len(missing_fair) > 0:
        print("\nBreakdown by market:")
        market_breakdown = missing_fair.groupby('market').size().sort_values(ascending=False)
        for market, count in market_breakdown.head(10).items():
            print(f"  {market}: {count:,} rows")
    
    # Bug 2: Missing EV% calculations
    print("\n\n🔍 BUG 2: MISSING EV% CALCULATIONS")
    print("-" * 80)
    missing_ev = df[df['EV%'].isna()]
    print(f"Rows with missing EV%: {len(missing_ev):,} ({len(missing_ev)/len(df)*100:.1f}%)")
    
    # Bug 3: NumSharps inconsistency
    print("\n\n🔍 BUG 3: NUM SHARPS INCONSISTENCY")
    print("-" * 80)
    sharps_by_market = df.groupby('market')['NumSharps'].agg(['mean', 'min', 'max', 'std'])
    print(sharps_by_market.round(2))
    
    # Bug 4: h2h_lay markets mixed in
    print("\n\n🔍 BUG 4: H2H_LAY MARKETS DETECTED")
    print("-" * 80)
    lay_markets = df[df['market'].str.contains('_lay', na=False)]
    print(f"Rows with lay markets: {len(lay_markets):,}")
    if len(lay_markets) > 0:
        print("⚠️  WARNING: Lay bets should be analyzed separately!")
        print(f"Unique lay markets: {lay_markets['market'].unique().tolist()}")
    
    # Bug 5: Empty bookmaker columns
    print("\n\n🔍 BUG 5: EMPTY BOOKMAKER COLUMNS")
    print("-" * 80)
    bookmaker_cols = [col for col in df.columns if col not in 
                      ['Time', 'sport', 'event', 'market', 'selection', 'bookmaker', 
                       'Book', 'Fair', 'EV%', 'Prob', 'Stake', 'NumSharps']]
    
    for col in bookmaker_cols:
        non_null = df[col].notna().sum()
        if non_null == 0:
            print(f"  ❌ {col}: COMPLETELY EMPTY")
        elif non_null < len(df) * 0.1:
            print(f"  ⚠️  {col}: {non_null:,} rows ({non_null/len(df)*100:.1f}%) - very sparse")
    
    # Bug 6: Probability math validation
    print("\n\n🔍 BUG 6: PROBABILITY MATH VALIDATION")
    print("-" * 80)
    df_with_fair = df[df['Fair'].notna()].copy()
    if len(df_with_fair) > 0:
        # Convert to numeric, coercing errors to NaN
        df_with_fair['Fair'] = pd.to_numeric(df_with_fair['Fair'], errors='coerce')
        df_with_fair['Prob'] = pd.to_numeric(df_with_fair['Prob'], errors='coerce')
        df_with_fair = df_with_fair[df_with_fair['Fair'].notna() & df_with_fair['Prob'].notna()]
        
        df_with_fair['calculated_prob'] = 1 / df_with_fair['Fair'] * 100
        df_with_fair['prob_diff'] = abs(df_with_fair['Prob'] - df_with_fair['calculated_prob'])
        
        large_errors = df_with_fair[df_with_fair['prob_diff'] > 0.5]
        print(f"Rows with probability errors > 0.5%: {len(large_errors):,}")
        
        if len(large_errors) > 0:
            print("\nSample errors:")
            print(large_errors[['event', 'market', 'Fair', 'Prob', 'calculated_prob', 'prob_diff']].head(5).to_string(index=False))
    
    # Bug 7: Negative EV with positive stakes
    print("\n\n🔍 BUG 7: NEGATIVE EV WITH POSITIVE STAKES")
    print("-" * 80)
    # Convert to numeric
    df['EV%'] = pd.to_numeric(df['EV%'].astype(str).str.replace('%', ''), errors='coerce')
    df['Stake'] = pd.to_numeric(df['Stake'].astype(str).str.replace('$', ''), errors='coerce')
    
    negative_ev_with_stake = df[(df['EV%'] < 0) & (df['Stake'] > 0)]
    print(f"Rows with negative EV but positive stake: {len(negative_ev_with_stake):,}")
    
    if len(negative_ev_with_stake) > 0:
        print("\nSample issues:")
        print(negative_ev_with_stake[['event', 'bookmaker', 'EV%', 'Stake']].head(5).to_string(index=False))
    
    # Bug 8: Duplicate betfair entries
    print("\n\n🔍 BUG 8: BETFAIR DUPLICATE ENTRIES")
    print("-" * 80)
    betfair_bookmakers = df[df['bookmaker'].str.contains('betfair', na=False, case=False)]['bookmaker'].unique()
    print(f"Betfair bookmaker variations found: {list(betfair_bookmakers)}")
    if len(betfair_bookmakers) > 1:
        print("⚠️  WARNING: Multiple Betfair entries may cause fair price calculation issues!")
    
    # Summary statistics
    print("\n\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"\nMarkets analyzed: {df['market'].nunique()}")
    print(f"Bookmakers: {df['bookmaker'].nunique()}")
    print(f"Events: {df['event'].nunique()}")
    print(f"\nAverage EV%: {df['EV%'].mean():.2f}%")
    print(f"Positive EV opportunities: {len(df[df['EV%'] > 0]):,} ({len(df[df['EV%'] > 0])/len(df)*100:.1f}%)")
    print(f"Recommended bets (Stake > 0): {len(df[df['Stake'] > 0]):,}")
    
    # Data quality score
    print("\n\n" + "=" * 80)
    print("DATA QUALITY SCORE")
    print("=" * 80)
    
    issues = 0
    if len(missing_fair) > len(df) * 0.05: issues += 1
    if len(lay_markets) > 0: issues += 1
    if len(negative_ev_with_stake) > 0: issues += 1
    if len(betfair_bookmakers) > 1: issues += 1
    
    quality_score = max(0, 100 - (issues * 15))
    print(f"\nOverall Quality Score: {quality_score}/100")
    
    if quality_score < 70:
        print("❌ POOR - Multiple critical issues detected")
    elif quality_score < 85:
        print("⚠️  FAIR - Some issues need attention")
    else:
        print("✅ GOOD - Minor issues only")
    
    return df

if __name__ == "__main__":
    csv_path = Path("data/all_odds_analysis.csv")
    
    if not csv_path.exists():
        print(f"❌ Error: Could not find {csv_path}")
        print("Make sure you're running this from the project root directory")
    else:
        analyze_csv_bugs(csv_path)
        
        print("\n\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("\n1. Review the issues identified above")
        print("2. Check the core/*.py files that generate this CSV")
        print("3. Focus on fixing missing Fair price calculations first")
        print("4. Consider separating h2h_lay markets into different analysis")
        print("\nPress any key to exit...")

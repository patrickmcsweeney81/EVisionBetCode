"""
Filter EV Hits - Apply thresholds and max-edge logic to all_odds_analysis.csv

This script reads the comprehensive all_odds_analysis.csv (which contains EVERY opportunity)
and applies filtering logic to produce the final hits_ev.csv with only qualifying bets.

Benefits:
- Test different thresholds without re-fetching API data
- Historical analysis of close-to-threshold opportunities
- Support multiple strategies (conservative, aggressive, etc.)
- Debug filtering logic separately from odds collection

Usage:
    python filter_ev_hits.py [--ev-min 0.03] [--prob-min 0.40] [--input all_odds_analysis.csv] [--output hits_ev_filtered.csv]
"""
import csv
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def load_all_odds(csv_path: Path) -> List[Dict]:
    """Load all opportunities from all_odds_analysis.csv"""
    if not csv_path.exists():
        print(f"[!] Input file not found: {csv_path}")
        return []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def calculate_fair_and_ev(opportunities: List[Dict], betfair_commission: float = 0.06,
                          bankroll: float = 1000, kelly_fraction: float = 0.25) -> List[Dict]:
    """
    Calculate Fair, EV%, Prob, and Stake for each opportunity using sharp bookmaker odds.
    
    Sharp books: Pinnacle, Betfair (with commission adjustment)
    Fair price = median of available sharp prices
    
    Args:
        opportunities: List of opportunity dicts with raw odds
        betfair_commission: Betfair commission (default 6%)
        bankroll: Bankroll for Kelly calculation
        kelly_fraction: Kelly fraction (default 0.25)
    
    Returns:
        List of opportunities with Fair, EV%, Prob, Stake populated
    """
    enriched = []
    
    for opp in opportunities:
        try:
            # Get bookmaker odds
            book_odds_str = opp.get('Book', '0')
            book_odds = float(book_odds_str)
            
            if book_odds <= 1.0:
                continue
            
            # Get sharp bookmaker odds
            sharp_odds = []
            
            # Pinnacle
            pinnacle_str = opp.get('pinnacle', '').strip()
            if pinnacle_str:
                pinnacle_odds = float(pinnacle_str)
                if pinnacle_odds > 1.0:
                    sharp_odds.append(pinnacle_odds)
            
            # Betfair (adjust for commission)
            betfair_str = opp.get('betfair', '').strip()
            if betfair_str:
                betfair_raw = float(betfair_str)
                if betfair_raw > 1.0:
                    # Adjust for commission: fair_odds = 1 + (raw_odds - 1) * (1 - commission)
                    betfair_adjusted = 1 + (betfair_raw - 1) * (1 - betfair_commission)
                    sharp_odds.append(betfair_adjusted)
            
            # Need at least one sharp book
            if not sharp_odds:
                continue
            
            # Fair price = median of sharp prices
            sharp_odds.sort()
            n = len(sharp_odds)
            if n % 2 == 1:
                fair_odds = sharp_odds[n // 2]
            else:
                fair_odds = (sharp_odds[n // 2 - 1] + sharp_odds[n // 2]) / 2.0
            
            # Calculate edge
            edge = (book_odds / fair_odds) - 1.0
            
            # Calculate probability
            implied_prob = 1.0 / book_odds
            
            # Calculate Kelly stake
            if edge > 0:
                kelly_full = (book_odds * implied_prob - (1 - implied_prob)) / book_odds
                kelly_stake_amt = bankroll * kelly_full * kelly_fraction
                kelly_stake_amt = max(0, min(kelly_stake_amt, bankroll * 0.1))  # Cap at 10% bankroll
                stake_str = f"${int(kelly_stake_amt)}"
            else:
                stake_str = "$0"
            
            # Populate calculated fields
            opp['Fair'] = f"{fair_odds:.3f}"
            opp['EV%'] = f"{edge * 100:.2f}%"
            opp['Prob'] = f"{implied_prob * 100:.2f}%"
            opp['Stake'] = stake_str
            
            enriched.append(opp)
            
        except (ValueError, KeyError, ZeroDivisionError):
            # Skip rows with missing/invalid data
            continue
    
    return enriched


def apply_filters(opportunities: List[Dict], ev_min: float, prob_min: float, min_sharps: int = 0) -> List[Dict]:
    """
    Filter opportunities by EV, probability, and sharp book count thresholds.
    
    Args:
        opportunities: List of opportunity dicts
        ev_min: Minimum EV percentage (e.g., 0.03 for 3%)
        prob_min: Minimum probability (e.g., 0.40 for 40%)
        min_sharps: Minimum number of sharp books (default 0 = no filter)
    
    Returns:
        List of filtered opportunities
    """
    filtered = []
    
    for opp in opportunities:
        try:
            # Parse EV% (remove % sign)
            ev_str = opp.get('EV%', '0%').strip('%')
            ev = float(ev_str) / 100.0
            
            # Parse Prob (remove % sign)
            prob_str = opp.get('Prob', '0%').strip('%')
            prob = float(prob_str) / 100.0
            
            # Parse NumSharps
            num_sharps_str = opp.get('NumSharps', '0')
            num_sharps = int(num_sharps_str) if num_sharps_str and num_sharps_str.strip() else 0
            
            # Apply thresholds
            if ev >= ev_min and prob >= prob_min and num_sharps >= min_sharps:
                filtered.append(opp)
        except (ValueError, AttributeError):
            # Skip rows with invalid data
            continue
    
    return filtered


def select_max_edge_per_event(opportunities: List[Dict]) -> List[Dict]:
    """
    For each event × market × selection, keep only the bookmaker(s) with max edge.
    
    This implements the "log only max edge" logic that was in ev_arb_bot_NEW.py
    """
    # Group by (event, market, selection)
    groups = defaultdict(list)
    
    for opp in opportunities:
        key = (opp.get('event'), opp.get('market'), opp.get('selection'))
        groups[key].append(opp)
    
    max_edge_opportunities = []
    
    for key, opps_group in groups.items():
        if not opps_group:
            continue
        
        # Find max edge in this group
        try:
            max_edge = max(float(o.get('EV%', '0%').strip('%')) for o in opps_group)
        except (ValueError, AttributeError):
            continue
        
        # Keep all bookmakers that have this max edge
        for opp in opps_group:
            try:
                opp_edge = float(opp.get('EV%', '0%').strip('%'))
                if abs(opp_edge - max_edge) < 0.01:  # Allow for rounding
                    max_edge_opportunities.append(opp)
            except (ValueError, AttributeError):
                continue
    
    return max_edge_opportunities


def combine_same_edge_bookmakers(opportunities: List[Dict]) -> List[Dict]:
    """
    Combine bookmakers with the same edge for the same selection into one row.
    
    This creates the "bookmaker1, bookmaker2" format in the output.
    """
    # Group by (event, market, selection, edge)
    groups = defaultdict(list)
    
    for opp in opportunities:
        key = (
            opp.get('event'),
            opp.get('market'),
            opp.get('selection'),
            opp.get('EV%'),  # Include edge in key
            opp.get('Book'),  # Include book odds in key
        )
        groups[key].append(opp)
    
    combined = []
    
    for key, opps_group in groups.items():
        if not opps_group:
            continue
        
        # Use first opportunity as template
        combined_opp = opps_group[0].copy()
        
        # Combine bookmaker names
        bookmakers = [o.get('bookmaker', '') for o in opps_group]
        combined_opp['bookmaker'] = ', '.join(bookmakers)
        
        combined.append(combined_opp)
    
    return combined


def write_filtered_csv(opportunities: List[Dict], output_path: Path):
    """Write filtered opportunities to CSV"""
    if not opportunities:
        print(f"[!] No opportunities to write")
        return
    
    # CSV structure matches all_odds_analysis.csv (amended names only)
    fieldnames = [
        "Start Time", "Sport", "Event", "Market", "Selection", "O/U + Y/N", "Book", "Price", "Fair", "EV%", "Prob", "Stake", "NumSharps",
        "Pinnacle", "Betfair", "Sportsbet", "Bet365", "Pointsbet", "Betright", "Tab", "Dabble", "Unibet", "Ladbrokes", "Playup", "Tabtouch", "Betr", "Neds", "Draftkings", "Fanduel", "Betmgm", "Betonline", "Bovada", "Boombet"
    ]
    key_map = {
        "pinnacle": "Pinnacle", "betfair": "Betfair", "sportsbet": "Sportsbet", "bet365": "Bet365", "pointsbetau": "Pointsbet", "betright": "Betright", "tab": "Tab", "dabble_au": "Dabble", "unibet": "Unibet", "ladbrokes": "Ladbrokes", "playup": "Playup", "tabtouch": "Tabtouch", "betr_au": "Betr", "neds": "Neds", "draftkings": "Draftkings", "fanduel": "Fanduel", "betmgm": "Betmgm", "betonlineag": "Betonline", "bovada": "Bovada", "boombet": "Boombet"
    }
    # Remap all opportunities to use only amended keys
    remapped = []
    for row in opportunities:
        new_row = {}
        for k, v in row.items():
            if k in key_map:
                new_row[key_map[k]] = v
            elif k in fieldnames:
                new_row[k] = v
        remapped.append(new_row)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remapped)
    print(f"[OK] Wrote {len(opportunities)} opportunities to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Filter EV opportunities from all_odds_analysis.csv into all_odds.csv')
    parser.add_argument('--ev-min', type=float, default=0.03, help='Minimum EV (default: 0.03 = 3%%)')
    parser.add_argument('--prob-min', type=float, default=0.40, help='Minimum probability (default: 0.40 = 40%%)')
    parser.add_argument('--min-sharps', type=int, default=0, help='Minimum number of sharp books (default: 0 = no filter)')
    parser.add_argument('--input', type=str, default='data/all_odds_analysis.csv', help='Input CSV path (must exist)')
    parser.add_argument('--output', type=str, default='data/all_odds.csv', help='Filtered summary output (enforced second CSV)')
    parser.add_argument('--no-max-edge', action='store_true', help='Skip max-edge filtering (keep all edges)')
    parser.add_argument('--no-combine', action='store_true', help='Skip bookmaker combining (one row per bookmaker)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("EV HITS FILTER")
    print("="*70)
    print(f"Input: {args.input}")
    print(f"Output: {args.output} (policy: only this and all_odds_analysis.csv retained)")
    print(f"EV Min: {args.ev_min*100:.1f}%")
    print(f"Prob Min: {args.prob_min*100:.1f}%")
    print(f"Min Sharp Books: {args.min_sharps if args.min_sharps > 0 else 'OFF'}")
    print(f"Max Edge Filter: {'OFF' if args.no_max_edge else 'ON'}")
    print(f"Combine Bookmakers: {'OFF' if args.no_combine else 'ON'}")
    print("="*70)
    
    # Load data
    print(f"\n[1/4] Loading opportunities from {args.input}...")
    opportunities = load_all_odds(Path(args.input))
    print(f"      Loaded: {len(opportunities)} opportunities")
    
    # Check if Fair/EV%/Prob are already populated (from Stage 1)
    # If empty, calculate them here (backward compatibility)
    needs_calculation = False
    if opportunities:
        first_opp = opportunities[0]
        if not first_opp.get('Fair') or not first_opp.get('EV%') or not first_opp.get('Prob'):
            needs_calculation = True
    
    if needs_calculation:
        print(f"\n[2/4] Calculating fair prices and EV from sharp bookmakers...")
        opportunities = calculate_fair_and_ev(opportunities)
        print(f"      Calculated: {len(opportunities)} opportunities with fair prices")
    else:
        print(f"\n[2/4] Fair prices already calculated in Stage 1 - skipping recalculation")
        # Filter out rows without Fair (sharp books not available)
        opportunities = [o for o in opportunities if o.get('Fair')]
    
    # Apply threshold filters
    print(f"\n[3/4] Applying EV, probability, and sharp book filters...")
    filtered = apply_filters(opportunities, args.ev_min, args.prob_min, args.min_sharps)
    print(f"      After filters: {len(filtered)} opportunities")
    
    # Apply max-edge logic
    if not args.no_max_edge:
        print(f"\n[4/4] Selecting max edge per event...")
        filtered = select_max_edge_per_event(filtered)
        print(f"      After max-edge: {len(filtered)} opportunities")
    else:
        print(f"\n[4/4] Skipping max-edge filter...")
    
    # Combine bookmakers
    if not args.no_combine:
        print(f"      Combining bookmakers with same edge...")
        filtered = combine_same_edge_bookmakers(filtered)
        print(f"      After combining: {len(filtered)} opportunities")
    else:
        print(f"      Skipping bookmaker combining...")
    
    # Write output
    print(f"\n[OUTPUT] Writing to {args.output}...")
    write_filtered_csv(filtered, Path(args.output))
    
    # Summary stats
    if filtered:
        ev_values = [float(o.get('EV%', '0%').strip('%') if o.get('EV%') else o.get('EV', '0').strip('%')) for o in filtered]
        prob_values = [float(o.get('Prob', '0%').strip('%') if o.get('Prob') else o.get('Probability', '0').strip('%')) for o in filtered]
        print(f"\n[STATS]")
        print(f"  EV Range: {min(ev_values):.2f}% to {max(ev_values):.2f}%")
        print(f"  Prob Range: {min(prob_values):.2f}% to {max(prob_values):.2f}%")
        
        # Count by sport
        sports = defaultdict(int)
        for o in filtered:
            sports[o.get('Sport', o.get('sport', 'unknown'))] += 1
        print(f"  By Sport:")
        for sport, count in sorted(sports.items()):
            print(f"    {sport}: {count}")
    
    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()

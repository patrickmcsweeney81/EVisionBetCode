"""
Export all player prop lines to CSV format for easy analysis.
Creates a table showing all available lines across bookmakers.
"""
import csv
from typing import Dict, List
from pathlib import Path
from display_player_lines import extract_all_player_lines


def export_player_lines_to_csv(
    event: Dict,
    market_key: str,
    output_file: str = "data/player_lines.csv"
):
    """
    Export all player lines to CSV.
    
    Output format:
    Player,Market,Line,Bookmaker,Over,Under
    Josh Allen,player_pass_yds,250.5,pinnacle,1.95,1.95
    Josh Allen,player_pass_yds,250.5,fanduel,1.91,1.99
    Josh Allen,player_pass_yds,275.5,pinnacle,2.20,1.75
    """
    # Disabled: Only all_odds_analysis.csv and all_odds.csv are allowed for output.
    raise NotImplementedError("CSV export is disabled except for all_odds_analysis.csv and all_odds.csv.")


def export_all_markets(
    event: Dict,
    markets: List[str],
    output_file: str = "data/all_player_lines.csv",
    append: bool = True
):
    """
    Export multiple markets to a single CSV.
    
    Args:
        event: Event dict with bookmakers data
        markets: List of market keys to export
        output_file: Path to output CSV
        append: If True, append to existing file. If False, overwrite.
    """
    # Disabled: Only all_odds_analysis.csv and all_odds.csv are allowed for output.
    raise NotImplementedError("CSV export is disabled except for all_odds_analysis.csv and all_odds.csv.")


def create_pivot_table(input_csv: str = "data/all_player_lines.csv", output_csv: str = "data/player_lines_pivot.csv"):
    """
    Create a pivot table showing all lines for each player in columns.
    
    Output format (similar to Sportsbet):
    Player,Market,15+ Over,15+ Under,20+ Over,20+ Under,25+ Over,25+ Under...
    Josh Allen,player_pass_yds,1.12,1.24,1.41,1.64,2.25,...
    """
    import pandas as pd
    
    # Read CSV
    df = pd.read_csv(input_csv)
    
    # Get unique lines sorted
    lines = sorted(df['Line'].unique())
    
    # Create pivot for each player/market combo
    pivot_rows = []
    
    for (player, market), group in df.groupby(['Player', 'Market']):
        row = {
            'Player': player,
            'Market': market
        }
        
        # For each line, get best Over and Under odds
        for line in lines:
            line_data = group[group['Line'] == line]
            
            if not line_data.empty:
                best_over = line_data['Over'].max()
                best_under = line_data['Under'].max()
                
                # Format line as integer if whole
                line_str = f"{int(line)}" if line == int(line) else f"{line:.1f}"
                
                row[f"{line_str}+ Over"] = best_over
                row[f"{line_str}+ Under"] = best_under
        
        pivot_rows.append(row)
    
    # Create DataFrame and save
    pivot_df = pd.DataFrame(pivot_rows)
    pivot_df.to_csv(output_csv, index=False)
    
    print(f"Created pivot table: {output_csv}")
    return output_csv


if __name__ == "__main__":
    print("Run this with event data from the API")
    print("Example:")
    print("  from export_all_lines import export_all_markets")
    print("  export_all_markets(event, ['player_pass_yds', 'player_rush_yds'])")

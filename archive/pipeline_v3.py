#!/usr/bin/env python
"""
V3 Pipeline Orchestrator
Run with: python pipeline_v3.py --sports basketball_nba
"""

import argparse
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from v3.extractors.nba_extractor import NBAExtractor


def main():
    parser = argparse.ArgumentParser(
        description="V3 Pipeline - Extract odds for specified sports"
    )
    parser.add_argument(
        "--sports",
        type=str,
        default="basketball_nba",
        help="Sports to extract (comma-separated)",
    )
    parser.add_argument(
        "--props",
        action="store_true",
        help="Include player props (more expensive)",
    )
    
    args = parser.parse_args()
    sports = [s.strip() for s in args.sports.split(",")]
    
    print("\n" + "="*70)
    print("EVisionBet V3 Pipeline")
    print("="*70)
    print(f"Sports: {', '.join(sports)}")
    print(f"Include props: {args.props}")
    print("="*70)
    
    for sport in sports:
        if sport == "basketball_nba":
            extractor = NBAExtractor()
            df = extractor.extract()
            if not df.empty:
                extractor.save_csv(df, "nba_raw.csv")
        else:
            print(f"\n⚠️  {sport} not yet implemented in V3")
    
    print("\n" + "="*70)
    print("Pipeline complete!")
    print("="*70)


if __name__ == "__main__":
    main()

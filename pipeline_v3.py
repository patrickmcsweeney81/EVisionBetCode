"""
Pipeline Orchestrator v3 - Config-driven sport extraction

Features:
- Config-driven sport selection (enable/disable in sports.py)
- Per-sport API tier control (base/props/advanced)
- Cost estimation before extraction
- Dry-run mode (estimate without executing)
- Per-sport region & fair odds customization
- Merge outputs into combined CSVs
- Error handling and logging
- Detailed summary reporting
"""

import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.v3.configs import (
    get_enabled_sports,
    get_sport_config,
    get_api_config_for_sport,
)
from src.v3.extractors import NBAExtractor, NFLExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Map sport keys to extractors
EXTRACTORS = {
    "basketball_nba": NBAExtractor,
    "americanfootball_nfl": NFLExtractor,
    # TODO: Add more sports
}


class PipelineV3:
    """Main pipeline orchestrator with config-driven sport extraction"""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """Initialize pipeline
        
        Args:
            dry_run: If True, estimate without executing
            verbose: If True, print detailed config info
        """
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.extracts_dir = self.data_dir / "extracts"
        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.dry_run = dry_run
        self.verbose = verbose
        self.total_api_cost = 0.0

    def run_sport(self, sport_key: str) -> Dict:
        """
        Run extractor for a single sport

        Args:
            sport_key: e.g., "basketball_nba"

        Returns:
            Result dict with status and metrics
        """
        if sport_key not in EXTRACTORS:
            logger.warning(f"No extractor found for {sport_key}")
            return {
                "sport": sport_key,
                "status": "skipped",
                "reason": "No extractor available",
            }

        try:
            # Load sport config
            sport_config = get_sport_config(sport_key)
            if not sport_config or not sport_config.get("enabled"):
                logger.warning(f"{sport_key} is disabled in config")
                return {
                    "sport": sport_key,
                    "status": "skipped",
                    "reason": "Disabled in config",
                }
            
            if self.verbose:
                logger.info(f"Config for {sport_key}:")
                logger.info(f"  - Title: {sport_config.get('title')}")
                logger.info(f"  - API Tiers: {sport_config.get('api_tiers')}")
            
            extractor_class = EXTRACTORS[sport_key]
            extractor = extractor_class()
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would extract {sport_key}")
                return {
                    "sport": sport_key,
                    "status": "dry_run",
                    "title": sport_config.get("title"),
                }
            
            result = extractor.run()
            return result
        except Exception as e:
            logger.error(f"Failed to run {sport_key}: {e}")
            return {
                "sport": sport_key,
                "status": "error",
                "error": str(e),
            }

    def run_all_sports(self) -> List[Dict]:
        """
        Run extractors for all enabled sports

        Returns:
            List of result dicts
        """
        enabled_sports = get_enabled_sports()
        logger.info(f"Running {len(enabled_sports)} enabled sports")

        results = []
        for sport_key in enabled_sports:
            result = self.run_sport(sport_key)
            results.append(result)
            self.results.append(result)

        return results

    def run_selected_sports(self, sport_keys: List[str]) -> List[Dict]:
        """
        Run extractors for selected sports

        Args:
            sport_keys: List of sport keys, e.g., ["basketball_nba", "americanfootball_nfl"]

        Returns:
            List of result dicts
        """
        logger.info(f"Running {len(sport_keys)} selected sports: {', '.join(sport_keys)}")

        results = []
        for sport_key in sport_keys:
            result = self.run_sport(sport_key)
            results.append(result)
            self.results.append(result)

        return results

    def estimate_cost(self, sports: Optional[List[str]] = None) -> Dict:
        """
        Estimate API cost before extraction

        Args:
            sports: Sports to estimate, or None for all enabled

        Returns:
            Dict with cost breakdown
        """
        target_sports = sports or get_enabled_sports()
        
        cost_breakdown = {}
        total_cost = 0.0
        
        for sport_key in target_sports:
            try:
                sport_config = get_sport_config(sport_key)
                if not sport_config or not sport_config.get("enabled"):
                    continue
                
                api_config = get_api_config_for_sport(sport_key)
                cost = api_config.get("estimated_cost_per_run", 0)
                
                cost_breakdown[sport_key] = {
                    "title": sport_config.get("title", sport_key),
                    "estimated_cost": cost,
                    "tier_1_enabled": api_config.get("tier_1_enabled", True),
                    "tier_2_enabled": api_config.get("tier_2_enabled", False),
                    "tier_3_enabled": api_config.get("tier_3_enabled", False),
                }
                total_cost += cost
            except Exception as e:
                logger.warning(f"Could not estimate cost for {sport_key}: {e}")
        
        return {
            "breakdown": cost_breakdown,
            "total_cost": total_cost,
            "sports_count": len([s for s in target_sports if get_sport_config(s) and get_sport_config(s).get("enabled")]),
        }

    def print_cost_estimate(self, estimate: Dict) -> None:
        """Print cost estimate to console"""
        logger.info("\n" + "=" * 70)
        logger.info("API COST ESTIMATION")
        logger.info("=" * 70)
        
        for sport_key, details in estimate.get("breakdown", {}).items():
            title = details.get("title", sport_key)
            cost = details.get("estimated_cost", 0)
            tiers = []
            if details.get("tier_1_enabled"):
                tiers.append("T1")
            if details.get("tier_2_enabled"):
                tiers.append("T2")
            if details.get("tier_3_enabled"):
                tiers.append("T3")
            
            logger.info(f"{title:20} ${cost:8.2f}  [{', '.join(tiers)}]")
        
        logger.info("-" * 70)
        total = estimate.get("total_cost", 0)
        sports_count = estimate.get("sports_count", 0)
        logger.info(f"Total ({sports_count} sports): ${total:.2f}")
        logger.info("=" * 70)

    def merge_extracts(self) -> None:
        """
        Merge all individual sport CSVs into combined all_raw_odds.csv
        """
        logger.info("Merging extracts...")

        combined_rows = []
        extract_files = list(self.extracts_dir.glob("*_raw.csv"))

        if not extract_files:
            logger.warning("No extract files found")
            return

        logger.info(f"Found {len(extract_files)} extract files")

        # Read all extract CSVs
        for csv_file in sorted(extract_files):
            logger.info(f"  Merging {csv_file.name}")
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        combined_rows.append(row)
            except Exception as e:
                logger.error(f"  Failed to read {csv_file}: {e}")
                continue

        logger.info(f"Total rows after merge: {len(combined_rows)}")

        # Write combined CSV
        output_file = self.data_dir / "raw_odds_pure.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if combined_rows:
            fieldnames = list(combined_rows[0].keys())
            try:
                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(combined_rows)
                logger.info(f"✓ Wrote merged CSV: {output_file}")
            except Exception as e:
                logger.error(f"Failed to write merged CSV: {e}")
        else:
            logger.warning("No rows to merge")

    def print_summary(self) -> None:
        """Print execution summary"""
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 70)

        successful = sum(1 for r in self.results if r.get("status") == "success")
        failed = sum(1 for r in self.results if r.get("status") == "error")
        skipped = sum(1 for r in self.results if r.get("status") == "skipped")

        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"Total: {len(self.results)}")

        if successful > 0:
            total_markets = sum(r.get("markets_found", 0) for r in self.results if r.get("status") == "success")
            logger.info(f"Total markets extracted: {total_markets}")

        logger.info("=" * 70)

    def run(self, sports: Optional[List[str]] = None, estimate_only: bool = False) -> None:
        """
        Main execution method

        Args:
            sports: Optional list of sports to run. If None, runs all enabled sports.
            estimate_only: If True, only show cost estimate, don't execute
        """
        logger.info("=" * 70)
        logger.info(f"EVisionBet Pipeline v3 - Started {datetime.now(timezone.utc)}")
        logger.info("=" * 70)
        
        if self.dry_run:
            logger.info("Mode: DRY RUN (no execution)")
        if self.verbose:
            logger.info("Mode: VERBOSE (detailed output)")

        try:
            # Get cost estimate
            estimate = self.estimate_cost(sports)
            self.print_cost_estimate(estimate)
            
            if estimate_only:
                logger.info("Mode: ESTIMATE ONLY (no execution)")
                return
            
            # Run extraction
            target_sports = sports or get_enabled_sports()
            logger.info(f"\nRunning extraction for {len(target_sports)} sports...")
            
            if self.dry_run:
                self.run_selected_sports(target_sports)
                logger.info("✓ Dry run complete (no API calls made)")
            else:
                if target_sports:
                    self.run_selected_sports(target_sports)
                else:
                    self.run_all_sports()
                
                # Merge results
                self.merge_extracts()
            
            self.print_summary()

            logger.info("✓ Pipeline complete")

        except Exception as e:
            logger.error(f"✗ Pipeline failed: {e}")
            sys.exit(1)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="EVisionBet v3 Pipeline - Config-driven sport extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all enabled sports (from config)
  python pipeline_v3.py
  
  # Run specific sports
  python pipeline_v3.py --sports basketball_nba americanfootball_nfl
  
  # Estimate API cost before extracting
  python pipeline_v3.py --estimate-cost
  
  # Dry run (simulate extraction without API calls)
  python pipeline_v3.py --dry-run
  
  # Verbose mode (show detailed config info)
  python pipeline_v3.py --verbose
  
  # Estimate cost for specific sports
  python pipeline_v3.py --sports basketball_nba --estimate-cost
  
  # Only merge existing extracts
  python pipeline_v3.py --merge-only
        """
    )
    
    parser.add_argument(
        "--sports",
        nargs="+",
        help="Sports to run (e.g., basketball_nba americanfootball_nfl). If omitted, runs all enabled sports from config.",
    )
    
    parser.add_argument(
        "--estimate-cost",
        action="store_true",
        help="Estimate API cost before extraction (dry run, no API calls)",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate extraction without making API calls",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed configuration and extraction info",
    )
    
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Only merge existing extracts, don't run extractors",
    )

    args = parser.parse_args()

    pipeline = PipelineV3(dry_run=args.dry_run or args.estimate_cost, verbose=args.verbose)

    if args.merge_only:
        logger.info("Merge-only mode")
        pipeline.merge_extracts()
    else:
        pipeline.run(sports=args.sports, estimate_only=args.estimate_cost)


if __name__ == "__main__":
    main()

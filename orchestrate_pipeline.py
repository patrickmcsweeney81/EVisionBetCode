"""
Orchestrate EVisionBet Pipeline - Parallel Processing with File Locking
=========================================================================

Workflow:
1. Archive & cleanup (manage_allsports_ev.py ONCE)
2. Extract all sports in parallel
3. Filter all sports in parallel
4. Calculate EV for all sports in parallel (with file locking)
5. Merge all sports into AllSports_EV.csv
6. Generate audit report

Usage:
    python orchestrate_pipeline.py
    python orchestrate_pipeline.py --extract-only
    python orchestrate_pipeline.py --calculate-only
    python orchestrate_pipeline.py --audit-only
"""

import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd
import glob


class PipelineOrchestrator:
    """Manage parallel pipeline execution."""

    def __init__(self):
        self.sports = ["nfl", "nba"]  # Expandable
        self.start_time = datetime.now()
        self.results = {}

    def run_command(self, sport, stage, script_name):
        """Run a single script and return result."""
        try:
            print(f"[START] {sport.upper()} {stage}...", flush=True)
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )

            if result.returncode == 0:
                print(f"[OK] {sport.upper()} {stage} completed", flush=True)
                return {
                    "sport": sport,
                    "stage": stage,
                    "status": "success",
                    "output": result.stdout,
                }
            else:
                print(
                    f"[ERROR] {sport.upper()} {stage} failed",
                    flush=True
                )
                return {
                    "sport": sport,
                    "stage": stage,
                    "status": "error",
                    "error": result.stderr,
                }
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {sport.upper()} {stage} exceeded 5 min")
            return {
                "sport": sport,
                "stage": stage,
                "status": "timeout",
            }
        except Exception as e:
            return {
                "sport": sport,
                "stage": stage,
                "status": "exception",
                "error": str(e),
            }

    def extract_parallel(self):
        """Run all extractors in parallel."""
        print("\n" + "=" * 60)
        print("[STAGE] EXTRACTION - Running all sports in parallel")
        print("=" * 60)

        extractors = {
            "nfl": "extract_nfl_v3.py",
            "nba": "extract_nba_v3.py",
        }

        with ThreadPoolExecutor(max_workers=len(self.sports)) as executor:
            futures = {
                executor.submit(
                    self.run_command, sport, "extraction", script
                ): sport
                for sport, script in extractors.items()
            }

            for future in as_completed(futures):
                result = future.result()
                self.results[f"{result['sport']}_extract"] = result

    def filter_parallel(self):
        """Run all filters in parallel."""
        print("\n" + "=" * 60)
        print("[STAGE] FILTERING - Running all sports in parallel")
        print("=" * 60)

        filters = {
            "nfl": "filter_nfl_v3.py",
            "nba": "filter_nba_v3.py",
        }

        with ThreadPoolExecutor(max_workers=len(self.sports)) as executor:
            futures = {
                executor.submit(self.run_command, sport, "filtering", script): sport
                for sport, script in filters.items()
            }

            for future in as_completed(futures):
                result = future.result()
                self.results[f"{result['sport']}_filter"] = result

    def manage_allsports(self):
        """Archive & cleanup ONCE (before parallel calculations)."""
        print("\n" + "=" * 60)
        print("[STAGE] MANAGEMENT - Archive & cleanup")
        print("=" * 60)

        try:
            result = subprocess.run(
                [sys.executable, "manage_allsports_ev.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.stdout:
                print(result.stdout)
            if result.returncode != 0:
                print(f"[WARN] Management script error: {result.stderr}")
        except Exception as e:
            print(f"[WARN] Could not run management script: {e}")

    def calculate_parallel(self):
        """Run all EV calculators in parallel."""
        print("\n" + "=" * 60)
        print("[STAGE] EV CALCULATION - Running all sports in parallel")
        print("=" * 60)

        calculators = {
            "nfl": "calculate_nfl_ev_full.py",
            "nba": "calculate_nba_ev_full.py",
        }

        with ThreadPoolExecutor(max_workers=len(self.sports)) as executor:
            futures = {
                executor.submit(
                    self.run_command, sport, "EV calculation", script
                ): sport
                for sport, script in calculators.items()
            }

            for future in as_completed(futures):
                result = future.result()
                self.results[f"{result['sport']}_calculate"] = result

    def merge_allsports(self):
        """Merge all sport EV files into AllSports_EV.csv."""
        print("\n" + "=" * 60)
        print("[STAGE] MERGE - Combining all sports")
        print("=" * 60)

        ev_files = sorted(
            glob.glob("data/v3/extracts/*_EV.csv")
        )
        if not ev_files:
            print("[ERROR] No EV CSV files found to merge")
            return

        print(f"Found {len(ev_files)} EV files to merge:")
        for f in ev_files:
            print(f"  {os.path.basename(f)}")

        dfs = []
        total_rows = 0
        for file_path in ev_files:
            try:
                df = pd.read_csv(file_path)
                dfs.append(df)
                total_rows += len(df)
                sport = os.path.basename(file_path).split("_")[0]
                print(f"  {sport}: {len(df):,} rows")
            except Exception as e:
                print(f"  ERROR reading {file_path}: {e}")

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            allsports_ev = "data/v3/extracts/AllSports_EV.csv"
            combined.to_csv(allsports_ev, index=False)
            print(
                f"\n[OK] AllSports_EV.csv merged: {len(combined):,} rows "
                f"({combined['sport'].nunique()} sports)"
            )
            self.results["merge"] = {
                "status": "success",
                "total_rows": len(combined),
                "sports": combined["sport"].nunique(),
            }
        else:
            print("[ERROR] No valid EV files to merge")

    def audit(self):
        """Generate audit report."""
        print("\n" + "=" * 60)
        print("[STAGE] AUDIT - Line count analysis")
        print("=" * 60)

        try:
            result = subprocess.run(
                [sys.executable, "audit_pipeline.py"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.stdout:
                print(result.stdout)
            if result.returncode != 0 and result.stderr:
                print(f"[WARN] Audit error: {result.stderr}")
        except Exception as e:
            print(f"[WARN] Could not run audit: {e}")

    def summary(self):
        """Print execution summary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "=" * 60)
        print("[SUMMARY] Pipeline Execution Report")
        print("=" * 60)

        success_count = sum(
            1
            for r in self.results.values()
            if isinstance(r, dict) and r.get("status") == "success"
        )
        total_count = len(self.results)

        print(f"Execution time: {elapsed:.1f} seconds")
        print(f"Tasks completed: {success_count}/{total_count}")
        print(
            f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if "merge" in self.results:
            merge = self.results["merge"]
            if isinstance(merge, dict):
                print(
                    f"\nFinal AllSports_EV.csv: "
                    f"{merge.get('total_rows', 'N/A'):,} rows, "
                    f"{merge.get('sports', 'N/A')} sports"
                )

        print()

    def run_full_pipeline(self):
        """Execute complete pipeline."""
        print("[ORCHESTRATE] Full Pipeline: Extract -> Filter -> Manage")
        print("              -> Calculate -> Merge -> Audit")
        print()

        self.extract_parallel()
        self.filter_parallel()
        self.manage_allsports()
        self.calculate_parallel()
        self.merge_allsports()
        self.audit()
        self.summary()

    def run_extract_only(self):
        """Extract only."""
        self.extract_parallel()
        self.summary()

    def run_calculate_only(self):
        """Manage, calculate, merge, and audit."""
        self.manage_allsports()
        self.calculate_parallel()
        self.merge_allsports()
        self.audit()
        self.summary()

    def run_audit_only(self):
        """Audit only."""
        self.audit()


def main():
    """Main entry point."""
    orchestrator = PipelineOrchestrator()

    if "--extract-only" in sys.argv:
        orchestrator.run_extract_only()
    elif "--calculate-only" in sys.argv:
        orchestrator.run_calculate_only()
    elif "--audit-only" in sys.argv:
        orchestrator.run_audit_only()
    else:
        orchestrator.run_full_pipeline()


if __name__ == "__main__":
    main()

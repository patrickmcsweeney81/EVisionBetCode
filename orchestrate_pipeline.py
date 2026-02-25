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
    python orchestrate_pipeline.py --sports nba,afl,nrl,tennis
    python orchestrate_pipeline.py --extract-only
    python orchestrate_pipeline.py --calculate-only
    python orchestrate_pipeline.py --audit-only
"""

import argparse
import glob
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd


class PipelineOrchestrator:
    """Manage parallel pipeline execution."""

    def __init__(self, sports: list[str] | None = None):
        # NOTE: Some sports may be extraction-only
        # until downstream scripts exist.
        self.sports = sports or ["nfl", "nba", "nbl", "afl", "nrl", "epl"]
        self.start_time = datetime.now()
        self.results: dict[str, dict] = {}

    def _selected(self, mapping: dict[str, str]) -> dict[str, str]:
        """Return mapping filtered to currently selected sports."""
        selected = {
            s: script for s, script in mapping.items() if s in self.sports
        }
        missing = [s for s in self.sports if s not in mapping]
        if missing:
            print(
                f"[INFO] No script registered for: {', '.join(missing)} "
                f"(skipping)",
                flush=True,
            )
        return selected

    def run_command(self, sport, stage, script_name):
        """Run a single script and return result."""
        try:
            print(f"[START] {sport.upper()} {stage}...", flush=True)
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
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
            "nbl": "extract_nbl_v3.py",
            "afl": "extract_afl_v3.py",
            "nrl": "extract_nrl_v3.py",
            "epl": "extract_soccer_epl_v3.py",
            "tennis": "extract_tennis_v3.py",
        }

        extractors = self._selected(extractors)
        if not extractors:
            print("[INFO] No extractors selected", flush=True)
            return

        with ThreadPoolExecutor(max_workers=len(extractors)) as executor:
            futures = {
                executor.submit(
                    self.run_command, sport, "extraction", script
                ): sport
                for sport, script in extractors.items()
            }

            for future in as_completed(futures):
                result = future.result()
                self.results[f"{result['sport']}_extract"] = result

    def merge_all_raw(self):
        """Merge per-sport raw extracts into AllSports_Raw.csv."""
        print("\n" + "=" * 60)
        print("[STAGE] RAW MERGE - Combining all sports raw extracts")
        print("=" * 60)

        raw_candidates = [
            f
            for f in glob.glob("data/v3/extracts/*_Raw*.csv")
            if not os.path.basename(f).startswith("AllSports_Raw")
        ]
        if not raw_candidates:
            print("[WARN] No raw CSV files found to merge")
            return

        raw_by_sport: dict[str, str] = {}
        for f in raw_candidates:
            sport_key = os.path.basename(f).split("_Raw")[0]
            if sport_key not in raw_by_sport or (
                os.path.getmtime(f) > os.path.getmtime(raw_by_sport[sport_key])
            ):
                raw_by_sport[sport_key] = f

        raw_files = sorted(raw_by_sport.values())
        print(f"Found {len(raw_files)} raw files to merge:")
        for f in raw_files:
            print(f"  {os.path.basename(f)}")

        sport_map = {
            "NBA": "basketball_nba",
            "NFL": "americanfootball_nfl",
            "NBL": "basketball_nbl",
            "AFL": "aussierules_afl",
            "NRL": "rugbyleague_nrl",
            "EPL": "soccer_epl",
            "TENNIS": "tennis",
        }

        dfs = []
        for file_path in raw_files:
            try:
                df = pd.read_csv(file_path)
                if df.empty:
                    continue

                prefix = os.path.basename(file_path).split("_")[0]
                if "sport" not in df.columns:
                    df["sport"] = sport_map.get(prefix, prefix.lower())

                if "event_name" in df.columns:
                    if "away_team" not in df.columns:
                        df["away_team"] = ""
                    if "home_team" not in df.columns:
                        df["home_team"] = ""
                    mask = (df["away_team"].astype(str).str.strip() == "") | (
                        df["home_team"].astype(str).str.strip() == ""
                    )
                    if mask.any():
                        ev = df.loc[mask, "event_name"].astype(str)
                        # Prefer " @ " delimiter used by extractors
                        parts_at = ev.str.split(" @ ", n=1, expand=True)
                        if parts_at.shape[1] == 2:
                            df.loc[mask, "away_team"] = parts_at[0].fillna("")
                            df.loc[mask, "home_team"] = parts_at[1].fillna("")
                        else:
                            parts_v = ev.str.split(" V ", n=1, expand=True)
                            if parts_v.shape[1] == 2:
                                df.loc[mask, "away_team"] = parts_v[0].fillna("")
                                df.loc[mask, "home_team"] = parts_v[1].fillna("")

                if "market" not in df.columns and "market_type" in df.columns:
                    df["market"] = df["market_type"]

                if "timestamp" not in df.columns and "extracted_at" in df.columns:
                    df["timestamp"] = df["extracted_at"]

                dfs.append(df)
                print(f"  {prefix}: {len(df):,} rows")
            except Exception as e:
                print(f"  ERROR reading {file_path}: {e}")

        if not dfs:
            print("[WARN] No valid raw files to merge")
            return

        combined = pd.concat(dfs, ignore_index=True)
        core_first = [
            c
            for c in [
                "timestamp",
                "sport",
                "event_id",
                "away_team",
                "home_team",
                "commence_time",
                "league",
                "event_name",
                "market",
                "market_type",
                "point",
                "selection",
                "player_name",
                "pair_id",
            ]
            if c in combined.columns
        ]
        remaining = [c for c in combined.columns if c not in set(core_first)]
        combined = combined[core_first + remaining]

        out_path = "data/v3/extracts/AllSports_Raw.csv"
        try:
            combined.to_csv(out_path, index=False)
            print(f"[OK] AllSports_Raw.csv merged: {len(combined):,} rows")
        except PermissionError:
            out_path = "data/v3/extracts/AllSports_Raw_new.csv"
            combined.to_csv(out_path, index=False)
            print(f"[WARN] AllSports_Raw locked, saved to: {out_path}")

        self.results["raw_merge"] = {
            "status": "success",
            "total_rows": len(combined),
            "sports": int(combined["sport"].nunique()) if "sport" in combined.columns else None,
        }

    def filter_parallel(self):
        """Run all filters in parallel."""
        print("\n" + "=" * 60)
        print("[STAGE] FILTERING - Running all sports in parallel")
        print("=" * 60)

        filters = {
            "nfl": "filter_nfl_v3.py",
            "nba": "filter_nba_v3.py",
            "nbl": "filter_nbl_v3.py",
            "afl": "filter_afl_v3.py",
        }

        filters = self._selected(filters)
        if not filters:
            print("[INFO] No filters selected", flush=True)
            return

        with ThreadPoolExecutor(max_workers=len(filters)) as executor:
            futures = {
                executor.submit(
                    self.run_command,
                    sport,
                    "filtering",
                    script,
                ): sport
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
                encoding="utf-8",
                errors="replace",
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
            "nbl": "calculate_nbl_ev_full.py",
            "afl": "calculate_afl_ev_full.py",
        }

        calculators = self._selected(calculators)
        if not calculators:
            print("[INFO] No EV calculators selected", flush=True)
            return

        with ThreadPoolExecutor(max_workers=len(calculators)) as executor:
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

        ev_candidates = [
            f
            for f in glob.glob("data/v3/extracts/*_EV*.csv")
            if not os.path.basename(f).startswith("AllSports_EV")
        ]
        ev_by_sport: dict[str, str] = {}
        for f in ev_candidates:
            sport_key = os.path.basename(f).split("_EV")[0]
            if sport_key not in ev_by_sport or (
                os.path.getmtime(f) > os.path.getmtime(ev_by_sport[sport_key])
            ):
                ev_by_sport[sport_key] = f
        ev_files = sorted(ev_by_sport.values())
        if not ev_files:
            print("[ERROR] No EV CSV files found to merge")
            return

        print(f"Found {len(ev_files)} EV files to merge:")
        for f in ev_files:
            print(f"  {os.path.basename(f)}")

        dfs = []
        total_rows = 0
        sport_map = {
            "NBA": "basketball_nba",
            "NFL": "americanfootball_nfl",
            "NBL": "basketball_nbl",
            "AFL": "aussierules_afl",
        }
        for file_path in ev_files:
            try:
                df = pd.read_csv(file_path)
                sport = os.path.basename(file_path).split("_")[0]
                if "sport" not in df.columns:
                    df["sport"] = sport_map.get(sport, sport.lower())
                dfs.append(df)
                total_rows += len(df)
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
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if result.stdout:
                print(result.stdout)
            if result.returncode != 0 and result.stderr:
                print(f"[WARN] Audit error: {result.stderr}")
        except Exception as e:
            print(f"[WARN] Could not run audit: {e}")

    def generate_pats_picks(self):
        """Generate Pats_Picks.csv from AllSports_EV.csv."""
        print("\n" + "=" * 60)
        print("[STAGE] PATS PICKS - Generate Pats_Picks.csv")
        print("=" * 60)

        try:
            result = subprocess.run(
                [sys.executable, "generate_pats_picks.py"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if result.stdout:
                print(result.stdout)
            if result.returncode != 0 and result.stderr:
                print(f"[WARN] Pats Picks error: {result.stderr}")
        except Exception as e:
            print(f"[WARN] Could not generate Pats Picks: {e}")

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
        self.merge_all_raw()
        self.filter_parallel()
        self.manage_allsports()
        self.calculate_parallel()
        self.merge_allsports()
        self.generate_pats_picks()
        self.audit()
        self.summary()

    def run_extract_only(self):
        """Extract only."""
        self.extract_parallel()
        self.merge_all_raw()
        self.summary()

    def run_calculate_only(self):
        """Manage, calculate, merge, and audit."""
        self.manage_allsports()
        self.calculate_parallel()
        self.merge_allsports()
        self.generate_pats_picks()
        self.audit()
        self.summary()

    def run_audit_only(self):
        """Audit only."""
        self.audit()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--sports",
        type=str,
        default="",
        help=(
            "Comma-separated sports to run (e.g. nba,afl,nrl,tennis). "
            "If omitted, runs the default set."
        ),
    )
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--calculate-only", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()

    sports = [s.strip().lower() for s in args.sports.split(",") if s.strip()]
    orchestrator = PipelineOrchestrator(sports=sports or None)

    if args.extract_only:
        orchestrator.run_extract_only()
    elif args.calculate_only:
        orchestrator.run_calculate_only()
    elif args.audit_only:
        orchestrator.run_audit_only()
    else:
        orchestrator.run_full_pipeline()


if __name__ == "__main__":
    main()

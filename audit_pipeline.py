"""
Audit Pipeline - Comprehensive Line Count Analysis
===================================================

Tracks every line through each stage:
- Raw extraction
- After filtering
- After outlier detection
- After EV calculation
- Final combined file

Identifies dropped lines and shows loss at each stage.

Usage:
    python audit_pipeline.py
"""

import os
import pandas as pd
import glob
from datetime import datetime

try:
    from tabulate import tabulate
except ImportError:
    # Fallback if tabulate not installed
    def tabulate(data, headers=None, tablefmt=None):
        if headers:
            return "\n".join(
                [", ".join(str(h) for h in headers)]
                + [", ".join(str(v) for v in row) for row in data]
            )
        return "\n".join([", ".join(str(v) for v in row) for row in data])


class PipelineAudit:
    """Audit line counts through pipeline stages."""

    def __init__(self):
        self.audit_log = {}
        self.stages = {
            "raw": "data/v3/extracts/[NF][BF][LA]_Raw.csv",
            "filtered": "data/v3/extracts/[NF][BF][LA]_Filtered.csv",
            "outliers": "data/v3/extracts/[NF][BF][LA]_Outliers.csv",
            "ev": "data/v3/extracts/[NF][BF][LA]_EV.csv",
        }
        # Simpler glob patterns
        self.stage_patterns = {
            "raw": "data/v3/extracts/*_Raw.csv",
            "filtered": "data/v3/extracts/*_Filtered.csv",
            "outliers": "data/v3/extracts/*_Outliers.csv",
            "ev": "data/v3/extracts/*_EV.csv",
        }

    def get_files(self, pattern):
        """Get files matching pattern, indexed by sport."""
        files = glob.glob(pattern)
        result = {}
        for f in files:
            base = os.path.basename(f)
            # Extract sport: NFL_Raw.csv → nfl, NBA_Filtered.csv → nba
            if base.startswith("NFL_"):
                sport = "nfl"
            elif base.startswith("NBA_"):
                sport = "nba"
            else:
                sport = base.split("_")[0].lower()
            result[sport] = f
        return result

    def get_row_count(self, file_path):
        """Safely get row count from CSV."""
        try:
            if not os.path.exists(file_path):
                return None
            df = pd.read_csv(file_path)
            return len(df)
        except Exception as e:
            print(f"[WARN] Could not read {file_path}: {e}")
            return None

    def audit_stage(self, stage_name, pattern):
        """Audit a single stage."""
        files = self.get_files(pattern)
        if not files:
            return None

        results = {}
        for sport, file_path in sorted(files.items()):
            count = self.get_row_count(file_path)
            results[sport] = count
        return results

    def analyze_dropoff(self, sport, counts):
        """Calculate line dropoff percentages between stages."""
        stages = ["raw", "filtered", "outliers", "ev"]
        dropoff = {}

        for i in range(len(stages) - 1):
            stage1 = stages[i]
            stage2 = stages[i + 1]

            if (
                counts.get(stage1) is not None
                and counts.get(stage2) is not None
            ):
                start = counts[stage1]
                end = counts[stage2]
                pct = ((start - end) / start * 100) if start > 0 else 0
                dropoff[f"{stage1}->{stage2}"] = {
                    "dropped": start - end,
                    "remaining": end,
                    "pct": pct,
                }

        return dropoff

    def run(self):
        """Execute full audit."""
        print("[AUDIT] Pipeline Line Count Analysis")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Stage 1: Audit each stage
        print("=" * 80)
        print("STAGE ANALYSIS")
        print("=" * 80)

        stage_results = {}
        for stage_name, pattern in self.stage_patterns.items():
            results = self.audit_stage(stage_name, pattern)
            if results:
                stage_results[stage_name] = results
                print(f"\n[{stage_name.upper()}] Line Counts:")
                for sport in sorted(results.keys()):
                    count = results[sport]
                    if count is not None:
                        print(f"  {sport.upper()}: {count:,} rows")
                    else:
                        print(f"  {sport.upper()}: [FILE NOT FOUND]")

        # Stage 2: Build sport-wise audit trail
        print("\n" + "=" * 80)
        print("LINE LOSS ANALYSIS (By Sport)")
        print("=" * 80)

        all_sports = set()
        for stage_results_dict in stage_results.values():
            all_sports.update(stage_results_dict.keys())

        for sport in sorted(all_sports):
            print(f"\n{sport.upper()} PIPELINE:")
            print("-" * 80)

            counts = {}
            for stage_name in ["raw", "filtered", "outliers", "ev"]:
                if stage_name in stage_results:
                    counts[stage_name] = stage_results[stage_name].get(sport)

            # Print counts
            count_table = []
            for stage, count in counts.items():
                if count is not None:
                    count_table.append([stage.upper(), f"{count:,}"])
                else:
                    count_table.append([stage.upper(), "[N/A]"])

            print(
                tabulate(
                    count_table,
                    headers=["Stage", "Rows"],
                    tablefmt="simple"
                )
            )

            # Print dropoff
            dropoff = self.analyze_dropoff(sport, counts)
            if dropoff:
                print("\nLine Loss:")
                loss_table = []
                for transition, data in dropoff.items():
                    loss_table.append([
                        transition.replace("→", "->"),
                        f"-{data['dropped']:,}",
                        f"{data['pct']:.1f}%",
                    ])
                print(
                    tabulate(
                        loss_table,
                        headers=["Transition", "Lost", "%"],
                        tablefmt="simple"
                    )
                )

        # Stage 3: Combined summary
        print("\n" + "=" * 80)
        print("COMBINED SUMMARY")
        print("=" * 80)

        combined_summary = []
        for stage in ["raw", "filtered", "outliers", "ev"]:
            if stage in stage_results:
                stage_data = stage_results[stage]
                total = sum(
                    c for c in stage_data.values() if c is not None
                )
                combined_summary.append(
                    [stage.upper(), f"{total:,}"]
                )

        print()
        print(
            tabulate(
                combined_summary,
                headers=["Stage", "Total Rows (All Sports)"],
                tablefmt="simple"
            )
        )

        # Stage 4: Check AllSports_EV.csv
        print("\n" + "=" * 80)
        print("FINAL OUTPUT")
        print("=" * 80)

        allsports_path = "data/v3/extracts/AllSports_EV.csv"
        if os.path.exists(allsports_path):
            df = pd.read_csv(allsports_path)
            print(f"\nAllSports_EV.csv: {len(df):,} rows")
            print("\nSports Breakdown:")
            sport_counts = df["sport"].value_counts().to_dict()
            breakdown = [
                [sport, f"{count:,}"]
                for sport, count in sorted(
                    sport_counts.items(),
                    key=lambda x: -x[1]
                )
            ]
            print(
                tabulate(
                    breakdown,
                    headers=["Sport", "Rows"],
                    tablefmt="simple"
                )
            )
        else:
            print(
                f"\n[ERROR] AllSports_EV.csv not found at {allsports_path}"
            )

        # Stage 5: Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)

        if stage_results.get("raw") and stage_results.get("ev"):
            for sport in all_sports:
                raw = stage_results["raw"].get(sport)
                ev = stage_results["ev"].get(sport)
                if raw and ev:
                    pct_kept = (ev / raw * 100) if raw > 0 else 0
                    if pct_kept < 5:
                        print(
                            f"\n⚠️  {sport.upper()}: Only {pct_kept:.1f}% "
                            f"of lines kept ({raw:,} → {ev:,})"
                        )
                        print(
                            "   Consider reviewing filter criteria or "
                            "outlier detection settings"
                        )
                    elif pct_kept > 80:
                        print(
                            f"\n✓ {sport.upper()}: {pct_kept:.1f}% "
                            f"of lines retained (good filtering)"
                        )

        print()


def main():
    """Run audit."""
    audit = PipelineAudit()
    audit.run()


if __name__ == "__main__":
    main()

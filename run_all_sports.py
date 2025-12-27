"""
Run all sport-specific extractors and merge into all_raw_odds.csv
This is the main entry point for the new sport-specific extraction pipeline.

Usage:
    python run_all_sports.py              # Extract all sports
    python run_all_sports.py --sports NFL NBA  # Extract specific sports only
    python run_all_sports.py --merge-only      # Skip extraction, just merge
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Available sport extractors
SPORT_EXTRACTORS = {
    "NFL": "raw_NFL.py",
    "NBA": "raw_NBA.py",
    "MLB": "raw_MLB.py",
    "NHL": "raw_NHL.py",
    "NCAAF": "raw_NCAAF.py",
}

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(message: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{message}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")


def print_success(message: str):
    """Print a success message."""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message: str):
    """Print an error message."""
    print(f"{RED}❌ {message}{RESET}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠️  {message}{RESET}")


def run_sport_extractor(sport: str, script_path: Path) -> bool:
    """Run a single sport extractor script."""
    print(f"\n{YELLOW}▶ Running {sport} extractor...{RESET}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print_success(f"{sport} extraction completed")
            return True
        else:
            print_error(f"{sport} extraction failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print_error(f"{sport} extraction timed out")
        return False
    except Exception as e:
        print_error(f"{sport} extraction error: {e}")
        return False


def run_merge_script() -> bool:
    """Run the merge script to combine all sport CSVs."""
    print_header("MERGING SPORT CSVs")
    
    merge_script = Path(__file__).parent / "merge_raw_odds.py"
    
    if not merge_script.exists():
        print_error(f"Merge script not found: {merge_script}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(merge_script)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print_success("Merge completed successfully")
            return True
        else:
            print_error("Merge failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    
    except Exception as e:
        print_error(f"Merge error: {e}")
        return False


def main():
    """Main execution flow."""
    start_time = datetime.now()
    
    print_header("SPORT-SPECIFIC ODDS EXTRACTION PIPELINE")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse command line arguments
    args = sys.argv[1:]
    merge_only = "--merge-only" in args
    
    # Get list of sports to extract
    if "--sports" in args:
        sports_idx = args.index("--sports")
        selected_sports = args[sports_idx + 1:]
        # Filter to keep only valid sports
        selected_sports = [s for s in selected_sports if s in SPORT_EXTRACTORS and not s.startswith("--")]
    else:
        selected_sports = list(SPORT_EXTRACTORS.keys())
    
    # Run extractors unless merge-only mode
    success_count = 0
    failed_sports = []
    
    if not merge_only:
        print(f"\n{BLUE}Sports to extract: {', '.join(selected_sports)}{RESET}")
        
        for sport in selected_sports:
            script_name = SPORT_EXTRACTORS[sport]
            script_path = Path(__file__).parent / script_name
            
            if not script_path.exists():
                print_warning(f"{sport} extractor not found: {script_path}")
                failed_sports.append(sport)
                continue
            
            if run_sport_extractor(sport, script_path):
                success_count += 1
            else:
                failed_sports.append(sport)
        
        # Summary of extraction
        print_header("EXTRACTION SUMMARY")
        print(f"  Successful: {success_count}/{len(selected_sports)}")
        if failed_sports:
            print(f"  Failed: {', '.join(failed_sports)}")
    else:
        print_warning("Skipping extraction (merge-only mode)")
    
    # Run merge
    merge_success = run_merge_script()
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("PIPELINE COMPLETE")
    print(f"  Duration: {duration:.1f} seconds")
    print(f"  End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if merge_success and (merge_only or success_count > 0):
        print_success("All operations completed successfully!")
        sys.exit(0)
    else:
        print_error("Pipeline completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()

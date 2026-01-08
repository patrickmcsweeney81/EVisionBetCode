#!/usr/bin/env python
"""
NBA Pipeline Orchestrator - Runs all scripts sequentially
Usage: 
    python run_nba_pipeline.py              # Skips extraction, uses existing raw data
    python run_nba_pipeline.py --extract    # Includes extraction (uses API credits)
"""

import subprocess
import sys
from datetime import datetime


def run_pipeline(extract_enabled=False):
    """Run NBA extraction pipeline in sequence"""
    
    # Determine which scripts to run
    scripts = []
    
    if extract_enabled:
        scripts.append(("Extract RAW", "extract_nba_v3.py"))
    else:
        print("⏭️  Extraction SKIPPED (use --extract flag to enable API calls)")
    
    scripts.extend([
        ("Filter", "filter_nba_v3.py"),
        ("Detect Outliers", "outlier_nba_v3.py"),
        ("Calculate EV", "calculate_nba_ev_full.py"),
    ])
    
    print("=" * 80)
    print(f"🏀 NBA PIPELINE ORCHESTRATOR - Started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    failed_scripts = []
    
    for stage_name, script_file in scripts:
        print(f"\n{'─' * 80}")
        print(f"📍 STAGE: {stage_name}")
        print(f"📝 Script: {script_file}")
        print(f"{'─' * 80}")
        
        try:
            result = subprocess.run(
                [sys.executable, script_file],
                check=True,
                capture_output=False,  # Show output in real-time
                text=True
            )
            print(f"✅ {stage_name} completed successfully\n")
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ {stage_name} FAILED with exit code {e.returncode}")
            failed_scripts.append((stage_name, script_file, e.returncode))
            print(f"Stopping pipeline.\n")
            break
        except FileNotFoundError:
            print(f"\n❌ {stage_name} - Script not found: {script_file}")
            failed_scripts.append((stage_name, script_file, "not found"))
            break
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 PIPELINE SUMMARY")
    print("=" * 80)
    
    if not failed_scripts:
        print(f"✅ All {len(scripts)} stages completed successfully!")
        print(f"📂 Latest files in data/v3/extracts/:")
        subprocess.run(["powershell", "-Command", "Get-ChildItem C:\\EVisionBetCode\\data\\v3\\extracts\\ -Name | Sort-Object -Descending | Select-Object -First 4"])
    else:
        print(f"❌ Pipeline failed at stage: {failed_scripts[0][0]}")
        print(f"   Script: {failed_scripts[0][1]}")
        print(f"   Error: {failed_scripts[0][2]}")
        sys.exit(1)
    
    print("=" * 80)


if __name__ == "__main__":
    # Check for --extract flag to enable API calls
    extract_enabled = "--extract" in sys.argv
    run_pipeline(extract_enabled=extract_enabled)

#!/usr/bin/env python3
"""
Local Scheduler for Reddit-to-LinkedIn Pipeline
Run this script to execute the pipeline on a schedule without GitHub Actions.

Usage:
    python local_scheduler.py                    # Run once now
    python local_scheduler.py --schedule daily   # Run daily at 8 AM
    python local_scheduler.py --schedule weekly  # Run weekly on Monday at 8 AM
    python local_scheduler.py --schedule hourly  # Run every hour (for testing)
    python local_scheduler.py --daemon           # Run as background daemon
"""

import argparse
import schedule
import time
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def log(message: str):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_pipeline(generate: bool = True, post_count: int = 3):
    """Execute the Reddit-to-LinkedIn pipeline."""
    log("Starting pipeline execution...")

    try:
        cmd = ["python", "run.py", "pipeline"]
        if not generate:
            cmd.append("--no-generate")
        else:
            cmd.extend(["--count", str(post_count)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        if result.returncode == 0:
            log("Pipeline completed successfully!")
            log(f"Output:\n{result.stdout}")
        else:
            log(f"Pipeline failed with code {result.returncode}")
            log(f"Error:\n{result.stderr}")

        return result.returncode == 0

    except Exception as e:
        log(f"Pipeline execution error: {e}")
        return False

def run_scan_only():
    """Run Reddit scan without generating posts."""
    return run_pipeline(generate=False)

def run_full_pipeline():
    """Run full pipeline with post generation."""
    return run_pipeline(generate=True)

def setup_schedule(frequency: str):
    """Setup the schedule based on frequency."""
    if frequency == "hourly":
        schedule.every().hour.do(run_full_pipeline)
        log("Scheduled to run every hour")
    elif frequency == "daily":
        schedule.every().day.at("08:00").do(run_full_pipeline)
        log("Scheduled to run daily at 8:00 AM")
    elif frequency == "weekly":
        schedule.every().monday.at("08:00").do(run_full_pipeline)
        log("Scheduled to run every Monday at 8:00 AM")
    elif frequency == "twice-daily":
        schedule.every().day.at("08:00").do(run_full_pipeline)
        schedule.every().day.at("18:00").do(run_full_pipeline)
        log("Scheduled to run twice daily at 8:00 AM and 6:00 PM")
    else:
        log(f"Unknown frequency: {frequency}")
        return False
    return True

def run_scheduler_loop():
    """Run the scheduler loop."""
    log("Scheduler started. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        log("Scheduler stopped by user.")

def main():
    parser = argparse.ArgumentParser(
        description="Local scheduler for Reddit-to-LinkedIn pipeline"
    )
    parser.add_argument(
        "--schedule",
        choices=["hourly", "daily", "weekly", "twice-daily"],
        help="Schedule frequency"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (keeps running in background)"
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan Reddit, don't generate posts"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of posts to generate (default: 3)"
    )

    args = parser.parse_args()

    # If no schedule specified, run once
    if not args.schedule:
        log("Running pipeline once...")
        if args.scan_only:
            success = run_scan_only()
        else:
            success = run_pipeline(generate=True, post_count=args.count)
        sys.exit(0 if success else 1)

    # Setup schedule
    if not setup_schedule(args.schedule):
        sys.exit(1)

    # Run immediately first, then on schedule
    log("Running initial execution...")
    if args.scan_only:
        run_scan_only()
    else:
        run_full_pipeline()

    # Enter scheduler loop
    run_scheduler_loop()

if __name__ == "__main__":
    main()

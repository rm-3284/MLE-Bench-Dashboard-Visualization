#!/usr/bin/env python3
"""
Automated visualization pipeline orchestrator with dynamic metric configuration.

This script automates the entire process:
1. judge_journal.py: journal.json → journal_with_judgements.json
2. plan_judge.py: journal_with_judgements.json → plan_redundancy_report.json
3. journal_viz_.py: Generates HTML visualization with metrics

Usage:
    python run_visualization_pipeline.py <journal_path> [OPTIONS]
    
    journal_path    Path to journal.json file or parent directory containing it
                    Format: .../competition_name_logid/logs/journal.json
                    Metrics will be auto-loaded from metrics.csv using startswith() matching
    
    Options:
    --skip-judge    Skip the judgment step (use existing journal_with_judgements.json)
    --skip-plan     Skip the plan redundancy analysis
    --output FILE   Specify custom HTML output filename (default: journal_viz_tree_dashboard.html)
    --metrics FILE  Path to metrics.csv (default: metrics.csv in current dir)

Examples:
    python run_visualization_pipeline.py ~/data/tensorflow2-question-answering_abc123/logs/journal.json
    python run_visualization_pipeline.py ~/data/tensorflow2-question-answering_abc123/logs --skip-judge --output final.html
"""

import os
import sys
import json
import argparse
import subprocess
import time
import csv
import re
from pathlib import Path
import traceback

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def log(level, message):
    """Print colored log messages."""
    if level == "INFO":
        print(f"{Colors.BLUE}[INFO]{Colors.END} {message}")
    elif level == "SUCCESS":
        print(f"{Colors.GREEN}[✓]{Colors.END} {message}")
    elif level == "WARNING":
        print(f"{Colors.YELLOW}[WARN]{Colors.END} {message}")
    elif level == "ERROR":
        print(f"{Colors.RED}[✗]{Colors.END} {message}")
    elif level == "STEP":
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{message}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def parse_journal_path(journal_path):
    """
    Parse journal path to extract competition name and log ID.
    Expected format: .../competition_name_logid/logs/journal.json
    Returns: (competition_name, log_id, working_dir, journal_file)
    """
    path = Path(journal_path).resolve()
    
    # If it's a directory, look for journal.json inside
    if path.is_dir():
        journal_file = path / "journal.json"
        if not journal_file.exists():
            return None, None, None, None
        working_dir = path
    else:
        # It's a file
        journal_file = path
        working_dir = path.parent
    
    # Extract competition_name_logid from parent directory name
    # Expected: {parent_dir}/{competition_name}_{log_id}/logs/journal.json
    parent_name = working_dir.parent.name  # Get the competition_name_log_id dir
    
    # Split by the last underscore to separate competition_name from log_id
    parts = parent_name.rsplit('_', 1)
    if len(parts) != 2:
        log("WARNING", f"Could not parse competition/log_id from: {parent_name}")
        return None, None, working_dir, journal_file
    
    competition_name = parts[0]
    log_id = parts[1]
    
    return competition_name, log_id, working_dir, journal_file

def load_metrics_from_csv(competition_name, metrics_csv_path="metrics.csv"):
    """
    Load metric info from metrics.csv based on competition name.
    Uses startswith() matching to find the competition.
    
    Returns: {
        "metric_name": str,
        "metric_description": str,
        "goal": "maximize" or "minimize",
        "ignore_buggy_without_metric": bool,
        "default_buggy_metric": float
    }
    """
    if not os.path.exists(metrics_csv_path):
        log("WARNING", f"Metrics CSV not found: {metrics_csv_path}")
        return None
    
    try:
        with open(metrics_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use startswith() to match competition name
                if row['competition_name'].lower().startswith(competition_name.lower()):
                    return {
                        "metric_name": row['metric_name'].title(),
                        "metric_description": row['metric_description'],
                        "goal": row['goal'].lower(),
                        "ignore_buggy_without_metric": row['buggy_ignore'].lower() == 'true',
                        "default_buggy_metric": float(row['default_value_for_buggy'])
                    }
        log("WARNING", f"Competition '{competition_name}' not found in metrics CSV")
        return None
    except Exception as e:
        log("ERROR", f"Failed to parse metrics CSV: {e}")
        return None

def update_journal_viz_config(metrics_info, competition_name=None):
    """
    Update METRIC_INFO, buggy handling configs, and competition name in journal_viz_.py
    """
    if not metrics_info:
        return False
    
    try:
        # Locate the original journal_viz_.py next to this script
        script_dir = Path(__file__).resolve().parent
        src_viz = script_dir / "journal_viz_.py"
        if not src_viz.exists():
            log("ERROR", f"Could not find journal_viz_.py in {script_dir}")
            return False

        with open(src_viz, "r") as f:
            content = f.read()
        
        # Update METRIC_INFO dict - match multi-line format
        old_metric_info = r'METRIC_INFO = \{\s*"NAME":[^}]*\}'
        new_metric_info = f'''METRIC_INFO = {{
    "NAME": "{metrics_info['metric_name']}",
    "DESCRIPTION": "{metrics_info['metric_description']}",
    "GOAL": "{metrics_info['goal']}" # Use "maximize" or "minimize"
}}'''
        content = re.sub(old_metric_info, new_metric_info, content, flags=re.DOTALL)
        
        # Update IGNORE_BUGGY_WITHOUT_METRIC
        content = re.sub(
            r'IGNORE_BUGGY_WITHOUT_METRIC = \w+',
            f'IGNORE_BUGGY_WITHOUT_METRIC = {str(metrics_info["ignore_buggy_without_metric"])}',
            content
        )
        
        # Update DEFAULT_BUGGY_METRIC
        content = re.sub(
            r'DEFAULT_BUGGY_METRIC = [\d\-\.]+',
            f'DEFAULT_BUGGY_METRIC = {metrics_info["default_buggy_metric"]}',
            content
        )
        
        # Update COMPETITION_NAME for description loading
        if competition_name:
            content = re.sub(
                r'COMPETITION_NAME = "[^"]*"',
                f'COMPETITION_NAME = "{competition_name}"',
                content
            )
        
        # Write the updated viz script into the current working directory
        target_viz = Path.cwd() / "journal_viz_.py"
        with open(target_viz, "w") as f:
            f.write(content)

        log("SUCCESS", f"Copied and updated journal_viz_.py to {target_viz} with metrics for {metrics_info['metric_name']}")
        return True
    except Exception as e:
        log("ERROR", f"Failed to update journal_viz_.py: {e}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists and log status."""
    p = Path(filepath)
    if p.exists():
        try:
            size = p.stat().st_size
        except Exception:
            size = -1
        log("SUCCESS", f"Found {description}: {p} ({size} bytes)")
        return True
    else:
        log("ERROR", f"Missing {description}: {p}")
        return False


def dump_directory_contents(d):
    """Log the files in directory `d` to help debugging."""
    try:
        p = Path(d)
        if not p.exists() or not p.is_dir():
            log("INFO", f"Working directory does not exist: {p}")
            return
        log("INFO", f"Contents of {p}:")
        for child in sorted(p.iterdir()):
            try:
                sz = child.stat().st_size
            except Exception:
                sz = -1
            log("INFO", f"  - {child.name} ({'dir' if child.is_dir() else 'file'}, {sz} bytes)")
    except Exception as e:
        log("WARNING", f"Could not list directory contents: {e}")

def run_judge_journal(working_dir):
    """Execute judge_journal.py with output files saved to working_dir"""
    log("STEP", "STEP 1: Judging Journal Entries")
    
    # Check prerequisites
    if not check_file_exists("journal.json", "Input journal"):
        dump_directory_contents(working_dir)
        return False
    
    # Check for API keys
    has_gemini = os.getenv("GOOGLE_API_KEY")
    has_openai = os.getenv("OPENAI_API_KEY")
    
    if not (has_gemini or has_openai):
        log("WARNING", "No API keys found (GOOGLE_API_KEY or OPENAI_API_KEY)")
        log("WARNING", "Set environment variables or edit judge_journal.py with your keys")
    
    log("INFO", "Running judge_journal.py...")
    try:
        # Prefer a copy in working_dir, otherwise run the script next to this orchestrator
        script_dir = Path(__file__).resolve().parent
        script_path = working_dir / "judge_journal.py"
        if not script_path.exists():
            script_path = script_dir / "judge_journal.py"

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            cwd=str(working_dir)  # Run in working directory so outputs are written there
        )
        
        if result.returncode != 0:
            log("ERROR", f"judge_journal.py failed with return code {result.returncode}")
            if result.stdout:
                log("ERROR", f"stdout: {result.stdout}")
            if result.stderr:
                log("ERROR", f"stderr: {result.stderr}")
            dump_directory_contents(working_dir)
            return False

        if result.stdout:
            log("INFO", result.stdout)
        
        # Verify output in working directory
        output_file = working_dir / "journal_with_judgements.json"
        if output_file.exists():
            log("SUCCESS", f"Output saved to {output_file.name}")
            return True
        else:
            log("ERROR", "journal_with_judgements.json not created")
            return False
            
    except subprocess.TimeoutExpired:
        log("ERROR", "judge_journal.py timed out after 1 hour")
        dump_directory_contents(working_dir)
        return False
    except Exception as e:
        log("ERROR", f"Exception running judge_journal.py: {e}")
        log("ERROR", traceback.format_exc())
        dump_directory_contents(working_dir)
        return False

def run_plan_judge(working_dir):
    """Execute plan_judge.py with output files saved to working_dir"""
    log("STEP", "STEP 2: Analyzing Plan Redundancy")
    
    # Check prerequisites
    input_file = working_dir / "journal_with_judgements.json"
    if not input_file.exists():
        log("ERROR", f"Missing input: {input_file.name}")
        dump_directory_contents(working_dir)
        return False
    
    log("INFO", "Running plan_judge.py...")
    try:
        # Prefer a copy in working_dir, otherwise run the script next to this orchestrator
        script_dir = Path(__file__).resolve().parent
        script_path = working_dir / "plan_judge.py"
        if not script_path.exists():
            script_path = script_dir / "plan_judge.py"

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes timeout
            cwd=str(working_dir)  # Run in working directory so outputs are written there
        )
        
        if result.returncode != 0:
            log("ERROR", f"plan_judge.py failed with return code {result.returncode}")
            if result.stdout:
                log("ERROR", f"stdout: {result.stdout}")
            if result.stderr:
                log("ERROR", f"stderr: {result.stderr}")
            dump_directory_contents(working_dir)
            return False

        if result.stdout:
            log("INFO", result.stdout)
        
        # Verify output in working directory
        output_file = working_dir / "plan_redundancy_report.json"
        if output_file.exists():
            log("SUCCESS", f"Output saved to {output_file.name}")
            return True
        else:
            log("ERROR", "plan_redundancy_report.json not created")
            return False
            
    except subprocess.TimeoutExpired:
        log("ERROR", "plan_judge.py timed out after 30 minutes")
        dump_directory_contents(working_dir)
        return False
    except Exception as e:
        log("ERROR", f"Exception running plan_judge.py: {e}")
        log("ERROR", traceback.format_exc())
        dump_directory_contents(working_dir)
        return False

def run_visualization(output_file, working_dir):
    """Execute journal_viz_.py with output files saved to working_dir"""
    log("STEP", "STEP 3: Generating Visualization Dashboard")
    
    # Check prerequisites
    input_file1 = working_dir / "journal_with_judgements.json"
    if not input_file1.exists():
        log("ERROR", f"Missing input: {input_file1.name}")
        dump_directory_contents(working_dir)
        return False
    
    input_file2 = working_dir / "plan_redundancy_report.json"
    if not input_file2.exists():
        log("WARNING", "Plan redundancy report not found. Visualization may be incomplete.")
    
    log("INFO", "Running journal_viz_.py...")
    
    # Temporarily update OUTPUT_FILE in journal_viz_.py if custom output specified
    original_content = None
    script_dir = Path(__file__).resolve().parent
    # Determine source viz script (prefer working_dir copy, else script_dir)
    src_viz = working_dir / "journal_viz_.py"
    if not src_viz.exists():
        src_viz = script_dir / "journal_viz_.py"

    if output_file != "journal_viz_tree_dashboard.html":
        log("INFO", f"Using custom output file: {output_file}")

        # Read the current journal_viz_.py (source)
        try:
            with open(src_viz, "r") as f:
                viz_content = f.read()

            # Replace OUTPUT_FILE
            original_content = None
            target_viz = working_dir / "journal_viz_.py"
            if target_viz.exists():
                try:
                    with open(target_viz, "r") as f:
                        original_content = f.read()
                except Exception:
                    original_content = None

            viz_content = viz_content.replace(
                'OUTPUT_FILE = "journal_viz_tree_dashboard.html"',
                f'OUTPUT_FILE = "{output_file}"'
            )

            # Write temporary version into working_dir
            with open(target_viz, "w") as f:
                f.write(viz_content)
        except Exception as e:
            log("WARNING", f"Could not update OUTPUT_FILE: {e}")
    
    try:
        # Prefer working_dir copy, otherwise run script next to orchestrator
        script_path = working_dir / "journal_viz_.py"
        if not script_path.exists():
            script_path = script_dir / "journal_viz_.py"

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
            cwd=str(working_dir)  # Run in working directory so outputs are written there
        )

        if result.returncode != 0:
            log("ERROR", f"journal_viz_.py failed with return code {result.returncode}")
            if result.stdout:
                log("ERROR", f"stdout: {result.stdout}")
            if result.stderr:
                log("ERROR", f"stderr: {result.stderr}")
            dump_directory_contents(working_dir)
            return False

        if result.stdout:
            log("INFO", result.stdout)

        # Verify output in working directory
        output_path = working_dir / output_file
        if output_path.exists():
            log("SUCCESS", f"Visualization generated: {output_file}")
            return True
        else:
            log("ERROR", f"Output file not created: {output_file}")
            dump_directory_contents(working_dir)
            return False

    except subprocess.TimeoutExpired:
        log("ERROR", "journal_viz_.py timed out after 10 minutes")
        dump_directory_contents(working_dir)
        return False
    except Exception as e:
        log("ERROR", f"Exception running journal_viz_.py: {e}")
        log("ERROR", traceback.format_exc())
        dump_directory_contents(working_dir)
        return False
    finally:
        # Restore original journal_viz_.py if modified
        if original_content:
            try:
                with open("journal_viz_.py", "w") as f:
                    f.write(original_content)
                log("INFO", "Restored original journal_viz_.py")
            except Exception as e:
                log("WARNING", f"Could not restore journal_viz_.py: {e}")

def setup_working_directory(working_dir):
    """Change to working directory and copy necessary files."""
    try:
        os.chdir(working_dir)
        log("SUCCESS", f"Working directory: {working_dir}")
        return True
    except Exception as e:
        log("ERROR", f"Failed to change to working directory: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Automate the visualization pipeline with dynamic metric configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_visualization_pipeline.py ~/data/tensorflow2-question-answering_abc123/logs/journal.json
  python run_visualization_pipeline.py ~/data/tensorflow2-question-answering_abc123/logs --skip-judge
  python run_visualization_pipeline.py ~/data/tensorflow2-question-answering_abc123/logs --output final.html
        """
    )
    
    parser.add_argument(
        "journal_path",
        nargs="?",
        help="Path to journal.json or parent directory (format: .../competition_name_logid/logs)"
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip judgment step (use existing journal_with_judgements.json)"
    )
    parser.add_argument(
        "--skip-plan",
        action="store_true",
        help="Skip plan redundancy analysis"
    )
    parser.add_argument(
        "--output",
        default="journal_viz_tree_dashboard.html",
        help="Output HTML file (default: journal_viz_tree_dashboard.html)"
    )
    parser.add_argument(
        "--metrics",
        default="metrics.csv",
        help="Path to metrics.csv (default: metrics.csv)"
    )
    
    args = parser.parse_args()
    
    # Print header
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   VISUALIZATION PIPELINE ORCHESTRATOR                    ║")
    print("║   Automated: Judge → Analyze Plans → Generate Dashboard  ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    # Parse journal path and load metrics
    if args.journal_path:
        log("STEP", "STEP 0: Loading Configuration")
        competition_name, log_id, working_dir, journal_file = parse_journal_path(args.journal_path)
        
        if not journal_file:
            log("ERROR", f"Could not find journal.json in {args.journal_path}")
            return 1
        
        log("SUCCESS", f"Found journal.json: {journal_file}")
        
        if competition_name and log_id:
            log("SUCCESS", f"Extracted: competition={competition_name}, log_id={log_id}")
            
            # Load metrics from CSV
            metrics_info = load_metrics_from_csv(competition_name, args.metrics)
            if metrics_info:
                log("SUCCESS", f"Loaded metrics: {metrics_info['metric_name']}")
                log("INFO", f"  Goal: {metrics_info['goal']}")
                log("INFO", f"  Ignore buggy without metric: {metrics_info['ignore_buggy_without_metric']}")
                log("INFO", f"  Default buggy metric: {metrics_info['default_buggy_metric']}")
            else:
                log("WARNING", "Could not load metrics; using defaults from journal_viz_.py")
        else:
            log("WARNING", "Could not extract competition name; using defaults")
            metrics_info = None
        
        # Change to working directory
        if not setup_working_directory(working_dir):
            return 1
        
        # Update journal_viz_.py if metrics were loaded
        if metrics_info:
            if not update_journal_viz_config(metrics_info, competition_name):
                log("WARNING", "Proceeding with default configuration")
        else:
            # Still update with competition name even if no metrics
            if competition_name:
                update_journal_viz_config({"metric_name": "Score", "metric_description": "Metric", "goal": "maximize", "ignore_buggy_without_metric": False, "default_buggy_metric": -0.1}, competition_name)
    else:
        log("INFO", "No journal path provided; using current directory")
        working_dir = Path.cwd()
        metrics_info = None
    
    # Track success
    steps_completed = []
    steps_failed = []
    
    # Step 1: Judge Journal
    if args.skip_judge:
        log("INFO", "Skipping judgment step (--skip-judge)")
        if check_file_exists(str(working_dir / "journal_with_judgements.json"), "journal_with_judgements.json"):
            steps_completed.append("judge")
        else:
            log("ERROR", "Cannot skip judge step: journal_with_judgements.json not found")
            steps_failed.append("judge")
    else:
        if run_judge_journal(working_dir):
            steps_completed.append("judge")
        else:
            steps_failed.append("judge")
    
    # Step 2: Plan Redundancy Analysis
    if steps_failed and "judge" in steps_failed:
        log("ERROR", "Skipping plan analysis due to judge failure")
        steps_failed.append("plan")
    elif args.skip_plan:
        log("INFO", "Skipping plan analysis (--skip-plan)")
        steps_completed.append("plan")
    else:
        if run_plan_judge(working_dir):
            steps_completed.append("plan")
        else:
            steps_failed.append("plan")
    
    # Step 3: Generate Visualization
    if steps_failed and "judge" in steps_failed:
        log("ERROR", "Skipping visualization due to judge failure")
        steps_failed.append("viz")
    else:
        if run_visualization(args.output, working_dir):
            steps_completed.append("viz")
        else:
            steps_failed.append("viz")
    
    # Print summary
    log("STEP", "PIPELINE SUMMARY")
    log("SUCCESS", f"Completed: {', '.join(steps_completed) if steps_completed else 'None'}")
    if steps_failed:
        log("ERROR", f"Failed: {', '.join(steps_failed)}")
        print(f"\n{Colors.RED}Pipeline FAILED{Colors.END}\n")
        return 1
    else:
        print(f"\n{Colors.GREEN}Pipeline COMPLETED SUCCESSFULLY{Colors.END}")
        print(f"\n{Colors.BOLD}Output:{Colors.END}")
        print(f"  • journal_with_judgements.json")
        print(f"  • plan_redundancy_report.json")
        print(f"  • {args.output}")
        print()
        return 0

if __name__ == "__main__":
    sys.exit(main())

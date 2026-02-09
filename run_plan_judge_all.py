#!/usr/bin/env python3
"""
Run plan_judge.py on all journal_with_judgements.json files to analyze plan redundancy.

This script:
1. Finds all journal_with_judgements.json files under runs/
2. Runs plan_judge.py on each file to analyze plan redundancy
3. Saves updated files with redundancy analysis

Usage:
    python run_plan_judge_all.py [--apply] [--limit N]
    
    --apply    Actually run plan_judge (default is dry-run)
    --limit N  Process only first N files
"""

import json
import sys
import subprocess
import time
from pathlib import Path

def get_analyzed_nodes(logs_dir):
    """
    Get the set of node IDs that have already been analyzed in plan_redundancy_report.json.
    Returns a set of node IDs that already have analysis.
    """
    report_path = logs_dir / "plan_redundancy_report.json"
    
    if not report_path.exists():
        return set()
    
    try:
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Report structure is typically {node_id: analysis_result, ...}
        if isinstance(report_data, dict):
            return set(report_data.keys())
        else:
            return set()
    except:
        return set()


def get_nodes_to_analyze(journal_path):
    """
    Get the set of node IDs from journal_with_judgements.json that have multiple children.
    Returns a set of node IDs that need analysis.
    """
    try:
        with open(journal_path, 'r') as f:
            data = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(data, list):
            nodes = data
        elif isinstance(data, dict) and "nodes" in data:
            nodes = data["nodes"]
        else:
            return set()
        
        # Find nodes with multiple children
        nodes_to_analyze = set()
        for node in nodes:
            if isinstance(node, dict) and "id" in node:
                children = node.get("children", [])
                if isinstance(children, list) and len(children) > 1:
                    nodes_to_analyze.add(node["id"])
        
        return nodes_to_analyze
    except:
        return set()


def run_plan_judge(journal_path, script_dir, apply=False, max_retries=3):
    """
    Run plan_judge.py on a single journal_with_judgements.json file.
    Skips if all nodes with multiple children already have analysis in plan_redundancy_report.json.
    Returns (success, message)
    """
    
    if not journal_path.exists():
        return False, "journal_with_judgements.json not found"
    
    logs_dir = journal_path.parent
    
    # Get nodes that already have analysis
    analyzed_nodes = get_analyzed_nodes(logs_dir)
    
    # Get nodes that need analysis
    nodes_to_analyze = get_nodes_to_analyze(journal_path)
    
    # Check if all nodes have already been analyzed
    if nodes_to_analyze and nodes_to_analyze.issubset(analyzed_nodes):
        return True, f"All {len(nodes_to_analyze)} nodes with multiple children already analyzed (skipping)"
    
    if not nodes_to_analyze:
        return True, "No nodes with multiple children found (skipping)"
    
    # Check if plan_judge.py exists
    plan_judge_script = script_dir / "plan_judge.py"
    if not plan_judge_script.exists():
        return False, f"plan_judge.py not found at {plan_judge_script}"
    
    # Build command - plan_judge.py takes journal_with_judgements.json as first arg
    cmd = ["python", str(plan_judge_script), str(journal_path)]
    
    if not apply:
        unananalyzed = nodes_to_analyze - analyzed_nodes
        return True, f"Would run plan_judge ({len(unananalyzed)}/{len(nodes_to_analyze)} nodes need analysis)"
    
    try:
        saw_429 = False
        for attempt in range(1, max_retries + 1):
            # Run plan_judge.py in the logs directory with the journal file
            result = subprocess.run(
                cmd,
                cwd=str(logs_dir),
                capture_output=True,
                text=True,
                timeout=300
            )

            stdout_text = result.stdout or ""
            stderr_text = result.stderr or ""
            combined = f"{stdout_text}\n{stderr_text}".lower()

            if result.returncode == 0:
                return True, "plan_judge succeeded"

            # Retry on 429 RESOURCE_EXHAUSTED
            if "429" in combined or "resource_exhausted" in combined:
                saw_429 = True
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue

            error_msg = (stderr_text or stdout_text)[:500]
            return False, f"plan_judge failed: {error_msg}"

        if saw_429:
            return False, "plan_judge failed: 429 RESOURCE_EXHAUSTED"
        return False, "plan_judge failed after retries"

    except subprocess.TimeoutExpired:
        return False, "plan_judge timed out (>5 min)"
    except Exception as e:
        return False, f"Error running plan_judge: {str(e)[:200]}"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run plan_judge on all journal_with_judgements.json files"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually run plan_judge (default is dry-run)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit processing to N files (0 = all)"
    )
    
    args = parser.parse_args()
    
    # Find all journal_with_judgements.json files
    script_dir = Path(__file__).resolve().parent
    runs_dir = script_dir.parent / "runs"
    
    print(f"Scanning {runs_dir} for journal_with_judgements.json files...")
    print(f"Mode: {'APPLY (running plan_judge)' if args.apply else 'DRY-RUN'}\n")
    
    journal_files = list(runs_dir.glob("**/journal_with_judgements.json"))
    journal_files.sort()
    
    if not journal_files:
        print("✗ No journal_with_judgements.json files found")
        return 1
    
    print(f"Found {len(journal_files)} files\n")
    
    files_processed = 0
    files_succeeded = 0
    files_skipped = 0
    errors = 0
    total_nodes_analyzed = 0
    
    for idx, journal_path in enumerate(journal_files, 1):
        if args.limit > 0 and idx > args.limit:
            print(f"Stopping at limit of {args.limit}")
            break
        
        rel_path = journal_path.relative_to(runs_dir)
        
        print(f"[{idx}/{len(journal_files)}] {rel_path}")
        
        success, message = run_plan_judge(journal_path, script_dir, apply=args.apply)
        
        if success:
            print(f"  ✓ {message}")
            files_processed += 1
            if "skipping" in message.lower():
                files_skipped += 1
            else:
                files_succeeded += 1
                # Extract number of nodes if mentioned
                if "/" in message:
                    try:
                        parts = message.split("/")
                        total = int(parts[-1].split()[0])
                        total_nodes_analyzed += total
                    except:
                        pass
        else:
            print(f"  ✗ {message}")
            errors += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files processed: {files_processed}")
    print(f"  Files executed plan_judge: {files_succeeded}")
    print(f"  Files skipped (already analyzed): {files_skipped}")
    print(f"  Errors: {errors}")
    if args.apply and total_nodes_analyzed > 0:
        print(f"  Total nodes analyzed: {total_nodes_analyzed}")
    
    if args.apply:
        print(f"\n✓ plan_judge has been run on all files")
    else:
        print(f"\nDry-run mode. To actually run plan_judge, use --apply")
    
    print(f"{'='*60}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

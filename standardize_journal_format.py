#!/usr/bin/env python3
"""
Standardize all journal_with_judgements.json files to plain list format.

This script:
1. Finds all journal_with_judgements.json files under runs/
2. Converts dict format {nodes: [...]} to plain list format [...]
3. Preserves existing list format
4. Reports what was changed

Usage:
    python standardize_journal_format.py [--apply] [--limit N]
    
    --apply    Actually update files (default is dry-run)
    --limit N  Process only first N files
"""

import json
import sys
from pathlib import Path

def standardize_journal_file(journal_path, apply=False):
    """
    Standardize a single journal_with_judgements.json file to list format.
    Returns (success, was_changed, message)
    """
    
    try:
        with open(journal_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return False, False, f"Failed to read: {e}"
    
    # Check format
    if isinstance(data, list):
        # Already in list format
        return True, False, "Already in list format"
    
    elif isinstance(data, dict) and "nodes" in data:
        # Dict format - convert to list
        nodes = data["nodes"]
        
        if apply:
            try:
                with open(journal_path, 'w') as f:
                    json.dump(nodes, f, indent=2)
                return True, True, f"Converted dict format to list format ({len(nodes)} nodes)"
            except Exception as e:
                return False, False, f"Failed to write: {e}"
        else:
            return True, True, f"Would convert dict format to list format ({len(nodes)} nodes)"
    
    else:
        return False, False, "Unexpected format (not a list or dict with 'nodes')"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Standardize journal_with_judgements.json files to list format"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually update files (default is dry-run)"
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
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}\n")
    
    journal_files = list(runs_dir.glob("**/journal_with_judgements.json"))
    journal_files.sort()
    
    if not journal_files:
        print("✗ No journal_with_judgements.json files found")
        return 1
    
    print(f"Found {len(journal_files)} files\n")
    
    total_converted = 0
    files_processed = 0
    files_changed = 0
    errors = 0
    
    for idx, journal_path in enumerate(journal_files, 1):
        if args.limit > 0 and idx > args.limit:
            print(f"Stopping at limit of {args.limit}")
            break
        
        rel_path = journal_path.relative_to(runs_dir)
        
        print(f"[{idx}/{len(journal_files)}] {rel_path}")
        
        success, was_changed, message = standardize_journal_file(journal_path, apply=args.apply)
        
        if success:
            print(f"  ✓ {message}")
            files_processed += 1
            if was_changed:
                files_changed += 1
                total_converted += 1
        else:
            print(f"  ✗ {message}")
            errors += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files processed: {files_processed}")
    print(f"  Files converted: {files_changed}")
    print(f"  Errors: {errors}")
    
    if args.apply:
        print(f"\n✓ Changes applied to files")
    else:
        print(f"\nDry-run mode. To apply changes, re-run with --apply")
    
    print(f"{'='*60}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

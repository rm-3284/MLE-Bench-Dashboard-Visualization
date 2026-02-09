#!/usr/bin/env python3
"""
Update journal_with_judgements.json using node2parent mapping from journal.json.

This script:
1. Reads journal.json to extract node2parent mapping
2. Reads journal_with_judgements.json (list of nodes with 'id' field)
3. Uses the node2parent mapping to update parent-children relationships based on node IDs
4. Saves the modified journal_with_judgements.json

Usage:
    python update_tree_structure.py [--apply] [--limit N]
    
    --apply    Actually update files (default is dry-run, just shows what would change)
    --limit N  Process only first N files
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def update_journal_file(logs_dir, apply=False):
    """
    Update journal_with_judgements.json in logs_dir using node2parent from journal.json.
    Returns (success, changes_made, message)
    """
    
    journal_path = logs_dir / "journal.json"
    journal_judged_path = logs_dir / "journal_with_judgements.json"
    
    # Check if both files exist
    if not journal_path.exists():
        return False, 0, "journal.json not found"
    
    if not journal_judged_path.exists():
        return False, 0, "journal_with_judgements.json not found"
    
    # Read journal.json to get node2parent mapping
    try:
        with open(journal_path, 'r') as f:
            journal_data = json.load(f)
    except Exception as e:
        return False, 0, f"Failed to read journal.json: {e}"
    
    # Extract node2parent mapping from journal.json
    node2parent = {}
    if isinstance(journal_data, dict):
        node2parent = journal_data.get("node2parent", {})
    
    if not node2parent:
        return True, 0, "No node2parent mapping found"
    
    # Read journal_with_judgements.json
    try:
        with open(journal_judged_path, 'r') as f:
            judged_data = json.load(f)
    except Exception as e:
        return False, 0, f"Failed to read journal_with_judgements.json: {e}"
    
    # Handle both formats: plain list or dict with "nodes" key
    if isinstance(judged_data, list):
        judged_nodes = judged_data
        is_dict_format = False
    elif isinstance(judged_data, dict) and "nodes" in judged_data:
        judged_nodes = judged_data["nodes"]
        is_dict_format = True
    else:
        return False, 0, "journal_with_judgements.json has unexpected format (not a list or dict with 'nodes')"
    
    # Build ID-to-node mapping for quick lookup
    # Each node has an 'id' field
    node_by_id = {}
    for node in judged_nodes:
        if isinstance(node, dict) and "id" in node:
            node_by_id[node["id"]] = node
    
    # Build parent and children mappings from node2parent
    # node2parent is {child_node_id: parent_node_id, ...}
    children_map = defaultdict(list)
    parent_map = {}
    
    for child_id, parent_id in node2parent.items():
        parent_map[child_id] = parent_id
        children_map[parent_id].append(child_id)
    
    # Update nodes with correct parent and children relationships
    changes_made = 0
    
    for node in judged_nodes:
        if not isinstance(node, dict) or "id" not in node:
            continue
        
        node_id = node["id"]
        
        # Update parent field based on node2parent mapping
        if node_id in parent_map:
            new_parent = parent_map[node_id]
            old_parent = node.get("parent")
            
            if old_parent != new_parent:
                node["parent"] = new_parent
                changes_made += 1
        else:
            # Root node or unmapped node - should have no parent
            old_parent = node.get("parent")
            if old_parent is not None:
                node["parent"] = None
                changes_made += 1
        
        # Update children list based on children_map
        if node_id in children_map:
            new_children = sorted(children_map[node_id])
            old_children = node.get("children", [])
            
            if old_children != new_children:
                node["children"] = new_children
                changes_made += 1
        else:
            # No children for this node
            if node.get("children"):
                node["children"] = []
                changes_made += 1
            elif "children" not in node:
                node["children"] = []
    
    # Write updated data if apply flag is set
    if apply:
        try:
            # Write back in the same format as it was read
            if is_dict_format:
                judged_data["nodes"] = judged_nodes
                with open(journal_judged_path, 'w') as f:
                    json.dump(judged_data, f, indent=2)
            else:
                # Plain list format
                with open(journal_judged_path, 'w') as f:
                    json.dump(judged_nodes, f, indent=2)
            
            return True, changes_made, f"Updated {changes_made} node relationships"
        except Exception as e:
            return False, 0, f"Failed to write journal_with_judgements.json: {e}"
    
    if changes_made == 0:
        return True, changes_made, "No changes needed"
    else:
        return True, changes_made, f"Would update {changes_made} node relationships (dry-run)"

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update tree structure using node2parent mapping from journal.json"
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
    
    # Find all journal.json files (source of node2parent mapping)
    script_dir = Path(__file__).resolve().parent
    runs_dir = script_dir.parent / "runs"
    
    print(f"Scanning {runs_dir} for journal.json files (to extract node2parent mapping)...")
    print(f"Will update corresponding journal_with_judgements.json files\n")
    
    journal_files = list(runs_dir.glob("**/logs/journal.json"))
    
    if not journal_files:
        print("✗ No journal.json files found")
        return 1
    
    journal_files.sort()
    print(f"Found {len(journal_files)} journal.json files\n")
    
    total_changes = 0
    files_updated = 0
    files_processed = 0
    errors = 0
    
    for idx, journal_path in enumerate(journal_files, 1):
        if args.limit > 0 and idx > args.limit:
            print(f"Stopping at limit of {args.limit}")
            break
        
        logs_dir = journal_path.parent
        rel_path = journal_path.relative_to(runs_dir)
        
        print(f"[{idx}/{len(journal_files)}] Processing: {journal_path}")
        print(f"         Relative: {rel_path}")
        
        success, changes, message = update_journal_file(logs_dir, apply=args.apply)
        
        if success:
            print(f"  ✓ {message}")
            files_processed += 1
            total_changes += changes
            if changes > 0:
                files_updated += 1
        else:
            print(f"  ✗ {message}")
            errors += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files processed: {files_processed}")
    print(f"  Files updated: {files_updated}")
    print(f"  Total relationship changes: {total_changes}")
    print(f"  Errors: {errors}")
    
    if args.apply:
        print(f"\n✓ Changes applied to journal_with_judgements.json files")
    else:
        print(f"\nDry-run mode. To apply changes, re-run with --apply")
    
    print(f"{'='*60}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

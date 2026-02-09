#!/usr/bin/env python3
"""
Debug script to check what nodes have multiple children and what's already analyzed.
Also runs plan_judge.py to see its output.
"""

import json
import subprocess
from pathlib import Path

# Check one example directory
runs_dir = Path("/Users/ryomitsuhashi/Desktop/Princeton/Research/MLE bench/runs")
example_journal = runs_dir / "2025-12-17T20-27-55-GMT_run-group_aide/tensorflow2-question-answering_a3cf875b-2303-466b-bd8d-5a2820cd34b3/logs/journal_with_judgements.json"
example_report = example_journal.parent / "plan_redundancy_report.json"
logs_dir = example_journal.parent

print("=" * 60)
print("Checking example directory:")
print(f"Journal path: {example_journal}")
print(f"Exists: {example_journal.exists()}")
print()

# Check journal_with_judgements.json
if example_journal.exists():
    with open(example_journal, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        nodes = data
    elif isinstance(data, dict) and "nodes" in data:
        nodes = data["nodes"]
    else:
        nodes = []
    
    print(f"Total nodes in journal: {len(nodes)}")
    
    # Find nodes with multiple children
    multi_child_nodes = []
    for node in nodes:
        if isinstance(node, dict) and "id" in node:
            children = node.get("children", [])
            if isinstance(children, list) and len(children) > 1:
                multi_child_nodes.append({
                    "id": node["id"],
                    "children_count": len(children),
                    "children": children[:3]  # Show first 3
                })
    
    print(f"Nodes with multiple children: {len(multi_child_nodes)}")
    if multi_child_nodes:
        print("\nFirst 3 examples:")
        for node in multi_child_nodes[:3]:
            print(f"  - Node ID: {node['id']}")
            print(f"    Children count: {node['children_count']}")
            print(f"    Children (first 3): {node['children']}")
    else:
        print("  (none found)")

print()
print("=" * 60)
print("Checking plan_redundancy_report.json BEFORE running plan_judge:")
print(f"Report path: {example_report}")
print(f"Exists: {example_report.exists()}")

if example_report.exists():
    with open(example_report, 'r') as f:
        report = json.load(f)
    
    print(f"Report type: {type(report)}")
    if isinstance(report, dict):
        print(f"Report keys/entries: {len(report)}")
        if report:
            print("Sample entries:")
            for node_id in list(report.keys())[:3]:
                print(f"  - {node_id}")
else:
    print("(Does not exist yet)")

print()
print("=" * 60)
print("Running plan_judge.py...")
print()

plan_judge_script = Path("/Users/ryomitsuhashi/Desktop/Princeton/Research/MLE bench/visualization_final/plan_judge.py")
cmd = ["python", str(plan_judge_script)]

try:
    result = subprocess.run(
        cmd,
        cwd=str(logs_dir),
        capture_output=True,
        text=True,
        timeout=300
    )
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    print(f"\nReturn code: {result.returncode}")
except Exception as e:
    print(f"Error running plan_judge: {e}")

print()
print("=" * 60)
print("Checking plan_redundancy_report.json AFTER running plan_judge:")
print(f"Report path: {example_report}")
print(f"Exists: {example_report.exists()}")

if example_report.exists():
    with open(example_report, 'r') as f:
        report = json.load(f)
    
    print(f"Report type: {type(report)}")
    if isinstance(report, dict):
        print(f"Report keys/entries: {len(report)}")
        if report:
            print("Sample entries:")
            for node_id in list(report.keys())[:3]:
                print(f"  - {node_id}: {report[node_id]}")
        else:
            print("(Report is empty - no redundancy found)")
    else:
        print(f"Report length: {len(report)}")

print("=" * 60)

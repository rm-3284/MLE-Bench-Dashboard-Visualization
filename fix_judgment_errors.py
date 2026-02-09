#!/usr/bin/env python3
"""
Fix judgment errors (e.g., 429 API rate limit errors) in journal_with_judgements.json 
by re-judging problematic entries with context preserved.

Usage:
    python fix_judgment_errors.py /path/to/journal_with_judgements.json
"""

import json
import sys
import os
import difflib
import time
from pathlib import Path

# Import LLM functions from judge_journal
sys.path.insert(0, str(Path(__file__).parent))
try:
    from judge_journal import get_llm_response
except ImportError:
    print("✗ Cannot import judge_journal module")
    sys.exit(1)

# Retry logic for rate limits
def get_llm_response_with_retry(sys_p, usr_p, max_retries=3):
    """Call LLM with exponential backoff on 429 errors."""
    for attempt in range(max_retries):
        try:
            result = get_llm_response(sys_p, usr_p)
            
            # Check if we got a rate limit error
            if isinstance(result, dict) and result.get("status") == "error":
                if "429" in result.get("reason", ""):
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    print(f"  ⚠ Rate limit (429), waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
            
            return result
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  ⚠ Rate limit error, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            raise
    
    return {"status": "error", "reason": "Max retries exceeded for rate limit"}

def load_journal(journal_path):
    """Load journal file."""
    with open(journal_path, 'r') as f:
        raw_data = json.load(f)
    
    if isinstance(raw_data, dict) and "nodes" in raw_data:
        return raw_data["nodes"], raw_data
    elif isinstance(raw_data, list):
        return raw_data, {"nodes": raw_data}
    else:
        raise ValueError("Unknown JSON structure")

def identify_error_entries(nodes):
    """Identify entries with judgment errors (status == "error")."""
    error_indices = []
    
    for i, node in enumerate(nodes):
        judgment = node.get("llm_judgment", {})
        if isinstance(judgment, dict) and judgment.get("status") == "error":
            reason = judgment.get("reason", "unknown error")
            error_indices.append((i, reason))
    
    return error_indices

def rejudge_entry(node, prev_code=None):
    """
    Re-judge a single entry using the LLM.
    Returns the judgment result.
    """
    curr_code = node.get('code', '')
    plan = node.get('plan', '')
    
    # Compute Diff
    diff = "\n".join(difflib.unified_diff(
        (prev_code or "").splitlines(), 
        curr_code.splitlines(), 
        lineterm=""
    ))
    
    # Skip if no meaningful changes
    if not diff.strip() or not plan.strip():
        return {"status": "skipped", "reason": "No meaningful code changes or plan."}
    
    # Call API with retry logic
    if len(diff) > 15000:
        diff = diff[:15000] + "\n...[Diff Truncated]"
    
    sys_p = "You are a senior code reviewer. Verify if the code changes strictly implement the user's plan."
    usr_p = f"PLAN:\n{plan}\n\nCODE DIFF:\n{diff}\n\nRespond with JSON: {{ 'status': 'aligned'|'partial'|'deviated', 'reason': 'concise explanation' }}"
    
    judgment = get_llm_response_with_retry(sys_p, usr_p)
    time.sleep(2)  # Longer delay to avoid rate limits
    
    return judgment

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_judgment_errors.py /path/to/journal_with_judgements.json")
        sys.exit(1)
    
    journal_path = sys.argv[1]
    
    if not Path(journal_path).exists():
        print(f"✗ File not found: {journal_path}")
        sys.exit(1)
    
    print(f"Analyzing {journal_path}...")
    nodes, raw_data = load_journal(journal_path)
    error_indices = identify_error_entries(nodes)
    
    if not error_indices:
        print(f"✓ No errors found in {journal_path}")
        return
    
    print(f"\nFound {len(error_indices)} entries with errors:")
    for idx, reason in error_indices[:5]:
        step = nodes[idx].get("step", "?")
        reason_short = reason[:80] + "..." if len(reason) > 80 else reason
        print(f"  - Entry {idx} (step {step}): {reason_short}")
    
    if len(error_indices) > 5:
        print(f"  ... and {len(error_indices) - 5} more")
    
    # Re-judge error entries
    print(f"\nRe-judging {len(error_indices)} error entries...")
    fixed_count = 0
    failed_count = 0
    
    # Build previous code map for context
    prev_codes = {}
    for i in range(len(nodes)):
        prev_codes[i] = nodes[i-1].get('code', '') if i > 0 else None
    
    for idx, _ in error_indices:
        try:
            step_num = nodes[idx].get("step", idx)
            print(f"  [{fixed_count + 1}/{len(error_indices)}] Judging step {step_num}...", end=" ", flush=True)
            
            new_judgment = rejudge_entry(nodes[idx], prev_codes[idx])
            nodes[idx]["llm_judgment"] = new_judgment
            
            status = new_judgment.get("status", "unknown")
            
            # Only count as fixed if status is NOT "error"
            if status == "error":
                print(f"[{status.upper()}] ✗ Still has error")
                failed_count += 1
            else:
                print(f"[{status.upper()}] ✓")
                fixed_count += 1
            
        except Exception as e:
            print(f"✗ Failed: {e}")
            failed_count += 1
    
    if fixed_count == 0:
        print(f"\n✗ Failed to fix any entries")
        return False
    
    # Only auto-replace if all fixed entries succeeded (no failed ones)
    if failed_count > 0:
        fixed_path = str(journal_path).replace(".json", "_fixed.json")
        with open(fixed_path, 'w') as f:
            json.dump(raw_data if "nodes" in raw_data else nodes, f, indent=2)
        
        print(f"\n⚠ Fixed {fixed_count} entries but {failed_count} still have errors")
        print(f"⚠ Saved to: {fixed_path}")
        print(f"Review before applying: mv {fixed_path} {journal_path}")
        return False
    else:
        # All entries successfully fixed - replace original
        with open(journal_path, 'w') as f:
            json.dump(raw_data if "nodes" in raw_data else nodes, f, indent=2)
        
        print(f"\n✓ Successfully fixed all {fixed_count} error entries")
        print(f"✓ Updated: {journal_path}")
        return True

if __name__ == "__main__":
    main()

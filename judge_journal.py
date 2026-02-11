import os
import json
import difflib
import time
import sys
from collections import defaultdict

# --- CONFIGURATION ---
INPUT_JSON = "journal.json"
OUTPUT_DATA = "journal_with_judgements.json"

# API Setup (Gemini or OpenAI)
LLM_PROVIDER = "gemini" 
GEMINI_MODEL = "gemini-2.0-flash" 
OPENAI_MODEL = "gpt-4o"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or "YOUR_GOOGLE_KEY_HERE"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_KEY_HERE"

def get_llm_response(sys_prompt, usr_prompt, max_retries=3):
    """Handles API calls to the selected provider with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            if LLM_PROVIDER == "gemini":
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=GOOGLE_API_KEY)
                resp = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=usr_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                return json.loads(resp.text)
            elif LLM_PROVIDER == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                resp = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role":"system","content":sys_prompt},{"role":"user","content":usr_prompt}],
                    response_format={"type":"json_object"}, temperature=0.1
                )
                return json.loads(resp.choices[0].message.content)
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"\n  ⚠ Rate limit (429), waiting {wait_time}s before retry...", flush=True)
                time.sleep(wait_time)
                continue
            # Return error on final attempt or non-429 errors
            return {"status": "error", "reason": str(e)}
    
    return {"status": "error", "reason": "Unknown provider"}

def build_tree_structure(steps, node2parent):
    """
    Update parent and children relationships in steps based on node2parent mapping.
    
    Args:
        steps: List of node dictionaries with 'id' field
        node2parent: Dict mapping child_node_id -> parent_node_id
    """
    # Build parent and children mappings from node2parent
    children_map = defaultdict(list)
    parent_map = {}
    
    for child_id, parent_id in node2parent.items():
        parent_map[child_id] = parent_id
        children_map[parent_id].append(child_id)
    
    # Update nodes with correct parent and children relationships
    for node in steps:
        if not isinstance(node, dict) or "id" not in node:
            continue
        
        node_id = node["id"]
        
        # Update parent field based on node2parent mapping
        if node_id in parent_map:
            node["parent"] = parent_map[node_id]
        else:
            # Root node or unmapped node - should have no parent
            node["parent"] = None
        
        # Update children list based on children_map
        if node_id in children_map:
            node["children"] = sorted(children_map[node_id])
        else:
            # No children for this node
            node["children"] = []


def main():
    if not os.path.exists(INPUT_JSON):
        print(f"Error: {INPUT_JSON} not found.")
        sys.exit(1)

    print(f"Reading {INPUT_JSON}...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Extract node2parent mapping if available
    node2parent = {}
    if isinstance(raw_data, dict):
        node2parent = raw_data.get("node2parent", {})
    
    # Handle different JSON structures (list vs dict)
    if isinstance(raw_data, dict) and "nodes" in raw_data:
        steps = raw_data["nodes"]
        is_dict_format = True
    elif isinstance(raw_data, list):
        steps = raw_data
        is_dict_format = False
    else:
        print("Error: Unknown JSON structure.")
        sys.exit(1)

    steps.sort(key=lambda x: x.get('step', 0))
    print(f"Loaded {len(steps)} steps. Starting judgement...")

    prev_code = None
    for i, step in enumerate(steps):
        # Skip if already judged (optional, remove check to force re-run)
        if 'llm_judgment' in step and step['llm_judgment'].get('status') != 'error':
            prev_code = step.get('code', '')
            continue

        curr_code = step.get('code', '')
        plan = step.get('plan', '')
        
        # Compute Diff
        diff = "\n".join(difflib.unified_diff(
            (prev_code or "").splitlines(), 
            curr_code.splitlines(), 
            lineterm=""
        ))

        # Call API if there is a plan and code change
        if not diff.strip() or not plan.strip():
            judgment = {"status": "skipped", "reason": "No meaningful code changes or plan."}
        else:
            print(f"Judging Step {step.get('step')}...", end=" ", flush=True)
            if len(diff) > 15000: diff = diff[:15000] + "\n...[Diff Truncated]"
            
            sys_p = "You are a senior code reviewer. Verify if the code changes strictly implement the user's plan."
            usr_p = f"PLAN:\n{plan}\n\nCODE DIFF:\n{diff}\n\nRespond with JSON: {{ 'status': 'aligned'|'partial'|'deviated', 'reason': 'concise explanation' }}"
            
            judgment = get_llm_response(sys_p, usr_p)
            print(f"[{judgment.get('status', 'ERR').upper()}]")
            time.sleep(2)  # Longer delay to avoid rate limits

        step['llm_judgment'] = judgment
        prev_code = curr_code

    # Build tree structure from node2parent mapping
    if node2parent:
        print("Building tree structure from node2parent mapping...")
        build_tree_structure(steps, node2parent)

    # Save Results as a list
    with open(OUTPUT_DATA, 'w', encoding='utf-8') as f:
        json.dump(steps, f, indent=4)
    
    print(f"\n✅ Judgments saved to: {OUTPUT_DATA}")

if __name__ == "__main__":
    main()

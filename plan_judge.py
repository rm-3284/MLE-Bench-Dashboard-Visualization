import json
from collections import defaultdict
from google import genai
import sys
import os

# --- CONFIGURATION ---
client = genai.Client(api_key="")
MODEL_ID = "gemini-2.0-flash"

def judge_plans_with_gemini(plans_list):
    """
    Groups plans by semantic intent using Gemini.
    Returns a list of lists containing indices.
    """
    if not plans_list or len(plans_list) < 2:
        return []

    # The prompt explicitly tells Gemini to ignore wording and look for intent
    prompt = f"""
    You are an AI research auditor. Analyze the following list of research plans.
    Identify which plans have the SAME technical intent or hypothesis, even if phrased differently.
    
    Plans:
    {chr(10).join([f"{i}: {p}" for i, p in enumerate(plans_list)])}
    
    Output ONLY a JSON list of lists, where each sub-list contains the indices of plans that are identical.
    Example: [[0, 2], [1, 3, 4]]
    If no plans are identical, return [].
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID, 
            contents=prompt
        )
        print(prompt) # Debug: Show the prompt sent to Gemini
        print(f"Gemini response: {response.text}") # Debug: Show raw response
        # Clean potential markdown from the response
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        return json.loads(text)
    except Exception as e:
        print(f"Error during LLM inference: {e}")
        return []

def analyze_all_plans(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Group nodes by parent to compare siblings
    parent_map = defaultdict(list)
    for node in data:
        parent_map[node.get('parent')].append(node)

    all_judgements = {}

    for pid, children in parent_map.items():
        if not pid or len(children) < 2:
            continue
        
        # Display short parent ID for tracking
        display_id = pid[:8] if pid else "Root"
        print(f"Judging {len(children)} sibling plans for Parent {display_id}...")
        
        plans = [c.get('plan', 'No plan provided') for c in children]
        groups = judge_plans_with_gemini(plans)
        
        # Map indices back to the actual Step numbers for clarity
        step_groups = []
        for group in groups:
            step_group = [children[idx]['step'] for idx in group]
            step_groups.append(sorted(step_group))
        
        if step_groups:
            all_judgements[pid] = step_groups

    # Save output to a separate file
    parent_dir = os.path.dirname(json_file)
    output_filename = os.path.join(parent_dir, 'plan_redundancy_report.json')
    with open(output_filename, 'w') as f:
        json.dump(all_judgements, f, indent=2)
    
    print(f"\nAudit complete. Found redundancy in {len(all_judgements)} parent branches.")
    print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'journal_with_judgements.json'
    analyze_all_plans(filepath)

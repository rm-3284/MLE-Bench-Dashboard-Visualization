import json
from collections import defaultdict
from google import genai
from openai import OpenAI
import sys
import os
import argparse

# --- CONFIGURATION ---
gemini_client = genai.Client(api_key="")
GEMINI_MODEL = "gemini-2.0-flash"

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
OPENAI_MODEL = "gpt-4-turbo"

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
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL, 
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
        print(f"Error during Gemini inference: {e}")
        return []

def judge_plans_with_openai(plans_list):
    """
    Groups plans by semantic intent using OpenAI.
    Returns a list of lists containing indices.
    """
    if not plans_list or len(plans_list) < 2:
        return []

    # The prompt explicitly tells OpenAI to ignore wording and look for intent
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
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an AI research auditor that identifies duplicate research plans based on intent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        print(prompt) # Debug: Show the prompt sent to OpenAI
        print(f"OpenAI response: {response.choices[0].message.content}") # Debug: Show raw response
        # Clean potential markdown from the response
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        return json.loads(text)
    except Exception as e:
        print(f"Error during OpenAI inference: {e}")
        return []

def analyze_all_plans(json_file, llm_provider="gemini"):
    """
    Analyze all plans and identify redundancy.
    
    Args:
        json_file: Path to the journal JSON file
        llm_provider: "gemini" or "openai" (default: "gemini")
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Group nodes by parent to compare siblings
    parent_map = defaultdict(list)
    for node in data:
        parent_map[node.get('parent')].append(node)

    all_judgements = {}
    
    # Choose the judgment function based on provider
    judge_func = judge_plans_with_openai if llm_provider == "openai" else judge_plans_with_gemini

    for pid, children in parent_map.items():
        if not pid or len(children) < 2:
            continue
        
        # Display short parent ID for tracking
        display_id = pid[:8] if pid else "Root"
        print(f"Judging {len(children)} sibling plans for Parent {display_id} using {llm_provider.upper()}...")
        
        plans = [c.get('plan', 'No plan provided') for c in children]
        groups = judge_func(plans)
        
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
    parser = argparse.ArgumentParser(description="Judge and identify redundant research plans")
    parser.add_argument("filepath", nargs="?", default="journal_with_judgements.json",
                        help="Path to the journal JSON file")
    parser.add_argument("--llm", choices=["gemini", "openai"], default="gemini",
                        help="LLM provider to use for plan judgment (default: gemini)")
    
    args = parser.parse_args()
    analyze_all_plans(args.filepath, llm_provider=args.llm)

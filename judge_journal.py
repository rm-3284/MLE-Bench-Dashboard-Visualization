import os
import json
import difflib
import time
import sys

# --- CONFIGURATION ---
INPUT_JSON = "journal.json"
OUTPUT_DATA = "journal_with_judgements.json"

# API Setup (Gemini or OpenAI)
LLM_PROVIDER = "gemini" 
GEMINI_MODEL = "gemini-2.0-flash" 
OPENAI_MODEL = "gpt-4o"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_KEY_HERE"

def get_llm_response(sys_prompt, usr_prompt):
    """Handles API calls to the selected provider."""
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
        return {"status": "error", "reason": str(e)}
    return {"status": "error", "reason": "Unknown provider"}

def main():
    if not os.path.exists(INPUT_JSON):
        print(f"Error: {INPUT_JSON} not found.")
        sys.exit(1)

    print(f"Reading {INPUT_JSON}...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Handle different JSON structures (list vs dict)
    if isinstance(raw_data, dict) and "nodes" in raw_data:
        steps = raw_data["nodes"]
    elif isinstance(raw_data, list):
        steps = raw_data
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
            time.sleep(1) # Safety delay

        step['llm_judgment'] = judgment
        prev_code = curr_code

    # Save Results
    with open(OUTPUT_DATA, 'w', encoding='utf-8') as f:
        json.dump(steps, f, indent=4)
    
    print(f"\n✅ Judgments saved to: {OUTPUT_DATA}")

if __name__ == "__main__":
    main()

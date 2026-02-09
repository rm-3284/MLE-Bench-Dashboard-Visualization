#!/usr/bin/env bash
# Quick reference for running the visualization pipeline

# ============================================================================
# QUICK START
# ============================================================================

# Run the full pipeline with auto-config:
python run_visualization_pipeline.py ~/data/competition-name-run_id/logs/journal.json

# ============================================================================
# COMMON SCENARIOS
# ============================================================================

# Scenario 1: You have journal.json but not judgements yet
# → This runs the full 3-step pipeline
python run_visualization_pipeline.py ~/data/my-comp-abc123/logs/journal.json

# Scenario 2: You already have judgements, just regenerate dashboard
# → This skips the slow LLM judgment step
python run_visualization_pipeline.py ~/data/my-comp-abc123/logs --skip-judge

# Scenario 3: You don't care about plan redundancy analysis
# → Skip the plan analysis step
python run_visualization_pipeline.py ~/data/my-comp-abc123/logs --skip-plan

# Scenario 4: You want a custom output filename
# → Saves to your specified file instead of default
python run_visualization_pipeline.py ~/data/my-comp-abc123/logs --output results.html

# Scenario 5: Combine options
# → Skip judge, custom output
python run_visualization_pipeline.py ~/data/my-comp-abc123/logs --skip-judge --output final.html

# ============================================================================
# PATH REQUIREMENTS
# ============================================================================

# Your path MUST follow this structure:
# /some/path/{competition_name}-{run_id}/logs/journal.json
#
# Examples of VALID paths:
# ✓ ~/data/tensorflow2-question-answering-a3cf875b-2303-466b-bd8d/logs/journal.json
# ✓ ~/data/dog-breed-identification-xyz789/logs/journal.json
# ✓ /tmp/new-york-city-taxi-fare-prediction-abc123/logs/
#
# Examples of INVALID paths:
# ✗ ~/data/my_experiment/journal.json (missing competition-runid format)
# ✗ ~/data/journal.json (wrong level)

# ============================================================================
# WHAT IT DOES
# ============================================================================

# Step 0: Load Configuration
#   - Extract competition name from path
#   - Look up metrics in metrics.csv
#   - Update journal_viz_.py with correct settings

# Step 1: Judge Journal
#   - Uses Gemini/GPT to verify code changes match plans
#   - Creates: journal_with_judgements.json
#   - Time: ~few minutes to hours depending on size

# Step 2: Analyze Plans
#   - Uses Gemini to detect duplicate/redundant plans
#   - Creates: plan_redundancy_report.json
#   - Time: ~few minutes to 30min depending on size

# Step 3: Generate Dashboard
#   - Creates interactive HTML visualization
#   - Creates: journal_viz_tree_dashboard.html (or custom name)
#   - Time: ~seconds to few minutes depending on size

# ============================================================================
# OUTPUT FILES
# ============================================================================

# Location: {parent_dir}/{competition_name}-{run_id}/logs/
#
# Files created:
# - journal_with_judgements.json     (step 1 output)
# - plan_redundancy_report.json      (step 2 output)
# - journal_viz_tree_dashboard.html  (step 3 output, or custom name)

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Q: "Could not find journal.json in {path}"
# A: Check the path exists and follows the format:
#    {competition_name}-{run_id}/logs/journal.json

# Q: "Competition 'xxx' not found in metrics CSV"
# A: The competition name doesn't match metrics.csv
#    Check: metrics.csv has the competition_name in its first column

# Q: "No API keys found (GOOGLE_API_KEY or OPENAI_API_KEY)"
# A: Set environment variables:
#    export GOOGLE_API_KEY="your_key_here"
#    export OPENAI_API_KEY="your_key_here"

# Q: "judge_journal.py failed / plan_judge.py failed"
# A: Check API key validity, network, or look at stderr output

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

# Optional - set these if using Gemini (recommended):
export GOOGLE_API_KEY="your_gemini_api_key"

# Optional - set this if using OpenAI instead:
export OPENAI_API_KEY="your_openai_api_key"

# ============================================================================
# ADVANCED: BATCH PROCESSING
# ============================================================================

# Process multiple experiments:
for dir in ~/experiments/*/logs; do
    echo "Processing: $dir"
    python run_visualization_pipeline.py "$dir" \
        --output "$(basename $(dirname "$dir"))_dashboard.html" \
        --skip-plan  # Skip if you don't need redundancy analysis
done

# ============================================================================
# ADVANCED: DRY RUN
# ============================================================================

# See what would be configured without running anything:
python -c "
from run_visualization_pipeline import parse_journal_path, load_metrics_from_csv
path = '~/data/my-competition-xyz/logs'
comp, run_id, wd, jf = parse_journal_path(path)
metrics = load_metrics_from_csv(comp)
print(f'Competition: {comp}')
print(f'Run ID: {run_id}')
print(f'Metrics: {metrics}')
"

# ============================================================================
# SUCCESS INDICATORS
# ============================================================================

# When you see this, it worked:
# ✓ [INFO] Found journal.json
# ✓ [INFO] Loaded metrics: Micro-F1-Score
# ✓ [INFO] Found journal_with_judgements.json
# ✓ [INFO] Found plan_redundancy_report.json
# ✓ [INFO] Found HTML visualization
# Pipeline COMPLETED SUCCESSFULLY

#!/bin/bash

# Script to run visualization pipeline for all runs from a specific date
# Usage: ./run_viz_by_date.sh YYYY-MM-DD
# Example: ./run_viz_by_date.sh 2025-12-18

if [ $# -eq 0 ]; then
    echo "Usage: $0 YYYY-MM-DD"
    echo "Example: $0 2025-12-18"
    exit 1
fi

DATE="$1"
RUNS_DIR="../runs"

# Find all directories matching the date pattern
echo "Searching for runs from date: $DATE in $RUNS_DIR"
echo "---"

count=0
success=0
failed=0

# Use find to locate all journal.json files: ../runs/{DATE}*/{comp_name}_{id}/logs/journal.json
while IFS= read -r journal_file; do
    [ -z "$journal_file" ] && continue
    
    dir=$(dirname "$journal_file")
    run_dir=$(dirname "$dir")
    dir_name=$(basename "$run_dir")
    
    count=$((count + 1))
    echo "[${count}] Running: $dir_name"
    
    # Only use --skip-judge if journal_with_judgements.json already exists
    #judge_flag=""
    #if [ -f "$(dirname "$journal_file")/journal_with_judgements.json" ]; then
    #    judge_flag="--skip-judge"
    #fi
    
    if python run_visualization_pipeline.py "$journal_file" $judge_flag; then
        success=$((success + 1))
        echo "✓ SUCCESS: $dir_name"
    else
        failed=$((failed + 1))
        echo "✗ FAILED: $dir_name"
    fi
    echo "---"
done < <(find "$RUNS_DIR/${DATE}"* -name "journal.json" -path "*/logs/journal.json" 2>/dev/null)

echo ""
echo "Summary for date $DATE:"
echo "  Total: $count"
echo "  Success: $success"
echo "  Failed: $failed"

#!/bin/bash
# Fix all judgment errors in journal_with_judgements.json files under runs/
# Auto-replaces original files when all entries are successfully fixed
# Usage: ./fix_all_judgment_errors.sh

RUNS_DIR="../runs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIX_SCRIPT="$SCRIPT_DIR/fix_judgment_errors.py"

if [ ! -f "$FIX_SCRIPT" ]; then
    echo "✗ Error: fix_judgment_errors.py not found at $FIX_SCRIPT"
    exit 1
fi

if [ ! -d "$RUNS_DIR" ]; then
    echo "✗ Error: runs directory not found at $RUNS_DIR"
    exit 1
fi

echo "Finding all journal_with_judgements.json files in $RUNS_DIR..."
echo ""

fixed=0
partial=0
skipped=0
count=0

find "$RUNS_DIR" -name "journal_with_judgements.json" -type f | while read -r file; do
    count=$((count + 1))
    dir=$(dirname "$file")
    # Extract the relative path from RUNS_DIR
    rel_path=$(echo "$dir" | sed "s|^$RUNS_DIR/||")
    
    printf "[$count] %-80s " "$rel_path"
    
    # Run fix script
    output=$(python "$FIX_SCRIPT" "$file" 2>&1)
    
    if echo "$output" | grep -q "No errors found"; then
        echo "✓ (no errors)"
        skipped=$((skipped + 1))
    elif echo "$output" | grep -q "Successfully fixed all"; then
        fixed_count=$(echo "$output" | grep "Successfully fixed" | grep -oE "[0-9]+ error" | grep -oE "[0-9]+")
        echo "✓ Fixed $fixed_count"
        fixed=$((fixed + 1))
    elif echo "$output" | grep -q "Fixed.*but.*still have errors"; then
        fixed_count=$(echo "$output" | grep "Fixed" | grep -oE "[0-9]+ entries" | head -1 | grep -oE "[0-9]+")
        echo "⚠ Partial ($fixed_count fixed, some failed)"
        partial=$((partial + 1))
    else
        echo "✗ Error"
    fi
done

echo ""
echo "========================================="
echo "Summary:"
echo "  Fully fixed: $fixed"
echo "  Partial fixes: $partial"
echo "  No errors: $skipped"
echo "========================================="

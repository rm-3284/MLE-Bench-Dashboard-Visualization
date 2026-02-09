#!/bin/bash
# Run only the visualization step (journal_viz_.py) for all runs under ../runs
# Usage: ./run_viz_only_all.sh [--apply] [--limit N]
# By default does a dry-run listing targets. Use --apply to actually run.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE="$SCRIPT_DIR/run_visualization_pipeline.py"
RUNS_DIR="../runs"
APPLY=0
LIMIT=0
LOGFILE="$SCRIPT_DIR/run_viz_only_all.log"

log_line() {
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "[$ts] $*" | tee -a "$LOGFILE"
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --apply) APPLY=1; shift ;;
    --limit) LIMIT=$2; shift 2 ;;
    -h|--help) echo "Usage: $0 [--apply] [--limit N]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [ ! -f "$PIPELINE" ]; then
  log_line "✗ Cannot find run_visualization_pipeline.py at $PIPELINE"
  exit 1
fi

if [ ! -d "$RUNS_DIR" ]; then
  log_line "✗ Runs directory not found: $RUNS_DIR"
  exit 1
fi

# Collect targets (portable: avoid bash-only mapfile)
targets_file=$(mktemp)
find "$RUNS_DIR" -type f -path "*/logs/journal_with_judgements.json" > "$targets_file"
total=$(wc -l < "$targets_file" | tr -d ' ')

log_line "Found $total journal_with_judgements.json files under $RUNS_DIR"

if [ "$total" -eq 0 ]; then
  rm -f "$targets_file"
  exit 0
fi

count=0
while IFS= read -r jfile; do
  count=$((count+1))
  # Derive logs dir
  logsdir=$(dirname "$jfile")
  relpath=$(echo "$logsdir" | sed "s|^$RUNS_DIR/||")
  # Show both relative run dir and the exact journal file path
  printf "[%3d/%3d] %s -> %s\n" "$count" "$total" "$relpath" "$jfile"

  if [ "$APPLY" -eq 0 ]; then
    echo " (dry-run)"
  else
    echo " -> running"
    run_output_file="${logsdir}/.run_viz_output.log"
    # Run pipeline and capture output
    python "$PIPELINE" "$logsdir" --skip-judge --skip-plan > "$run_output_file" 2>&1
    rc=$?
    # Log run output header and tail (include exact file path)
    log_line "--- Begin pipeline output for: $relpath -- $jfile ---"
    if [ -f "$run_output_file" ]; then
      sed -n '1,400p' "$run_output_file" >> "$LOGFILE" 2>/dev/null || true
    fi
    log_line "--- End pipeline output for: $relpath -- $jfile (exit $rc) ---"

    if [ $rc -ne 0 ]; then
      log_line "✗ Visualization failed for: $relpath (exit $rc)"
    else
      log_line "✓ Visualization completed for: $relpath"
    fi
  fi

  # Limit if requested
  if [ "$LIMIT" -ne 0 ] && [ "$count" -ge "$LIMIT" ]; then
    echo "Reached limit of $LIMIT, stopping"
    break
  fi

done < "$targets_file"

rm -f "$targets_file"

if [ "$APPLY" -eq 0 ]; then
  log_line "Dry-run complete. To execute visualizations, re-run with --apply."
else
  log_line "All visualizations attempted."
fi

# Visualization Pipeline Automation

## Overview

The `run_visualization_pipeline.py` script automates the complete visualization workflow:

1. **Judge Journal** (`judge_journal.py`) - Uses LLM to verify code changes match plans
2. **Analyze Plans** (`plan_judge.py`) - Detects redundant/duplicate plans  
3. **Generate Dashboard** (`journal_viz_.py`) - Creates interactive HTML visualization

## Key Feature: Automatic Metric Configuration

The script automatically extracts the **competition name** from your journal path and loads the corresponding metrics from `metrics.csv`. This means you don't have to manually edit `METRIC_INFO`, `IGNORE_BUGGY_WITHOUT_METRIC`, or `DEFAULT_BUGGY_METRIC` in `journal_viz_.py` anymore.

### Path Format

Expected directory structure:
```
/parent/dir/{competition_name}-{run_id}/logs/journal.json
```

Examples:
- `~/data/tensorflow2-question-answering-abc123def456/logs/journal.json`
- `/tmp/dog-breed-identification-xyz789/logs/journal.json`

The script extracts:
- **competition_name**: `tensorflow2-question-answering` (matches `metrics.csv`)
- **run_id**: `abc123def456` (UUID-like identifier)

## Installation

No additional dependencies needed beyond the existing requirements.

## Usage

### Basic Usage (Full Pipeline)

```bash
python run_visualization_pipeline.py ~/data/my-competition-run-123/logs/journal.json
```

This will:
1. ✅ Load metrics for `my-competition` from `metrics.csv`
2. ✅ Judge all journal entries
3. ✅ Analyze plan redundancy
4. ✅ Generate interactive dashboard

### Skip Judgment (Reuse Existing)

If you already have `journal_with_judgements.json`:

```bash
python run_visualization_pipeline.py ~/data/my-competition-run-123/logs --skip-judge
```

### Custom Output File

```bash
python run_visualization_pipeline.py ~/data/my-competition-run-123/logs --output my_dashboard.html
```

### Skip Plan Analysis

```bash
python run_visualization_pipeline.py ~/data/my-competition-run-123/logs --skip-plan
```

### Custom Metrics File

If `metrics.csv` is in a different location:

```bash
python run_visualization_pipeline.py ~/data/my-competition-run-123/logs --metrics ~/metrics.csv
```

### Use Current Directory (No Auto-Config)

```bash
python run_visualization_pipeline.py
```

(Uses defaults from `journal_viz_.py`)

## Metrics Configuration

The script looks up your competition in `metrics.csv` and automatically applies:

| Column | Usage |
|--------|-------|
| `competition_name` | Matched against extracted competition name |
| `metric_name` | Updates `METRIC_INFO["NAME"]` |
| `metric_description` | Updates `METRIC_INFO["DESCRIPTION"]` |
| `goal` | Updates `METRIC_INFO["GOAL"]` (maximize/minimize) |
| `buggy_ignore` | Updates `IGNORE_BUGGY_WITHOUT_METRIC` |
| `default_value_for_buggy` | Updates `DEFAULT_BUGGY_METRIC` |

Example from `metrics.csv`:
```csv
competition_name,metric_name,metric_description,goal,buggy_ignore,default_value_for_buggy
tensorflow2-question-answering,micro-f1-score,"The harmonic mean...",maximize,False,-0.1
```

## Output Files

After successful execution:
- **journal_with_judgements.json** - Input journal with LLM verdicts added
- **plan_redundancy_report.json** - Groups of redundant plans
- **journal_viz_tree_dashboard.html** (or custom) - Interactive dashboard

## Troubleshooting

### "Could not find journal.json"
- Check the path exists and contains `journal.json` at the expected location
- Path should be: `.../competition-runid/logs/journal.json`

### "Competition not found in metrics CSV"
- The competition name extracted from your path doesn't match any entry in `metrics.csv`
- Check if the competition name in your path matches the CSV exactly (case-insensitive)
- Add the missing competition to `metrics.csv` if needed

### "No API keys found"
- Set `GOOGLE_API_KEY` or `OPENAI_API_KEY` environment variables
- Or edit `judge_journal.py` to hardcode keys (not recommended for shared systems)

### LLM Step Fails
- Verify API keys are valid
- Check network connectivity
- Review the error message for quota/rate limit issues

## Script Architecture

### Key Functions

**`parse_journal_path(journal_path)`**
- Extracts `{competition_name}-{run_id}` from directory name
- Returns competition name, run ID, working directory, journal file path

**`load_metrics_from_csv(competition_name, metrics_csv_path)`**
- Looks up competition in CSV
- Returns dict with metric configuration

**`update_journal_viz_config(metrics_info)`**
- Modifies `journal_viz_.py` with loaded metrics
- Updates METRIC_INFO, IGNORE_BUGGY_WITHOUT_METRIC, DEFAULT_BUGGY_METRIC

**`run_judge_journal()`, `run_plan_judge()`, `run_visualization()`**
- Execute each step with error handling and verification

## Advanced Usage

### Batch Process Multiple Runs

```bash
#!/bin/bash
for dir in ~/data/*/logs; do
    echo "Processing: $dir"
    python run_visualization_pipeline.py "$dir" --output "$(basename $(dirname $dir))_dashboard.html"
done
```

### Dry Run (Check Configuration Only)

```bash
python -c "
from run_visualization_pipeline import parse_journal_path, load_metrics_from_csv

path = '~/data/my-competition-xyz/logs'
comp, run_id, wd, jf = parse_journal_path(path)
metrics = load_metrics_from_csv(comp)
print(f'Competition: {comp}')
print(f'Metrics: {metrics}')
"
```

## Notes

- The script **temporarily modifies** `journal_viz_.py` during execution and restores it afterward (unless using a custom output file)
- File I/O is done with UTF-8 encoding to support special characters
- Timeouts: Judge (1h), Plan (30min), Visualization (10min)
- All output is color-coded for easy reading in terminal

## Future Enhancements

- [ ] Support for multiple metric formats (beyond CSV)
- [ ] Parallel processing for large journal files
- [ ] Incremental updates (only process changed entries)
- [ ] Export summary statistics to JSON

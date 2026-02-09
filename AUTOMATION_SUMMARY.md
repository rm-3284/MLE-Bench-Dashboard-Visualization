# Automated Visualization Pipeline - Summary

## What Changed

You now have a fully automated pipeline that takes a single path and handles everything:

```bash
python run_visualization_pipeline.py ~/data/my-competition-xyz/logs/journal.json
```

This replaces the manual process of:
1. Running `judge_journal.py` manually
2. Running `plan_judge.py` manually  
3. Manually editing `METRIC_INFO`, `IGNORE_BUGGY_WITHOUT_METRIC`, `DEFAULT_BUGGY_METRIC` in `journal_viz_.py`
4. Running `journal_viz_.py` manually

## Key Features

### ✨ Automatic Metric Configuration

The script automatically:
1. **Parses your path** to extract `{competition_name}-{run_id}` from the directory structure
2. **Looks up metrics** in `metrics.csv` based on the competition name
3. **Updates `journal_viz_.py`** with the correct settings:
   - `METRIC_INFO["NAME"]`
   - `METRIC_INFO["DESCRIPTION"]`
   - `METRIC_INFO["GOAL"]` (maximize/minimize)
   - `IGNORE_BUGGY_WITHOUT_METRIC`
   - `DEFAULT_BUGGY_METRIC`

### 🚀 Smart Options

- `--skip-judge` - Reuse existing judgements (for faster iteration)
- `--skip-plan` - Skip plan redundancy analysis if not needed
- `--output FILE` - Custom HTML filename
- `--metrics FILE` - Custom metrics CSV path

### 🛡️ Robust Error Handling

- Validates each step's inputs and outputs
- Checks for required API keys
- Prevents cascading failures
- Color-coded terminal output for easy reading

## Files Created

1. **`run_visualization_pipeline.py`** - Main orchestrator script
2. **`PIPELINE_README.md`** - Comprehensive documentation
3. **`QUICK_START.sh`** - Quick reference guide

## Example Workflows

### Full Pipeline with Auto-Config
```bash
python run_visualization_pipeline.py ~/data/tensorflow2-question-answering-abc123/logs/journal.json
```

Output:
```
✓ Found journal.json: /path/to/journal.json
✓ Extracted: competition=tensorflow2-question-answering, run_id=abc123...
✓ Loaded metrics: Micro-F1-Score
  Goal: maximize
  Ignore buggy without metric: False
  Default buggy metric: -0.1
✓ Updated journal_viz_.py with metrics
[Steps 1-3 execute automatically]
✓ Pipeline COMPLETED SUCCESSFULLY
```

### Fast Iteration (Skip Judgment)
```bash
python run_visualization_pipeline.py ~/data/my-competition-xyz/logs --skip-judge
```

### Batch Process Multiple Runs
```bash
for dir in ~/experiments/*/logs; do
    python run_visualization_pipeline.py "$dir" --output "$(basename $(dirname $dir))_dashboard.html"
done
```

## How It Works

### Path Parsing
Expects: `.../competition_name-run_id/logs/journal.json`

Extracts:
- **competition_name**: Used to look up metrics in CSV
- **run_id**: UUID-like identifier (extracted but not strictly used)
- **working_dir**: Where all files are processed
- **journal_file**: Input file to process

### Metric Lookup
Matches competition name from path against `metrics.csv`:

```csv
competition_name,metric_name,metric_description,goal,buggy_ignore,default_value_for_buggy
tensorflow2-question-answering,micro-f1-score,The harmonic mean...,maximize,False,-0.1
```

### Configuration Update
Dynamically modifies `journal_viz_.py` with loaded settings, then restores it after visualization step.

## Requirements

### For Judging (Step 1)
- API Key: `GOOGLE_API_KEY` (Gemini) or `OPENAI_API_KEY` (OpenAI)
- Set environment variable: `export GOOGLE_API_KEY="your_key"`

### For Everything Else
- Python 3.7+
- Standard libraries (os, sys, json, csv, re, subprocess, pathlib)

## Metrics CSV Format

Required columns:
- `competition_name` - Must match the extracted name from your path
- `metric_name` - What you call the metric
- `metric_description` - Detailed explanation
- `goal` - "maximize" or "minimize"
- `buggy_ignore` - "True" or "False"
- `default_value_for_buggy` - Numeric value for buggy nodes without scores

See `metrics.csv` in visualization_final/ for examples.

## Troubleshooting

**Problem**: "Could not find journal.json"
- **Solution**: Ensure path follows format: `{parent}/{competition}-{runid}/logs/journal.json`

**Problem**: "Competition 'xyz' not found in metrics CSV"
- **Solution**: Check metrics.csv has the competition_name in the first column (case-insensitive match)

**Problem**: "No API keys found"
- **Solution**: Set environment variable: `export GOOGLE_API_KEY="your_key"`

**Problem**: "Could not parse competition/run_id"
- **Solution**: Directory name must be `{name}-{uuid}` format. Check the parent directory name.

## Next Steps

1. **Try it out**:
   ```bash
   cd visualization_final/
   python run_visualization_pipeline.py --help
   ```

2. **Use with your data**:
   ```bash
   python run_visualization_pipeline.py ~/your/path/to/competition-run/logs/journal.json
   ```

3. **Read the full docs**:
   - See `PIPELINE_README.md` for detailed documentation
   - See `QUICK_START.sh` for quick reference

## Design Philosophy

- **Zero manual configuration** - Just provide the path, metrics are auto-loaded
- **Fail fast** - Each step validates its inputs/outputs
- **Be idempotent** - Can re-run without issues (files are overwritten)
- **Clear output** - Color-coded logging shows exactly what's happening
- **Smart defaults** - Falls back gracefully if auto-config fails

---

**Created**: February 3, 2026  
**Location**: `visualization_final/run_visualization_pipeline.py`  
**Status**: Ready for production use

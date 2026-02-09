# Visualization Pipeline Automation - Implementation Summary

## What You Asked For

> I want to automate the process. When I do `python run_visualization_pipeline "path"`, where path is structured as `{some parent dir}/{competition_name}-{run-id}/logs/journal.json`, it will look up the competition_name from metrics.csv and use that info to change METRIC_INFO, IGNORE_BUGGY_WITHOUT_METRIC, DEFAULT_BUGGY_METRIC in journal_viz_.py

## ✅ What Was Built

A complete automation solution that:

1. **Accepts a path** to `journal.json` with automatic metric configuration
2. **Parses the path** to extract competition name and run ID
3. **Looks up metrics** in your `metrics.csv`
4. **Updates `journal_viz_.py`** with the correct configuration
5. **Runs the full pipeline** (judge → analyze → visualize)
6. **Handles all errors gracefully** with color-coded output

## 📦 Files Created

### Main Script
- **`run_visualization_pipeline.py`** - The orchestrator that handles everything

### Documentation
- **`PIPELINE_README.md`** - Complete documentation with examples
- **`QUICK_START.sh`** - Quick reference with common scenarios
- **`AUTOMATION_SUMMARY.md`** - High-level overview

## 🚀 How to Use

### Basic Usage
```bash
python run_visualization_pipeline.py ~/data/tensorflow2-question-answering-abc123/logs/journal.json
```

The script will:
1. ✓ Extract `tensorflow2-question-answering` from the path
2. ✓ Look it up in `metrics.csv`
3. ✓ Auto-update `journal_viz_.py` with:
   - Metric name
   - Metric description
   - Goal (maximize/minimize)
   - Buggy node handling settings
   - Default buggy metric value
4. ✓ Run judge_journal.py → plan_judge.py → journal_viz_.py
5. ✓ Generate your dashboard

### With Options
```bash
# Skip judgment step (reuse existing judgements)
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --skip-judge

# Custom output filename
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --output results.html

# Skip plan analysis
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --skip-plan

# Combine options
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --skip-judge --output final.html
```

## 🔧 How It Works

### Path Parsing
```
Input: /parent/dir/tensorflow2-question-answering_a3cf875b/logs/journal.json
         └─ competition ─┘ └─ run_id ──┘
Extracts: 
  - competition_name: "tensorflow2-question-answering"
  - run_id: "a3cf875b"
```

### Metric Lookup
```python
# Looks up in metrics.csv:
competition_name,metric_name,metric_description,goal,buggy_ignore,default_value_for_buggy
tensorflow2-question-answering,micro-f1-score,...,maximize,False,-0.1

# Updates journal_viz_.py with:
METRIC_INFO["NAME"] = "Micro-F1-Score"
METRIC_INFO["GOAL"] = "maximize"
IGNORE_BUGGY_WITHOUT_METRIC = False
DEFAULT_BUGGY_METRIC = -0.1
```

### Pipeline Execution
```
Step 0: Load Configuration
  ├─ Parse path
  ├─ Load metrics from CSV
  └─ Update journal_viz_.py

Step 1: Judge Journal
  └─ Run judge_journal.py → journal_with_judgements.json

Step 2: Analyze Plans
  └─ Run plan_judge.py → plan_redundancy_report.json

Step 3: Generate Dashboard
  └─ Run journal_viz_.py → journal_viz_tree_dashboard.html
```

## 🎯 Key Features

### Automatic Configuration
- No manual editing of `journal_viz_.py` needed
- Competition name extracted from path
- All settings loaded from `metrics.csv`

### Smart Options
- `--skip-judge` - Fast re-generation without LLM calls
- `--skip-plan` - Skip if you don't need redundancy analysis
- `--output FILE` - Custom output filename
- `--metrics FILE` - Custom CSV path

### Robust Error Handling
- Validates each step's inputs/outputs
- Checks for required API keys
- Provides helpful error messages
- Color-coded terminal output
- Graceful fallback to defaults

### Intelligent Logging
```
[INFO] Configuration loading...
[✓] Found journal.json
[✓] Extracted: competition=tensorflow2-question-answering, run_id=a3cf875b
[✓] Loaded metrics: Micro-F1-Score
[INFO]   Goal: maximize
[INFO]   Ignore buggy without metric: False
[INFO]   Default buggy metric: -0.1
[✓] Updated journal_viz_.py with metrics
```

## 📋 Requirements

### Environment
- Python 3.7+
- Standard library only (no new dependencies!)

### For Judgment Step
- API Key: `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- Set: `export GOOGLE_API_KEY="your_key"`

### For Everything Else
- Path follows: `{parent}/{competition}-{run_id}/logs/journal.json`
- `metrics.csv` in current directory (or `--metrics` option)

## ✨ Example Real-World Usage

Your workspace already has journal files! Try:

```bash
cd visualization_final/

# Full pipeline with auto-config
python run_visualization_pipeline.py \
  ../mle-bench-fork/runs/2025-12-17T20-27-55-GMT_run-group_aide/tensorflow2-question-answering_a3cf875b-2303-466b-bd8d-5a2820cd34b3/logs/journal.json

# Or with options
python run_visualization_pipeline.py \
  ../mle-bench-fork/runs/.../tensorflow2-question-answering_xxx/logs \
  --skip-judge --output tensorflow2_results.html
```

## 🔍 Metrics CSV Format

Your `metrics.csv` has all the needed columns:

| Column | Example |
|--------|---------|
| `competition_name` | `tensorflow2-question-answering` |
| `metric_name` | `micro-f1-score` |
| `metric_description` | `The harmonic mean...` |
| `goal` | `maximize` |
| `buggy_ignore` | `False` |
| `default_value_for_buggy` | `-0.1` |

The script matches competition name (case-insensitive) and loads all values.

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Could not find journal.json" | Check path: `{comp}-{id}/logs/journal.json` |
| "Competition not found in metrics CSV" | Add entry to CSV or check name matches |
| "No API keys found" | Set: `export GOOGLE_API_KEY="your_key"` |
| "judge_journal.py failed" | Check API key validity and network |

## 📊 What Gets Created

In `{parent}/{competition}-{run_id}/logs/`:

- **journal_with_judgements.json** - Original with LLM verdicts
- **plan_redundancy_report.json** - Duplicate plan analysis
- **journal_viz_tree_dashboard.html** - Interactive dashboard (customizable)

## 🎓 Learning Path

1. **Try the help**
   ```bash
   python run_visualization_pipeline.py --help
   ```

2. **Read quick reference**
   ```bash
   cat QUICK_START.sh
   ```

3. **Run with a real path**
   ```bash
   python run_visualization_pipeline.py ~/your/path/to/logs --skip-judge
   ```

4. **Read full docs**
   ```bash
   cat PIPELINE_README.md
   ```

## ✅ Verification

To verify everything works:

```bash
# Check the script runs
python run_visualization_pipeline.py --help

# Test path parsing with your real data
python -c "
from run_visualization_pipeline import parse_journal_path, load_metrics_from_csv
path = 'path/to/tensorflow2-question-answering_xyz/logs'
comp, run_id, wd, jf = parse_journal_path(path)
metrics = load_metrics_from_csv(comp)
print(f'Metrics loaded: {metrics[\"metric_name\"]}')
"
```

## 🚀 Next Steps

1. **Set your API key**:
   ```bash
   export GOOGLE_API_KEY="your_gemini_api_key_here"
   ```

2. **Run with your data**:
   ```bash
   cd visualization_final/
   python run_visualization_pipeline.py /path/to/your/competition-xyz/logs/journal.json
   ```

3. **Enjoy!** The dashboard will be generated automatically with the correct metrics.

---

**Status**: ✅ Ready for production  
**Location**: `visualization_final/run_visualization_pipeline.py`  
**Created**: February 3, 2026

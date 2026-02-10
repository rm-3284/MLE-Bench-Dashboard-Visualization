# Visualization Pipeline Automation - Complete Documentation Index

## Quick Navigation

### For First-Time Users

1. Start here: [IMPLEMENTATION.md](IMPLEMENTATION.md) - 5-minute overview
2. Try it: `python run_visualization_pipeline.py --help`
3. Run it: `python run_visualization_pipeline.py /path/to/logs/journal.json`
4. Detailed help: [QUICK_START.sh](QUICK_START.sh)

### For Reference

- [PIPELINE_README.md](PIPELINE_README.md) - Complete documentation
- [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md) - Implementation details
- [AUTOMATION_SUMMARY.md](AUTOMATION_SUMMARY.md) - Architecture overview

## What This Does

Automates the visualization pipeline:

```
journal.json → [Judge] → [Analyze] → [Visualize] → dashboard.html
                                  ↑
                        Auto-config from metrics.csv
```

## Quick Start

```bash
# Run with automatic metric configuration
python run_visualization_pipeline.py ~/path/to/competition-name-uuid/logs/journal.json

# That's it! The dashboard is ready.
```

## Files in This Directory

### Core Pipeline Scripts

```
run_visualization_pipeline.py          ← Main orchestrator (607 lines)
                                         Runs 3-step pipeline: judge → plan → viz
                                         Auto-configures from metrics.csv
                                         Usage: python script.py /path/to/logs

journal_viz_.py                        ← Interactive HTML dashboard generator (480 lines)
                                         Creates tree visualization with metrics, diffs, LLM judgments
                                         Handles both 'parent' and 'parent_id' field formats
                                         Reads: journal_with_judgements.json, plan_redundancy_report.json

judge_journal.py                       ← LLM code verifier (150 lines)
                                         Uses Vertex AI to judge code correctness vs plan
                                         Compares child code to parent code
                                         Outputs: journal_with_judgements.json

plan_judge.py                          ← Plan redundancy analyzer (95 lines)
                                         Detects duplicate execution plans among sibling nodes
                                         Uses Gemini API for semantic similarity detection
                                         Outputs: plan_redundancy_report.json
```

### Batch Processing & Utilities

```
run_viz_only_all.sh                    ← Batch visualization regenerator (105 lines)
                                         Runs journal_viz_.py on all 169 runs
                                         Usage: ./script.sh --apply [--limit N]
                                         Skips judge/plan steps, only updates dashboards

run_viz_by_date.sh                     ← Date-based batch processor (120 lines)
                                         Processes runs grouped by date directory
                                         Supports --skip-judge for fast iteration
                                         Logs progress to run_viz_by_date.log

run_plan_judge_all.py                  ← Batch plan analyzer (243 lines)
                                         Runs plan_judge.py on all multi-child nodes
                                         Skips already-analyzed nodes (checks plan_redundancy_report.json)
                                         Handles 429 API errors with exponential backoff (2, 4, 8s)
                                         Usage: python script.py --apply [--limit N]

fix_judgment_errors.py                 ← LLM judgment error fixer (135 lines)
                                         Re-runs failed LLM judgments (status == "error")
                                         Exponential backoff on 429 RESOURCE_EXHAUSTED
                                         Max 3 retry attempts per entry

fix_all_judgment_errors.sh             ← Batch judgment error fixer (35 lines)
                                         Finds all journal_with_judgements.json with errors
                                         Calls fix_judgment_errors.py on each

update_tree_structure.py               ← Parent-child relationship reconstructor (229 lines)
                                         Rebuilds parent/children fields from node2parent mapping
                                         Handles both list and dict journal formats
                                         Usage: python script.py --apply [--limit N]
                                         Applied to 169 files: 29 updated, 1827 changes

standardize_journal_format.py          ← Journal format converter (116 lines)
                                         Converts {"nodes": [...]} to plain [...] format
                                         Ensures consistency across all journal files
                                         Usage: python script.py --apply [--limit N]
```

### Dashboard & Serving

```
generate_hyper_dashboard.py            ← Static hyper-dashboard generator (330 lines)
                                         Creates index HTML linking all run dashboards
                                         Groups by competition, shows metrics
                                         Outputs: hyper_dashboard.html

serve_hyper_dashboard.py               ← Dynamic dashboard HTTP server (400 lines)
                                         Live HTTP server on localhost:8000
                                         Auto-scans runs/ directory on each request
                                         No static file generation needed
                                         Usage: python script.py
```

### Testing & Debugging

```
test_pipeline.py                       ← Pipeline function tester (15 lines)
                                         Tests parse_journal_path() and load_metrics_from_csv()
                                         Uses real paths for validation

debug_plan_judge.py                    ← Plan judge debugger (147 lines)
                                         Shows nodes with multiple children
                                         Compares plan_redundancy_report.json before/after
                                         Real-time output streaming from plan_judge.py
```

### Documentation

```
IMPLEMENTATION.md                      ← 5-minute project overview
PIPELINE_README.md                     ← Complete usage guide with examples
QUICK_START.sh                         ← Command reference with Q&A
TECHNICAL_REFERENCE.md                 ← Implementation deep dive
AUTOMATION_SUMMARY.md                  ← Architecture and design decisions
ARCHITECTURE_DIAGRAMS.md               ← Visual system architecture
COMPLETION_SUMMARY.md                  ← Project completion report
QUICK_REFERENCE.md                     ← Command cheat sheet
README_INDEX.md                        ← This file - navigation hub
```

### Configuration & Data

```
metrics.csv                            ← Competition metrics database
                                         Fields: competition, metric_name, goal,
                                                ignore_buggy_without_metric, default_buggy_metric

config_0.7_20_3600.jsonl               ← LLM API configuration
experiments.csv                        ← Experiment tracking data
```

### Generated Files (Created by Pipeline)

```
journal_with_judgements.json           ← Judge output (per run)
                                         Original journal + LLM verification

plan_redundancy_report.json            ← Plan analysis output (per run)
                                         Maps parent_id → [[redundant child steps]]

journal_viz_tree_dashboard.html        ← Interactive dashboard (per run)
                                         Full tree visualization with metrics

hyper_dashboard.html                   ← Index of all run dashboards (top-level)
run_viz_only_all.log                   ← Batch processing log
```

## Documentation Structure

```
IMPLEMENTATION.md
├─ What You Asked For
├─ What Was Built
├─ How to Use
├─ How It Works
├─ Key Features
├─ Requirements
└─ Next Steps

PIPELINE_README.md
├─ Overview
├─ Installation
├─ Usage (Basic & Advanced)
├─ Metrics Configuration
├─ Output Files
├─ Troubleshooting
└─ Notes

QUICK_START.sh
├─ Quick Start Examples
├─ Common Scenarios
├─ Path Requirements
├─ What It Does
├─ Output Files
├─ Troubleshooting Q&A
├─ Environment Variables
├─ Batch Processing
└─ Success Indicators

TECHNICAL_REFERENCE.md
├─ Core Functions Reference
├─ Configuration Changes
├─ Error Handling Strategy
├─ Logging System
├─ File I/O Operations
├─ Key Design Decisions
├─ Testing Checklist
├─ Performance Characteristics
├─ Compatibility
└─ Future Enhancements
```

## Key Features at a Glance

| Feature                | Details                                                  |
| ---------------------- | -------------------------------------------------------- |
| **Auto Configuration** | Reads competition name from path, loads metrics from CSV |
| **One-Line Execution** | `python run_visualization_pipeline.py /path`             |
| **Smart Options**      | `--skip-judge`, `--skip-plan`, `--output`, `--metrics`   |
| **Error Recovery**     | Fails gracefully with helpful error messages             |
| **Color-Coded Output** | Easy to read terminal logging                            |
| **Zero Dependencies**  | Uses only Python standard library                        |
| **Idempotent**         | Safe to run multiple times                               |
| **Fast Iteration**     | Skip expensive steps with options                        |

## Workflow Overview

```
USER PROVIDES PATH
    ↓
PATH PARSING
    ├─ Extract: {competition_name}-{run_id}
    └─ Find: journal.json
    ↓
METRIC LOADING
    ├─ Look up competition in metrics.csv
    └─ Load: metric_name, goal, buggy_settings
    ↓
CONFIGURATION UPDATE
    ├─ Update METRIC_INFO in journal_viz_.py
    ├─ Update IGNORE_BUGGY_WITHOUT_METRIC
    └─ Update DEFAULT_BUGGY_METRIC
    ↓
STEP 1: JUDGE
    ├─ Run judge_journal.py
    └─ Output: journal_with_judgements.json
    ↓
STEP 2: ANALYZE
    ├─ Run plan_judge.py
    └─ Output: plan_redundancy_report.json
    ↓
STEP 3: VISUALIZE
    ├─ Run journal_viz_.py
    └─ Output: journal_viz_tree_dashboard.html
    ↓
SUCCESS
    └─ Dashboard ready for viewing
```

## Usage Examples

### Most Common

```bash
# Full pipeline with auto-config (this is all you need)
python run_visualization_pipeline.py ~/data/my-competition-xyz/logs/journal.json
```

### With Options

```bash
# Fast iteration (skip LLM judgment)
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --skip-judge

# Custom output
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --output results.html

# Combine options
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --skip-judge --output final.html
```

### Batch Processing

```bash
# Process multiple experiments
for dir in ~/experiments/*/logs; do
    python run_visualization_pipeline.py "$dir"
done
```

## Reading Order

1. [IMPLEMENTATION.md](IMPLEMENTATION.md) - Overview
2. [PIPELINE_README.md](PIPELINE_README.md) - Complete guide
3. [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md) - Deep dive
4. [AUTOMATION_SUMMARY.md](AUTOMATION_SUMMARY.md) - Architecture

## FAQ

### Q: What's the path format?

A: `.../competition_name-run_id/logs/journal.json`

### Q: Do I need to edit journal*viz*.py manually?

A: No! The script does it automatically.

### Q: What if I don't have API keys?

A: Set `export GOOGLE_API_KEY="your_key"` or use OpenAI key.

### Q: Can I skip the judgment step?

A: Yes! Use `--skip-judge` flag.

### Q: How long does it take?

A: Depends on data size. Typically 5-30 minutes for full pipeline.

### Q: What if something breaks?

A: Check error messages (color-coded in terminal) or see Troubleshooting section.

### Q: Can I use a different metrics file?

A: Yes! Use `--metrics /path/to/metrics.csv`

### Q: Does it work on Windows?

A: Yes! Uses pathlib for cross-platform compatibility.

## Next Steps

1. **Try it immediately**:

   ```bash
   python run_visualization_pipeline.py --help
   ```

2. **Read the docs**:

   ```bash
   cat IMPLEMENTATION.md  # 5-minute overview
   ```

3. **Run with your data**:

   ```bash
   python run_visualization_pipeline.py /path/to/your/logs/journal.json
   ```

4. **Check the output**:
   ```bash
   open journal_viz_tree_dashboard.html  # View in browser
   ```

## Support

### Common Issues

**"Could not find journal.json"**

- Check path format: `{comp}-{id}/logs/journal.json`

**"Competition not found in metrics CSV"**

- Add entry to metrics.csv or check name matches

**"No API keys found"**

- Set: `export GOOGLE_API_KEY="your_key"`

### Debug Info

Run with full output:

```bash
python run_visualization_pipeline.py /path --skip-judge
```

Check what was parsed:

```bash
python -c "
from run_visualization_pipeline import parse_journal_path
comp, run_id, wd, jf = parse_journal_path('/your/path')
print(f'Competition: {comp}')
print(f'Working Dir: {wd}')
"
```

# Quick Reference Card

## 🚀 Run It (Copy-Paste Ready)

```bash
cd visualization_final/

# Most common usage
python run_visualization_pipeline.py ~/data/competition-name-uuid/logs/journal.json

# Fast iteration (skip judgment)
python run_visualization_pipeline.py ~/data/competition-name-uuid/logs --skip-judge

# Custom output
python run_visualization_pipeline.py ~/data/competition-name-uuid/logs --output results.html
```

## 📋 Command Reference

```bash
# Full help
python run_visualization_pipeline.py --help

# Show path parsing result (for debugging)
python -c "
from run_visualization_pipeline import parse_journal_path
comp, run_id, wd, jf = parse_journal_path('/your/path')
print(f'Competition: {comp}')
"

# Check metrics CSV lookup
python -c "
from run_visualization_pipeline import load_metrics_from_csv
metrics = load_metrics_from_csv('tensorflow2-question-answering')
print(metrics)
"
```

## 📁 File Organization

```
YOUR_WORKSPACE/visualization_final/

CORE PIPELINE:
├── run_visualization_pipeline.py      ← Main orchestrator (607 lines)
├── journal_viz_.py                    ← Dashboard generator (480 lines)
├── judge_journal.py                   ← LLM verifier (150 lines)
└── plan_judge.py                      ← Plan analyzer (95 lines)

BATCH PROCESSING:
├── run_viz_only_all.sh                ← Regenerate all dashboards (105 lines)
├── run_viz_by_date.sh                 ← Process by date groups (120 lines)
├── run_plan_judge_all.py              ← Batch plan analysis (243 lines)
├── fix_judgment_errors.py             ← Retry failed judgments (135 lines)
└── fix_all_judgment_errors.sh         ← Fix all errors (35 lines)

DATA UTILITIES:
├── update_tree_structure.py           ← Rebuild parent-child links (229 lines)
└── standardize_journal_format.py      ← Convert journal format (116 lines)

DASHBOARD TOOLS:
├── generate_hyper_dashboard.py        ← Static index generator (330 lines)
└── serve_hyper_dashboard.py           ← Live HTTP server (400 lines)

TESTING/DEBUG:
├── test_pipeline.py                   ← Unit tests (15 lines)
└── debug_plan_judge.py                ← Debug plan analysis (147 lines)

CONFIGURATION:
├── metrics.csv                        ← Competition metrics database
└── config_0.7_20_3600.jsonl           ← LLM API config

DOCUMENTATION:
├── README_INDEX.md                    ← Navigation hub (this is best start)
├── IMPLEMENTATION.md                  ← 5-minute overview
├── PIPELINE_README.md                 ← Complete guide
├── QUICK_REFERENCE.md                 ← This file (command cheatsheet)
├── TECHNICAL_REFERENCE.md             ← Deep technical dive
├── AUTOMATION_SUMMARY.md              ← Architecture overview
├── ARCHITECTURE_DIAGRAMS.md           ← Visual diagrams
└── COMPLETION_SUMMARY.md              ← Project report

GENERATED FILES (per run):
├── journal_with_judgements.json       ← Judge output
├── plan_redundancy_report.json        ← Plan analysis output
└── journal_viz_tree_dashboard.html    ← Interactive dashboard

BATCH LOGS:
├── run_viz_only_all.log               ← Batch regeneration log
└── hyper_dashboard.html               ← Index of all runs (top-level)
```

## 🎯 Path Format

```
REQUIRED:  /parent/{competition_name}-{run_id}/logs/journal.json
                   └──────────────────┬──────────────────┘
                        Must match metrics.csv

EXAMPLES:
✓ ~/data/tensorflow2-question-answering-abc123/logs/journal.json
✓ ~/experiments/dog-breed-identification_xyz/logs/
✓ ./relative/path/new-york-city-taxi-fare-prediction-uuid/logs

✗ ~/data/journal.json (missing competition-uuid format)
✗ ~/data/my_experiment/logs (underscore instead of dash)
```

## 🔧 Common Scenarios

### Scenario 1: First time running

```bash
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs/journal.json
# Waits 5-30 min, then dashboard ready
```

### Scenario 2: Iterating (skip slow LLM step)

```bash
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --skip-judge
# Much faster (minutes instead of hours)
```

### Scenario 3: Process multiple experiments

```bash
for dir in ~/experiments/*/logs; do
    python run_visualization_pipeline.py "$dir" \
        --output "$(basename $(dirname $dir))_dashboard.html"
done
```

### Scenario 4: Skip plan analysis (optional step)

```bash
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs --skip-plan
```

### Scenario 5: Combine options

```bash
python run_visualization_pipeline.py ~/data/my-comp-xyz/logs \
    --skip-judge --skip-plan --output final.html
```

## ⚙️ Configuration

### Set API Key (required for judgment)

```bash
# For Gemini (recommended)
export GOOGLE_API_KEY="your_gemini_key_here"

# OR for OpenAI
export OPENAI_API_KEY="your_openai_key_here"
```

### Custom Metrics CSV

```bash
python run_visualization_pipeline.py /path --metrics /custom/metrics.csv
```

## 📊 Expected Output

```
[✓] Found journal.json
[✓] Extracted: competition=tensorflow2-question-answering, run_id=abc123...
[✓] Loaded metrics: Micro-F1-Score
[✓] Updated journal_viz_.py
[✓] Running judgment...
[✓] Found journal_with_judgements.json
[✓] Running plan analysis...
[✓] Found plan_redundancy_report.json
[✓] Running visualization...
[✓] Found HTML visualization
Pipeline COMPLETED SUCCESSFULLY

Output:
  • journal_with_judgements.json
  • plan_redundancy_report.json
  • journal_viz_tree_dashboard.html
```

## ❌ Common Errors & Fixes

| Error                         | Fix                                                |
| ----------------------------- | -------------------------------------------------- |
| "Could not find journal.json" | Check path format: `{comp}-{id}/logs/journal.json` |
| "Competition not found"       | Add entry to metrics.csv or check name matches     |
| "No API keys found"           | Set: `export GOOGLE_API_KEY="key"`                 |
| "judge_journal.py failed"     | Check API key validity                             |
| "Path does not exist"         | Use absolute path: `/full/path/to/logs`            |

## 🎓 Documentation

| File                     | When to Read                 |
| ------------------------ | ---------------------------- |
| README_INDEX.md          | **Always start here**        |
| COMPLETION_SUMMARY.md    | Overview of what was built   |
| IMPLEMENTATION.md        | How to use (5 minutes)       |
| QUICK_START.sh           | Command examples (this file) |
| PIPELINE_README.md       | Detailed guide               |
| TECHNICAL_REFERENCE.md   | Implementation details       |
| ARCHITECTURE_DIAGRAMS.md | Visual system design         |

## 🚦 Status Check

### Verify script works

```bash
python run_visualization_pipeline.py --help
```

### Check metrics CSV exists

```bash
head metrics.csv
```

### Test path parsing

```bash
python -c "
from run_visualization_pipeline import parse_journal_path
comp, _, _, jf = parse_journal_path('~/your/path')
print(f'✓ Competition: {comp}')
print(f'✓ Journal: {jf.name}')
"
```

## ⏱️ Timing Expectations

| Step               | Time         | Skippable          |
| ------------------ | ------------ | ------------------ |
| Configuration Load | <1 sec       | No                 |
| Judge Journal      | 5-30 min     | Yes (--skip-judge) |
| Analyze Plans      | 1-5 min      | Yes (--skip-plan)  |
| Visualization      | 1-2 min      | No                 |
| **Total**          | **7-40 min** | **-**              |

## 🎯 Exit Codes

```
0 = Success (ready to view HTML)
1 = Failure (check error messages)
```

## 📞 Get Help

1. Check error message (color-coded)
2. See "Troubleshooting" in PIPELINE_README.md
3. Check QUICK_START.sh FAQ section
4. Review TECHNICAL_REFERENCE.md

## ✨ Pro Tips

1. Use `--skip-judge` during iteration (10x faster)
2. Set `GOOGLE_API_KEY` environment variable to avoid prompts
3. Use absolute paths to avoid confusion
4. Check generated HTML immediately to verify success
5. Use batch scripts for processing multiple runs

## 🔁 Batch Processing Commands

### Regenerate All Dashboards (No Judge/Plan)

```bash
cd visualization_final/

# Dry-run (show what would happen)
./run_viz_only_all.sh

# Execute on all 169 runs
./run_viz_only_all.sh --apply

# Test on first 5 runs
./run_viz_only_all.sh --apply --limit 5
```

### Analyze Plans for All Runs

```bash
# Dry-run (check which files would be processed)
python run_plan_judge_all.py

# Execute plan analysis on all multi-child nodes
python run_plan_judge_all.py --apply

# Test on first 10 files
python run_plan_judge_all.py --apply --limit 10

# Rerun to retry 429 errors (skips successful ones)
python run_plan_judge_all.py --apply
```

### Fix Failed LLM Judgments

```bash
# Fix single file
python fix_judgment_errors.py /path/to/journal_with_judgements.json

# Fix all files with errors
./fix_all_judgment_errors.sh
```

### Update Tree Structures

```bash
# Dry-run (show what would change)
python update_tree_structure.py

# Apply to all files
python update_tree_structure.py --apply

# Test on first 5
python update_tree_structure.py --apply --limit 5
```

### Standardize Journal Formats

```bash
# Dry-run
python standardize_journal_format.py

# Apply conversion
python standardize_journal_format.py --apply
```

### Generate Dashboard Index

```bash
# Static HTML index
python generate_hyper_dashboard.py
# Creates: ../runs/hyper_dashboard.html

# Live HTTP server (auto-updates)
python serve_hyper_dashboard.py
# Open: http://localhost:8000/hyper_dashboard.html
```

## 🐛 Debug Commands

### Check Plan Judge Output

```bash
python debug_plan_judge.py
# Shows nodes with multiple children
# Displays plan_redundancy_report.json before/after
```

### Test Pipeline Functions

```bash
python test_pipeline.py
# Tests path parsing and metrics loading
```

### Verify File Exists

```bash
ls -lh ../runs/*/logs/journal_with_judgements.json | wc -l
# Should show 169 files
```

### Check for Errors

```bash
# Find journals with LLM errors
grep -l '"status": "error"' ../runs/*/logs/journal_with_judgements.json

# Count successfully analyzed plans
find ../runs -name "plan_redundancy_report.json" | wc -l
```

## 📈 Batch Processing Status

### Check Logs

```bash
# View visualization batch log
tail -100 run_viz_only_all.log

# Count successes
grep "✓ Visualization completed" run_viz_only_all.log | wc -l

# Find failures
grep "✗ Visualization failed" run_viz_only_all.log
```

### Verify Outputs

```bash
# Count generated dashboards
find ../runs -name "journal_viz_tree_dashboard.html" | wc -l

# Check recent modifications
find ../runs -name "journal_viz_tree_dashboard.html" -mtime -1
```

2. Test with `--skip-judge --skip-plan` first to verify config
3. Run batch jobs with nohup: `nohup python run_visualization_pipeline.py ... &`
4. Save outputs with different names: `--output exp1.html`, `--output exp2.html`
5. Check metrics.csv matches your competition exactly (case-insensitive but must exist)

## 🔒 Safe Defaults

- Original files are **never** permanently modified
- `journal_viz_.py` is restored after execution
- All outputs go to the logs directory
- Timeouts prevent hanging processes
- Validation prevents cascading failures

## 📈 What Gets Auto-Configured

From CSV → Your Dashboard:

```
Metric Name          ✓ Loaded
Metric Description   ✓ Loaded
Goal (max/min)       ✓ Loaded
Buggy Node Handling  ✓ Loaded
Default Buggy Value  ✓ Loaded
```

All 5 settings are now automatic!

---

**Ready to go?** Run this:

```bash
python run_visualization_pipeline.py ~/path/to/your/logs/journal.json
```

**Questions?** Read README_INDEX.md

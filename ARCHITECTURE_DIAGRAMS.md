# Visualization Pipeline Architecture Diagrams

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       USER INPUT                                │
│          python run_visualization_pipeline.py [path]            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  STEP 0: CONFIGURATION LOADING    │
         └───────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐    ┌──────────┐    ┌──────────────┐
   │Parse    │    │Load      │    │Update        │
   │Path     │───▶│Metrics   │───▶│journal_viz   │
   │         │    │from CSV  │    │Config        │
   └─────────┘    └──────────┘    └──────────────┘
        │              │                │
        └──────────────┼────────────────┘
                       │
                       ▼
         ┌───────────────────────────────────┐
         │   STEP 1: JUDGE JOURNAL            │
         │  (Run judge_journal.py)            │
         │  journal.json ──▶ journal_with_   │
         │                  judgements.json   │
         └───────────────────────────────────┘
                       │
                       ▼
         ┌───────────────────────────────────┐
         │   STEP 2: ANALYZE PLANS           │
         │  (Run plan_judge.py)              │
         │  journal_with_judgements.json ───▶│
         │                 plan_redundancy   │
         │                 _report.json      │
         └───────────────────────────────────┘
                       │
                       ▼
         ┌───────────────────────────────────┐
         │   STEP 3: GENERATE DASHBOARD      │
         │  (Run journal_viz_.py)            │
         │  journal_with_judgements.json ───▶│
         │  plan_redundancy_report.json ────▶│
         │              journal_viz_tree_    │
         │              dashboard.html       │
         └───────────────────────────────────┘
                       │
                       ▼
         ┌───────────────────────────────────┐
         │         SUCCESS                    │
         │  Dashboard ready for viewing      │
         └───────────────────────────────────┘
```

## Path Parsing Detail

```
INPUT PATH:
  /parent/dir/tensorflow2-question-answering_a3cf875b-2303-466b/logs/journal.json
                └────────────────────────────┘ └────────────────┘
                      competition_name           run_id

EXTRACTION:
  1. Resolve to absolute path
  2. Check if file or directory
  3. If directory, append /journal.json
  4. Get parent directory name
  5. Match pattern: ^(.+?)-([a-f0-9]+)$
  6. Extract competition name and run ID

OUTPUT:
  competition_name: "tensorflow2-question-answering_a3cf875b-2303-466b"
  run_id: "{last-segment}"
  working_dir: "/parent/dir/tensorflow2-question-answering_a3cf875b-2303-466b/logs"
  journal_file: PosixPath("...journal.json")
```

## Metric Configuration Process

```
METRICS CSV (metrics.csv):
┌─────────────────────────────────────────────────────────────┐
│competition_name,metric_name,...                              │
│tensorflow2-question-answering,micro-f1-score,...             │
│dog-breed-identification,multi-class-log-loss,...            │
│new-york-city-taxi-fare-prediction,root-mean-squared-error...│
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Lookup: competition_name
                         │ (case-insensitive)
                         ▼
         ┌────────────────────────────────┐
         │ EXTRACTED METRICS INFO          │
         ├────────────────────────────────┤
         │ metric_name: "Micro-F1-Score"  │
         │ metric_description: "The..."   │
         │ goal: "maximize"               │
         │ ignore_buggy: False            │
         │ default_buggy: -0.1            │
         └────────────────────────────────┘
                         │
                         │ Apply via Regex
                         ▼
         ┌────────────────────────────────┐
         │ UPDATED journal_viz_.py          │
         ├────────────────────────────────┤
         │ METRIC_INFO["NAME"] =          │
         │   "Micro-F1-Score"             │
         │ METRIC_INFO["GOAL"] =          │
         │   "maximize"                   │
         │ IGNORE_BUGGY_WITHOUT_METRIC =  │
         │   False                        │
         │ DEFAULT_BUGGY_METRIC = -0.1    │
         └────────────────────────────────┘
```

## Pipeline State Diagram

```
START
  │
  ├─ Configuration Step
  │  └─ Success ──▶ Proceed to Judge
  │  └─ Fail ──▶ Stop (cannot continue)
  │
  ├─ Judge Step
  │  ├─ Skip Requested ──▶ Use existing journal_with_judgements.json
  │  ├─ Success ──▶ Proceed to Plan Analysis
  │  └─ Fail ──▶ Stop (prevents later steps)
  │
  ├─ Plan Analysis Step
  │  ├─ Skip Requested ──▶ Skip to Visualization
  │  ├─ Success ──▶ Proceed to Visualization
  │  └─ Fail ──▶ Warn but continue (optional step)
  │
  ├─ Visualization Step
  │  ├─ Success ──▶ COMPLETE
  │  └─ Fail ──▶ FAILED
  │
  └─ END
```

## Subprocess Execution Flow

```
run_visualization_pipeline.py
│
├─ Step 1: judge_journal.py
│  ├─ [Subprocess spawned]
│  ├─ Returns: CompletedProcess
│  ├─ Check returncode == 0
│  ├─ Capture stdout/stderr
│  ├─ Timeout: 1 hour
│  └─ Verify: journal_with_judgements.json exists
│
├─ Step 2: plan_judge.py
│  ├─ [Subprocess spawned]
│  ├─ Returns: CompletedProcess
│  ├─ Check returncode == 0
│  ├─ Capture stdout/stderr
│  ├─ Timeout: 30 minutes
│  └─ Verify: plan_redundancy_report.json exists
│
└─ Step 3: journal_viz_.py
   ├─ Optionally update OUTPUT_FILE
   ├─ [Subprocess spawned]
   ├─ Returns: CompletedProcess
   ├─ Check returncode == 0
   ├─ Capture stdout/stderr
   ├─ Timeout: 10 minutes
   ├─ Verify: HTML file exists
   └─ Restore original journal_viz_.py
```

## File Lifecycle Diagram

```
INPUT FILES (User provides):
  journal.json ─────────────────────────┐
                                        │
                                        ▼
                        ┌──────────────────────────┐
                        │  STEP 1: Judge Journal    │
                        │  judge_journal.py         │
                        └──────────────────────────┘
                                        │
                                        ▼
INTERMEDIATE FILE 1:              
  journal_with_judgements.json ─────────────────────┐
                                        │
                                        ▼
                        ┌──────────────────────────┐
                        │  STEP 2: Analyze Plans    │
                        │  plan_judge.py            │
                        └──────────────────────────┘
                                        │
                                        ▼
INTERMEDIATE FILE 2:
  plan_redundancy_report.json ────────────────────┐
                                        │
                                        ▼
                        ┌──────────────────────────┐
                        │  STEP 3: Visualize        │
                        │  journal_viz_.py          │
                        └──────────────────────────┘
                                        │
                                        ▼
OUTPUT FILE:
  journal_viz_tree_dashboard.html
```

## Error Handling Tree

```
Pipeline Execution
│
├─ Configuration Errors
│  ├─ Path not found
│  │  └─ ACTION: Stop and report
│  ├─ journal.json not found
│  │  └─ ACTION: Stop and report
│  ├─ Cannot parse competition name
│  │  └─ ACTION: Warn and use defaults
│  └─ Metrics CSV not found
│     └─ ACTION: Warn and use defaults
│
├─ Execution Errors
│  ├─ Subprocess failed (returncode != 0)
│  │  └─ ACTION: Log error and stop
│  ├─ Subprocess timeout
│  │  └─ ACTION: Kill and report
│  ├─ Output file not created
│  │  └─ ACTION: Log error and stop
│  └─ File I/O error
│     └─ ACTION: Restore original and stop
│
└─ Recovery Strategy
   ├─ If Step 1 fails → Stop (no journal_with_judgements)
   ├─ If Step 2 fails → Warn but continue (optional)
   └─ If Step 3 fails → Stop (no dashboard)
```

## Data Flow Diagram

```
User Request
    │
    │ Path: ".../tensorflow2-question-answering_xyz/logs/journal.json"
    ▼
┌────────────────────┐
│ Parse Path         │
└────────────────────┘
    │
    │ Extracted: "tensorflow2-question-answering"
    ▼
┌────────────────────┐
│ Load metrics.csv   │
└────────────────────┘
    │
    │ Result: {"metric_name": "Micro-F1-Score", ...}
    ▼
┌────────────────────┐
│ Update             │
│ journal_viz_.py    │
└────────────────────┘
    │
    │ journal.json
    ▼
┌────────────────────┐
│ Judge Journal      │
│ (LLM Verification) │
└────────────────────┘
    │
    │ journal_with_judgements.json
    ▼
┌────────────────────┐
│ Analyze Plans      │
│ (Redundancy Check) │
└────────────────────┘
    │
    │ plan_redundancy_report.json
    ▼
┌────────────────────┐
│ Generate Dashboard │
│ (Visualization)    │
└────────────────────┘
    │
    │ journal_viz_tree_dashboard.html
    ▼
  SUCCESS
```

## Command-Line Interface Diagram

```
run_visualization_pipeline.py
│
├─ Positional Arguments:
│  └─ journal_path (optional)
│     └─ Path to journal.json or parent directory
│
├─ Optional Arguments:
│  ├─ --skip-judge
│  │  └─ Skip judgment step (reuse existing)
│  │
│  ├─ --skip-plan
│  │  └─ Skip plan redundancy analysis
│  │
│  ├─ --output OUTPUT
│  │  └─ Specify custom HTML output filename
│  │
│  └─ --metrics METRICS
│     └─ Path to metrics.csv (default: metrics.csv)
│
└─ Outputs:
   ├─ journal_with_judgements.json
   ├─ plan_redundancy_report.json
   └─ journal_viz_tree_dashboard.html (or custom name)
```

## Feature Matrix

```
FEATURE                    AVAILABLE   NOTES
─────────────────────────────────────────────────────────────
Path Parsing              ✓           Extracts {name}-{uuid}
Auto Metrics Loading      ✓           From CSV lookup
Config Auto-Update        ✓           journal_viz_.py
Judge Journal             ✓           Via subprocess
Plan Analysis             ✓           Via subprocess
Dashboard Generation      ✓           Via subprocess
Skip Judge                ✓           Flag: --skip-judge
Skip Plan Analysis        ✓           Flag: --skip-plan
Custom Output File        ✓           Flag: --output FILE
Custom Metrics Path       ✓           Flag: --metrics FILE
Error Recovery            ✓           Graceful fallback
Color-Coded Output        ✓           Terminal logging
API Key Validation        ✓           Warns if missing
Timeout Handling          ✓           1h/30m/10m limits
File Restoration          ✓           Original preserved
Parallel Execution        ✗           Sequential only
Dry-Run Mode              ✗           Executes by default
Config File Support       ✗           CLI args only
```

## Integration Points

```
run_visualization_pipeline.py
│
├─ Integrates with: judge_journal.py
│  └─ Via: subprocess.run()
│  └─ Input: journal.json
│  └─ Output: journal_with_judgements.json
│
├─ Integrates with: plan_judge.py
│  └─ Via: subprocess.run()
│  └─ Input: journal_with_judgements.json
│  └─ Output: plan_redundancy_report.json
│
├─ Integrates with: journal_viz_.py
│  └─ Via: subprocess.run()
│  └─ First: Updates configuration via regex
│  └─ Input: journal_with_judgements.json, plan_redundancy_report.json
│  └─ Output: journal_viz_tree_dashboard.html
│  └─ Finally: Restores original state
│
└─ Integrates with: metrics.csv
   └─ Via: csv.DictReader()
   └─ Lookup: competition_name (case-insensitive)
   └─ Output: dict with metric config
```

---

These diagrams illustrate the complete system architecture and data flow.

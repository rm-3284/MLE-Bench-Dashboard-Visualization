# Implementation Details - Technical Reference

## File Architecture Overview

### Core Pipeline Components

#### 1. run_visualization_pipeline.py (607 lines)

**Purpose**: Main orchestration script for the 3-step visualization pipeline

**Key Functions**:

- `parse_journal_path(journal_path)` - Extracts competition name and UUID from path using regex
- `load_metrics_from_csv(competition_name, metrics_csv_path)` - Loads metric config from CSV
- `update_journal_viz_config(metrics_info)` - Dynamically updates journal*viz*.py with metrics
- `run_judge_journal(working_dir)` - Executes judge_journal.py with 1hr timeout
- `run_plan_judge(working_dir)` - Executes plan_judge.py with 30min timeout
- `run_visualization(output_file, working_dir)` - Executes journal*viz*.py with 10min timeout

**Command-Line Interface**:

```bash
python run_visualization_pipeline.py <journal_path> [options]
--skip-judge        Skip LLM verification (use existing journal_with_judgements.json)
--skip-plan         Skip plan analysis (use existing plan_redundancy_report.json)
--output FILE       Custom HTML output filename (default: journal_viz_tree_dashboard.html)
--metrics PATH      Custom metrics CSV path (default: metrics.csv)
```

**Data Flow**:

```
journal.json → [parse path] → [load metrics] → [update viz config]
    ↓                                              ↓
[judge_journal.py] → journal_with_judgements.json → [plan_judge.py]
    ↓                                                  ↓
plan_redundancy_report.json → [journal_viz_.py] → dashboard.html
```

---

#### 2. journal*viz*.py (480 lines)

**Purpose**: Generates interactive HTML dashboard with tree visualization

**Key Features**:

- D3.js tree layout for node hierarchy
- Side-by-side code diffs with syntax highlighting
- Chart.js metrics visualization over time
- LLM judgment display with status colors
- Plan and code redundancy analysis tabs
- Resizable sidebar with drag handle

**Key Functions**:

- `get_ast_logic(code_str)` - Parses code into AST for comparison
- `analyze_code_redundancy(nodes)` - Detects duplicate code among siblings
- `generate_side_by_side_diff(code_a, code_b)` - Creates HTML diff view
- `main()` - Orchestrates HTML generation with embedded data

**Configuration Variables** (Auto-updated by pipeline):

```python
DATA_FILE = "journal_with_judgements.json"
PLAN_RED_FILE = "plan_redundancy_report.json"
OUTPUT_FILE = "journal_viz_tree_dashboard.html"
METRIC_INFO = {
    "NAME": "Micro-F1-Score",
    "DESCRIPTION": "The harmonic mean...",
    "GOAL": "maximize"
}
FORCE_BUGGY_TO_DEFAULT = False
IGNORE_BUGGY_WITHOUT_METRIC = False
DEFAULT_BUGGY_METRIC = -0.1
```

**Field Compatibility**: Handles both `'parent_id'` and `'parent'` field formats from journal files

---

#### 3. judge_journal.py (150 lines)

**Purpose**: Uses LLM to verify code correctness against plan

**API Integration**: Vertex AI Gemini (via Google Cloud)

**Key Functions**:

- `get_llm_response(sys_prompt, usr_prompt)` - Calls Vertex AI API
- `main()` - Iterates through journal nodes, compares code to parent

**Judgment Format**:

```json
{
  "status": "aligned|partial|deviated",
  "reason": "Explanation text"
}
```

**Output**: Updates nodes with `llm_judgment` field → `journal_with_judgements.json`

---

#### 4. plan_judge.py (95 lines)

**Purpose**: Detects semantic redundancy in execution plans among sibling nodes

**API Integration**: Vertex AI Gemini (via Google Cloud)

**Key Functions**:

- `judge_plans_with_gemini(plans_list)` - LLM groups similar plans
- `analyze_all_plans(json_file)` - Finds nodes with multiple children, analyzes their plans

**Output Format** (`plan_redundancy_report.json`):

```json
{
  "parent_node_id": [
    [98, 99, 100], // Group 1: redundant plans
    [110, 111, 112] // Group 2: redundant plans
  ]
}
```

**Usage**: `python plan_judge.py /path/to/journal_with_judgements.json`

---

### Batch Processing Scripts

#### 5. run_viz_only_all.sh (105 lines)

**Purpose**: Regenerate all dashboards without re-running judge/plan steps

**Features**:

- Finds all 169 `journal_with_judgements.json` files
- Runs `run_visualization_pipeline.py` with `--skip-judge --skip-plan`
- Dry-run mode (default) shows targets without execution
- `--apply` flag executes actual regeneration
- `--limit N` processes only first N files
- Progress logging to `run_viz_only_all.log`

**Usage**:

```bash
./run_viz_only_all.sh              # Dry-run (show what would happen)
./run_viz_only_all.sh --apply      # Execute on all 169 files
./run_viz_only_all.sh --apply --limit 5  # Test on first 5
```

---

#### 6. run_viz_by_date.sh (120 lines)

**Purpose**: Process runs grouped by date directory

**Features**:

- Groups runs by date pattern `YYYY-MM-DDT*`
- Supports `--skip-judge` for fast iteration
- Logs to `run_viz_by_date.log`

**Usage**: `./run_viz_by_date.sh [--skip-judge]`

---

#### 7. run_plan_judge_all.py (243 lines)

**Purpose**: Batch analyze all nodes with multiple children for plan redundancy

**Key Features**:

- Skips nodes already in `plan_redundancy_report.json`
- Handles 429 API errors with exponential backoff (2s, 4s, 8s)
- Max 3 retry attempts per file
- Dry-run mode (default)
- `--apply` executes actual analysis
- `--limit N` for testing

**Key Functions**:

- `get_analyzed_nodes(logs_dir)` - Reads existing report, returns set of analyzed node IDs
- `get_nodes_to_analyze(journal_path)` - Finds nodes with `len(children) > 1`
- `run_plan_judge(journal_path, script_dir, apply, max_retries)` - Executes plan_judge.py with retry logic

**Usage**:

```bash
python run_plan_judge_all.py                # Dry-run
python run_plan_judge_all.py --apply        # Execute all
python run_plan_judge_all.py --apply --limit 10  # Test on first 10
```

**Error Recovery**: Rerunning `--apply` only processes files that previously failed or have new multi-child nodes

---

#### 8. fix_judgment_errors.py (135 lines)

**Purpose**: Re-run failed LLM judgments (status == "error")

**Key Features**:

- Identifies nodes with `llm_judgment.status == "error"`
- Retries with exponential backoff on 429 errors
- Max 3 attempts per entry
- Updates `journal_with_judgements.json` in-place

**Key Functions**:

- `get_llm_response_with_retry(sys_p, usr_p, max_retries)` - API call with backoff
- `identify_error_entries(nodes)` - Finds failed judgments
- `rejudge_entry(node, prev_code)` - Re-runs LLM verification

**Usage**: `python fix_judgment_errors.py /path/to/journal_with_judgements.json`

---

#### 9. fix_all_judgment_errors.sh (35 lines)

**Purpose**: Find and fix all judgment errors across all runs

**Logic**:

```bash
find ../runs -name "journal_with_judgements.json" | while read file; do
  if grep -q '"status": "error"' "$file"; then
    python fix_judgment_errors.py "$file"
  fi
done
```

---

### Data Structure Utilities

#### 10. update_tree_structure.py (229 lines)

**Purpose**: Rebuild parent-child relationships from `node2parent` mapping

**Key Features**:

- Handles both list `[...]` and dict `{"nodes": [...]}` formats
- Updates `parent` and `children` fields based on `node2parent` mapping
- `--apply` writes changes, default is dry-run
- `--limit N` for testing

**Key Functions**:

- `update_journal_file(logs_dir, apply)` - Processes single journal file
- Validates node IDs exist before creating relationships

**Results**: Applied to 169 files, 29 updated with 1,827 total relationship changes

**Usage**:

```bash
python update_tree_structure.py              # Dry-run
python update_tree_structure.py --apply      # Execute
python update_tree_structure.py --apply --limit 5  # Test
```

---

#### 11. standardize_journal_format.py (116 lines)

**Purpose**: Convert all journal files to consistent list format

**Conversion**:

```python
# Before (dict format)
{"nodes": [{...}, {...}]}

# After (list format)
[{...}, {...}]
```

**Key Functions**:

- `standardize_journal_file(journal_path, apply)` - Converts single file
- Handles both formats gracefully
- `--apply` writes changes

**Usage**: `python standardize_journal_format.py [--apply] [--limit N]`

---

### Dashboard Management

#### 12. generate_hyper_dashboard.py (330 lines)

**Purpose**: Create static HTML index of all run dashboards

**Key Features**:

- Scans `runs/` for all `journal_viz_tree_dashboard.html`
- Groups by competition
- Extracts metrics from each dashboard
- Generates card-based layout

**Key Functions**:

- `find_visualization_files(runs_dir)` - Recursively finds dashboard files
- `generate_card_html(viz_file)` - Creates card with competition info
- `generate_html(viz_files)` - Builds full HTML index

**Output**: `hyper_dashboard.html` in runs/ directory

**Usage**: `python generate_hyper_dashboard.py`

---

#### 13. serve_hyper_dashboard.py (400 lines)

**Purpose**: Live HTTP server with dynamic dashboard generation

**Key Features**:

- HTTP server on `localhost:8000`
- Scans `runs/` on every request (no static file needed)
- Auto-detects new runs without restart
- Serves individual dashboards and main index

**Key Classes**:

- `DashboardHTTPHandler` - Custom HTTP handler
  - `do_GET()` - Handles requests
  - `generate_dashboard_html()` - Creates HTML on-the-fly
  - `find_visualization_files()` - Scans runs/
  - `generate_card_html()` - Card generation

**Usage**:

```bash
python serve_hyper_dashboard.py
# Open http://localhost:8000/hyper_dashboard.html
```

---

### Testing & Debugging

#### 14. test_pipeline.py (15 lines)

**Purpose**: Unit test for pipeline functions

**Tests**:

- `parse_journal_path()` with real paths
- `load_metrics_from_csv()` with real competition names
- Validates output format

**Usage**: `python test_pipeline.py`

---

#### 15. debug_plan_judge.py (147 lines)

**Purpose**: Debug plan_judge.py execution with detailed output

**Key Features**:

- Shows nodes with multiple children
- Displays plan_redundancy_report.json before/after
- Real-time streaming of plan_judge.py output
- Uses threading for stdout/stderr capture

**Key Functions**:

- `stream_output(pipe, prefix)` - Thread for output capture
- Compares analyzed nodes before/after execution

**Usage**: `python debug_plan_judge.py`

---

## Core Functions Reference

### 1. Path Parsing

```python
def parse_journal_path(journal_path):
    """
    Extract competition name and run ID from path.

    Input format: .../competition_name-run_id/logs/journal.json

    Returns: (competition_name, run_id, working_dir, journal_file)

    Examples:
    Input:  '/data/tensorflow2-question-answering_a3cf875b-2303-466b/logs/journal.json'
    Output: ('tensorflow2-question-answering_a3cf875b-2303-466b', 'bd8d-5a28...', PosixPath(...), PosixPath(...))

    Input:  '/data/dog-breed-identification-xyz789/logs/'
    Output: ('dog-breed-identification', 'xyz789', PosixPath(...), PosixPath(...))
    """
    # Handles both file paths and directory paths
    # Uses regex: ^(.+?)-([a-f0-9]+)$ to extract {name}-{uuid}
    # Returns None values if parsing fails
```

### 2. Metrics Loading

```python
def load_metrics_from_csv(competition_name, metrics_csv_path="metrics.csv"):
    """
    Load metric configuration from CSV based on competition name.

    CSV format:
    competition_name,metric_name,metric_description,goal,buggy_ignore,default_value_for_buggy
    tensorflow2-question-answering,micro-f1-score,The harmonic mean...,maximize,False,-0.1

    Returns: dict with keys:
    - metric_name: str (title-cased)
    - metric_description: str
    - goal: str ("maximize" or "minimize")
    - ignore_buggy_without_metric: bool
    - default_buggy_metric: float

    Returns None if CSV not found or competition not in CSV.
    """
    # Case-insensitive matching
    # Converts CSV string booleans: "True"/"False" → True/False
    # Converts default value to float
```

### 3. Configuration Update

```python
def update_journal_viz_config(metrics_info):
    """
    Dynamically update journal_viz_.py with loaded metrics.

    Modifies in-place:
    METRIC_INFO = {
        "NAME": "...",
        "DESCRIPTION": "...",
        "GOAL": "maximize|minimize"
    }
    IGNORE_BUGGY_WITHOUT_METRIC = True|False
    DEFAULT_BUGGY_METRIC = float_value

    Uses regex replacements to maintain code structure.
    Preserves whitespace and comments.

    Returns: bool (success/failure)
    """
    # Regex patterns:
    # - METRIC_INFO: r'METRIC_INFO = \{[^}]*\}'
    # - IGNORE_BUGGY: r'IGNORE_BUGGY_WITHOUT_METRIC = \w+'
    # - DEFAULT_BUGGY: r'DEFAULT_BUGGY_METRIC = [\d\-\.]+'
```

### 4. Pipeline Orchestration

```python
def run_judge_journal():
    """Execute judge_journal.py with error handling."""
    # Checks for journal.json
    # Warns about missing API keys
    # Runs with 1 hour timeout
    # Verifies output exists
    # Returns: bool

def run_plan_judge():
    """Execute plan_judge.py with error handling."""
    # Checks for journal_with_judgements.json
    # Runs with 30 minute timeout
    # Verifies plan_redundancy_report.json created
    # Returns: bool

def run_visualization(output_file):
    """Execute journal_viz_.py with error handling."""
    # Optionally updates OUTPUT_FILE in journal_viz_.py
    # Restores original file after execution
    # Runs with 10 minute timeout
    # Verifies HTML output created
    # Returns: bool
```

## Configuration Changes Made to journal*viz*.py

### Before

```python
METRIC_INFO = {
    "NAME": "Micro F1 Score",
    "DESCRIPTION": "Harmonic mean of global precision and global recall across all classes.",
    "GOAL": "maximize"
}
IGNORE_BUGGY_WITHOUT_METRIC = False
DEFAULT_BUGGY_METRIC = -0.1
```

### After (automatically updated based on metrics.csv)

```python
METRIC_INFO = {
    "NAME": "Root-Mean-Squared-Error",
    "DESCRIPTION": "The square root of the average of squared differences between predicted and actual values.",
    "GOAL": "minimize"
}
IGNORE_BUGGY_WITHOUT_METRIC = True
DEFAULT_BUGGY_METRIC = 8.0
```

## Error Handling Strategy

### Validation Points

1. **Path Parsing**
   - Check if file/directory exists
   - Check if journal.json exists
   - Check if directory name matches {name}-{uuid} format
   - Fallback: Return None values and warn user

2. **Metric Loading**
   - Check if metrics.csv exists
   - Check if competition found in CSV
   - Fallback: Return None and warn user

3. **Configuration Update**
   - Try regex replacements
   - Catch exceptions during file I/O
   - Fallback: Proceed with defaults and warn user

4. **Pipeline Execution**
   - Check input file exists before each step
   - Verify output file created after each step
   - Check process return code
   - Handle timeouts gracefully
   - Restore original files on error

### Timeouts

- Judge: 1 hour (LLM API calls can be slow)
- Plan: 30 minutes (Gemini analysis)
- Visualization: 10 minutes (HTML generation)

## Logging System

### Log Levels

- **STEP**: Major phase separator (blue background)
- **SUCCESS**: Successful operation (green ✓)
- **WARNING**: Non-fatal issue (yellow ⚠)
- **ERROR**: Fatal issue (red ✗)
- **INFO**: Informational message (blue)

### Example Output

```
============================================================
STEP 0: Loading Configuration
============================================================

[✓] Found journal.json: /path/to/journal.json
[✓] Extracted: competition=tensorflow2-question-answering, run_id=a3cf875b
[✓] Loaded metrics: Micro-F1-Score
[INFO]   Goal: maximize
[INFO]   Ignore buggy without metric: False
[INFO]   Default buggy metric: -0.1
[✓] Updated journal_viz_.py with metrics for Micro-F1-Score
[✓] Working directory: /path/to/logs
```

## File I/O Operations

### Reading

- **metrics.csv** - CSV format with DictReader for flexibility
- **journal*viz*.py** - Full file read for regex-based updates
- **judge_journal.py** - Subprocess output capture

### Writing

- **journal*viz*.py** - Conditional updates with regex patterns
- **Subprocess outputs** - Captured and logged

### Encoding

- All files: UTF-8
- Handles special characters correctly
- No BOM (Byte Order Mark) issues

## Subprocess Management

```python
subprocess.run(
    [sys.executable, script_name],
    capture_output=True,      # Capture stdout/stderr
    text=True,                # Return strings not bytes
    timeout=seconds           # Prevent hangs
)

# Returns: CompletedProcess
# - returncode: 0 = success, != 0 = failure
# - stdout: Script output
# - stderr: Error messages
```

## Key Design Decisions

### 1. Regex-Based Updates (Not AST)

- **Why**: Preserves comments, formatting, whitespace
- **Alternative**: AST parsing would reformat file
- **Trade-off**: More fragile to code structure changes

### 2. Temporary File Modification

- **Why**: Minimal changes to existing code
- **Alternative**: Pass configuration as environment variables
- **Trade-off**: Requires file restoration

### 3. Case-Insensitive Name Matching

- **Why**: Flexibility with user input
- **Example**: "TensorFlow2-Question-Answering" matches "tensorflow2-question-answering"
- **Safety**: Still warns if not found

### 4. CSV Over JSON for Metrics

- **Why**: Easy to edit in spreadsheet apps
- **Alternative**: JSON would be more structured
- **Trade-off**: Less strict validation

## Testing Checklist

### Unit Testing

- [ ] Parse valid path ✓
- [ ] Parse path without UUID ✓
- [ ] Load existing metrics ✓
- [ ] Load non-existent metrics ✓
- [ ] Update journal*viz*.py ✓

### Integration Testing

- [ ] Full pipeline execution
- [ ] Skip judge option
- [ ] Skip plan option
- [ ] Custom output filename
- [ ] Custom metrics CSV path
- [ ] Error recovery and logging

### Manual Testing (Real Workspace)

- [ ] Path: `../mle-bench-fork/runs/.../tensorflow2-question-answering_xxx/logs`
- [ ] Verify metrics loaded correctly
- [ ] Verify journal*viz*.py updated
- [ ] Verify HTML generated

## Performance Characteristics

### Memory Usage

- Loads entire CSV into memory (~1KB)
- Loads entire journal*viz*.py into memory (~50KB)
- Subprocess memory depends on data size

### Time Complexity

- Path parsing: O(1)
- CSV loading: O(n) where n = number of competitions (typically <20)
- File updates: O(m) where m = file size (~50KB)
- Pipeline execution: O(data_size) for each step

### I/O Patterns

- 1x read journal.json (via subprocess)
- 1x read metrics.csv
- 1x read journal*viz*.py
- 1x write journal*viz*.py (updated)
- 1x write journal*viz*.py (restored)
- N subprocess executions

## Compatibility

### Python Versions

- Tested: Python 3.7+
- Uses: pathlib (3.4+), f-strings (3.6+), subprocess (all versions)
- No external dependencies

### Operating Systems

- macOS ✓ (tested)
- Linux ✓ (pathlib compatible)
- Windows ✓ (pathlib handles path separators)

### Backward Compatibility

- Works with existing journal.json format
- Works with existing metrics.csv format
- Doesn't break existing scripts
- Can be run alongside manual process

## Future Enhancement Ideas

- [ ] Parallel processing for large journal files
- [ ] Incremental updates (only process changed entries)
- [ ] Config file support (.pipeline.yaml)
- [ ] Database backend for metrics instead of CSV
- [ ] Web UI for configuration
- [ ] Automatic API key detection from environment
- [ ] Dry-run mode (print changes without executing)
- [ ] Hook system for pre/post steps
- [ ] Summary statistics export to JSON

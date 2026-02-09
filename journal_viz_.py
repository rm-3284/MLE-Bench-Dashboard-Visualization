import os
import json
import ast
import difflib
from collections import defaultdict
from pathlib import Path

# --- CONFIGURATION ---
DATA_FILE = "journal_with_judgements.json"
PLAN_RED_FILE = "plan_redundancy_report.json"
OUTPUT_FILE = "journal_viz_tree_dashboard.html"
COMPETITION_NAME = "tensorflow2-question-answering"  # Auto-updated by pipeline
METRIC_INFO = {
    "NAME": "Micro F1 Score",
    "DESCRIPTION": "Harmonic mean of global precision and global recall across all classes.",
    "GOAL": "maximize" # Use "maximize" or "minimize"
}

# --- BUGGY NODE HANDLING ---
# --- BUGGY NODE HANDLING ---
# If True, buggy nodes are set to DEFAULT_BUGGY_METRIC even if they have a score.
# If False, we only use DEFAULT_BUGGY_METRIC if the node has NO score.
FORCE_BUGGY_TO_DEFAULT = False 

# If a buggy node has no metric and FORCE is False:
#   True  -> Exclude it from the graph entirely.
#   False -> Show it on the graph using DEFAULT_BUGGY_METRIC.
IGNORE_BUGGY_WITHOUT_METRIC = False 

DEFAULT_BUGGY_METRIC = -0.1

# ==========================================
# 1. LOGIC & DIFF UTILS
# ==========================================
def get_ast_logic(code_str):
    try:
        tree = ast.parse(code_str)
        return ast.dump(tree, annotate_fields=False)
    except:
        return code_str

def load_competition_description(competition_name):
    """
    Load the competition description from ../mle-bench-fork/mlebench/competitions/{competition_name}/description.md
    Returns the content as a string, or empty string if not found.
    """
    if not competition_name:
        return ""
    
    try:
        # Try multiple possible paths
        current_dir = Path.cwd()
        possible_paths = [
            current_dir.parent.parent / "mle-bench-fork" / "mlebench" / "competitions" / competition_name / "description.md",
            Path("/Users/ryomitsuhashi/Desktop/Princeton/Research/MLE bench/mle-bench-fork/mlebench/competitions") / competition_name / "description.md",
        ]
        
        for desc_path in possible_paths:
            if desc_path.exists():
                with open(desc_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return ""
    except Exception as e:
        return ""

def analyze_code_redundancy(nodes):
    siblings_map = defaultdict(list)
    for n in nodes:
        pid = n.get('parent_id')
        if pid and pid != 'SUPER_ROOT':
            siblings_map[pid].append(n)
            
    redundancy_map = {}
    for pid, children in siblings_map.items():
        if len(children) < 2: continue
        groups = defaultdict(list)
        for child in children:
            norm = get_ast_logic(child.get('code', ""))
            groups[norm].append(child['id'])
        duplicates = [g for g in groups.values() if len(g) > 1]
        if duplicates: redundancy_map[pid] = duplicates
    return redundancy_map

def generate_side_by_side_diff(code_a, code_b):
    if code_a is None: code_a = ""
    if code_b is None: code_b = ""
    lines_a = code_a.splitlines()
    lines_b = code_b.splitlines()
    diff = list(difflib.ndiff(lines_a, lines_b))
    html_a, html_b = [], []
    for line in diff:
        prefix, content = line[:2], line[2:].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if prefix == '  ': 
            html_a.append(f'<div class="diff-row">{content}</div>')
            html_b.append(f'<div class="diff-row">{content}</div>')
        elif prefix == '- ': 
            html_a.append(f'<div class="diff-row diff-removed">{content}</div>')
            html_b.append('<div class="diff-row empty">&nbsp;</div>')
        elif prefix == '+ ': 
            html_a.append('<div class="diff-row empty">&nbsp;</div>')
            html_b.append(f'<div class="diff-row diff-added">{content}</div>')
    return {'left': "".join(html_a), 'right': "".join(html_b)}

# ==========================================
# 2. MODULAR HTML PIECES
# ==========================================

HTML_HEAD = """
<head>
    <meta charset="UTF-8">
    <title>Agent Forest Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root { --bg: #1e1e1e; --panel: #252526; --border: #3e3e42; --text: #d4d4d4; --accent: #007fd4; --valid: #4ec9b0; --buggy: #f48771; --partial: #ce9178; }
        * { box-sizing: border-box; }
        body { margin: 0; display: flex; height: 100vh; background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; overflow: hidden; }
        
        /* Layout */
        .sidebar { width: 400px; min-width: 200px; background: var(--panel); display: flex; flex-direction: column; flex-shrink: 0; }
        /* NEW: Resizer Handle Styles */
        .resizer { width: 4px; background: var(--bg); border-left: 1px solid var(--border); border-right: 1px solid var(--border); cursor: col-resize; flex-shrink: 0; transition: background 0.2s; z-index: 10; }
        .resizer:hover, .resizer.active { background: var(--accent); }

        .main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .tabs { display: flex; background: #2d2d30; border-bottom: 1px solid var(--border); height: 40px; flex-shrink: 0; }
        .tab { padding: 0 20px; display: flex; align-items: center; cursor: pointer; border-right: 1px solid var(--border); color: #858585; font-size: 13px; }
        .tab.active { background: var(--bg); color: var(--valid); border-top: 2px solid var(--valid); font-weight: 600; }
        .tab-content { display: none; padding: 0; flex: 1; overflow-y: auto; }
        .tab-content.active { display: block; }

        /* Tree Forest */
        .tree-container { flex: 1; overflow: hidden; cursor: grab; position: relative; }
        .node circle { fill: #2d2d30; stroke: #555; stroke-width: 2.5px; }
        .node.valid circle { stroke: var(--valid); }
        .node.buggy circle { stroke: var(--buggy); }
        .node text { font-size: 12px; font-weight: 600; fill: #fff; text-shadow: 1px 1px 2px #000; pointer-events: none; }
        .node.selected circle { r: 9; filter: brightness(1.5); fill: #fff; }
        .link { fill: none; stroke: var(--border); stroke-width: 1.5px; opacity: 0.6; }

        /* Components */
        .panel-padding { padding: 30px; margin: 0; }
        .section { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 20px; margin-bottom: 20px; }
        .metric-grid { width: 100%; margin-bottom: 30px; }
        .metric-card { display: inline-block; width: 19%; margin-right: 1%; text-align: center; background: #2d2d30; padding: 12px 8px; border-radius: 4px; border: 1px solid var(--border); vertical-align: top; }
        .metric-card label { display: block; font-size: 10px; color: #888; text-transform: uppercase; margin-bottom: 5px; }
        .metric-card span { font-size: 14px; font-weight: bold; }

        /* Static Diff */
        .diff-container { display: flex; font-family: 'Consolas', monospace; font-size: 11px; background: #1e1e1e; border: 1px solid var(--border); }
        .code-pane { width: 50%; padding: 10px; white-space: pre; overflow-x: auto; }
        .diff-row { min-height: 1.2em; line-height: 1.2em; }
        .diff-added { background: rgba(46, 160, 67, 0.15); color: #b4f0b0; }
        .diff-removed { background: rgba(248, 81, 73, 0.15); color: #ffb0a0; }
        .empty { background: #252526; opacity: 0.3; }

        details { cursor: pointer; background: #1a1a1a; padding: 10px; border-radius: 4px; border: 1px solid var(--border); }
        pre { color: #9cdcfe; font-family: Consolas, monospace; font-size: 13px; white-space: pre-wrap; word-break: break-all; }
        .red-group { margin-bottom: 15px; padding: 12px; background: #2d2d30; border-radius: 6px; border-left: 4px solid var(--accent); }
        .badge-id { display: inline-block; padding: 2px 6px; background: #1e1e1e; border: 1px solid #555; border-radius: 4px; margin-right: 5px; font-size: 11px; }

        /* GitHub Markdown Style */
        .markdown-content { font-size: 14px; line-height: 1.6; color: #d4d4d4; }
        .markdown-content h1 { font-size: 2em; font-weight: 600; margin: 24px 0 16px 0; padding-bottom: 0.3em; border-bottom: 1px solid #3e3e42; }
        .markdown-content h2 { font-size: 1.5em; font-weight: 600; margin: 24px 0 16px 0; padding-bottom: 0.3em; border-bottom: 1px solid #3e3e42; }
        .markdown-content h3 { font-size: 1.25em; font-weight: 600; margin: 24px 0 16px 0; }
        .markdown-content h4 { font-size: 1em; font-weight: 600; margin: 24px 0 16px 0; }
        .markdown-content h5 { font-size: 0.875em; font-weight: 600; margin: 24px 0 16px 0; }
        .markdown-content h6 { font-size: 0.85em; font-weight: 600; margin: 24px 0 16px 0; color: #a0a0a0; }
        .markdown-content p { margin: 0 0 16px 0; }
        .markdown-content ul, .markdown-content ol { padding-left: 2em; margin: 0 0 16px 0; }
        .markdown-content li { margin: 8px 0; }
        .markdown-content code { background: #1a1a1a; padding: 0.2em 0.4em; border-radius: 3px; font-family: Consolas, monospace; font-size: 0.9em; color: #ce9178; }
        .markdown-content pre { background: #1a1a1a; border: 1px solid #3e3e42; border-radius: 6px; padding: 16px; overflow-x: auto; margin: 0 0 16px 0; }
        .markdown-content pre code { background: none; padding: 0; color: #9cdcfe; }
        .markdown-content blockquote { border-left: 4px solid #3e3e42; padding-left: 16px; margin: 0 0 16px 0; color: #a0a0a0; font-style: italic; }
        .markdown-content table { border-collapse: collapse; margin: 0 0 16px 0; }
        .markdown-content table th { background: #2d2d30; padding: 8px 12px; border: 1px solid #3e3e42; font-weight: 600; }
        .markdown-content table td { padding: 8px 12px; border: 1px solid #3e3e42; }
        .markdown-content a { color: #007fd4; text-decoration: none; }
        .markdown-content a:hover { text-decoration: underline; }
        .markdown-content strong { font-weight: 600; }
        .markdown-content em { font-style: italic; }
        .markdown-content hr { background: #3e3e42; border: 0; height: 1px; margin: 24px 0; }
    </style>
</head>
"""

SIDEBAR_PART = """
<div class="sidebar" id="sidebar">
    <div style="padding: 15px; background: #2d2d30; border-bottom: 1px solid var(--border); flex-shrink: 0;">
        <h2 style="margin:0; font-size: 14px; text-transform: uppercase; color: #fff;">🌲 Search Forest</h2>
    </div>
    <div id="d3-container" class="tree-container"></div>
</div>
"""

STATS_PART = """
<div id="tab-stats" class="tab-content">
    <div class="panel-padding">
        <div class="section"><h1>Global Statistics</h1></div>
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:15px; margin-bottom:20px;">
            <div class="section stat-card"><div class="stat-val" id="st-total">0</div><div style="color:#888; font-size:11px">Total Steps</div></div>
            <div class="section stat-card"><div class="stat-val" style="color:var(--valid)" id="st-valid">0</div><div style="color:#888; font-size:11px">Valid</div></div>
            <div class="section stat-card"><div class="stat-val" style="color:var(--buggy)" id="st-buggy">0</div><div style="color:#888; font-size:11px">Buggy</div></div>
            <div class="section stat-card"><div class="stat-val" id="st-best">0</div><div style="color:#888; font-size:11px">Best Result</div></div>
        </div>
        <div class="section"><div style="height:450px;"><canvas id="metricChart"></canvas></div></div>
    </div>
</div>
"""

DETAIL_PART = """
<div id="tab-detail" class="tab-content active">
    <div class="panel-padding">
        <div id="detail-view" style="display:none">
            <div class="metric-grid" id="detail-stats"></div>
            <div class="section" id="detail-verification"></div>
            <div class="section"><h3>📝 Plan</h3><div id="detail-plan" style="color: #ccc;"></div></div>
            <div class="section"><h3>🔍 Analysis</h3><div id="detail-analysis" style="color: #aaa; font-style: italic;"></div></div>
            <div class="section"><details><summary>View Full Code Implementation</summary><pre id="detail-full-code"></pre></details></div>
            <div class="section"><h3>💻 Code Changes (vs Parent)</h3>
                <div class="diff-container"><div class="code-pane" id="diff-left"></div><div class="code-pane" id="diff-right"></div></div>
            </div>
        </div>
        <div id="empty-state" style="text-align:center; margin-top:100px; color:#555;"><h2>Select a node from the tree to view details</h2></div>
    </div>
</div>
"""

BRANCH_PART = """
<div id="tab-branch" class="tab-content">
    <div class="panel-padding" style="height:100%; display:flex; flex-direction:column;">
        <div class="section"><h1>Branching & Redundancy</h1></div>
        <div style="display: flex; gap: 20px; flex: 1; min-height: 0;">
            <div id="branch-list" style="width: 250px; overflow-y: auto; background: var(--panel); border: 1px solid var(--border); border-radius: 6px;"></div>
            <div id="branch-detail" style="flex: 1; overflow-y: auto; background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 20px;">
                <p style="color:#777; text-align:center; margin-top:50px;">Select a branching step to analyze.</p>
            </div>
        </div>
    </div>
</div>
"""

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
def main():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict): data = data.get("nodes", [])

    id_to_node = {n['id']: n for n in data}
    for n in data:
        # Handle both old format (parent_id) and new format (parent)
        pid = n.get('parent_id') or n.get('parent')
        if not pid or pid not in id_to_node: 
            n['parent_id'] = 'SUPER_ROOT'
        else:
            n['parent_id'] = pid
        p_code = id_to_node.get(n['parent_id'], {}).get('code', "")
        n['diff_html'] = generate_side_by_side_diff(p_code, n.get('code', ""))

    # Load competition description
    description = load_competition_description(COMPETITION_NAME)
    # Escape special JSON characters in description
    if description:
        description = (description
            .replace('\\', '\\\\')  # Escape backslashes first
            .replace('"', '\\"')     # Escape quotes
            .replace('\n', '\\n')    # Escape newlines for JSON
            .replace('\r', '\\r'))   # Escape carriage returns
    
    data.insert(0, {"id": "SUPER_ROOT", "parent_id": None, "step": 0, "code": "", "is_buggy": False, "description": description})

    # Redundancy Setup
    code_red_map = analyze_code_redundancy(data)
    plan_red_map = {}
    step_to_id = {str(n['step']): n['id'] for n in data if 'step' in n}
    if os.path.exists(PLAN_RED_FILE):
        try:
            with open(PLAN_RED_FILE, 'r') as f:
                raw = json.load(f)
                for pid, groups in raw.items():
                    plan_red_map[pid] = [[step_to_id.get(str(s), str(s)) for s in g] for g in groups]
        except: pass

    goal_type = METRIC_INFO.get("GOAL", "maximize").lower()
    goal_icon = "⬆️" if goal_type == "maximize" else "⬇️"
    goal_text = "Higher is better" if goal_type == "maximize" else "Lower is better"

    full_html = """<!DOCTYPE html><html lang="en">""" + HTML_HEAD + """
<body>
    """ + SIDEBAR_PART + """
    <div id="drag-handle" class="resizer"></div>
    <div class="main-content">
        <div class="tabs">
            <div class="tab" onclick="switchTab('stats')">📊 Stats</div>
            <div class="tab active" onclick="switchTab('detail')">📄 Detail</div>
            <div class="tab" onclick="switchTab('branch')">🌿 Branching</div>
        </div>
        """ + STATS_PART + DETAIL_PART + BRANCH_PART + """
    </div>
    <script>
        const stepsData = """ + json.dumps(data) + """;
        const planRedData = """ + json.dumps(plan_red_map) + """;
        const codeRedData = """ + json.dumps(code_red_map) + """;
        const METRIC_NAME = \"""" + METRIC_INFO['NAME'] + """\";
        const METRIC_DESC = \"""" + METRIC_INFO['DESCRIPTION'] + """\";
        const GOAL_TYPE = \"""" + goal_type + """\";
        const GOAL_ICON = \"""" + goal_icon + """\";
        const GOAL_TEXT = \"""" + goal_text + """\";
        
        // --- CONSTANTS ---
        const CONF_FORCE_DEFAULT = """ + str(FORCE_BUGGY_TO_DEFAULT).lower() + """;
        const CONF_IGNORE_MISSING = """ + str(IGNORE_BUGGY_WITHOUT_METRIC).lower() + """;
        const CONF_DEFAULT_VAL = """ + str(DEFAULT_BUGGY_METRIC) + """;
        
        let treeMap = {};
        stepsData.forEach(s => treeMap[s.id] = s);

        function switchTab(n) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const map = {'stats': 0, 'detail': 1, 'branch': 2};
            document.querySelectorAll('.tab')[map[n]].classList.add('active');
            document.getElementById('tab-'+n).classList.add('active');
        }

        function getMetric(s) {
            if(!s) return null;
            return typeof s.metric === 'number' ? s.metric : (s.metric?.value || null);
        }

        function getStatusColor(status) {
            const s = (status || "").toLowerCase();
            if (s === 'aligned') return 'var(--valid)';
            if (s === 'partial') return 'var(--partial)';
            if (s === 'deviated') return 'var(--buggy)';
            return 'var(--text)';
        }

        function initStats() {
            const realSteps = stepsData.filter(s => s.id !== 'SUPER_ROOT');
            const metricsOnly = realSteps.map(s => getMetric(s)).filter(v => v !== null);
            let best = metricsOnly.length > 0 ? (GOAL_TYPE === 'maximize' ? Math.max(...metricsOnly) : Math.min(...metricsOnly)).toFixed(4) : "N/A";
            document.getElementById('st-total').innerText = realSteps.length;
            document.getElementById('st-valid').innerText = realSteps.filter(s => !s.is_buggy).length;
            document.getElementById('st-buggy').innerText = realSteps.filter(s => s.is_buggy).length;
            document.getElementById('st-best').innerText = best;

            const dataPts = realSteps.map(s => {
                let val = getMetric(s);
                
                if (s.is_buggy) {
                    if (CONF_FORCE_DEFAULT) {
                        val = CONF_DEFAULT_VAL;
                    } else if (val === null) {
                        if (CONF_IGNORE_MISSING) return null;
                        val = CONF_DEFAULT_VAL;
                    }
                }
                
                if (val === null) return null;
                
                // --- Pass 'is_buggy' status to the data point ---
                return {x: s.step, y: val, is_buggy: s.is_buggy};
            }).filter(d => d !== null).sort((a,b) => a.x - b.x);

            if(dataPts.length > 0) {
                // --- Generate Color Array ---
                const pointColors = dataPts.map(d => d.is_buggy ? '#f48771' : '#4ec9b0');

                new Chart(document.getElementById('metricChart'), {
                    type: 'line',
                    data: {
                        labels: dataPts.map(d => 'Step ' + d.x),
                        datasets: [{ 
                            label: METRIC_NAME, 
                            data: dataPts.map(d => d.y), 
                            borderColor: '#4ec9b0', 
                            tension: 0.2,
                            // --- Apply Colors ---
                            pointBackgroundColor: pointColors,
                            pointBorderColor: pointColors,
                            pointRadius: 5,
                            pointHoverRadius: 7
                        }]
                    },
                    options: { 
                        maintainAspectRatio: false,
                        plugins: { subtitle: { display: true, text: [METRIC_DESC, GOAL_ICON + " " + GOAL_TEXT], color: '#aaa', font: { style: 'italic' } } }
                    }
                });
            }
        }

        function initD3() {
            const stratify = d3.stratify().id(d => d.id).parentId(d => d.parent_id);
            const root = stratify(stepsData);
            const svg = d3.select("#d3-container").append("svg").attr("width", "100%").attr("height", "100%");
            const g = svg.append("g").attr("transform", "translate(60,60)");
            svg.call(d3.zoom().on("zoom", (e) => g.attr("transform", e.transform)));
            d3.tree().nodeSize([50, 160])(root);
            
            g.selectAll(".link").data(root.links()).enter().append("path").attr("class", "link")
                .attr("d", d => "M" + d.source.y + "," + d.source.x + "C" + (d.source.y + d.target.y) / 2 + "," + d.source.x + " " + (d.source.y + d.target.y) / 2 + "," + d.target.x + " " + d.target.y + "," + d.target.x);
            
            const node = g.selectAll(".node").data(root.descendants()).enter().append("g")
                .attr("class", d => d.data.id === 'SUPER_ROOT' ? 'node root' : (d.data.is_buggy ? 'node buggy' : 'node valid'))
                .attr("id", d => "node-" + d.data.id).attr("transform", d => "translate(" + d.y + "," + d.x + ")")
                .on("click", (e, d) => { selectNode(d.data.id); });
            
            node.append("circle").attr("r", 7);
            node.append("text").attr("dy", -15).attr("text-anchor", "middle").text(d => d.data.id === 'SUPER_ROOT' ? 'START' : "Step " + d.data.step);
        }

        function selectNode(id) {
            const step = treeMap[id];
            d3.selectAll(".node circle").style("fill", "");
            d3.select("#node-"+id+" circle").style("fill", "#fff");
            
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('detail-view').style.display = 'block';

            // Special handling for SUPER_ROOT (start node)
            if (id === 'SUPER_ROOT') {
                // Hide all detail sections except description for SUPER_ROOT
                document.getElementById('detail-stats').style.display = 'none';
                document.querySelectorAll('div.section').forEach(el => {
                    if (el.querySelector('#detail-plan') || el.querySelector('#detail-analysis') || 
                        el.querySelector('#detail-full-code') || el.querySelector('.diff-container')) {
                        el.style.display = 'none';
                    }
                });
                
                // Display competition description if available
                const description = step.description || '';
                if (description) {
                    // Unescape JSON-escaped content using simple string replacement
                    let unescapedDesc = description;
                    unescapedDesc = unescapedDesc.split('\\\\n').join('\\n');
                    unescapedDesc = unescapedDesc.split('\\\\r').join('\\r');
                    unescapedDesc = unescapedDesc.split('\\\\"').join('"');
                    unescapedDesc = unescapedDesc.split('\\\\\\\\').join('\\\\');
                    
                    // Use marked.js to render markdown
                    const htmlContent = marked.parse(unescapedDesc);
                    
                    document.getElementById('detail-verification').style.display = 'block';
                    document.getElementById('detail-verification').innerHTML = `
                        <div class="markdown-content">
                            ${htmlContent}
                        </div>
                    `;
                } else {
                    document.getElementById('detail-verification').style.display = 'block';
                    document.getElementById('detail-verification').innerHTML = `
                        <h3>📋 Competition Description</h3>
                        <p style="color: #888; font-style: italic;">No description available.</p>
                    `;
                }
                
                switchTab('detail');
                return;
            }
            
            // For regular nodes, show all sections
            document.getElementById('detail-stats').style.display = 'block';
            document.querySelectorAll('div.section').forEach(el => {
                if (el.querySelector('#detail-plan') || el.querySelector('#detail-analysis') || 
                    el.querySelector('#detail-full-code') || el.querySelector('.diff-container')) {
                    el.style.display = 'block';
                }
            });
            document.getElementById('detail-verification').style.display = 'block';

            const mVal = getMetric(step) || 0;
            const jud = step.llm_judgment || {};
            
            const statusText = step.is_buggy ? "BUGGY" : "VALID";
            const statusColor = step.is_buggy ? "var(--buggy)" : "var(--valid)";
            
            document.getElementById('detail-stats').innerHTML = `<div class="metric-card"><label>Step</label><span>${step.step}</span></div><div class="metric-card"><label>Status</label><span style="color:${statusColor}">${statusText}</span></div><div class="metric-card"><label>Exec Time</label><span>${step.exec_time || 'N/A'}s</span></div><div class="metric-card"><label>${METRIC_NAME}</label><span>${Number(mVal).toFixed(4)}</span></div><div class="metric-card"><label>Magnitude</label><span>${step.magnitude || '0'}</span></div>`;

            document.getElementById('detail-verification').innerHTML = `
                <h3>🤖 LLM Verification</h3>
                <div style="color:${getStatusColor(jud.status)}; font-weight:bold; text-transform: uppercase;">
                    ${jud.status || 'Unknown'}
                </div>
                <p style="font-size: 12px; margin-top: 5px;">${jud.reason || 'No reasoning provided.'}</p>
            `;
            
            document.getElementById('detail-plan').innerText = step.plan || "N/A";
            document.getElementById('detail-analysis').innerText = step.analysis || "N/A";
            document.getElementById('detail-full-code').innerText = step.code || "";
            document.getElementById('diff-left').innerHTML = step.diff_html?.left || "";
            document.getElementById('diff-right').innerHTML = step.diff_html?.right || "";
            switchTab('detail');
        }

        function initBranchList() {
            const counts = {};
            stepsData.forEach(s => { if(s.parent_id && s.parent_id !== 'SUPER_ROOT') counts[s.parent_id] = (counts[s.parent_id]||0)+1; });
            const branches = stepsData.filter(s => counts[s.id] > 1).sort((a,b) => a.step - b.step);
            const list = document.getElementById('branch-list');
            branches.forEach(s => {
                const el = document.createElement('div');
                el.style.cssText = "padding:15px; border-bottom:1px solid var(--border); cursor:pointer;";
                el.innerHTML = "<strong>Step " + s.step + "</strong> <span style='color:#888; font-size:11px;'>(" + counts[s.id] + " paths)</span>";
                el.onclick = () => {
                    document.querySelectorAll('#branch-list div').forEach(i => i.style.background = "transparent");
                    el.style.background = "#37373d";
                    showBranchDetail(s.id);
                };
                list.appendChild(el);
            });
        }

        function showBranchDetail(pid) {
            const cont = document.getElementById('branch-detail');
            const step = treeMap[pid];
            let html = "<h2>Branch Analysis for Step " + step.step + "</h2>";
            let found = false;

            const draw = (dataMap, title, color) => {
                if (!dataMap[pid]) return "";
                found = true;
                let h = "<div class='section'><h3>" + title + "</h3>";
                dataMap[pid].forEach((g, i) => {
                    const badges = g.map(id => "<span class='badge-id'>Step " + (treeMap[id]?.step || id) + "</span>").join("");
                    h += "<div class='red-group' style='border-left-color:" + color + "'><strong>Group " + (i+1) + ":</strong> " + badges + "</div>";
                });
                return h + "</div>";
            };

            html += draw(planRedData, "Plan Redundancy", "#d97706");
            html += draw(codeRedData, "Code Logic Redundancy", "#dc2626");
            if (!found) html += "<p>No redundancy found.</p>";
            cont.innerHTML = html;
        }

        function initResizer() {
            const sidebar = document.getElementById('sidebar');
            const handle = document.getElementById('drag-handle');
            let isResizing = false;

            handle.addEventListener('mousedown', (e) => {
                isResizing = true;
                handle.classList.add('active');
                document.body.style.cursor = 'col-resize';
                e.preventDefault();
            });

            document.addEventListener('mousemove', (e) => {
                if (!isResizing) return;
                const newWidth = e.clientX;
                if (newWidth > 200 && newWidth < 800) {
                    sidebar.style.width = newWidth + 'px';
                }
            });

            document.addEventListener('mouseup', () => {
                if (isResizing) {
                    isResizing = false;
                    handle.classList.remove('active');
                    document.body.style.cursor = 'default';
                }
            });
        }

        window.onload = () => { 
            try {
                console.log('Dashboard initialization starting...');
                console.log('D3 available:', typeof d3 !== 'undefined');
                console.log('Chart available:', typeof Chart !== 'undefined');
                console.log('stepsData loaded:', stepsData ? stepsData.length + ' nodes' : 'NOT LOADED');
                
                initD3();
                console.log('✅ initD3() completed');
                
                initStats();
                console.log('✅ initStats() completed');
                
                initBranchList();
                console.log('✅ initBranchList() completed');
                
                initResizer();
                console.log('✅ initResizer() completed');
                
                console.log('✅ Dashboard fully initialized!');
            } catch(e) {
                console.error('❌ Dashboard initialization failed:', e);
                console.error('Stack:', e.stack);
                document.body.innerHTML += '<div style="position:fixed; top:10px; left:10px; background:#f48771; color:white; padding:20px; border-radius:4px; z-index:9999; max-width:500px;"><strong>Error:</strong> ' + e.message + '<br><pre style="margin:10px 0; font-size:11px;">' + e.stack + '</pre></div>';
            }
        };
    </script>
</body></html>"""

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f: 
        f.write(full_html)
        
    print(f"✅ Dashboard generated: {OUTPUT_FILE}")

if __name__ == "__main__": main()

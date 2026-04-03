#!/usr/bin/env python3
"""
Generate hyper_dashboard.html - a master dashboard linking to all visualization files.
Scans runs/ directory for journal_viz_tree_dashboard.html files and creates an index.

Usage:
    python generate_hyper_dashboard.py
    
Output:
    Creates ../runs/hyper_dashboard.html
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime

def load_metrics_goal():
    """Load competition -> goal ('maximize'/'minimize') from metrics.csv."""
    goal = {}
    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir / 'metrics.csv'
    if csv_path.exists():
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('competition_name', '').strip()
                g = row.get('goal', '').strip().lower()
                if name and g in ('maximize', 'minimize'):
                    goal[name] = g
    return goal

def find_visualization_files(runs_dir):
    """Find all journal_viz_tree_dashboard.html files under runs_dir."""
    results = []
    
    for root, dirs, files in os.walk(runs_dir):
        if 'journal_viz_tree_dashboard.html' in files:
            viz_path = os.path.join(root, 'journal_viz_tree_dashboard.html')
            rel_path = os.path.relpath(viz_path, runs_dir)
            
            # Extract run info from path structure
            parts = rel_path.split(os.sep)
            if len(parts) >= 3:
                date_run = parts[0]  # e.g., 2026-02-03T06-58-07-GMT_run-group_aide
                competition_id = parts[1]  # e.g., competition_abc123
                
                results.append({
                    'rel_path': rel_path,
                    'date_run': date_run,
                    'competition_id': competition_id,
                    'abs_path': viz_path
                })
    
    return sorted(results, key=lambda x: x['date_run'], reverse=True)

def generate_html(viz_files):
    """Generate HTML dashboard with links to all visualizations."""
    metrics_goal = load_metrics_goal()
    
    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
{head_section()}
<body>
    <div class=\"container\">
        {header_section(viz_files)}
        <div style=\"display:flex; align-items:center; gap:20px; margin-bottom:20px;\">
            <button id=\"compareBtn\" style=\"padding:10px 24px; font-size:1em; border-radius:8px; background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;font-weight:600;cursor:pointer;opacity:0.5;pointer-events:none;\">Compare Selected Runs</button>
            <span id=\"compareHint\" style=\"color:#888;font-size:0.95em;\">Select two runs to compare</span>
              <button id=\"clearSelectionBtn\" style=\"padding:8px 18px; font-size:0.95em; border-radius:8px; background:linear-gradient(135deg,#f5a623 0%,#f76b1c 100%);color:white;border:none;font-weight:600;cursor:pointer;\">Clear Selection</button>
        </div>
        {cards_grid_section(viz_files)}
        {empty_state_section()}
            {compare_modal_section()}
    </div>
    {footer_section()}
    {script_section(metrics_goal)}
</body>
</html>
"""
    return html
def compare_modal_section():
    return '''
    <div id="compareModal" style="display:none;position:fixed;z-index:10000;left:0;top:0;width:100vw;height:100vh;background:rgba(40,40,60,0.75);align-items:center;justify-content:center;overflow:auto;">
        <div style="background:white;max-width:1200px;width:96vw;min-width:320px;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,0.25);padding:32px 24px 24px 24px;position:relative;animation:fadeIn 0.2s;max-height:90vh;overflow:auto;">
            <button onclick="document.getElementById('compareModal').style.display='none';" style="position:absolute;top:18px;right:18px;background:none;border:none;font-size:2em;color:#888;cursor:pointer;">&times;</button>
            <div id="compareContent" style="max-height:75vh;overflow:auto;"></div>
        </div>
    </div>
    <style>
        #compareModal { display:none; align-items:center; justify-content:center; }
        #compareModal[style*='display: flex'] { display:flex !important; }
        @keyframes fadeIn { from { opacity:0; transform:scale(0.98);} to { opacity:1; transform:scale(1);} }
        #compareContent pre { background:#f8f8f8; border-radius:8px; padding:12px; }
        #compareContent table { width:100%; border-collapse:separate; border-spacing:18px 12px; }
        #compareContent th, #compareContent td { text-align:left; vertical-align:top; }
        #compareContent th { font-size:1.1em; }
    </style>
    '''

# --- Modular HTML Section Functions ---
def head_section():
    return """
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>MLE Bench Visualization Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        header { background: white; padding: 40px; border-radius: 12px; margin-bottom: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 10px; font-size: 2.5em; }
        .subtitle { color: #666; font-size: 1.1em; margin-bottom: 20px; }
        .stats { display: flex; gap: 30px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }
        .stat { display: flex; flex-direction: column; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { font-size: 0.9em; color: #999; text-transform: uppercase; letter-spacing: 1px; }
        .search-bar { margin-top: 20px; }
        input[type=\"text\"] { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 1em; transition: border-color 0.3s; }
        input[type=\"text\"]:focus { outline: none; border-color: #667eea; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); transition: transform 0.3s, box-shadow 0.3s; cursor: pointer; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0,0,0,0.15); }
        .card-date { font-size: 0.85em; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
        .card-title { font-size: 1.3em; font-weight: 600; color: #333; margin-bottom: 16px; word-break: break-word; }
        .card-link { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; transition: transform 0.3s; font-weight: 600; }
        .card-link:hover { transform: scale(1.05); }
        .card-path { font-size: 0.8em; color: #999; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; word-break: break-all; }
        .empty-state { text-align: center; padding: 60px 20px; background: white; border-radius: 12px; }
        .empty-state h2 { color: #999; margin-bottom: 10px; }
        .empty-state p { color: #bbb; }
        .hidden { display: none; }
        footer { text-align: center; color: white; padding: 20px; margin-top: 40px; font-size: 0.9em; }
    </style>
</head>
"""

def header_section(viz_files):
    return f"""
<header>
    <h1>📊 MLE Bench Visualization Dashboard</h1>
    <p class=\"subtitle\">Browse all generated competition visualizations</p>
    {stats_section(viz_files)}
    {search_bar_section()}
</header>
"""

def stats_section(viz_files):
    return f"""
    <div class=\"stats\">
        <div class=\"stat\">
            <span class=\"stat-number\">{len(viz_files)}</span>
            <span class=\"stat-label\">Visualizations</span>
        </div>
        <div class=\"stat\">
            <span class=\"stat-number\">{len(set(v['date_run'] for v in viz_files))}</span>
            <span class=\"stat-label\">Run Dates</span>
        </div>
    </div>
"""

def search_bar_section():
    return """
    <div class=\"search-bar\">
        <input 
            type=\"text\" 
            id=\"searchInput\" 
            placeholder=\"🔍 Search by competition name or date...\"
            onkeyup=\"filterCards()\"
        />
    </div>
"""

def cards_grid_section(viz_files):
    return f"""
    <div id=\"cardsContainer\" class=\"grid\">
        {''.join(generate_card_html(v) for v in viz_files)}
    </div>
"""

def empty_state_section():
    return """
    <div id=\"emptyState\" class=\"empty-state hidden\">
        <h2>No visualizations found</h2>
        <p>Try adjusting your search filter</p>
    </div>
"""

def footer_section():
    return f"""
    <footer>
        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • MLE Bench Visualization Suite
    </footer>
"""

def script_section(metrics_goal):
    metrics_goal_js = json.dumps(metrics_goal)
    return f"""
    <script>
        const METRICS_GOAL = {metrics_goal_js};
    </script>""" + r"""
    <script>
        // Ensure all cards have a compare-checkbox input (for static HTML)
        window.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.card').forEach(card => {
                // Remove any existing checkboxes to avoid duplicates
                card.querySelectorAll('.compare-checkbox').forEach(cb => cb.remove());
                // Insert a single checkbox as the first child
                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.className = 'compare-checkbox';
                cb.style = 'position:absolute;top:18px;right:18px;transform:scale(1.4);z-index:2;';
                cb.onclick = handleCheckbox;
                card.style.position = 'relative';
                card.insertBefore(cb, card.firstChild);
            });
            updateCompareBtn(); // Ensure button state is correct on first load
        });
        // --- Comparison Logic ---
        let selectedCards = [];
        function handleCheckbox(e) {
            const card = e.target.closest('.card');
            if (e.target.checked) {
                if (selectedCards.length < 2) {
                    selectedCards.push(card);
                } else {
                    e.target.checked = false;
                    return;
                }
            } else {
                selectedCards = selectedCards.filter(c => c !== card);
            }
            updateCompareBtn();
        }
        function updateCompareBtn() {
            const btn = document.getElementById('compareBtn');
            const clearBtn = document.getElementById('clearSelectionBtn');
            if (selectedCards.length === 2) {
                btn.style.opacity = 1;
                btn.style.pointerEvents = 'auto';
                document.getElementById('compareHint').textContent = 'Ready to compare!';
            } else {
                btn.style.opacity = 0.5;
                btn.style.pointerEvents = 'none';
                document.getElementById('compareHint').textContent = 'Select two runs to compare';
            }
            // Update clear selection button state
            if (clearBtn) {
                if (selectedCards.length === 0) {
                    clearBtn.style.opacity = 0.5;
                    clearBtn.style.pointerEvents = 'none';
                    clearBtn.style.background = 'linear-gradient(135deg,#eee 0%,#ccc 100%)';
                    clearBtn.style.color = '#888';
                } else {
                    clearBtn.style.opacity = 1;
                    clearBtn.style.pointerEvents = 'auto';
                    clearBtn.style.background = 'linear-gradient(135deg,#f5a623 0%,#f76b1c 100%)';
                    clearBtn.style.color = 'white';
                }
            }
        }
        document.getElementById('compareBtn').onclick = async function() {
            if (selectedCards.length !== 2) return;
            const [card1, card2] = selectedCards;
            const info1 = extractRunInfo(card1);
            const info2 = extractRunInfo(card2);
            // Fetch general info and code for both runs
            const [details1, details2] = await Promise.all([
                fetchRunDetails(info1),
                fetchRunDetails(info2)
            ]);
            showCompareModal(info1, details1, info2, details2);
        };
        function extractRunInfo(card) {
            return {
                date: card.querySelector('.card-date').textContent,
                title: card.querySelector('.card-title').textContent,
                path: card.querySelector('.card-path').textContent,
            };
        }
        async function fetchRunDetails(info) {
            let gen = '';
            let code = '';
            let displayedStep = 'N/A';
            try {
                // Compute the JSON path from the HTML path
                let jsonPath = info.path.replace('journal_viz_tree_dashboard.html', 'journal_with_judgements.json');
                jsonPath = jsonPath.replace(/^\/+/, '');
                if (!jsonPath.startsWith('.') && !jsonPath.startsWith('/')) {
                    jsonPath = './' + jsonPath;
                }
                // Log the fetch path for debugging
                console.log('Fetching JSON:', jsonPath);
                const resp = await fetch(jsonPath);
                if (!resp.ok) throw new Error('Fetch failed: ' + jsonPath + ' (status ' + resp.status + ')');
                const data = await resp.json();
                // Log the actual JSON data for debugging
                console.log('Fetched JSON data:', data);
                // If the JSON is an array, treat it as steps
                const steps = Array.isArray(data) ? data.filter(s => s && s.id !== 'SUPER_ROOT') : [];
                const valid = steps.filter(s => s && s.is_buggy === false).length;
                const buggy = steps.filter(s => s && s.is_buggy === true).length;
                const total = steps.length;
                // Extract metric from s.metric.value if present and numeric
                const metricSteps = steps.filter(s => s && s.metric && typeof s.metric.value === 'number');
                const metricsOnly = metricSteps.map(s => s.metric.value);
                // Determine maximize/minimize: use metrics.csv lookup first, fall back to JSON field
                const compName = info.title.split('_')[0];
                let maximize = true;
                if (typeof METRICS_GOAL !== 'undefined' && METRICS_GOAL.hasOwnProperty(compName)) {
                    maximize = METRICS_GOAL[compName] === 'maximize';
                } else {
                    for (let s of metricSteps) {
                        if (typeof s.metric.maximize === 'boolean') {
                            maximize = s.metric.maximize;
                            break;
                        }
                    }
                }
                let best = 'N/A';
                if (metricsOnly.length > 0) {
                    best = maximize ? Math.max(...metricsOnly) : Math.min(...metricsOnly);
                }
                function getMetricValue(step) {
                    return step && step.metric && typeof step.metric.value === 'number' ? step.metric.value : null;
                }
                let stats = `<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px;'>` +
                    `<div class=\"section stat-card\"><div class=\"stat-val\">${total}</div><div style=\"color:#888; font-size:11px\">Total Steps</div></div>` +
                    `<div class=\"section stat-card\"><div class=\"stat-val\" style=\"color:var(--valid)\">${valid}</div><div style=\"color:#888; font-size:11px\">Valid</div></div>` +
                    `<div class=\"section stat-card\"><div class=\"stat-val\" style=\"color:var(--buggy)\">${buggy}</div><div style=\"color:#888; font-size:11px\">Buggy</div></div>` +
                    `<div class=\"section stat-card\"><div class=\"stat-val\">${best}</div><div style=\"color:#888; font-size:11px\">Best Result</div></div>` +
                    `</div>`;
                // Find best step by metric, fallback to first step if none
                let bestStep = null;
                if (steps.length > 0) {
                    if (metricsOnly.length > 0) {
                        bestStep = metricSteps.reduce((currentBest, step) => {
                            if (!currentBest) return step;
                            const currentValue = getMetricValue(currentBest);
                            const nextValue = getMetricValue(step);
                            if (currentValue === null) return step;
                            if (nextValue === null) return currentBest;
                            return maximize
                                ? (nextValue > currentValue ? step : currentBest)
                                : (nextValue < currentValue ? step : currentBest);
                        }, null);
                    } else {
                        bestStep = steps[0];
                    }
                }
                if (bestStep) {
                    if (bestStep.step !== undefined && bestStep.step !== null) {
                        displayedStep = `Step ${bestStep.step}`;
                    } else if (bestStep.id) {
                        displayedStep = `Node ${bestStep.id}`;
                    }
                }
                let plan = (bestStep && typeof bestStep.plan === 'string' && bestStep.plan.trim()) ? bestStep.plan : 'N/A';
                let analysis = (bestStep && typeof bestStep.analysis === 'string' && bestStep.analysis.trim()) ? bestStep.analysis : 'N/A';
                let desc = (bestStep && typeof bestStep.description === 'string') ? bestStep.description : '';
                code = (bestStep && typeof bestStep.code === 'string' && bestStep.code.trim()) ? bestStep.code : '<em style=\"color:#c00\">No code found in JSON.</em>';
                // Warn if expected fields are missing or empty
                let warnings = '';
                if (!Array.isArray(data)) warnings += '<div style="color:#c00">Warning: JSON is not an array of steps.</div>';
                if (!plan || plan === 'N/A') warnings += '<div style="color:#c00">Warning: plan missing.</div>';
                if (!analysis || analysis === 'N/A') warnings += '<div style="color:#c00">Warning: analysis missing.</div>';
                if (!code || code.includes('No code found')) warnings += '<div style="color:#c00">Warning: code missing.</div>';
                gen = warnings + `<div>${stats}</div><div style='margin-top:12px;'><strong>Plan:</strong> <pre style='background:#f8f8f8;padding:8px;border-radius:6px;max-height:320px;overflow:auto;white-space:pre-wrap;'>${plan}</pre></div><div style='margin-top:12px;'><strong>Analysis:</strong> <pre style='background:#f8f8f8;padding:8px;border-radius:6px;max-height:320px;overflow:auto;white-space:pre-wrap;'>${analysis}</pre></div><div style='margin-top:12px;'>${desc}</div>`;
            } catch(e) {
                gen = `<em style=\"color:#c00\">Failed to load general info.<br>Path: ${typeof jsonPath !== 'undefined' ? jsonPath : ''}<br>Error: ${e.message}</em>`;
                code = `<em style=\"color:#c00\">Failed to load code.<br>Path: ${typeof jsonPath !== 'undefined' ? jsonPath : ''}<br>Error: ${e.message}</em>`;
                // Also log error to console for debugging
                console.error('Error fetching or parsing JSON:', e, jsonPath);
            }
            return { gen, code, displayedStep };
        }
        function showCompareModal(info1, details1, info2, details2) {
            const modal = document.getElementById('compareModal');
            const content = document.getElementById('compareContent');
            const { gen: gen1, code: code1, displayedStep: displayedStep1 } = details1;
            const { gen: gen2, code: code2, displayedStep: displayedStep2 } = details2;
            // Helper to extract sections robustly
            function extractSection(gen, label, fallback='') {
                const regex = new RegExp(`<strong>${label}:<\\/strong> <pre.*?>([\\s\\S]*?)<\\/pre>`, 'i');
                const m = gen.match(regex);
                return m ? m[1] : fallback;
            }
            function extractStats(html) {
                // Try to extract the statistics grid from the generated HTML (robust to style attribute order)
                const gridMatch = html.match(/<div[^>]*class=["']section stat-card["'][^>]*>[\s\S]*?<\/div>[\s\S]*?<div[^>]*class=["']section stat-card["'][^>]*>[\s\S]*?<\/div>[\s\S]*?<div[^>]*class=["']section stat-card["'][^>]*>[\s\S]*?<\/div>[\s\S]*?<div[^>]*class=["']section stat-card["'][^>]*>[\s\S]*?<\/div>/);
                if (gridMatch) {
                    // Extract all four stat-card divs
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = gridMatch[0];
                    const cards = tempDiv.querySelectorAll('.stat-card');
                    const labels = ['Total Steps', 'Valid', 'Buggy', 'Best Result'];
                    let out = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px;">';
                    for (let i = 0; i < 4; ++i) {
                        if (cards[i]) {
                            const value = cards[i].querySelector('.stat-val')?.textContent || '';
                            out += `<div class="section stat-card"><div class="stat-val">${value}</div><div style="color:#888; font-size:11px">${labels[i]}</div></div>`;
                        } else {
                            out += `<div class="section stat-card"><div class="stat-val">N/A</div><div style="color:#888; font-size:11px">${labels[i]}</div></div>`;
                        }
                    }
                    out += '</div>';
                    return out;
                }
                return '<span style="color:#888">N/A</span>';
            }
            content.innerHTML = `
                <table style="width:100%;border-collapse:separate;border-spacing:18px 12px;table-layout:fixed;">
                    <colgroup>
                        <col style="width:200px;">
                        <col style="width:1fr;min-width:340px;">
                        <col style="width:1fr;min-width:340px;">
                    </colgroup>
                    <thead>
                        <tr>
                            <th></th>
                            <th style="text-align:center;font-weight:bold;font-size:1.1em;padding:8px 0 8px 0;border-bottom:2px solid #eee;border-right:8px solid transparent;">${info1.title} <span style='color:#888;font-size:0.9em;'>(${info1.date})</span></th>
                            <th style="text-align:center;font-weight:bold;font-size:1.1em;padding:8px 0 8px 0;border-bottom:2px solid #eee;">${info2.title} <span style='color:#888;font-size:0.9em;'>(${info2.date})</span></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="font-weight:bold;padding:12px 8px 0 0;vertical-align:top;">Global Statistics</td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;border-right:8px solid transparent;">${extractStats(gen1)}</td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;">${extractStats(gen2)}</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;padding:12px 8px 0 0;vertical-align:top;">Displayed Step</td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;border-right:8px solid transparent;">
                                <div style='background:#f8f8f8;border-radius:8px;padding:16px;font-weight:600;'>${escapeHtml(displayedStep1)}</div>
                            </td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;">
                                <div style='background:#f8f8f8;border-radius:8px;padding:16px;font-weight:600;'>${escapeHtml(displayedStep2)}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;padding:12px 8px 0 0;vertical-align:top;">Plan</td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;border-right:8px solid transparent;">
                                <div style='background:#f8f8f8;border-radius:8px;padding:16px;max-height:320px;overflow:auto;white-space:pre-wrap;'>${extractSection(gen1, 'Plan', 'N/A')}</div>
                            </td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;">
                                <div style='background:#f8f8f8;border-radius:8px;padding:16px;max-height:320px;overflow:auto;white-space:pre-wrap;'>${extractSection(gen2, 'Plan', 'N/A')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;padding:12px 8px 0 0;vertical-align:top;">Analysis</td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;border-right:8px solid transparent;">
                                <div style='background:#f8f8f8;border-radius:8px;padding:16px;max-height:320px;overflow:auto;white-space:pre-wrap;'>${extractSection(gen1, 'Analysis', 'N/A')}</div>
                            </td>
                            <td style="padding:8px 0 8px 0;vertical-align:top;">
                                <div style='background:#f8f8f8;border-radius:8px;padding:16px;max-height:320px;overflow:auto;white-space:pre-wrap;'>${extractSection(gen2, 'Analysis', 'N/A')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;padding:12px 8px 0 0;vertical-align:top;">Best Solution Code</td>
                            <td style="vertical-align:top;border-right:8px solid transparent;">
                                <pre style='background:#222;color:#eee;padding:24px;border-radius:8px;max-height:700px;overflow:auto;font-size:12px;'>${escapeHtml(code1)}</pre>
                            </td>
                            <td style="vertical-align:top;">
                                <pre style='background:#222;color:#eee;padding:24px;border-radius:8px;max-height:700px;overflow:auto;font-size:12px;'>${escapeHtml(code2)}</pre>
                            </td>
                        </tr>
                    </tbody>
                </table>
            `;
            modal.style.display = 'flex';
        }
        function closeCompareModal() {
            document.getElementById('compareModal').style.display = 'none';
        }
        function escapeHtml(text) {
            if (!text) return '';
            return text.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
        }
        // Deselect checkboxes and clear selection when modal closes
        document.getElementById('compareModal').addEventListener('click', function(e) {
            if (e.target === this) closeCompareModal();
        });
        function clearCompareSelection() {
            selectedCards.forEach(card => {
                const cb = card.querySelector('.compare-checkbox');
                if (cb) cb.checked = false;
            });
            selectedCards = [];
            updateCompareBtn();
        }
        window.addEventListener('DOMContentLoaded', function() {
            const clearBtn = document.getElementById('clearSelectionBtn');
            if (clearBtn) {
                clearBtn.onclick = function() {
                    clearCompareSelection();
                };
            }
        });
        function closeCompareModal() {
            document.getElementById('compareModal').style.display = 'none';
            clearCompareSelection();
        }
        function filterCards() {
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.card');
            let visibleCount = 0;
            
            cards.forEach(card => {
                // Hide checkboxes if card is hidden
                const cb = card.querySelector('.compare-checkbox');
                if (cb) cb.style.display = card.classList.contains('hidden') ? 'none' : 'block';
                const text = card.textContent.toLowerCase();
                if (text.includes(searchInput)) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });
            
            // Show empty state if no cards visible
            const emptyState = document.getElementById('emptyState');
            if (visibleCount === 0) {
                emptyState.classList.remove('hidden');
            } else {
                emptyState.classList.add('hidden');
            }
        }
    </script>
"""

def generate_card_html(viz_file):
    """Generate a card HTML for a single visualization file."""
    
    # Parse date for display
    date_str = viz_file['date_run'].split('T')[0] if 'T' in viz_file['date_run'] else viz_file['date_run']
    
    return f"""<div class=\"card\" style=\"position:relative;\">
        <input type=\"checkbox\" class=\"compare-checkbox\" style=\"position:absolute;top:16px;right:16px;transform:scale(1.4);z-index:2;\" onclick=\"event.stopPropagation();\">
        <div class=\"card-date\">{date_str}</div>
        <div class=\"card-title\">{viz_file['competition_id']}</div>
        <a href=\"{viz_file['rel_path'].replace(os.sep, '/')}\" class=\"card-link\" target=\"_blank\">View Visualization →</a>
        <div class=\"card-path\">{viz_file['rel_path']}</div>
    </div>
"""

def main():
    # Determine paths
    script_dir = Path(__file__).resolve().parent
    runs_dir = script_dir.parent / "runs"
    output_file = runs_dir / "hyper_dashboard.html"
    
    if not runs_dir.exists():
        print(f"✗ Runs directory not found: {runs_dir}")
        return False
    
    print(f"Scanning {runs_dir} for visualization files...")
    
    # Find all visualization files
    viz_files = find_visualization_files(str(runs_dir))
    
    if not viz_files:
        print(f"✗ No visualization files found under {runs_dir}")
        return False
    
    print(f"Found {len(viz_files)} visualization files")
    
    # Generate HTML
    html_content = generate_html(viz_files)
    
    # Write to output file
    try:
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"✓ Dashboard generated: {output_file}")
        print(f"  Open in browser: file://{output_file}")
        return True
    except Exception as e:
        print(f"✗ Error writing dashboard: {e}")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)

#!/usr/bin/env python3
"""
Dynamic HTTP server for hyper_dashboard.html
Generates the dashboard on-the-fly by scanning runs/ directory on each request.
No need to re-run Python script - just refresh the browser!

Usage:
    python serve_hyper_dashboard.py
    
Then open: http://localhost:8000/hyper_dashboard.html
"""

import os
import http.server
import socketserver
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

PORT = 8000

class DashboardHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves dynamic dashboard."""
    
    def do_GET(self):
        """Handle GET requests."""
        
        # If requesting the dashboard, generate it dynamically
        if self.path == '/hyper_dashboard.html' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            
            # Get the runs directory (parent of parent of this script)
            script_dir = Path(__file__).resolve().parent
            runs_dir = script_dir.parent / "runs"
            
            # Generate dashboard HTML dynamically
            html_content = self.generate_dashboard(runs_dir)
            self.wfile.write(html_content.encode('utf-8'))
            return
        
        # For all other requests, use default handler (serve files)
        super().do_GET()
    
    def generate_dashboard(self, runs_dir):
        """Generate dashboard HTML by scanning runs_dir."""
        
        # Find all visualization files
        viz_files = self.find_visualization_files(runs_dir)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLE Bench Visualization Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        
        .refresh-info {{
            background: #f0f0f0;
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #666;
            border-left: 4px solid #667eea;
        }}
        
        .stats {{
            display: flex;
            gap: 30px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        
        .stat {{
            display: flex;
            flex-direction: column;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .search-bar {{
            margin-top: 20px;
        }}
        
        input[type="text"] {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }}
        
        input[type="text"]:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }}
        
        .card-date {{
            font-size: 0.85em;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}
        
        .card-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
            margin-bottom: 16px;
            word-break: break-word;
        }}
        
        .card-link {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            transition: transform 0.3s;
            font-weight: 600;
        }}
        
        .card-link:hover {{
            transform: scale(1.05);
        }}
        
        .card-path {{
            font-size: 0.8em;
            color: #999;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #f0f0f0;
            word-break: break-all;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 12px;
        }}
        
        .empty-state h2 {{
            color: #999;
            margin-bottom: 10px;
        }}
        
        .empty-state p {{
            color: #bbb;
        }}
        
        .hidden {{
            display: none;
        }}
        
        footer {{
            text-align: center;
            color: white;
            padding: 20px;
            margin-top: 40px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 MLE Bench Visualization Dashboard</h1>
            <p class="subtitle">Browse all generated competition visualizations</p>
            
            <div class="refresh-info">
                ✨ This dashboard updates automatically when you refresh the page. Create new visualizations and refresh to see them!
            </div>
            
            <div class="stats">
                <div class="stat">
                    <span class="stat-number">{len(viz_files)}</span>
                    <span class="stat-label">Visualizations</span>
                </div>
                <div class="stat">
                    <span class="stat-number">{len(set(v['date_run'] for v in viz_files))}</span>
                    <span class="stat-label">Run Dates</span>
                </div>
            </div>
            
            <div class="search-bar">
                <input 
                    type="text" 
                    id="searchInput" 
                    placeholder="🔍 Search by competition name or date..."
                    onkeyup="filterCards()"
                    autofocus
                />
            </div>
        </header>
        
        <div id="cardsContainer" class="grid">
            {''.join(self.generate_card_html(v) for v in viz_files)}
        </div>
        
        <div id="emptyState" class="empty-state hidden">
            <h2>No visualizations found</h2>
            <p>Run the visualization pipeline first or refresh the page</p>
        </div>
    </div>
    
    <footer>
        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • MLE Bench Dynamic Dashboard Server
    </footer>
    
    <script>
        function filterCards() {{
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.card');
            let visibleCount = 0;
            
            cards.forEach(card => {{
                const text = card.textContent.toLowerCase();
                if (text.includes(searchInput)) {{
                    card.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    card.classList.add('hidden');
                }}
            }});
            
            // Show empty state if no cards visible
            const emptyState = document.getElementById('emptyState');
            if (visibleCount === 0) {{
                emptyState.classList.remove('hidden');
            }} else {{
                emptyState.classList.add('hidden');
            }}
        }}
    </script>
</body>
</html>
"""
        
        return html
    
    def find_visualization_files(self, runs_dir):
        """Find all journal_viz_tree_dashboard.html files under runs_dir."""
        results = []
        
        try:
            for root, dirs, files in os.walk(runs_dir):
                if 'journal_viz_tree_dashboard.html' in files:
                    viz_path = os.path.join(root, 'journal_viz_tree_dashboard.html')
                    rel_path = os.path.relpath(viz_path, runs_dir)
                    
                    # Extract run info from path structure
                    parts = rel_path.split(os.sep)
                    if len(parts) >= 3:
                        date_run = parts[0]
                        competition_id = parts[1]
                        
                        results.append({
                            'rel_path': rel_path,
                            'date_run': date_run,
                            'competition_id': competition_id,
                            'abs_path': viz_path
                        })
        except Exception as e:
            print(f"Error scanning directory: {e}")
        
        return sorted(results, key=lambda x: x['date_run'], reverse=True)
    
    def generate_card_html(self, viz_file):
        """Generate a card HTML for a single visualization file."""
        
        # Parse date for display
        date_str = viz_file['date_run'].split('T')[0] if 'T' in viz_file['date_run'] else viz_file['date_run']
        
        # Use relative path for links
        rel_path = viz_file['rel_path'].replace(os.sep, '/')
        
        return f"""        <div class="card">
            <div class="card-date">{date_str}</div>
            <div class="card-title">{viz_file['competition_id']}</div>
            <a href="{rel_path}" class="card-link" target="_blank">
                View Visualization →
            </a>
            <div class="card-path">{rel_path}</div>
        </div>
"""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

def main():
    script_dir = Path(__file__).resolve().parent
    runs_dir = script_dir.parent / "runs"
    
    # Change to runs directory so relative links work
    os.chdir(runs_dir)
    
    print(f"\n{'='*60}")
    print(f"  MLE Bench Dynamic Dashboard Server")
    print(f"{'='*60}")
    print(f"\n  📍 Serving from: {runs_dir}")
    print(f"\n  🌐 Open your browser and go to:")
    print(f"     http://localhost:{PORT}/hyper_dashboard.html")
    print(f"\n  💡 Just refresh the page to see new visualizations!")
    print(f"  ❌ Press Ctrl+C to stop the server")
    print(f"\n{'='*60}\n")
    
    try:
        with socketserver.TCPServer(("", PORT), DashboardHTTPHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped.")
    except OSError as e:
        print(f"\n✗ Error: {e}")
        if e.errno == 48:
            print(f"   Port {PORT} is already in use. Try a different port.")

if __name__ == "__main__":
    main()

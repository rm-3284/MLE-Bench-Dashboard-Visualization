import sys
sys.path.insert(0, '.')
from run_visualization_pipeline import parse_journal_path, load_metrics_from_csv

real_path = '/Users/ryomitsuhashi/Desktop/Princeton/Research/MLE bench/mle-bench-fork/runs/2025-12-17T20-27-55-GMT_run-group_aide/tensorflow2-question-answering_a3cf875b-2303-466b-bd8d-5a2820cd34b3/logs/journal.json'

print('Testing with real path from workspace:')
comp, run_id, wd, jf = parse_journal_path(real_path)
print(f'Competition: {comp}')
print(f'Run ID: {run_id}')

metrics = load_metrics_from_csv(comp, 'metrics.csv')
if metrics:
    print(f'Metrics: {metrics["metric_name"]} ({metrics["goal"]})')
    print(f'Ignore buggy: {metrics["ignore_buggy_without_metric"]}')
    print(f'Default buggy: {metrics["default_buggy_metric"]}')

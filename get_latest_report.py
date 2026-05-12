import json
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_FILE = os.path.join(BASE_DIR, "data", "ai_reports.json")
with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
    reports = json.load(f)
if reports:
    latest = reports[-1]
    print(latest.get('text', ''))
else:
    print('No reports')
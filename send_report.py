import json
import os
import sys
sys.path.insert(0, '/home/alex/wb_ai_system_dist')
import app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, 'config', 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Get latest report
reports_path = os.path.join(BASE_DIR, 'data', 'ai_reports.json')
with open(reports_path, 'r', encoding='utf-8') as f:
    reports = json.load(f)
if not reports:
    print('No reports found')
    sys.exit(1)
latest_report = reports[-1]['text']

# Send to Telegram if credentials exist
tg_config = config.get('telegram', {})
bot_token = tg_config.get('bot_token')
chat_id = tg_config.get('chat_id')
if bot_token and chat_id and bot_token != 'ВАШ_ТОКЕН_ОТ_BOTFATHER' and chat_id != 'ВАШ_CHAT_ID_ОТ_USERINFOBOT':
    # Use the function from app
    success = app.send_telegram_report(bot_token, chat_id, latest_report)
    if not success:
        print('Warning: Failed to send Telegram message', file=sys.stderr)
else:
    print('Info: Telegram credentials not configured or are placeholders; not sending.', file=sys.stderr)

# Output the report as final response
print(latest_report)
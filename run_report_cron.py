#!/usr/bin/env python3
import sys
import os
import json

# Add the project directory to the path
sys.path.insert(0, '/home/alex/wb_ai_system_dist')

try:
    # Import required functions from app.py
    from app import load_data, generate_ai_report, send_telegram_report
    
    print("Starting Wildberries report generation...")
    
    # Step 1: Load data from Google Sheets
    print("Loading data from Google Sheets...")
    data = load_data()
    print(f"Data loaded successfully. Shape: {data.shape if hasattr(data, 'shape') else 'N/A'}")
    
    # Step 2: Generate AI report
    print("Generating AI report...")
    report = generate_ai_report(data)
    print(f"Report generated. Length: {len(report)} characters")
    print(f"Report preview: {report[:200]}...")
    
    # Step 3: Load config and Send to Telegram
    print("Loading Telegram config...")
    config_path = os.path.join('/home/alex/wb_ai_system_dist', "config", "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    bot_token = config.get('telegram', {}).get('bot_token')
    chat_id = config.get('telegram', {}).get('chat_id')
    
    if not bot_token or 'ВАШ_ТОКЕН' in bot_token:
        print("WARNING: Telegram bot_token not configured in config.json!")
        print("Report generated but NOT sent to Telegram.")
        print(f"Report content:\n{report}")
    else:
        print(f"Sending report to Telegram (chat_id: {chat_id})...")
        send_telegram_report(bot_token, chat_id, report)
        print("Report sent successfully to Telegram!")
    
except ImportError as e:
    print(f"ERROR: Failed to import functions from app.py: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: An error occurred during report generation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

#!/usr/bin/env python3
"""
Скрипт для ежедневной отправки отчета WB в Telegram.
Запускать через планировщик (cron/Task Scheduler) раз в сутки.
"""
import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")
REPORTS_FILE = os.path.join(BASE_DIR, "data", "ai_reports.json")

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки конфига: {e}")
        return None

def load_data(config):
    """Загрузка данных из Google Sheets или CSV"""
    if config.get('google_sheets', {}).get('enabled', False):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            gs_config = config.get('google_sheets', {})
            key_file = gs_config.get('key_file', gs_config.get('cred_file', 'config/bubble-key.json'))
            key_file = os.path.join(BASE_DIR, key_file)
            
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(key_file, scopes=scope)
            client = gspread.authorize(creds)
            
            sheet_id = gs_config.get('sheet_id', '')
            worksheet_name = gs_config.get('worksheet_name', 'Sheet1')
            
            if '/' in sheet_id or len(sheet_id) > 30:
                sheet = client.open_by_key(sheet_id)
            else:
                sheet = client.open(sheet_id)
            
            worksheet = sheet.worksheet(worksheet_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Ошибка Google Sheets: {e}")
    
    # CSV fallback
    csv_path = os.path.join(BASE_DIR, "data", "wb_test_data.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df
    
    return None

def generate_simple_report(df):
    """Простой отчет без AI (для случая, если AI недоступен)"""
    if df is None or len(df) == 0:
        return "Нет данных для отчета"
    
    # Берем последние 2 дня
    if 'date' in df.columns:
        df = df.sort_values('date')
        last_date = df['date'].max()
        prev_date = last_date - pd.Timedelta(days=1)
        
        last_data = df[df['date'] == last_date]
        prev_data = df[df['date'] == prev_date]
        
        report = f"📊 Отчет WB за {last_date.strftime('%Y-%m-%d')}\n\n"
        
        # Основные метрики
        for col in ['orders', 'buyouts', 'ctr', 'cr', 'cpc', 'drr']:
            if col in df.columns:
                last_val = last_data[col].mean() if len(last_data) > 0 else 0
                prev_val = prev_data[col].mean() if len(prev_data) > 0 else 0
                
                if prev_val != 0:
                    delta = ((last_val - prev_val) / prev_val) * 100
                    report += f"{col}: {last_val:.2f} ({delta:+.1f}%)\n"
                else:
                    report += f"{col}: {last_val:.2f}\n"
        
        return report
    return "Ошибка формирования отчета"

def send_telegram_report(token, chat_id, text):
    """Отправка в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get("ok", False)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

def main():
    print(f"[{datetime.now()}] Запуск ежедневной отправки отчета...")
    
    # Загружаем конфиг
    config = load_config()
    if config is None:
        print("Не удалось загрузить конфиг")
        sys.exit(1)
    
    # Проверяем Telegram
    tg_config = config.get('telegram', {})
    if not tg_config.get('enabled', False) or not tg_config.get('bot_token') or not tg_config.get('chat_id'):
        print("Telegram не настроен или не включен")
        sys.exit(1)
    
    # Загружаем данные
    df = load_data(config)
    
    # Генерируем отчет
    report_text = generate_simple_report(df)
    
    # Отправляем
    success = send_telegram_report(tg_config['bot_token'], tg_config['chat_id'], report_text)
    
    if success:
        print("Отчет успешно отправлен в Telegram")
        # Сохраняем в историю
        reports = []
        if os.path.exists(REPORTS_FILE):
            try:
                with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                    reports = json.load(f)
            except:
                reports = []
        
        reports.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": report_text
        })
        
        if len(reports) > 20:
            reports = reports[-20:]
        
        os.makedirs(os.path.dirname(REPORTS_FILE), exist_ok=True)
        with open(REPORTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)
    else:
        print("Ошибка отправки отчета")
        sys.exit(1)

if __name__ == "__main__":
    main()

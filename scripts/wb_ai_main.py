#!/usr/bin/env python3
"""
WB AI System - Автоматический отчёт
"""
import os
import json
import pandas as pd
from datetime import datetime
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)

def load_config():
    config_path = os.path.join(BASE_DIR, "config", "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки config.json: {e}")
        return None

def load_data(config):
    if config.get("google_sheets", {}).get("enabled", False):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            key_file = os.path.join(BASE_DIR, config["google_sheets"]["key_file"])
            scope = ["https://www.googleapis.com/auth/spreadsheets", 
                     "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(key_file, scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open(config["google_sheets"]["sheet_name"]).worksheet(
                config["google_sheets"]["worksheet_name"])
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            return df
        except Exception as e:
            print(f"⚠️ Ошибка Google Sheets: {e}")
    
    csv_path = os.path.join(BASE_DIR, "data", "test_data.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    
    print("❌ Данные не найдены")
    return None

def analyze_data(df):
    if df is None or df.empty:
        return None
    
    metrics = ["orders", "ctr", "cr", "cpc", "drr"]
    available = [m for m in metrics if m in df.columns]
    
    if len(df) < 2:
        return None
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    lines = []
    date_str = last["date"].strftime("%Y-%m-%d") if "date" in last else "сегодня"
    lines.append(f"🤖 WB AI Отчёт за {date_str}")
    lines.append("")
    lines.append("📈 Изменения (день к дню):")
    
    for m in available[:5]:
        if m in last and m in prev and prev[m] != 0:
            pct = (last[m] - prev[m]) / prev[m] * 100
            emoji = "🚀" if pct > 0 else "📉"
            lines.append(f"  {emoji} {m}: {pct:+.1f}% ({prev[m]:.1f} → {last[m]:.1f})")
    
    lines.append("")
    lines.append("⚠️ Аномалии:")
    anomalies = []
    for m in available:
        if m in df.columns:
            series = df[m].dropna()
            if len(series) >= 3:
                zscore = (last[m] - series.mean()) / series.std()
                if abs(zscore) > 2.0:
                    anomalies.append(f"  • {m}: {last[m]:.1f} (z-score {zscore:.1f})")
    
    if anomalies:
        lines.extend(anomalies)
    else:
        lines.append("  ✅ Аномалий не обнаружено")
    
    lines.append("")
    lines.append("💡 Рекомендации:")
    lines.append("  • Проверьте изменения в карточках товаров")
    lines.append("  • Сравните цены с конкурентами")
    lines.append("  • Усильте рекламу для растущих товаров")
    
    return "\n".join(lines)

def send_to_telegram(config, text):
    bot_token = config.get("telegram", {}).get("bot_token", "")
    chat_id = config.get("telegram", {}).get("chat_id", "")
    
    if not bot_token or not chat_id or bot_token.startswith("ВАШ") or chat_id.startswith("ВАШ"):
        print("❌ Telegram не настроен в config.json")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.json().get("ok"):
            print("✅ Отчёт отправлен в Telegram")
            return True
        else:
            print(f"❌ Ошибка Telegram: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

def main():
    print(f"🚀 WB AI Автоотчёт запущен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = load_config()
    if not config:
        return
    
    df = load_data(config)
    if df is None:
        return
    
    report = analyze_data(df)
    if not report:
        print("❌ Не удалось сформировать отчёт")
        return
    
    print("📝 Сформирован отчёт:")
    print(report)
    print()
    
    send_to_telegram(config, report)

if __name__ == "__main__":
    main()

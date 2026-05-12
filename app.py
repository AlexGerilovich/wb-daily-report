import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import json
from datetime import datetime, timedelta
import threading
import time

# ОТЛАДКА: проверка версии файла
st.sidebar.write("Файл обновлен: 2026-05-06 09:40")

# ======================== ЗАГРУЗКА КОНФИГА =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_resource
def load_config():
    config_path = os.path.join(BASE_DIR, "config", "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки config.json: {e}")
        return None

config = load_config()
if config is None:
    st.warning("⚠️ Конфигурация не загружена. Работаем в демо-режиме.")
    config = {
        "google_sheets": {"enabled": False},
        "telegram": {"enabled": False},
        "ai_settings": {"enabled": False}
    }

ANOMALY_ZSCORE = config.get('anomaly_thresholds', {}).get('zscore', 2.0)
ANOMALY_PERCENT = config.get('anomaly_thresholds', {}).get('percent_change', 30)

# ======================== ЗАГРУЗКА ДАННЫХ =======================
@st.cache_data(ttl=300)
def load_data():
    # Google Sheets
    if config.get('google_sheets', {}).get('enabled', False):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            # Получаем путь к ключу (поддержка старых и новых конфигов)
            gs_config = config.get('google_sheets', {})
            key_file = gs_config.get('key_file', gs_config.get('cred_file', 'config/bubble-key.json'))
            key_file = os.path.join(BASE_DIR, key_file)
            
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(key_file, scopes=scope)
            client = gspread.authorize(creds)
            
            sheet_id = gs_config.get('sheet_id', '')
            worksheet_name = gs_config.get('worksheet_name', gs_config.get('sheet_name', 'Sheet1'))
            
            # Определяем, это ID или имя таблицы
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
            st.warning(f"Ошибка Google Sheets: {e}")
    
    # CSV fallback
    csv_path = os.path.join(BASE_DIR, "data", "wb_test_data.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df
    
    # Тестовые данные
    dates = pd.date_range('2026-05-01', periods=14)
    skus = ['111', '222', '333']
    data = []
    for sku in skus:
        for d in dates:
            data.append({
                'date': d,
                'sku': sku,
                'orders': np.random.randint(5, 20),
                'ctr': round(np.random.uniform(1.5, 3.0), 2),
                'cr': round(np.random.uniform(0.8, 1.6), 2),
                'cpc': np.random.randint(10, 25),
                'drr': round(np.random.uniform(8, 15), 2),
                'clicks': np.random.randint(100, 500),
                'buyouts': np.random.randint(5, 18)
            })
    return pd.DataFrame(data)

# ======================== AI АНАЛИТИКА (АВТОНОМНАЯ) =======================
REPORTS_FILE = os.path.join(BASE_DIR, "data", "ai_reports.json")
SCHEDULER_INTERVAL = 3600  # раз в час

def load_reports():
    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_reports(reports):
    os.makedirs(os.path.dirname(REPORTS_FILE), exist_ok=True)
    with open(REPORTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

def generate_ai_report(df, date_range=None):
    if df is None or len(df) == 0:
        return "Нет данных для анализа"
    # Конвертируем Timestamp в строки для JSON сериализации
    df_copy = df.copy()
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
    last_data = df_copy.tail(10).to_dict(orient='records')
    
    # Формируем информацию о периоде
    period_info = ""
    if date_range and len(date_range) >= 2:
        period_info = f"Период анализа: {date_range[0]} - {date_range[1]}\n\n"
    
    prompt = f"""{period_info}Ты — автономный AI-аналитик Wildberries.

Данные (10 последних строк):
{json.dumps(last_data, ensure_ascii=False, indent=2)}

Сделай анализ и рекомендации:
1. ПРОБЛЕМЫ: что не так?
2. РОСТ: где потенциал?
3. ДЕЙСТВИЯ: что конкретно сделать?
Пиши структурировано, по делу."""

    if config.get('openai', {}).get('enabled', False):
        try:
            import openai
            openai.api_key = config['openai']['api_key']
            response = openai.ChatCompletion.create(
                model=config['openai']['model'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка OpenAI: {e}\n\nИспользую заглушку.\n\n" + mock_ai_report(df, date_range)
    else:
        return mock_ai_report(df, date_range)

def mock_ai_report(df, date_range=None):
    problems, growth, actions = [], [], []
    
    # Добавляем период в начало отчета
    report_header = ""
    if date_range and len(date_range) >= 2:
        report_header = f"ПЕРИОД АНАЛИЗА: {date_range[0]} - {date_range[1]}\n\n"
    
    if df is None or len(df) == 0:
        return "Нет данных для анализа"
    
    # Анализ CPC
    if 'cpc' in df.columns:
        avg_cpc = df['cpc'].mean()
        high_cpc_products = df.groupby('product')['cpc'].mean().sort_values(ascending=False)
        top_high_cpc = high_cpc_products.head(3)
        
        if avg_cpc > 20:
            problems.append(f"CPC слишком высокий (средний: {avg_cpc:.1f} ₽)")
            problems.append(f"Топ-3 товара с максимальным CPC:")
            for prod, cpc_val in top_high_cpc.items():
                # Считаем CTR для этого товара
                prod_data = df[df['product'] == prod]
                avg_ctr = prod_data['ctr'].mean() if 'ctr' in df.columns else 0
                avg_cr = prod_data['cr'].mean() if 'cr' in df.columns else 0
                problems.append(f"  • {prod}: {cpc_val:.1f} ₽ (CTR: {avg_ctr:.2f}%, CR: {avg_cr:.2f}%)")
            
            # Ищем причину
            if 'ctr' in df.columns and df['ctr'].mean() < 1.0:
                problems.append("Причина: низкий CTR — креативы не кликабельные")
            if 'cr' in df.columns and df['cr'].mean() < 0.7:
                problems.append("Причина: низкий CR — плохая карточка или высокая цена")
    
    # Анализ CTR
    if 'ctr' in df.columns:
        low_ctr = df.groupby('product')['ctr'].mean().sort_values().head(3)
        if low_ctr.mean() < 1.0:
            problems.append(f"CTR ниже нормы (средний: {df['ctr'].mean():.2f}%)")
            growth.append("Рост: обновить мейн-изображения и заголовки для товаров с низким CTR")
            for prod, ctr_val in low_ctr.items():
                actions.append(f"Обновить креативы для '{prod}' (CTR: {ctr_val:.2f}%)")
    
    # Анализ заказов и выкупов
    if 'buyouts' in df.columns and 'orders' in df.columns:
        df['buyout_rate'] = df['buyouts'] / df['orders'] * 100
        low_buyout = df.groupby('product')['buyout_rate'].mean().sort_values().head(3)
        if low_buyout.mean() < 70:
            problems.append(f"Низкий процент выкупа (средний: {df['buyout_rate'].mean():.1f}%)")
            for prod, rate in low_buyout.items():
                actions.append(f"Улучшить описание и фото для '{prod}' (выкуп: {rate:.1f}%)")
    
    # Рост
    if 'orders' in df.columns:
        growing = df.groupby('product')['orders'].mean().sort_values(ascending=False).head(3)
        growth.append("Топ-3 товара по заказам (потенциал масштабирования):")
        for prod, orders in growing.items():
            growth.append(f"  • {prod}: {orders:.0f} заказов/день")
        growth.append("Рекомендация: увеличить ставки на эти товары при стабильном CR")
    
    # Действия по оптимизации
    if 'cpc' in df.columns and 'orders' in df.columns:
        # Считаем стоимость заказа
        df['cost_per_order'] = df['cpc'] / (df['orders'] / df['clicks']) if 'clicks' in df.columns else df['cpc'] / (df['orders'] / 1000)
        inefficient = df.groupby('product').apply(
            lambda x: x['cpc'].mean() / max(x['orders'].mean(), 1)
        ).sort_values(ascending=False).head(3)
        
        actions.append("Снизить ставки на неэффективные товары (высокая стоимость заказа):")
        for prod, ratio in inefficient.items():
            actions.append(f"  • {prod}: стоимость заказа {ratio:.1f} ₽ (снизить ставку на 20-30%)")
    
    if not problems:
        problems.append("Серьезных проблем не обнаружено")
    if not growth:
        growth.append("Потенциал роста: тестировать новые креативы и расширять семантику")
    if not actions:
        actions.append("Продолжать мониторинг, A/B тестировать креативы")
    
    report = "ПРОБЛЕМЫ:\n"
    for p in problems:
        report += f"- {p}\n"
    report += "\nРОСТ:\n"
    for g in growth:
        report += f"- {g}\n"
    report += "\nДЕЙСТВИЯ:\n"
    for a in actions:
        report += f"- {a}\n"
    return report_header + report

def send_telegram_report(token, chat_id, text):
    """Отправка отчета в Telegram"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get("ok", False)
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False

def run_ai_agent(date_range=None):
    try:
        # Загружаем данные
        df = load_data()
        if df is None or len(df) == 0:
            report_text = "Нет данных для анализа"
        else:
            # Фильтрация по периоду, если указан
            if date_range and len(date_range) >= 2:
                start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            if len(df) == 0:
                report_text = "Нет данных за выбранный период"
            else:
                report_text = generate_ai_report(df, date_range)
        
        report = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": report_text
        }
        reports = load_reports()
        reports.append(report)
        if len(reports) > 20:
            reports = reports[-20:]
        save_reports(reports)
        
        # Отправка в Telegram, если включено
        tg_config = config.get('telegram', {})
        if tg_config.get('enabled', False) and tg_config.get('bot_token') and tg_config.get('chat_id'):
            send_telegram_report(tg_config['bot_token'], tg_config['chat_id'], report_text)
        
        return True
    except Exception as e:
        reports = load_reports()
        reports.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": f"Ошибка генерации отчёта: {e}"
        })
        save_reports(reports)
        return False

def scheduler_loop():
    while True:
        run_ai_agent()
        time.sleep(SCHEDULER_INTERVAL)

# Запуск планировщика (один раз)
scheduler_thread = None
for t in threading.enumerate():
    if t.name == "ai_scheduler":
        scheduler_thread = t
        break
if scheduler_thread is None or not scheduler_thread.is_alive():
    t = threading.Thread(target=scheduler_loop, name="ai_scheduler", daemon=True)
    t.start()

# ======================== СТИЛИ =======================
st.set_page_config(layout="wide", page_title="WB AI Аналитика")

st.markdown("""
<style>
body { background-color: #f5f7fb; }
.kpi-box {
    background: #1f2a44;
    padding: 15px;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 10px;
}
.big-title {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 20px;
}
.block {
    background: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}
.report-box {
    background: #fff3cd;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #ffc107;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ======================== АНАЛИТИКА =======================
def calculate_changes(df, metrics):
    df = df.copy()
    if 'date' in df.columns:
        df = df.sort_values('date')
    
    for m in metrics:
        if m in df.columns:
            df[f'{m}_pct_day'] = df[m].pct_change() * 100
            df[f'{m}_pct_week'] = df[m].pct_change(periods=7) * 100
    
    last = df.iloc[-1] if len(df) > 0 else None
    prev_day = df.iloc[-2] if len(df) > 1 else None
    prev_week = df.iloc[-8] if len(df) > 7 else None
    return df, last, prev_day, prev_week

def detect_anomalies(df, metrics, last_row):
    anomalies = []
    for m in metrics:
        if m not in df.columns or m not in last_row:
            continue
        series = df[m].dropna()
        if len(series) < 3:
            continue
        zscore = (last_row[m] - series.mean()) / series.std()
        if abs(zscore) > ANOMALY_ZSCORE:
            anomalies.append({
                'metric': m,
                'value': round(last_row[m], 2),
                'zscore': round(zscore, 2),
                'direction': '↑ выше нормы' if zscore > 0 else '↓ ниже нормы'
            })
    return anomalies

def find_patterns(df, metrics):
    patterns = []
    if len(df) < 5:
        return patterns
    numeric_df = df[metrics].dropna()
    if len(numeric_df) < 5:
        return patterns
    corr = numeric_df.corr()
    for i, m1 in enumerate(metrics):
        for j, m2 in enumerate(metrics):
            if i >= j:
                continue
            if m1 in corr.columns and m2 in corr.index:
                val = corr.loc[m1, m2]
                if abs(val) > 0.7:
                    patterns.append({
                        'm1': m1,
                        'm2': m2,
                        'corr': round(val, 2),
                        'type': 'сильная связь ↑' if val > 0 else 'обратная связь ↓'
                    })
    return patterns

def generate_report(anomalies, growth, declines, patterns):
    lines = []
    if growth:
        lines.append("**🚀 ВЫРОСЛО:**")
        for g in growth:
            lines.append(f"  • {g['metric']} +{g['change_pct']}% ({g['old_value']:.1f} → {g['new_value']:.1f})")
        lines.append("")
    if declines:
        lines.append("**📉 УПАЛО:**")
        for d in declines:
            lines.append(f"  • {d['metric']} {d['change_pct']}% ({d['old_value']:.1f} → {d['new_value']:.1f})")
        lines.append("")
    if anomalies:
        lines.append("**⚠️ АНОМАЛИИ:**")
        for a in anomalies:
            lines.append(f"  • {a['metric']}: {a['value']} — {a['direction']} (z={a['zscore']})")
        lines.append("")
    if patterns:
        lines.append("**🔗 СВЯЗКИ:**")
        for p in patterns:
            lines.append(f"  • {p['m1']} ↔ {p['m2']}: {p['type']} ({p['corr']})")
        lines.append("")
    lines.append("**💡 РЕКОМЕНДАЦИИ:**")
    if declines:
        lines.append("  • Проверьте карточки товаров, цены, рекламу")
    if anomalies:
        lines.append("  • Проверьте сбои, сезонность, алгоритмы WB")
    if growth:
        lines.append("  • Усильте топ-товары: больше рекламы, сток")
    return "\n".join(lines)

def find_growth_declines(df, metrics, last, prev):
    growth, declines = [], []
    if prev is None:
        return growth, declines
    for m in metrics:
        if m not in df.columns or m not in last or m not in prev:
            continue
        if prev[m] == 0:
            continue
        pct = (last[m] - prev[m]) / prev[m] * 100
        if pct > ANOMALY_PERCENT:
            growth.append({'metric': m, 'change_pct': round(pct, 1), 'new_value': last[m], 'old_value': prev[m]})
        elif pct < -ANOMALY_PERCENT:
            declines.append({'metric': m, 'change_pct': round(pct, 1), 'new_value': last[m], 'old_value': prev[m]})
    return growth, declines

# ======================== ИНТЕРФЕЙС =======================
col_title, col_settings = st.columns([5, 1])
with col_title:
    st.markdown('<div class="big-title">🤖 WB AI Аналитика</div>', unsafe_allow_html=True)
with col_settings:
    if st.button("⚙️ Настройки", use_container_width=True):
        import subprocess, sys, os
        # Используем глобальный BASE_DIR (уже определен в начале файла)
        launcher_path = os.path.join(BASE_DIR, "launcher.py")
        # Используем pythonw из venv для скрытого запуска
        venv_pythonw = os.path.join(BASE_DIR, "venv", "Scripts", "pythonw.exe")
        if not os.path.exists(venv_pythonw):
            venv_pythonw = sys.executable
        try:
            subprocess.Popen([venv_pythonw, launcher_path])
            time.sleep(1)
            os._exit(0)
        except Exception as e:
            st.error(f"Ошибка запуска настроек: {e}")

df_raw = None
try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ Ошибка загрузки данных: {e}")
    df_raw = None

if df_raw is None or df_raw.empty:
    st.warning("⚠️ Данные не загружены. Проверьте настройки Google Sheets или наличие файла wb_test_data.csv")
    st.stop()

metrics = ['orders', 'ctr', 'cr', 'cpc', 'drr', 'clicks', 'buyouts']
available_metrics = [m for m in metrics if m in df_raw.columns]

# Фильтры
colf1, colf2, colf3 = st.columns([2,2,2])
if 'sku' in df_raw.columns:
    sku = colf1.selectbox("Артикул", df_raw["sku"].unique())
else:
    sku = None

if 'date' in df_raw.columns:
    df_raw['date'] = pd.to_datetime(df_raw['date'])
    date_range = colf2.date_input("Период", [df_raw["date"].min(), df_raw["date"].max()])
    # Проверка, что date_range содержит две даты
    if len(date_range) < 2:
        date_range = (df_raw["date"].min(), df_raw["date"].max())
    mask = (df_raw["date"] >= pd.to_datetime(date_range[0])) & (df_raw["date"] <= pd.to_datetime(date_range[1]))
    if sku:
        mask &= (df_raw["sku"] == sku)
    filtered_df = df_raw[mask]
else:
    filtered_df = df_raw

# Аналитика
df_analyzed, last, prev_day, prev_week = calculate_changes(filtered_df, available_metrics)
anomalies = detect_anomalies(df_analyzed, available_metrics, last) if last is not None and not last.empty else []
growth, declines = find_growth_declines(df_analyzed, available_metrics, last, prev_day) if last is not None and prev_day is not None and not last.empty and not prev_day.empty else ([], [])
patterns = find_patterns(filtered_df, available_metrics)
report = generate_report(anomalies, growth, declines, patterns)

# KPI
st.subheader("📈 Ключевые метрики (последний день)")

# Предварительно вычисляем значения
if last is not None and not last.empty:
    orders_val = int(last['orders']) if 'orders' in last.index else 0
    ctr_val = f"{last['ctr']:.2f}%" if 'ctr' in last.index else "N/A"
    cpc_val = f"{last['cpc']:.1f} ₽" if 'cpc' in last.index else "N/A"
    cr_val = f"{last['cr']:.2f}%" if 'cr' in last.index else "N/A"
    drr_val = f"{last['drr']:.1f}%" if 'drr' in last.index else "N/A"
else:
    orders_val = 0
    ctr_val = "N/A"
    cpc_val = "N/A"
    cr_val = "N/A"
    drr_val = "N/A"

k1,k2,k3,k4,k5 = st.columns(5)
with k1:
    st.metric("Заказы", orders_val)
with k2:
    st.metric("CTR", ctr_val)
with k3:
    st.metric("CPC", cpc_val)
with k4:
    st.metric("CR", cr_val)
with k5:
    st.metric("DRR", drr_val)

# Сравнение
st.markdown("---")
st.subheader("📊 Сравнение")
c1,c2 = st.columns(2)
with c1:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.markdown("**Day-to-Day:**")
    if prev_day is not None and last is not None and not prev_day.empty and not last.empty:
        for m in available_metrics[:5]:
            pct = df_analyzed.iloc[-1][f'{m}_pct_day'] if f'{m}_pct_day' in df_analyzed.columns else 0
            st.text(f"  • {m}: {pct:+.1f}%")
    else:
        st.text("Недостаточно данных")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.markdown("**Week-to-Week:**")
    if prev_week is not None and last is not None and not prev_week.empty and not last.empty:
        for m in available_metrics[:5]:
            pct = df_analyzed.iloc[-1][f'{m}_pct_week'] if f'{m}_pct_week' in df_analyzed.columns else 0
            st.text(f"  • {m}: {pct:+.1f}%")
    else:
        st.text("Недостаточно данных (нужно 8+ дней)")
    st.markdown('</div>', unsafe_allow_html=True)

# Отчёт
st.markdown("---")
st.subheader("📝 Структурированный отчёт")
st.markdown('<div class="report-box">', unsafe_allow_html=True)
st.markdown(report)
st.markdown('</div>', unsafe_allow_html=True)

# Графики
st.markdown("---")
st.subheader("📉 Графики")
g1,g2 = st.columns(2)
with g1:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    if 'orders' in filtered_df.columns:
        fig = px.line(filtered_df, x="date", y="orders", title="Заказы", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with g2:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    if 'ctr' in filtered_df.columns and 'cpc' in filtered_df.columns:
        fig = px.line(filtered_df, x="date", y=["ctr", "cpc"], title="CTR и CPC", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Таблица
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("📊 Данные")
st.dataframe(filtered_df.tail(50), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# AI Аналитика
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("🤖 AI Аналитик (автономный)")
reports = load_reports()
if reports:
    for report in reversed(reports[-10:]):
        with st.expander(f"Отчёт от {report['time']}"):
            st.text(report['text'])
else:
    st.info("Отчётов пока нет. Они генерируются автоматически раз в час.")

if st.button("🚀 Запустить AI-анализ сейчас"):
    with st.spinner("Генерация отчёта..."):
        success = run_ai_agent(date_range)
        if success:
            st.success("Отчёт сгенерирован!")
        else:
            st.error("Ошибка генерации")
    st.rerun()

if st.button("📤 Отправить отчет в Telegram"):
    with st.spinner("Отправка..."):
        tg_config = config.get('telegram', {})
        if tg_config.get('enabled', False) and tg_config.get('bot_token') and tg_config.get('chat_id'):
            reports = load_reports()
            if reports:
                last_report = reports[-1]['text']
                if send_telegram_report(tg_config['bot_token'], tg_config['chat_id'], last_report):
                    st.success("Отчет отправлен в Telegram!")
                else:
                    st.error("Ошибка отправки в Telegram")
            else:
                st.warning("Нет сгенерированных отчетов")
        else:
            st.error("Telegram не настроен или не включен")

st.markdown('</div>', unsafe_allow_html=True)

if st.button("🔄 Обновить"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

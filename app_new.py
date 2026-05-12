import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import json
from datetime import datetime, timedelta

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
    st.stop()

ANOMALY_ZSCORE = config.get('anomaly_thresholds', {}).get('zscore', 2.0)
ANOMALY_PERCENT = config.get('anomaly_thresholds', {}).get('percent_change', 30)

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

# ======================== ЗАГРУЗКА ДАННЫХ =======================
@st.cache_data(ttl=300)
def load_data():
    # Google Sheets
    if config.get('google_sheets', {}).get('enabled', False):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            key_file = os.path.join(BASE_DIR, config['google_sheets']['key_file'])
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(key_file, scopes=scope)
            client = gspread.authorize(creds)
            
            sheet_name = config['google_sheets']['sheet_name']
            # Определяем, это ID или имя таблицы
            if '/' in sheet_name or len(sheet_name) > 30:
                sheet = client.open_by_key(sheet_name)
            else:
                sheet = client.open(sheet_name)
            
            worksheet = sheet.worksheet(config['google_sheets']['worksheet_name'])
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            st.warning(f"Ошибка Google Sheets: {e}")
    
    # CSV fallback
    csv_path = os.path.join(BASE_DIR, "data", "test_data.csv")
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
st.markdown('<div class="big-title">🤖 WB AI Аналитика</div>', unsafe_allow_html=True)

df_raw = load_data()
if df_raw is None or df_raw.empty:
    st.error("❌ Данные не загружены")
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
    if prev_day and last:
        for m in available_metrics[:5]:
            pct = df_analyzed.iloc[-1][f'{m}_pct_day'] if f'{m}_pct_day' in df_analyzed.columns else 0
            st.text(f"  • {m}: {pct:+.1f}%")
    else:
        st.text("Недостаточно данных")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.markdown("**Week-to-Week:**")
    if prev_week and last:
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

if st.button("🔄 Обновить"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

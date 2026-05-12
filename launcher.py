import streamlit as st
import os
import json
import subprocess
import sys
import time
from datetime import datetime

st.set_page_config(page_title="WB AI Launcher", page_icon="🚀", layout="centered")

# CSS для выравнивания высоты полей и индикаторов
st.markdown('''
<style>
/* Выравнивание индикаторов по центру высоты поля ввода */
[data-testid="column"]:nth-child(2) {
    display: flex;
    align-items: center;
    padding-top: 28px;
}
</style>
''', unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")
CRED_PATH = os.path.join(BASE_DIR, "config", "bubble-key.json")
DASHBOARD_PORT = 8502
DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

if 'config' not in st.session_state:
    st.session_state.config = load_config()

st.title("🚀 WB AI Аналитика - Настройка")

# Google Sheets Section
st.header("1. Подключение данных (Google)")
st.info("Для работы с Google Таблицами нужен сервисный аккаунт")

# File upload
uploaded_key = st.file_uploader("Загрузите файл ключа (JSON) перетаскиванием или выберите на компьютере", type=['json'])
if uploaded_key is not None:
    key_path = os.path.join(BASE_DIR, "config", "bubble-key.json")
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(uploaded_key.getbuffer())
    st.success(f"✅ Файл {uploaded_key.name} загружен!")
    if 'google_sheets' not in st.session_state.config:
        st.session_state.config['google_sheets'] = {}
    st.session_state.config['google_sheets']['key_file'] = "config/bubble-key.json"

# Fields with indicators
cfg_gs = st.session_state.config.get("google_sheets", {})

col1, col2 = st.columns([3,1])
with col1:
    sheet_id = st.text_input("ID Таблицы Google", placeholder="1wMDIgZgrQt_BBzPkF2ntaBW570olxgQvesjY2h8sjDA")
with col2:
    if sheet_id:
        st.success("✅")
    else:
        st.error("❌")

col1, col2 = st.columns([3,1])
with col1:
    worksheet_name = st.text_input("Имя листа (вкладки)", placeholder="Sheet1")
with col2:
    if worksheet_name:
        st.success("✅")
    else:
        st.error("❌")

# Telegram Section
st.header("2. Telegram (необязательно)")
cfg_tg = st.session_state.config.get("telegram", {})

col1, col2 = st.columns([3,1])
with col1:
    tg_token = st.text_input("Telegram Bot Token", placeholder="123456:ABC-DEF...", type="password")
with col2:
    if tg_token:
        try:
            import requests
            resp = requests.get(f"https://api.telegram.org/bot{tg_token}/getMe", timeout=3)
            if resp.json().get("ok"):
                st.success("✅")
            else:
                st.error("❌")
        except:
            st.warning("?")
    else:
        st.warning("")

col1, col2 = st.columns([3,1])
with col1:
    tg_chat = st.text_input("Telegram Chat ID", placeholder="464488196")
with col2:
    if tg_chat:
        st.success("✅")
    else:
        st.warning("")

# AI Section
st.header("3. AI Аналитика (необязательно)")
cfg_ai = st.session_state.config.get("ai_settings", {})

col1, col2 = st.columns([3,1])
with col1:
    openai_key = st.text_input("OpenAI API Key (для AI-аналитики)", placeholder="sk-...", type="password")
with col2:
    if openai_key:
        st.success("✅")
    else:
        st.warning("")

# Save and Launch Button
if st.button("💾 Сохранить и запустить дашборд", use_container_width=True, type="primary"):
    # Update config
    st.session_state.config['google_sheets'] = {
        "enabled": True,
        "sheet_id": sheet_id,
        "worksheet_name": worksheet_name,
        "key_file": "config/bubble-key.json"
    }
    st.session_state.config['telegram'] = {
        "enabled": bool(tg_token),
        "bot_token": tg_token,
        "chat_id": tg_chat
    }
    st.session_state.config['ai_settings'] = {
        "enabled": bool(openai_key),
        "api_key": openai_key
    }
    save_config(st.session_state.config)
    st.success("✅ Настройки сохранены!")

st.markdown('</div>', unsafe_allow_html=True)

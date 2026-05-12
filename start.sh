#!/bin/bash
echo "============================================"
echo "WB AI Analytics - Launcher"
echo "============================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 не установлен."
    echo "Установите Python: sudo apt install python3 python3-venv (Linux) или brew install python (Mac)"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Создание venv
if [ ! -d "venv" ]; then
    echo "[INFO] Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Установка зависимостей
echo "[INFO] Установка библиотек..."
source venv/bin/activate
pip install -r requirements.txt

# Запуск
echo "[INFO] Запуск мастера настройки..."
open http://localhost:8501 2>/dev/null || xdg-open http://localhost:8501 2>/dev/null
streamlit run launcher.py --server.port 8501

read -p "Нажмите Enter для выхода..."

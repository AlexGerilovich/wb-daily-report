#!/bin/bash
echo "=== Запуск WB AI Dashboard ==="
echo ""

# Активация venv
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Виртуальное окружение не найдено! Запустите сначала install.sh"
    exit 1
fi

source venv/bin/activate

# Загрузка порта из конфига
PORT=$(python3 -c "import json; print(json.load(open('config/config.json'))['dashboard']['port'])" 2>/dev/null || echo "8502")

echo "🚀 Запуск дашборда на порту $PORT..."
echo "Откройте в браузере: http://localhost:$PORT"
echo ""

streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0

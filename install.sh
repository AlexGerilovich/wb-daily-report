#!/bin/bash
echo "=== WB AI System - Установка (Linux/Mac) ==="
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден! Установите Python 3.8+ и попробуйте снова."
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"
echo ""

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка создания venv"
        exit 1
    fi
fi

# Активация и установка зависимостей
echo "📥 Установка зависимостей..."
source venv/bin/activate
pip install -r requirements.txt -q

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Установка завершена успешно!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Отредактируйте config/config.json (впишите ключи)"
    echo "2. Запустите дашборд: bash run.sh"
else
    echo "❌ Ошибка установки зависимостей"
    exit 1
fi

# WB AI System - Аналитика Wildberries

Готовое приложение для аналитики магазина на Wildberries с дашбордом и автоматическими отчётами в Telegram.

## Быстрый старт

### 1. Установка
```bash
# Windows:
install.bat

# Linux/Mac:
bash install.sh
```

### 2. Настройка
Отредактируйте файл `config/config.json`, вписав ваши ключи:
- **Telegram Bot Token** (от @BotFather)
- **Telegram Chat ID** (ваш ID от @userinfobot)
- **Google Sheets** (если используете) - положите `wb-creds.json` в папку `config/`

### 3. Запуск
```bash
# Windows:
run.bat

# Linux/Mac:
bash run.sh
```

Дашборд откроется по адресу: http://localhost:8502

## Что делает система

✅ Загружает данные (из Google Sheets или CSV)  
✅ Сравнивает показатели день-к-дню и неделя-к-неделе  
✅ Выявляет аномалии (CTR, CR, CPC, DRR...)  
✅ Находит связки и закономерности  
✅ Формирует структурированный отчёт с рекомендациями  
✅ Отправляет отчёты в Telegram (при настройке)

## Структура

```
wb_ai_system/
├── config/
│   ├── config.json      # Ключи и настройки (ЗАПОЛНИТЕ!)
│   └── wb-creds.json   # Ключ Google Sheets (опционально)
├── data/
│   └── test_data.csv   # Тестовые данные
├── scripts/
│   └── wb_ai_main.py  # Основной скрипт для cron/автозапуска
├── app.py              # Дашборд Streamlit
├── requirements.txt    # Зависимости
├── install.sh          # Установка (Linux/Mac)
├── install.bat         # Установка (Windows)
├── run.sh              # Запуск (Linux/Mac)
├── run.bat             # Запуск (Windows)
└── README.md           # Этот файл
```

## Подготовка данных

### Вариант 1: Google Sheets
1. Создайте таблицу с колонками: `date, sku, orders, ctr, cr, cpc, drr, clicks, buyouts`
2. Создайте сервисный аккаунт Google (инструкция: https://gspread.readthedocs.io/)
3. Скачайте JSON-ключ, переименуйте в `wb-creds.json`, положите в `config/`
4. Откройте доступ к таблице для email из JSON-ключа

### Вариант 2: CSV файл
Просто отредактируйте `data/test_data.csv` или положите свой CSV в папку `data/`

## Автоматические отчёты

Для ежедневных отчётов в Telegram добавьте в cron (Linux/Mac):
```bash
crontab -e
# Добавьте строку (отправка каждый день в 09:00):
0 9 * * * cd /path/to/wb_ai_system && venv/bin/python scripts/wb_ai_main.py
```

Windows: используйте Планировщик задач.

## Техподдержка

При ошибках проверьте:
1. Заполнен ли `config/config.json`
2. Установлен ли Python 3.8+
3. Есть ли доступ к интернету (для Telegram API)

---
Версия: 1.0 | Сделано для WB аналитики

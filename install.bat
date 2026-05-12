@echo off
echo === WB AI System - Установка (Windows) ===
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+ и попробуйте снова.
    exit /b 1
)

echo ✅ Python найден
echo.

REM Создание виртуального окружения
if not exist "venv" (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Ошибка создания venv
        exit /b 1
    )
)

REM Активация и установка зависимостей
echo 📥 Установка зависимостей...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    exit /b 1
)

echo.
echo ✅ Установка завершена успешно!
echo.
echo Следующие шаги:
echo 1. Отредактируйте config/config.json (впишите ключи)
echo 2. Запустите дашборд: run.bat

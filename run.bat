@echo off
echo === Запуск WB AI Dashboard ===
echo.

REM Активация venv
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Виртуальное окружение не найдено! Запустите сначала install.bat
    exit /b 1
)

call venv\Scripts\activate.bat

REM Чтение порта из конфига (упрощенно)
set PORT=8502

echo 🚀 Запуск дашборда на порту %PORT%...
echo Откройте в браузере: http://localhost:%PORT%
echo.

streamlit run app.py --server.port %PORT% --server.headless true --server.address 0.0.0.0

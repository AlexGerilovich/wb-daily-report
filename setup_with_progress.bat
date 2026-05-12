@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo WB AI System - Установка зависимостей
echo ========================================
echo.

set /a total_steps=4
set /a current_step=0

:: Step 1: Check Python
set /a current_step+=1
call :show_progress "Проверка Python" %current_step% %total_steps%
python --version >nul 2>&1
if errorlevel 1 (
    echo Установка Python через winget...
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%
    timeout /t 5 /nobreak >nul
) else (
    echo Python уже установлен
)
call :step_done

:: Step 2: Create venv
set /a current_step+=1
call :show_progress "Создание виртуального окружения" %current_step% %total_steps%
if not exist "venv" (
    python -m venv venv
    echo Виртуальное окружение создано
) else (
    echo Виртуальное окружение уже существует
)
call :step_done

:: Step 3: Install requirements
set /a current_step+=1
call :show_progress "Установка зависимостей (pip install)" %current_step% %total_steps%
if exist "venv\Scripts\pip.exe" (
    venv\Scripts\pip.exe install -r requirements.txt -q
    echo Зависимости установлены
) else (
    echo Ошибка: pip не найден
    exit 1
)
call :step_done

:: Step 4: Ready
set /a current_step+=1
call :show_progress "Готово!" %current_step% %total_steps%
echo.
echo ========================================
echo Установка завершена успешно!
echo Теперь запустится дашборд...
echo ========================================
call :step_done

timeout /t 2 /nobreak >nul
exit /b 0

:show_progress
set "step_name=%~1"
set /a step_num=%2
set /a total=%3
set /a percent=(step_num * 100) / total

cls
echo ========================================
echo WB AI System - Установка
echo ========================================
echo.
echo Шаг %step_num% из %total%: %step_name%
echo.
echo Прогресс: [
set /a filled=(percent * 40) / 100
set /a empty=40 - filled
set "bar="
for /L %%i in (1,1,%filled%) do set "bar=!bar!="
for /L %%i in (1,1,%empty%) do set "bar=!bar! "
echo !bar!] %percent%%
echo.
goto :eof

:step_done
echo ✓ Выполнено
echo.
goto :eof

@echo off
echo DataQuery Pro Backend - Корпоративная конфигурация
echo IP: 172.28.80.18 | Порт: 1555
echo ================================================

REM Проверяем, активировано ли виртуальное окружение
if not exist "venv\Scripts\activate.bat" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo Установка/обновление зависимостей...
pip install -r requirements.txt

REM Проверяем наличие .env файла
if not exist ".env" (
    echo Создание .env файла из корпоративного шаблона...
    copy env_example.txt .env
    echo.
    echo ВНИМАНИЕ: Настройте параметры Oracle в файле .env
    echo Затем запустите скрипт снова
    echo.
    pause
    exit /b 1
)

echo.
echo Тестирование подключения к Oracle...
python test_connection.py
if errorlevel 1 (
    echo.
    echo Ошибка подключения к базе данных!
    echo Проверьте настройки в .env файле
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🚀 Запуск FastAPI сервера...
echo ========================================
echo 📊 API документация: http://172.28.80.18:1555/docs
echo 🔧 Health check: http://172.28.80.18:1555/health
echo 📋 ReDoc: http://172.28.80.18:1555/redoc
echo.
echo Для остановки сервера нажмите Ctrl+C
echo ========================================

REM Явно указываем IP и порт для корпоративной среды
set APP_HOST=172.28.80.18
set APP_PORT=1555

python main.py

echo.
echo Сервер остановлен
pause 
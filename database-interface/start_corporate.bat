@echo off
echo DataQuery Pro Frontend - Корпоративная конфигурация
echo Backend: http://172.28.80.18:1555
echo ================================================

REM Проверяем наличие node_modules
if not exist "node_modules" (
    echo Установка зависимостей...
    npm install
)

REM Настройка корпоративного .env файла
if not exist ".env" (
    echo Создание .env файла для корпоративной среды...
    copy env.production .env
    echo ✅ Настройки созданы: Backend URL = http://172.28.80.18:1555
)

echo.
echo Проверка подключения к backend...
curl -s http://172.28.80.18:1555/health > nul
if errorlevel 1 (
    echo ⚠️  ВНИМАНИЕ: Backend недоступен на http://172.28.80.18:1555
    echo    Убедитесь, что backend запущен перед использованием фронтенда
    echo.
) else (
    echo ✅ Backend доступен на http://172.28.80.18:1555
    echo.
)

echo ========================================
echo 🚀 Запуск React фронтенда...
echo ========================================
echo 🌐 Веб-интерфейс: http://localhost:3000
echo 📡 Backend API: http://172.28.80.18:1555
echo.
echo Для остановки нажмите Ctrl+C
echo ========================================

npm start 
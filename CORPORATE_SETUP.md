# 🏢 DataQuery Pro - Корпоративная конфигурация

## 🔧 Настройка для корпоративной среды

### Конфигурация портов:
- **Backend**: `172.28.80.18:1555`
- **Frontend**: `localhost:3000` (стандартный React порт)

## 🚀 Быстрый запуск

### 1. Запуск Backend (Terminal 1)
```bash
cd database-backend
start_corporate.bat
```

### 2. Запуск Frontend (Terminal 2)  
```bash
cd database-interface
start_corporate.bat
```

## 📊 URL-адреса после запуска

### Backend API:
- **API документация**: http://172.28.80.18:1555/docs
- **Health check**: http://172.28.80.18:1555/health
- **ReDoc документация**: http://172.28.80.18:1555/redoc

### Frontend:
- **Веб-интерфейс**: http://localhost:3000
- **Подключается к**: http://172.28.80.18:1555

## ⚙️ Ручная настройка (если нужно)

### Backend (.env в database-backend/):
```env
# Oracle Database
ORACLE_HOST=your-oracle-server.company.com
ORACLE_PORT=1521
ORACLE_SID=PROD
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password

# Application Configuration
APP_HOST=172.28.80.18
APP_PORT=1555

# CORS для фронтенда
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend (.env в database-interface/):
```env
REACT_APP_API_URL=http://172.28.80.18:1555
```

## 🧪 Тестирование интеграции

### 1. Проверка Backend:
```bash
curl http://172.28.80.18:1555/health
# Ответ: {"status": "healthy", "timestamp": "..."}
```

### 2. Проверка API:
```bash
curl http://172.28.80.18:1555/databases
# Ответ: [{"id": "dssb_app", "name": "...", ...}]
```

### 3. Проверка Frontend:
- Откройте http://localhost:3000
- Dashboard должен загрузить статистику с backend
- Конструктор запросов должен показать базы данных

## 🛡️ Безопасность в корпоративной среде

### Firewall настройки:
- Разрешить входящие соединения на порт **1555** для IP **172.28.80.18**
- Разрешить исходящие соединения к Oracle серверу на порт **1521**

### Network Access:
- Backend доступен по IP **172.28.80.18:1555**
- Frontend доступен только локально на **localhost:3000**
- CORS настроен для безопасного взаимодействия

## 🔍 Troubleshooting

### Порт 1555 занят:
```bash
netstat -an | findstr :1555
```
Если порт занят, выберите другой свободный порт и обновите настройки.

### Backend недоступен:
1. Проверьте запущен ли process на порту 1555
2. Проверьте firewall settings
3. Убедитесь что IP 172.28.80.18 доступен

### Frontend не подключается:
1. Проверьте файл `.env` в database-interface
2. Убедитесь что CORS настроен корректно в backend
3. Проверьте network connectivity

## 📞 Поддержка

**Backend logs**: Проверьте вывод в терминале где запущен backend
**Frontend console**: F12 → Console в браузере
**Network issues**: Обратитесь к сетевому администратору 
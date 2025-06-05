# 🚀 DataQuery Pro Backend - Быстрый старт

## Минимальная настройка для запуска

### 1. Настройка переменных окружения
```bash
# Скопируйте пример настроек
copy env_example.txt .env

# Отредактируйте .env файл с вашими данными Oracle:
ORACLE_HOST=your-oracle-server.company.com
ORACLE_PORT=1521
ORACLE_SID=PROD
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
```

### 2. Установка зависимостей
```bash
# Windows - двойной клик на файл:
start_server.bat

# Или вручную:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Тестирование подключения
```bash
python test_connection.py
```

### 4. Запуск сервера
```bash
python main.py
```

## 📖 После запуска

- **API документация**: http://172.28.80.18:1555/docs
- **Альтернативная документация**: http://172.28.80.18:1555/redoc
- **Проверка здоровья**: http://172.28.80.18:1555/health

## 🔧 Настройка фронтенда

В фронтенд проекте создайте файл `.env` с настройками:

```bash
# Скопируйте в корень database-interface
copy env.production .env
```

Или укажите URL вручную в (`database-interface/src/services/api.js`):

```javascript
const API_BASE_URL = 'http://172.28.80.18:1555';
```

## 🗃 Доступные таблицы

Backend предоставляет доступ к этим таблицам:
- `employees` - Сотрудники
- `customers` - Клиенты  
- `orders` - Заказы
- `products` - Продукты
- `sales` - Продажи

## 🆘 Проблемы?

1. **cx_Oracle ошибки**: Установите Oracle Instant Client
2. **Подключение не работает**: Проверьте настройки в `.env`
3. **CORS ошибки**: Добавьте URL фронтенда в `ALLOWED_ORIGINS`

**Полная документация**: [README.md](README.md) 
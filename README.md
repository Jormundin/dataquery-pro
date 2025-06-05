# 🏢 DataQuery Pro - Корпоративный интерфейс для Oracle Database

Современный веб-интерфейс для работы с корпоративными базами данных Oracle без необходимости знания SQL.

## 📋 Обзор проекта

DataQuery Pro позволяет пользователям без технических навыков легко взаимодействовать с корпоративными базами данных через интуитивный визуальный интерфейс.

### ✨ Основные возможности

- 🎯 **Визуальный конструктор запросов** - создание запросов без написания SQL
- 📊 **Панель управления** - статистика и мониторинг активности
- 👀 **Просмотр данных** - пагинация, поиск, сортировка, экспорт
- ⚙️ **Настройки системы** - конфигурация подключений и пользовательских предпочтений
- 🔢 **Подсчет строк** - мгновенная оценка размера выборки
- 🌐 **Русский интерфейс** - полная локализация

## 🏗️ Архитектура

```
DataQuery Pro/
├── 🖥️ database-interface/     # React Frontend
│   ├── src/
│   │   ├── components/        # Переиспользуемые компоненты
│   │   ├── pages/            # Страницы приложения
│   │   └── services/         # API клиенты
│   └── package.json
├── 🚀 database-backend/       # FastAPI Backend
│   ├── main.py              # Основное приложение
│   ├── models.py            # Pydantic модели
│   ├── database.py          # Логика работы с БД
│   ├── query_builder.py     # Безопасное построение SQL
│   └── requirements.txt
└── README.md
```

## 🚀 Быстрый старт

### Предварительные требования

- **Python 3.8+** для бэкенда
- **Node.js 16+** для фронтенда
- **Oracle Database** (доступ к серверу)
- **Git** для клонирования репозитория

### 1️⃣ Клонирование репозитория

```bash
git clone <repository-url>
cd DataQuery-Pro
```

### 2️⃣ Настройка бэкенда

```bash
cd database-backend

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл с вашими настройками Oracle

# Запуск сервера
python main.py
```

Бэкенд будет доступен по адресу: http://localhost:8000

### 3️⃣ Настройка фронтенда

```bash
cd database-interface

# Установка зависимостей
npm install

# Запуск в режиме разработки
npm start
```

Фронтенд будет доступен по адресу: http://localhost:3000

## ⚙️ Конфигурация

### Переменные окружения бэкенда (.env)

```env
# Oracle Database
ORACLE_HOST=your-oracle-host
ORACLE_PORT=1521
ORACLE_SID=your-sid
ORACLE_USER=your-username
ORACLE_PASSWORD=your-password

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000

# Security
SECRET_KEY=your-secret-key
```

### Переменные окружения фронтенда

```env
REACT_APP_API_URL=http://localhost:8000
```

## 🛡️ Безопасность

- ✅ SQL-инъекции предотвращены через параметризованные запросы
- ✅ Валидация всех пользовательских входных данных
- ✅ Ограничение доступа к таблицам через whitelist
- ✅ Санитизация идентификаторов SQL
- ✅ CORS настроен для разрешенных доменов

## 📊 API Документация

FastAPI автоматически генерирует интерактивную документацию:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты

```
GET  /databases                    # Список баз данных
GET  /databases/{id}/tables        # Таблицы БД
GET  /databases/{id}/tables/{name}/columns  # Столбцы таблицы
POST /query/execute               # Выполнение запроса
POST /query/count                 # Подсчет строк
GET  /query/history               # История запросов
```

## 🔧 Разработка

### Структура компонентов React

```
src/
├── components/
│   └── Layout.js              # Основной макет с навигацией
├── pages/
│   ├── Dashboard.js           # Панель управления
│   ├── QueryBuilder.js        # Конструктор запросов
│   ├── DataViewer.js          # Просмотр данных
│   └── Settings.js            # Настройки
└── services/
    └── api.js                 # API клиенты
```

### Добавление новых таблиц

Отредактируйте `database-backend/database.py`:

```python
ALLOWED_TABLES = {
    "YOUR_DB": {
        "YOUR_TABLE": {
            "description": "Описание таблицы",
            "columns": [
                {"name": "ID", "type": "NUMBER", "description": "Идентификатор"},
                # ... другие столбцы
            ]
        }
    }
}
```

## 🐛 Отладка

### Логи бэкенда

```bash
# Включить подробные логи
uvicorn main:app --reload --log-level debug
```

### Логи фронтенда

- Откройте DevTools браузера (F12)
- Проверьте консоль на ошибки JavaScript
- Вкладка Network для отладки API запросов

## 📦 Развертывание

### Production сборка фронтенда

```bash
cd database-interface
npm run build
```

### Production запуск бэкенда

```bash
cd database-backend
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker (опционально)

Создайте Dockerfile для каждого сервиса или используйте docker-compose для оркестрации.

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

- 📧 Email: support@dataquery-pro.com
- 📖 Документация: [docs.dataquery-pro.com]
- 🐛 Баг-репорты: [GitHub Issues]

---

**DataQuery Pro** - Делаем работу с корпоративными данными простой и доступной! 🚀 
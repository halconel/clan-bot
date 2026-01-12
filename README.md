# Clan Registration Bot

Telegram бот для управления регистрацией и учетом участников клана.

## Возможности

- 📝 Регистрация новых участников через бот
- 📸 Загрузка скриншотов профиля
- ✅ Одобрение/отклонение заявок администратором
- 👥 Просмотр списка всех участников
- 🚫 Отчисление участников с указанием причины
- 💾 Хранение данных в PostgreSQL
- 🔄 Database миграции через Alembic

## Технологический стек

- **Python 3.10+**
- **aiogram 3.3** - асинхронный фреймворк для Telegram ботов
- **SQLAlchemy 2.0** - ORM для работы с базой данных
- **PostgreSQL** - основная база данных
- **Alembic** - миграции базы данных
- **UV** - современный менеджер пакетов Python
- **pytest** - фреймворк для тестирования

## Установка

### 1. Клонировать репозиторий

```bash
git clone <repository-url>
cd clan-bot
```

### 2. Установить UV (если еще не установлен)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Установить зависимости

```bash
uv sync
```

### 4. Настроить переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите свои данные:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
LEADER_TELEGRAM_ID=your_telegram_id

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/clan_bot

# Storage Configuration
SCREENSHOTS_DIR=data/screenshots
TEMP_STORAGE_FILE=data/pending.json

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

### 5. Создать базу данных PostgreSQL

```bash
# Подключитесь к PostgreSQL
psql -U postgres

# Создайте базу данных
CREATE DATABASE clan_bot;

# Создайте пользователя (опционально)
CREATE USER clan_bot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE clan_bot TO clan_bot_user;
```

### 6. Применить миграции

```bash
uv run alembic upgrade head
```

## Запуск

### Режим разработки

```bash
uv run python main.py
```

### Режим production

Рекомендуется использовать process manager, например systemd или supervisor.

Пример systemd service (`/etc/systemd/system/clan-bot.service`):

```ini
[Unit]
Description=Clan Registration Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/clan-bot
Environment="PATH=/path/to/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/path/to/.local/bin/uv run python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl enable clan-bot
sudo systemctl start clan-bot
sudo systemctl status clan-bot
```

## Команды бота

### Для игроков:

- `/start` - Начать работу с ботом
- `/register` - Зарегистрироваться в клане
- `/help` - Показать справку

### Для администраторов:

- `/pending` - Показать ожидающие заявки
- `/list` - Показать список всех игроков
- `/exclude @username причина` - Отчислить игрока из клана

## Тестирование

### Запуск тестов

```bash
# Все тесты
uv run pytest

# С покрытием
uv run pytest --cov=. --cov-report=html

# Конкретный файл
uv run pytest tests/test_database.py -v
```

### Текущее покрытие

- **Общее покрытие: 74%**
- database/database.py: 84%
- database/models.py: 95%
- database/repository.py: 74%

## Архитектура

```
clan-bot/
├── alembic/              # Database migrations
│   └── versions/         # Migration files
├── bot/
│   ├── handlers/         # Message and callback handlers
│   │   ├── admin.py      # Admin commands
│   │   ├── common.py     # Common commands (start, help)
│   │   └── registration.py  # Registration flow
│   ├── keyboards/        # Inline keyboards
│   │   └── admin.py      # Admin keyboards
│   └── states/           # FSM states
│       └── registration.py  # Registration states
├── config/               # Configuration
│   ├── database.py       # Database config
│   └── settings.py       # Main settings
├── database/             # Database layer
│   ├── database.py       # Database manager (DI)
│   ├── models.py         # SQLAlchemy models
│   └── repository.py     # Repository pattern
├── models/               # Domain models (dataclasses)
│   └── player.py         # Player and PendingRegistration
├── tests/                # Tests
│   ├── test_database.py  # Database tests
│   ├── test_repository.py  # Repository tests
│   └── test_validators.py  # Validator tests
├── utils/                # Utilities
│   ├── formatters.py     # Text formatters
│   └── validators.py     # Input validators
├── main.py               # Entry point
└── pyproject.toml        # Project dependencies
```

## Dependency Injection

Проект использует Dependency Injection для улучшения тестируемости:

- `Database` класс инкапсулирует соединение с БД
- `Settings` загружаются динамически, без глобального состояния
- `Repository` принимает `session` через конструктор

Пример использования:

```python
from config.settings import load_settings
from database.database import create_database
from database.repository import PlayerRepository

# Load settings
settings = load_settings()

# Create database instance
db = create_database(settings.database.database_url)

# Use in async context
async for session in db.get_session():
    repo = PlayerRepository(session)
    players = await repo.get_all_players()
```

## Разработка

### Линтинг и форматирование

```bash
# Ruff linting
uv run ruff check .

# Ruff formatting
uv run ruff format .

# MyPy type checking
uv run mypy .
```

### Создание новой миграции

```bash
# Auto-generate migration
uv run alembic revision --autogenerate -m "Description"

# Create empty migration
uv run alembic revision -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

## Deployment на Railway.app

1. Создайте проект на [Railway.app](https://railway.app/)
2. Добавьте PostgreSQL сервис
3. Установите переменные окружения:
   - `BOT_TOKEN`
   - `LEADER_TELEGRAM_ID`
   - `DATABASE_URL` (автоматически из PostgreSQL)
4. Запустите деплой

Railway автоматически применит миграции при старте.

## Лицензия

MIT

## Автор

Dmitriy Vinogradov
